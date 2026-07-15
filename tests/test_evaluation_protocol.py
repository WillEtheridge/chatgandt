import copy
import atexit
from collections import Counter
import hashlib
from importlib.metadata import version as package_version
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import torch

from jsonschema import Draft202012Validator, FormatChecker

from chatgnt.evaluation_protocol import (
    INTENT_FAMILIES,
    WITHHELD_DOMAINS,
    accepted_audit_ids,
    build_evaluation_generation_manifest,
    build_judgment_packets,
    canonical_records_sha256,
    cosine_similarity,
    evaluation_run_configuration_sha256,
    evaluation_run_records_from_harness,
    evaluation_system_configuration,
    compute_stage5_semantic_retrieval,
    heldout_authoring_schedule,
    lexical_neighbours,
    lexical_score,
    load_protocol,
    merge_neighbours,
    metadata_neighbours,
    normalize_text,
    normative_protocol_value,
    generate_response_similarity_semantic_evidence,
    generate_stage5_semantic_evidence,
    paired_bootstrap_interval,
    pairwise_order_schedule,
    pair_packet_id,
    protocol_normative_sha256,
    qualitative_packet_id,
    render_pairwise_response,
    render_pairwise_packet,
    render_qualitative_packet,
    response_similarity_text_view,
    select_human_pair_calibration,
    select_human_response_calibration,
    semantic_collision_decision,
    semantic_neighbours,
    text_identity,
    tokenization_diagnostics,
    validate_calibration_records,
    validate_heldout_records,
    validate_judge_calibration,
    validate_judge_manifest,
    validate_judgment_records,
    validate_protocol_value,
    validate_freeze_transition,
    validate_protocol_manifest,
    validate_response_similarity_calibration,
    validate_response_similarity_records,
    validate_stage5_freeze_bundle,
    validate_stage3_verification_evidence,
    withheld_domain_evidence_sha256,
    wilson_interval,
    weighted_cohens_kappa,
)
from chatgnt.configuration import CONFIG_ROOT, PROJECT_ROOT, PromptAsset, SystemDefinition
from chatgnt.harness import execute_run
from chatgnt.records import ContractError, GenerationResult, canonical_json
from chatgnt.records import canonical_line, read_strict_json
from chatgnt.identity import execution_order_seed, schedule_attempts, tree_digest
from chatgnt.prompting import validate_five_shot_prompt_v3
from scripts.capture_stage3_verification import (
    COMMANDS as STAGE3_CAPTURE_COMMANDS,
    _AUTHORIZATION_GUARD,
    _LiveGateAuthorization,
    run_gate,
)
from scripts.orchestrate_stage3_review import orchestrate


def deterministic_test_embedder(texts, model_id, revision, device="cpu"):
    """Fast deterministic stand-in at the canonical embedding boundary."""

    del model_id, revision, device
    vectors, diagnostics = [], []
    for text in texts:
        digest = hashlib.sha256(text.encode()).digest()
        vector = [(digest[index] - 127.5) / 127.5 for index in range(16)]
        vectors.append(vector)
        count = max(1, len(text.split()))
        diagnostics.append({
            "pre_truncation_wordpieces": count,
            "semantic_input_truncated": count > 256,
        })
    return vectors, diagnostics


def frozen_manifest_test_result():
    value, raw = read_strict_json(Path("config/evaluation-protocol-manifest-v1.json"))
    return {
        "result": "pass", "asset_count": len(value["assets"]),
        "aggregate_sha256": value["aggregate_sha256"],
        "protocol_normative_sha256": value["protocol_normative_sha256"],
        "manifest_sha256": hashlib.sha256(raw).hexdigest(),
    }


def rewrite_semantic_stdout(artifact, kind, records_key):
    records = artifact[records_key]
    stdout = canonical_json({
        "generator": "chatgnt-semantic-evidence-v1", "kind": kind,
        "model_id": "sentence-transformers/all-MiniLM-L6-v2",
        "model_revision": "1110a243fdf4706b3f48f1d95db1a4f5529b4d41",
        "record_count": len(records), "records_sha256": canonical_records_sha256(records),
        "result": "pass",
    })
    artifact["verifier_stdout"] = stdout
    artifact["verifier_stdout_sha256"] = hashlib.sha256(stdout.encode()).hexdigest()


def heldout_records():
    records = []
    input_forms = ["question"] * 15 + ["direct_request_or_command"] * 30 + ["statement_or_fragment"] * 15
    index = 0
    roles = ("format_pressure", "behaviour_pressure", "serialization_pressure")
    for family_index, family in enumerate(INTENT_FAMILIES):
        for within in range(12):
            if within < 6:
                reporting_slice = "target_use"
                robustness_role = None
                withheld_domain = None
            elif within < 9:
                reporting_slice = "cross_domain"
                robustness_role = None
                withheld_domain = WITHHELD_DOMAINS[within - 6]
            else:
                reporting_slice = "robustness"
                robustness_role = roles[within - 9]
                withheld_domain = None
            constraint = within in (0, 11)
            composed = within == 0 or within >= 9
            complexity_sources = []
            if within == 0:
                complexity_sources.append("ordinary_content_constraint")
            if within >= 9:
                complexity_sources.append("robustness_pressure")
            if within == 11:
                complexity_sources.extend(["supplied_content", "ordinary_content_constraint"])
            records.append(
                {
                    "record_schema_version": 1,
                    "prompt_id": f"heldout-v1-{index + 1:03d}",
                    "prompt": f"Unique protocol test prompt {index + 1}",
                    "authored_at_utc":"2026-07-15T14:00:00Z",
                    "intent_family": family,
                    "reporting_slice": reporting_slice,
                    "input_form": input_forms[index],
                    "complexity": "composed" if composed else "standard",
                    "complexity_sources": complexity_sources,
                    "constraint_bearing": constraint,
                    "robustness_role": robustness_role,
                    "withheld_domain": withheld_domain,
                    "topic": f"topic {family_index} {within}",
                    "user_goal": f"goal {family_index} {within}",
                    "requested_task_or_artefact": f"task {family_index} {within}",
                    "scenario_summary": f"scenario {family_index} {within}",
                    "important_constraints": ["brief"] if constraint else [],
                }
            )
            index += 1
    return records


def stage5_evidence(selection_only=False):
    heldout = heldout_records()
    audits = set(accepted_audit_ids([item["prompt_id"] for item in heldout]))
    digest = "0" * 64
    searched_source_ids = [
        "source-v1-worked_examples", "source-v1-prompt_development",
        "source-v1-evaluation_calibration", "source-v1-training", "source-v1-validation",
        "source-v1-accepted_heldout_candidates", "source-v1-rejected_heldout_candidates",
    ]

    metadata = {field:"shared" for field in ("topic","user_goal","requested_task_or_artefact","scenario_summary")}
    metadata["important_constraints"] = []
    rejected_prompt="Selection-only candidate outside the declared scope." if selection_only else "Duplicated training prompt."
    replacements = [{"record_schema_version":1,"replacement_record_id":"replace-v1-001","matrix_prompt_id":"heldout-v1-001",
        "candidate_id":"rejected-001","candidate_prompt":rejected_prompt,
        "candidate_metadata":{key:value for key,value in heldout[0].items() if key not in {"record_schema_version","prompt_id","prompt","authored_at_utc"}},
        "original_sha256":text_identity(rejected_prompt)["original_sha256"],
        "normalized_sha256":text_identity(rejected_prompt)["normalized_sha256"],"reason":"scope_or_answerability" if selection_only else "exact_collision",
        "rationale":"Outside the declared scope." if selection_only else "Exact training collision.","source_identity_ids":[],"retrieved_reference_ids":[],
        "retrieval_report_sha256":None if selection_only else digest,"review_ids":[],"replacement_status":"replaced",
        "replacement_candidate_id":"heldout-v1-001","author_identity":"author-1","decision_identity":"audit-agent",
        "recorded_at_utc":"2026-07-15T14:00:00Z"}]
    schedule = heldout_authoring_schedule(heldout, replacements)
    schedule_by_candidate = {item["candidate_id"]:item for item in schedule}
    source_records = {}
    for source_id in searched_source_ids[:5]:
        collection = source_id.removeprefix("source-v1-")
        source_records[source_id] = [
            {"record_id":f"{collection}-{index:03d}",
             "text":"Duplicated training prompt." if not selection_only and collection == "training" and index == 1 else f"Frozen {collection} source text {index}.",
             "metadata":copy.deepcopy(metadata)} for index in (1, 2)
        ]
    source_records["source-v1-accepted_heldout_candidates"] = [
        {"record_id":item["prompt_id"],"text":item["prompt"],
         "metadata":{field:item[field] for field in ("topic","user_goal","requested_task_or_artefact","scenario_summary","important_constraints")}}
        for item in heldout
    ]
    source_records["source-v1-rejected_heldout_candidates"] = [
        {"record_id":"rejected-001","text":rejected_prompt,
         "metadata":{field:copy.deepcopy(replacements[0]["candidate_metadata"][field]) for field in ("topic","user_goal","requested_task_or_artefact","scenario_summary","important_constraints")}}
    ]
    collections = ["worked_examples","prompt_development","evaluation_calibration","training","validation","accepted_heldout_candidates","rejected_heldout_candidates"]
    sources = [{"record_schema_version":1,"source_identity_id":f"source-v1-{collection}","collection":collection,
        "version_id":f"{collection}-v1","record_count":len(source_records[f"source-v1-{collection}"]),
        "content_sha256":canonical_records_sha256(source_records[f"source-v1-{collection}"]),
        "frozen":True,"frozen_at_utc":"2026-07-15T14:00:00Z"} for collection in collections]
    source_by_id = {item["source_identity_id"]:item for item in sources}

    def eligible(candidate_id, source_id):
        records = source_records[source_id]
        collection = source_by_id[source_id]["collection"]
        if collection not in {"accepted_heldout_candidates","rejected_heldout_candidates"}:
            return records
        current = schedule_by_candidate[candidate_id]["authoring_index"]
        wanted_final = collection == "accepted_heldout_candidates"
        allowed = {item["candidate_id"] for item in schedule if item["authoring_index"] < current and item["final_for_slot"] is wanted_final}
        return [record for record in records if record["record_id"] in allowed]

    candidate_texts = {item["prompt_id"]:item["prompt"] for item in heldout} | {"rejected-001":rejected_prompt}
    with patch("chatgnt.evaluation_protocol.embed_texts_with_diagnostics", deterministic_test_embedder):
        semantic_records = compute_stage5_semantic_retrieval(
            heldout, replacements, sources, source_records, schedule
        )

    semantic_by_pair = {(item["candidate_id"],item["source_identity_id"]):item for item in semantic_records}
    candidate_metadata = {item["prompt_id"]:{field:item[field] for field in ("topic","user_goal","requested_task_or_artefact","scenario_summary","important_constraints")} for item in heldout}
    candidate_metadata["rejected-001"] = replacements[0]["candidate_metadata"]

    def review_base(matrix_prompt_id, candidate_id):
        candidate_prompt = candidate_texts[candidate_id]
        candidate_identity = text_identity(candidate_prompt)
        coverage, neighbours = [], []
        for source_id in searched_source_ids:
            records = eligible(candidate_id, source_id)
            lexical = lexical_neighbours(candidate_prompt,[{"record_id":item["record_id"],"text":item["text"]} for item in records],5)
            metadata_hits = metadata_neighbours(candidate_metadata[candidate_id],[{"record_id":item["record_id"],**item["metadata"]} for item in records],5)
            semantic_hits = semantic_by_pair[(candidate_id,source_id)]["neighbours"]
            exact_ids = {item["record_id"] for item in records if normalize_text(item["text"]) == candidate_identity["normalized_text"]}
            union = {item["record_id"] for item in lexical} | {item["record_id"] for item in metadata_hits} | {item["reference_id"] for item in semantic_hits} | exact_ids
            lexical_by = {item["record_id"]:(rank,item["lexical_score"]) for rank,item in enumerate(lexical,1)}
            metadata_by = {item["record_id"]:(rank,item) for rank,item in enumerate(metadata_hits,1)}
            semantic_by = {item["reference_id"]:item for item in semantic_hits}
            record_by = {item["record_id"]:item for item in records}
            coverage.append({"source_identity_id":source_id,"eligible_record_count":len(records),"eligible_record_ids":[item["record_id"] for item in records],
                "lexical_returned":len(lexical),"semantic_returned":len(semantic_hits),"metadata_returned":len(metadata_hits),
                "exact_match_count":len(exact_ids),"withheld_domain_checked":True,"search_complete":True})
            for reference_id in sorted(union):
                reference = record_by[reference_id]; ref_identity=text_identity(reference["text"]); signals=[]
                lexical_value=lexical_by.get(reference_id); semantic_value=semantic_by.get(reference_id); metadata_value=metadata_by.get(reference_id)
                if reference_id in exact_ids: signals.append("exact")
                if lexical_value: signals.append("lexical")
                if semantic_value: signals.append("semantic")
                if metadata_value: signals.append("metadata")
                exact = reference_id in exact_ids
                neighbours.append({"source_identity_id":source_id,"reference_id":reference_id,"retrieval_signals":signals,
                    "reference_original_sha256":ref_identity["original_sha256"],"reference_normalized_sha256":ref_identity["normalized_sha256"],
                    "reference_pre_truncation_wordpieces":semantic_value["reference_pre_truncation_wordpieces"] if semantic_value else max(1,len(reference["text"].split())),
                    "reference_semantic_input_truncated":False,"complete_text_reviewed":True,"exact_normalized_match":exact,
                    "lexical_rank":lexical_value[0] if lexical_value else None,"lexical_score":lexical_value[1] if lexical_value else None,
                    "semantic_rank":semantic_value["semantic_rank"] if semantic_value else None,"semantic_score":semantic_value["semantic_score"] if semantic_value else None,
                    "metadata_rank":metadata_value[0] if metadata_value else None,"metadata_score":metadata_value[1]["metadata_score"] if metadata_value else None,
                    "matching_metadata_fields":metadata_value[1]["matching_metadata_fields"] if metadata_value else [],
                    "same_user_goal":"yes" if exact else "no","same_substantive_situation":"yes" if exact else "no",
                    "answer_reusable_with_surface_changes":"yes" if exact else "no","decision":"reject" if exact else "allow",
                    "rationale":"Exact duplicate." if exact else "Distinct scenario."})
        return {"record_schema_version":1,"matrix_prompt_id":matrix_prompt_id,"candidate_id":candidate_id,
            "candidate_original_sha256":candidate_identity["original_sha256"],"candidate_normalized_sha256":candidate_identity["normalized_sha256"],
            "candidate_pre_truncation_wordpieces":max(1,len(candidate_prompt.split())),"candidate_semantic_input_truncated":False,
            "candidate_complete_text_reviewed":True,"review_scope":"contamination","searched_source_identity_ids":searched_source_ids,
            "retrieval_coverage":coverage,"neighbours":neighbours,"reviewed_at_utc":"2026-07-15T14:00:00Z"}

    reviews = []
    for item in heldout:
        review_id=f"prompt-review-v1-primary-{item['prompt_id']}"; base=review_base(item["prompt_id"],item["prompt_id"])
        reviews.append({**base,"review_id":review_id,"review_round":"primary","trigger":"routine","reviewer_type":"llm_agent",
            "reviewer_identity":"primary-agent","blind_to_prior_decision":False,"prior_review_ids":[],"decision":"allow","rationale":"No collision found."})
        if item["prompt_id"] in audits:
            reviews.append({**base,"review_id":f"prompt-review-v1-audit-{item['prompt_id']}","review_round":"second","trigger":"accepted_audit",
                "reviewer_type":"llm_agent","reviewer_identity":"audit-agent","blind_to_prior_decision":True,
                "prior_review_ids":[review_id],"decision":"allow","rationale":"Independent audit allows candidate."})
    rejected_primary = "prompt-review-v1-primary-rejected-001"
    rejected_second = "prompt-review-v1-second-rejected-001"
    rejected_base=review_base("heldout-v1-001", "rejected-001")
    if selection_only:
        reviews.append({**rejected_base,"review_id":rejected_primary,"review_round":"primary","trigger":"routine",
            "reviewer_type":"llm_agent","reviewer_identity":"primary-agent","blind_to_prior_decision":False,
            "prior_review_ids":[],"decision":"allow","rationale":"No contamination collision."})
        selection_base={**rejected_base,"review_scope":"selection","searched_source_identity_ids":[],"retrieval_coverage":[],"neighbours":[]}
        selection_primary="prompt-review-v1-selection-primary-rejected-001"
        selection_second="prompt-review-v1-selection-second-rejected-001"
        reviews.extend([
            {**selection_base,"review_id":selection_primary,"review_round":"primary","trigger":"routine",
             "reviewer_type":"llm_agent","reviewer_identity":"selection-primary","blind_to_prior_decision":False,
             "prior_review_ids":[],"decision":"reject","rationale":"Outside the declared evaluation scope."},
            {**selection_base,"review_id":selection_second,"review_round":"second","trigger":"selection_rejection",
             "reviewer_type":"llm_agent","reviewer_identity":"selection-second","blind_to_prior_decision":True,
             "prior_review_ids":[selection_primary],"decision":"reject","rationale":"Independent scope rejection."},
        ])
        replacement_review_ids=[selection_primary,selection_second]
    else:
        reviews.extend([
            {**rejected_base, "review_id":rejected_primary,"review_round":"primary",
             "trigger":"routine","reviewer_type":"llm_agent","reviewer_identity":"primary-agent","blind_to_prior_decision":False,
             "prior_review_ids":[],"decision":"reject","rationale":"Exact duplicate."},
            {**rejected_base, "review_id":rejected_second,"review_round":"second",
             "trigger":"rejection_confirmation","reviewer_type":"llm_agent","reviewer_identity":"audit-agent","blind_to_prior_decision":True,
             "prior_review_ids":[rejected_primary],"decision":"reject","rationale":"Independent confirmation."},
        ])
        replacement_review_ids=[rejected_primary,rejected_second]
    rejected_reviews=[item for item in reviews if item["candidate_id"]=="rejected-001" and item["review_scope"]=="contamination"]
    decisive=[neighbour for review in rejected_reviews for neighbour in review["neighbours"] if neighbour["decision"] in ("reject","uncertain")]
    replacements[0].update({"source_identity_ids":sorted({item["source_identity_id"] for item in decisive}),
        "retrieved_reference_ids":sorted({item["reference_id"] for item in decisive}),
        "retrieval_report_sha256":None if selection_only else canonical_records_sha256(rejected_reviews),"review_ids":replacement_review_ids})
    withheld_checks = [
        {"record_schema_version":1,"check_id":f"withheld-check-v1-{domain}-{collection}",
         "withheld_domain":domain,"source_identity_id":f"source-v1-{collection}","source_collection":collection,
         "checked_absent":True,"decision":"absence_confirmed",
         "attestation_statement":"I reviewed the complete bound source collection for the named withheld domain and found no material occurrence.",
         "attestation_sha256":withheld_domain_evidence_sha256(source_by_id[f"source-v1-{collection}"],domain,"author-1","Manual source inspection found no domain material."),
         "reviewer_type":"human","reviewer_identity":"author-1",
         "attested_at_utc":"2026-07-15T14:00:00Z","notes":"Manual source inspection found no domain material."}
        for domain in WITHHELD_DOMAINS
        for collection in collections[:5]
    ]
    protocol_manifest = frozen_manifest_test_result()
    candidate_attestations=[{"candidate_id":item["prompt_id"],"matrix_prompt_id":item["prompt_id"],
            "candidate_original_sha256":text_identity(item["prompt"])["original_sha256"],
            "candidate_normalized_sha256":text_identity(item["prompt"])["normalized_sha256"],
            "scope_fit":True,"complexity_correct":True,"underlying_task_clear":True,"answerable":True,"natural":True,
            "scorable":True,"complete_text_reviewed":True,"rationale":"Independent complete-set review passed."} for item in heldout]
    with patch("chatgnt.evaluation_protocol.embed_texts_with_diagnostics", deterministic_test_embedder):
        semantic_artifact=generate_stage5_semantic_evidence(
            heldout, replacements, sources, source_records, schedule, candidate_attestations,
            artifact_id="stage5-semantic-review-v1-test", verifier_identity="semantic-verifier-1",
            started_at_utc="2026-07-15T14:00:00Z", verified_at_utc="2026-07-15T14:00:00Z",
        )
    order_schedule = pairwise_order_schedule([item["prompt_id"] for item in heldout])
    flattened=[{"source_identity_id":source_id,**record} for source_id in sorted(source_records) for record in source_records[source_id]]
    bundle = {"schema_version":1,"bundle_id":"heldout-freeze-v1-test","status":"frozen",
        "reviewed_protocol_manifest_sha256":protocol_manifest["manifest_sha256"],"protocol_aggregate_sha256":protocol_manifest["aggregate_sha256"],
        "heldout_prompts_sha256":canonical_records_sha256(heldout),
        "prompt_reviews_sha256":canonical_records_sha256(reviews),"replacement_log_sha256":canonical_records_sha256(replacements),
        "source_identities_sha256":canonical_records_sha256(sources),"source_records_sha256":canonical_records_sha256(flattened),
        "withheld_domain_checks_sha256":canonical_records_sha256(withheld_checks),
        "semantic_review_artifact_sha256":hashlib.sha256(canonical_json(semantic_artifact).encode()).hexdigest(),
        "authoring_schedule_sha256":canonical_records_sha256(schedule),
        "authoring_ledger_entry_count":len(schedule),"authoring_ledger_final_entry_sha256":schedule[-1]["entry_sha256"],
        "authoring_ledger_reviewer_identity":"independent-ledger-reviewer",
        "authoring_ledger_attestation":"I reviewed the complete append-only authoring ledger and attest that it contains every candidate attempt, including rejected attempts, in actual authoring order.",
        "authoring_ledger_attested_at_utc":"2026-07-15T14:00:00Z",
        "pair_order_schedule_sha256":canonical_records_sha256(order_schedule),
        "accepted_prompt_count":60,"accepted_audit_count":6,"rejected_candidate_count":1,
        "withheld_domain_check_count":15,"pair_order_count":60,
        "source_identity_ids":[item["source_identity_id"] for item in sources],"model_training_started":False,
        "heldout_generation_started":False,"frozen_at_utc":"2026-07-15T14:00:00Z"}
    return heldout, reviews, replacements, sources, source_records, withheld_checks, semantic_artifact, schedule, bundle


GENERATED_HARNESS_ROOT=Path("tests/.generated-evaluation-harness")
atexit.register(lambda: shutil.rmtree(GENERATED_HARNESS_ROOT,ignore_errors=True))


def formal_harness_fixture(heldout, valid_systems="ABCD"):
    """Produce a complete contained fixture through the canonical harness writer."""
    run_dir=GENERATED_HARNESS_ROOT/f"run-{valid_systems or 'none'}"
    shutil.rmtree(run_dir,ignore_errors=True); GENERATED_HARNESS_ROOT.mkdir(parents=True,exist_ok=True)
    prompt_raw=b"".join(canonical_line({"prompt_id":item["prompt_id"],"prompt":item["prompt"],"metadata":{}}) for item in heldout)
    source_prompts=GENERATED_HARNESS_ROOT/f"prompts-{valid_systems or 'none'}.jsonl"; source_prompts.write_bytes(prompt_raw)
    systems=[]
    for system,path in (("A","config/prompts/minimal-v1.json"),("B","config/prompts/five-shot-v3.json"),
                        ("C","config/prompts/minimal-v1.json"),("D","config/prompts/five-shot-v3.json")):
        source,raw=read_strict_json(Path(path)); asset=PromptAsset(Path(path).resolve(),hashlib.sha256(raw).hexdigest(),
            source["schema_version"],source["prompt_asset_id"],source["version"],source["worked_example_count"],source["content"])
        systems.append(SystemDefinition(system,system in "CD",asset))
    files=[{"path":"adapter_config.json","size_bytes":1,"sha256":"a"*64},
           {"path":"adapter_model.safetensors","size_bytes":1,"sha256":"b"*64}]
    adapter_digest=tree_digest(files); historical,_=read_strict_json(Path("experiments/runs/development-ab-v1-20260715/manifest.json"))
    base=historical["configuration"]["model"]["values"]["base_model"]
    provenance={"schema_version":1,"adapter_id":"chatgnt-lora-v1","adapter_version":"1",
        "adapter_digest":adapter_digest,"base_model_id":base["id"],"base_model_revision":base["revision"],
        "base_weights_sha256":base["weights_sha256"],"training_run_id":"training-v1",
        "training_dataset_id":"chatgnt-training-v1","training_dataset_sha256":"c"*64,"peft_version":package_version("peft")}
    adapter={"adapter_id":"chatgnt-lora-v1","adapter_version":"1","adapter_digest":adapter_digest,
        "behaviour_files":files,"provenance":provenance,
        "provenance_sha256":hashlib.sha256(canonical_json(provenance).encode()).hexdigest(),"peft_config":{},
        "active_adapters":["chatgnt"],"trainable_parameter_count":0,"parameter_dtypes":["torch.bfloat16"],"merged":False}
    valid_response={"title":"Test Drink","ingredients":[{"amount":1,"unit":"parts","name":"care"},
        {"amount":2,"unit":"dashes","name":"clarity"},{"amount":3,"unit":"ml","name":"effort"}],
        "method":["Stir carefully.","Serve with a plan."],"garnish":"A clear next step."}
    raw_valid=render_pairwise_response(valid_response)
    class Qwen2Tokenizer:
        eos_token_id=151645; all_special_ids=[151643,151645]
        _config,_raw=read_strict_json(PROJECT_ROOT/"artifacts/models/Qwen--Qwen2.5-1.5B-Instruct/989aa7980e4cf806f80c7fef2b1adb7bc71aa306/tokenizer_config.json")
        chat_template=_config["chat_template"]
        def __len__(self): return 151665
    class Engine:
        def __init__(self,adapted):
            self.device=torch.device("cuda:0"); self.tokenizer=Qwen2Tokenizer(); self.last_failure_fatal=False
            self.runtime_evidence={"parameter_count":1543714304,"base_dtypes":["torch.bfloat16"],
                "attention_implementation":"sdpa","effective_generation_config":{},"adapter":adapter if adapted else None}
        def generate(self,request,profile,timing):
            del profile,timing
            raw=raw_valid if request.system_id in valid_systems or request.prompt_id=="warmup" else "not json"
            messages=({"role":"system","content":request.system_content},{"role":"user","content":request.user_prompt})
            return GenerationResult("success",messages,"rendered",(1,),1,(7,151645),2,1,raw,
                hashlib.sha256(raw.encode()).hexdigest(),"eos_token",151645,False,1,None)
    model_files,_=read_strict_json(CONFIG_ROOT/"model-files.json"); environment=copy.deepcopy(historical["environment"])
    environment["peft"]=package_version("peft"); system_source=Path("config/systems/evaluation-abcd-v1.json")
    with patch("chatgnt.harness._verify_device",return_value=torch.device("cuda:0")), \
         patch("chatgnt.harness.verify_model_files",return_value=model_files["files"]), \
         patch("chatgnt.harness.load_system_set",return_value=(systems,system_source.read_bytes())), \
         patch("chatgnt.harness.load_engine",side_effect=lambda snapshot,device,mode,project,**kwargs:Engine(mode=="adapted")), \
         patch("chatgnt.harness._environment",return_value=environment):
        code,actual_run,report=execute_run(source_prompts,system_source,20260715,"cuda:0",
            adapter_path=Path("artifacts/adapters/chatgnt-lora-v1"),run_id=run_dir.name,runs_root=GENERATED_HARNESS_ROOT)
    if code != 0 or actual_run.resolve() != run_dir.resolve() or not report["complete"]: raise AssertionError(report)
    return (run_dir/"manifest.json").as_posix()


def judgment_evidence_v4(valid_systems="ABCD"):
    response={"title":"Test Drink","ingredients":[{"amount":1,"unit":"parts","name":"care"},
        {"amount":2,"unit":"dashes","name":"clarity"},{"amount":3,"unit":"ml","name":"effort"}],
        "method":["Stir carefully.","Serve with a plan."],"garnish":"A clear next step."}
    heldout=heldout_records(); harness_path=formal_harness_fixture(heldout,valid_systems)
    run_records=evaluation_run_records_from_harness(heldout,harness_path)
    generation_manifest=build_evaluation_generation_manifest(heldout,run_records,
        source_harness_manifest_path=harness_path)
    heldout_sha=canonical_records_sha256(heldout)
    response_packets,pair_packets,schedule=build_judgment_packets(heldout,run_records,generation_manifest)
    runs_sha=canonical_records_sha256(run_records); generation_manifest_sha=hashlib.sha256(canonical_json(generation_manifest).encode()).hexdigest()
    protocol_sha=hashlib.sha256(Path("config/evaluation-protocol-v1.json").read_bytes()).hexdigest()
    rubric_sha=hashlib.sha256(Path("config/evaluation-rubric-v1.json").read_bytes()).hexdigest()
    manifest,manifest_sha=validate_judge_manifest(); qualitative=[]
    selected=set(select_human_response_calibration(response_packets))
    for packet in response_packets:
        if not packet["schema_valid"]: continue
        base={"record_schema_version":1,"protocol_sha256":protocol_sha,"heldout_records_sha256":heldout_sha,
            "run_records_sha256":runs_sha,"generation_manifest_sha256":generation_manifest_sha,
            "rubric_sha256":rubric_sha,"judge_manifest_sha256":manifest_sha,
            "instruction_sha256":manifest["qualitative"]["instruction_sha256"],"packet_id":packet["packet_id"],"packet_sha256":packet["packet_sha256"],
            "prompt_id":packet["prompt_id"],"response_id":packet["response_id"],"blinded_label":"candidate","prior_judgment_id":None,
            "resolution_status":"resolved","scores":{"underlying_answer_quality":3,"metaphorical_coherence":3,"recipe_style_execution":3},
            "rationales":{"underlying_answer_quality":"Useful.","metaphorical_coherence":"Coherent.","recipe_style_execution":"Executed."},
            "recorded_at_utc":"2026-07-15T14:00:00Z"}
        qualitative.append({**base,"judgment_id":f"qual-v1-primary-{packet['response_id']}","judge_role":"llm","judge_identity":"judge",
            "judge_session_id":f"qual-primary-{packet['response_id']}","exposed_model_id":"GPT-5","judgment_round":"primary"})
        if packet["packet_id"] in selected:
            qualitative.append({**base,"judgment_id":f"qual-v1-human-{packet['response_id']}","judge_role":"human","judge_identity":"human",
                "judge_session_id":f"qual-human-{packet['response_id']}","exposed_model_id":None,"judgment_round":"human_calibration"})
    pairwise=[]; selected_pairs=set(select_human_pair_calibration(pair_packets))
    for packet in pair_packets:
        if not packet["conditional_eligible"]: continue
        base={"record_schema_version":1,"protocol_sha256":protocol_sha,"heldout_records_sha256":heldout_sha,
            "run_records_sha256":runs_sha,"generation_manifest_sha256":generation_manifest_sha,"judge_manifest_sha256":manifest_sha,
            "instruction_sha256":manifest["pairwise"]["instruction_sha256"],"packet_id":packet["packet_id"],"packet_sha256":packet["packet_sha256"],
            "renderer_id":manifest["pairwise"]["renderer_id"],"prompt_id":packet["prompt_id"],"response_a_id":packet["response_a_id"],
            "response_b_id":packet["response_b_id"],"order_schedule_sha256":packet["order_schedule_sha256"],"prior_judgment_id":None,
            "resolution_status":"resolved","choice":"tie","rationale":"Tie.","recorded_at_utc":"2026-07-15T14:00:00Z"}
        pairwise.append({**base,"judgment_id":f"pair-v1-primary-{packet['prompt_id']}","judge_role":"llm","judge_identity":"judge",
            "judge_session_id":f"pair-primary-{packet['prompt_id']}","exposed_model_id":"GPT-5","judgment_round":"primary"})
        if packet["prompt_id"] in selected_pairs:
            pairwise.append({**base,"judgment_id":f"pair-v1-human-{packet['prompt_id']}","judge_role":"human","judge_identity":"human",
                "judge_session_id":f"pair-human-{packet['prompt_id']}","exposed_model_id":None,"judgment_round":"human_calibration"})
    return qualitative,pairwise,heldout,run_records,generation_manifest


def response_similarity_evidence():
    def value(title):
        return {"title":title,"ingredients":[{"amount":1,"unit":"parts","name":"care"},
            {"amount":2,"unit":"dashes","name":"clarity"},{"amount":3,"unit":"ml","name":"effort"}],
            "method":["Stir carefully.","Serve with a plan."],"garnish":"A clear next step."}
    shared=value("Shared Drink"); other=value("Other Drink")
    responses=[]
    for prompt in heldout_records():
        for system in "ABCD":
            parsed=copy.deepcopy(shared) if system=="A" and prompt["prompt_id"]=="heldout-v1-001" else value(f"{system} Drink {prompt['prompt_id']}")
            responses.append({"response_id":f"response-{system}-{prompt['prompt_id']}","prompt_id":prompt["prompt_id"],
                "system_id":system,"raw_output":render_pairwise_response(parsed),"parsed_response":parsed})
    references={"worked_example_responses":[{"reference_id":"worked-1","raw_output":render_pairwise_response(shared),"parsed_response":shared},
        {"reference_id":"worked-2","raw_output":render_pairwise_response(other),"parsed_response":other}],
        "training_responses":[{"reference_id":"train-1","raw_output":render_pairwise_response(other),"parsed_response":other},
        {"reference_id":"train-2","raw_output":render_pairwise_response(value("Third Drink")),"parsed_response":value("Third Drink")} ]}
    with patch("chatgnt.evaluation_protocol.embed_texts_with_diagnostics", deterministic_test_embedder):
        artifact=generate_response_similarity_semantic_evidence(
            responses, references, artifact_id="response-similarity-evidence-v1-test",
            verifier_identity="semantic-verifier-1", started_at_utc="2026-07-15T14:00:00Z",
            verified_at_utc="2026-07-15T14:00:00Z",
        )
    semantic_records={(item["response_id"],item["reference_collection"]):item for item in artifact["records"]}
    reviews=[]
    for response in responses:
        response_view=response_similarity_text_view(response["raw_output"],response["parsed_response"])
        collections={**references,"heldout_system_responses":[{"reference_id":item["response_id"],"raw_output":item["raw_output"],"parsed_response":item["parsed_response"]}
            for item in responses if item["system_id"]==response["system_id"] and item["response_id"]!=response["response_id"]]}
        for collection,records in collections.items():
            corpus=[{"record_id":item["reference_id"],"text":response_similarity_text_view(item["raw_output"],item["parsed_response"])} for item in records]
            lexical=lexical_neighbours(response_view,corpus,5)
            evidence=semantic_records[(response["response_id"],collection)]
            semantic=evidence["neighbours"]
            lexical_by={item["record_id"]:(rank,item["lexical_score"]) for rank,item in enumerate(lexical,1)}
            semantic_by={item["reference_id"]:item for item in semantic}; record_by={item["reference_id"]:item for item in records}
            exact_ids={item["record_id"] for item in corpus if item["text"]==response_view}
            for reference_id in sorted(set(lexical_by)|set(semantic_by)|exact_ids):
                reference=record_by[reference_id]; reference_view=response_similarity_text_view(reference["raw_output"],reference["parsed_response"])
                signals=[]; lexical_value=lexical_by.get(reference_id); semantic_value=semantic_by.get(reference_id)
                if reference_id in exact_ids: signals.append("exact")
                if lexical_value: signals.append("lexical")
                if semantic_value: signals.append("semantic")
                within=collection=="heldout_system_responses"; exact=reference_id in exact_ids
                reviews.append({"record_schema_version":1,"review_id":f"response-review-v1-{response['response_id']}-{collection}-{reference_id}",
                    "system_id":response["system_id"],"response_id":response["response_id"],
                    "response_original_sha256":hashlib.sha256(response["raw_output"].encode()).hexdigest(),
                    "response_text_view_sha256":hashlib.sha256(response_view.encode()).hexdigest(),
                    "response_pre_truncation_wordpieces":evidence["response_pre_truncation_wordpieces"],
                    "response_semantic_input_truncated":evidence["response_semantic_input_truncated"],
                    "reference_collection":collection,"reference_id":reference_id,
                    "exposure_status":"within_system_diversity" if within else (
                        "exposed" if collection in ({"B":{"worked_example_responses"},"C":{"training_responses"},
                        "D":{"worked_example_responses","training_responses"}}.get(response["system_id"],set())) else "diagnostic_not_exposed"),
                    "reference_original_sha256":hashlib.sha256(reference["raw_output"].encode()).hexdigest(),
                    "reference_text_view_sha256":hashlib.sha256(reference_view.encode()).hexdigest(),
                    "reference_pre_truncation_wordpieces":next(item["reference_pre_truncation_wordpieces"] for item in evidence["reference_diagnostics"] if item["reference_id"]==reference_id),
                    "reference_semantic_input_truncated":next(item["reference_semantic_input_truncated"] for item in evidence["reference_diagnostics"] if item["reference_id"]==reference_id),
                    "retrieval_signals":signals,"exact_text_view_match":exact,
                    "lexical_rank":lexical_value[0] if lexical_value else None,"lexical_score":lexical_value[1] if lexical_value else None,
                    "semantic_rank":semantic_value["semantic_rank"] if semantic_value else None,
                    "semantic_score":semantic_value["semantic_score"] if semantic_value else None,"complete_text_reviewed":True,
                    "decision":"generic_collapse_flag" if exact and within else ("exact_project_response" if exact else "no_concern"),
                    "rationale":"Exact match." if exact else "No distinctive overlap.","reviewer_type":"llm_agent","reviewer_identity":"reviewer-1"})
    return responses,references,reviews,artifact,heldout_records()


class IdentityAndRetrievalTests(unittest.TestCase):
    def test_normalization_is_frozen_and_preserves_punctuation(self):
        self.assertEqual(normalize_text("  CAFÉ\r\n\tPlan!  "), "café plan!")
        self.assertNotEqual(normalize_text("plan!"), normalize_text("plan?"))
        identity = text_identity("Plan")
        self.assertEqual(len(identity["original_sha256"]), 64)
        self.assertEqual(identity["normalized_text"], "plan")

    def test_lexical_retrieval_is_ranked_and_deterministic(self):
        corpus = [
            {"record_id": "b", "text": "prepare for an interview"},
            {"record_id": "a", "text": "grow tomatoes"},
        ]
        result = lexical_neighbours("interview preparation", corpus, top_k=2)
        self.assertEqual(result[0]["record_id"], "b")
        self.assertGreater(lexical_score("one two", "two one"), 90)

    def test_semantic_and_metadata_retrieval_and_merge(self):
        self.assertAlmostEqual(cosine_similarity([1, 0], [2, 0]), 1.0)
        semantic = semantic_neighbours([1, 0], [("a", [0, 1]), ("b", [1, 0])], top_k=1)
        metadata = metadata_neighbours(
            {"topic": "Work", "user_goal": "Choose"},
            [
                {"record_id": "b", "topic": "work", "user_goal": "choose"},
                {"record_id": "a", "topic": "garden", "user_goal": "choose"},
            ],
        )
        merged = merge_neighbours(semantic, metadata)
        self.assertEqual([item["record_id"] for item in merged], ["a", "b"])
        self.assertIn("semantic_score", merged[1])
        self.assertEqual(merged[1]["metadata_score"], 2.0)

    def test_collision_decision_requires_all_three_answers(self):
        self.assertEqual(semantic_collision_decision(True, True, True), "reject")
        self.assertEqual(semantic_collision_decision(True, False, True), "allow")
        self.assertEqual(semantic_collision_decision(True, None, True), "uncertain")

    def test_lexical_similarity_retrieves_but_does_not_decide(self):
        self.assertGreater(lexical_score("plan the interview", "interview plan"), 90)
        self.assertEqual(semantic_collision_decision(True, False, True), "allow")

    def test_tokenization_diagnostics_exposes_truncation(self):
        class FakeTokenizer:
            def __call__(self, texts, **_keywords):
                return {"input_ids": [text.split() for text in texts]}

        result = tokenization_diagnostics(["short input", " ".join(["word"] * 257)], FakeTokenizer())
        self.assertEqual(result[0]["pre_truncation_wordpieces"], 2)
        self.assertFalse(result[0]["semantic_input_truncated"])
        self.assertTrue(result[1]["semantic_input_truncated"])

    def test_human_calibration_selectors_have_fixed_vectors(self):
        responses = [
            {"packet_id": f"{system}-{reporting_slice}-{index}", "system_id": system,
             "reporting_slice": reporting_slice, "schema_valid": True}
            for system in "ABCD" for reporting_slice in ("target_use", "cross_domain", "robustness")
            for index in range(3)
        ]
        self.assertEqual(select_human_response_calibration(responses), [
            "A-target_use-1","A-target_use-0","A-cross_domain-1","A-cross_domain-0","A-robustness-2","A-robustness-0",
            "B-target_use-2","B-target_use-0","B-cross_domain-1","B-cross_domain-0","B-robustness-1","B-robustness-0",
            "C-target_use-0","C-target_use-2","C-cross_domain-2","C-cross_domain-0","C-robustness-2","C-robustness-1",
            "D-target_use-0","D-target_use-2","D-cross_domain-1","D-cross_domain-2","D-robustness-0","D-robustness-2",
        ])
        pairs = [
            {"prompt_id": f"{reporting_slice}-{index}", "reporting_slice": reporting_slice, "conditional_eligible": True}
            for reporting_slice in ("target_use", "cross_domain", "robustness") for index in range(6)
        ]
        self.assertEqual(select_human_pair_calibration(pairs), [
            "target_use-2","target_use-1","target_use-0","target_use-4","target_use-5",
            "cross_domain-3","cross_domain-2","cross_domain-0","cross_domain-1","cross_domain-4",
            "robustness-1","robustness-0","robustness-4","robustness-5","robustness-2",
        ])

    def test_pair_order_renderer_and_response_views_have_fixed_vectors(self):
        prompt_ids = [f"heldout-v1-{index:03d}" for index in range(1, 61)]
        schedule = pairwise_order_schedule(prompt_ids)
        self.assertEqual(canonical_records_sha256(schedule), "cec539fec19dfd6e5f1f25451d75e9ccd69dec43dd460414b3d1be60b9f84543")
        self.assertEqual(Counter(item["response_a_system"] for item in schedule), Counter({"B": 30, "C": 30}))
        value = {"garnish":"G","method":["M1","M2"],"ingredients":[
            {"name":"N","unit":"ml","amount":5},{"amount":2,"name":"X","unit":"dashes"},{"unit":"parts","amount":1,"name":"Y"}],"title":"T"}
        rendered = render_pairwise_response(value)
        self.assertEqual(hashlib.sha256(rendered.encode()).hexdigest(), "d1fdb46a2aa541f35e70b531308e9909f3f720ae7425973c1b3784560abbb922")
        self.assertEqual(hashlib.sha256(render_pairwise_packet("packet-1", "User?", value, value).encode()).hexdigest(), "54ae5dd105946ddb379561c5a25811fe75380acf0bbd94c2aad9dbf32aa5fbef")
        self.assertEqual(hashlib.sha256(render_qualitative_packet("packet-1", "User?", rendered).encode()).hexdigest(), "7896a8db5d7f0ec131f4c8c74055b6963930e18e933ad9c8d46fc94621b742d9")
        self.assertEqual(
            response_similarity_text_view(rendered, value),
            "title: t ingredient: 5 ml n ingredient: 2 dashes x ingredient: 1 parts y method: m1 method: m2 garnish: g",
        )
        self.assertEqual(accepted_audit_ids(prompt_ids), ["heldout-v1-048","heldout-v1-007","heldout-v1-058","heldout-v1-041","heldout-v1-027","heldout-v1-017"])


class ProtocolValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls._semantic_patch = patch(
            "chatgnt.evaluation_protocol.embed_texts_with_diagnostics",
            deterministic_test_embedder,
        )
        cls._semantic_patch.start()

    @classmethod
    def tearDownClass(cls):
        cls._semantic_patch.stop()

    def test_protocol_and_calibration_assets_validate(self):
        protocol, digest = load_protocol()
        self.assertEqual(protocol["sample"]["prompt_count"], 60)
        self.assertEqual(len(digest), 64)
        self.assertEqual(validate_calibration_records()["case_count"], 12)
        self.assertEqual(validate_judge_calibration()["packet_count"], 6)
        self.assertEqual(validate_response_similarity_calibration()["case_count"], 2)
        manifest, manifest_digest = validate_judge_manifest()
        self.assertEqual(manifest["primary"]["model_family"], "GPT-5")
        self.assertEqual(len(manifest_digest), 64)

    def test_protocol_has_deterministic_review_candidate_to_frozen_transition(self):
        protocol, _ = read_strict_json(Path("config/evaluation-protocol-v1.json"))
        candidate = normative_protocol_value(protocol)
        frozen = copy.deepcopy(candidate)
        orchestrator_sha = hashlib.sha256(Path("scripts/orchestrate_stage3_review.py").read_bytes()).hexdigest()
        frozen["status"] = "frozen"
        frozen["freeze_gate"] = {
            "independent_review_required": True,
            "review_id": "stage3-adversarial-v1",
            "reviewer_identity": "independent-review-agent",
            "review_verdict": "pass",
            "unresolved_blocking_findings": 0,
            "frozen_at_utc": "2026-07-15T14:00:00Z",
            "review_artifact_path": "reviews/stage3-adversarial-v1.json",
            "review_artifact_sha256": "0" * 64,
            "verification_evidence_path": "reviews/stage3-verification-v1.json",
            "verification_evidence_sha256": "0" * 64,
            "transition_orchestrator_sha256": orchestrator_sha,
        }
        candidate_sha = protocol_normative_sha256(candidate)
        fake_manifest = {"aggregate_sha256":"a"*64}
        authorization = _LiveGateAuthorization(candidate_sha, fake_manifest["aggregate_sha256"], _AUTHORIZATION_GUARD)
        self.assertEqual(validate_protocol_value(frozen)["status"], "frozen")
        with patch("chatgnt.evaluation_protocol.validate_protocol_manifest", return_value=fake_manifest):
            self.assertEqual(validate_freeze_transition(
                candidate, frozen, live_gate_authorization=authorization,
            )["result"], "pass")
            with self.assertRaises(ContractError):
                validate_freeze_transition(candidate, frozen, live_gate_authorization={"stored":"evidence"})
        broken = copy.deepcopy(frozen)
        broken["freeze_gate"]["unresolved_blocking_findings"] = 1
        with self.assertRaises(ContractError):
            validate_protocol_value(broken)
        broken = copy.deepcopy(frozen)
        broken["freeze_gate"]["frozen_at_utc"] = "2999-01-01T00:00:00Z"
        with self.assertRaises(ContractError):
            validate_protocol_value(broken)
        broken = copy.deepcopy(frozen)
        broken["sample"]["prompt_count"] = 61
        with self.assertRaises(ContractError):
            validate_freeze_transition(candidate, broken, live_gate_authorization=authorization)
        broken = copy.deepcopy(frozen)
        broken["freeze_gate"]["review_artifact_path"] = "../../outside.json"
        with self.assertRaises(ContractError):
            validate_protocol_value(broken)

    def test_stage3_orchestrator_failed_gate_and_dry_review_never_transition(self):
        protocol, _ = read_strict_json(Path("config/evaluation-protocol-v1.json"))
        candidate = normative_protocol_value(protocol)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir(); (root / "reviews").mkdir()
            protocol_path = root / "config" / "evaluation-protocol-v1.json"
            original = (canonical_json(candidate) + "\n").encode()
            protocol_path.write_bytes(original)
            with (
                patch("scripts.orchestrate_stage3_review.PROJECT_ROOT", root),
                patch("scripts.orchestrate_stage3_review.PROTOCOL_PATH", protocol_path),
            ):
                with self.assertRaises(ContractError):
                    orchestrate(
                        mode="freeze", evidence_path="reviews/evidence.json",
                        review_artifact_path="reviews/review.json", review_id="stage3-review-v1-test",
                        reviewer_identity="reviewer", report_path="docs/report.md",
                        capture=lambda: (_ for _ in ()).throw(ContractError("controlled gate failed")),
                    )
                self.assertEqual(protocol_path.read_bytes(), original)
                self.assertFalse((root / "reviews" / "evidence.json").exists())
                result = orchestrate(
                    mode="dry-review", evidence_path="reviews/evidence.json",
                    capture=lambda: ({"protocol_aggregate_sha256":"a"*64}, object()),
                )
                self.assertEqual(result["transition"], "not_attempted")
                self.assertEqual(protocol_path.read_bytes(), original)

    def test_stage3_orchestrator_success_path_uses_live_authorization_then_transitions(self):
        protocol, _ = read_strict_json(Path("config/evaluation-protocol-v1.json"))
        candidate = normative_protocol_value(protocol)
        candidate_sha = protocol_normative_sha256(candidate)
        fake_manifest = {
            "aggregate_sha256":"a"*64, "manifest_sha256":"b"*64,
            "protocol_normative_sha256":candidate_sha,
        }
        authorization = _LiveGateAuthorization(candidate_sha, fake_manifest["aggregate_sha256"], _AUTHORIZATION_GUARD)
        evidence = {
            "protocol_aggregate_sha256":fake_manifest["aggregate_sha256"],
            "created_at_utc":"2026-07-15T14:00:00Z",
        }
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "config").mkdir(); (root / "reviews").mkdir(); (root / "docs").mkdir()
            protocol_path = root / "config" / "evaluation-protocol-v1.json"
            protocol_path.write_text(canonical_json(candidate) + "\n")
            (root / "docs" / "report.md").write_text("Independent review passed.\n")
            with (
                patch("scripts.orchestrate_stage3_review.PROJECT_ROOT", root),
                patch("scripts.orchestrate_stage3_review.PROTOCOL_PATH", protocol_path),
                patch("scripts.orchestrate_stage3_review.validate_protocol_manifest", return_value=fake_manifest),
                patch("chatgnt.evaluation_protocol.validate_protocol_manifest", return_value=fake_manifest),
            ):
                result = orchestrate(
                    mode="freeze", evidence_path="reviews/evidence.json",
                    review_artifact_path="reviews/review.json", review_id="stage3-review-v1-test",
                    reviewer_identity="independent-reviewer", report_path="docs/report.md",
                    capture=lambda: (evidence, authorization),
                )
            frozen, _ = read_strict_json(protocol_path)
            self.assertEqual(result["transition"], "frozen")
            self.assertEqual(frozen["status"], "frozen")
            self.assertTrue((root / "reviews" / "evidence.json").is_file())
            self.assertTrue((root / "reviews" / "review.json").is_file())
    def test_canonical_protocol_manifest_covers_current_normative_assets(self):
        result = validate_protocol_manifest()
        self.assertGreaterEqual(result["asset_count"], 30)
        self.assertEqual(len(result["aggregate_sha256"]), 64)

    def test_stage3_verification_evidence_binds_all_final_gates(self):
        manifest=validate_protocol_manifest(); digest="0"*64
        runner_sha=hashlib.sha256(Path("scripts/capture_stage3_verification.py").read_bytes()).hexdigest()
        verifier_sha=hashlib.sha256(Path("scripts/verify_evaluation_protocol.py").read_bytes()).hexdigest()
        test_entries=[{"path":path.as_posix(),"sha256":hashlib.sha256(path.read_bytes()).hexdigest()}
            for path in sorted(Path("tests").glob("test_*.py"))]
        tests_sha=hashlib.sha256(canonical_json(test_entries).encode()).hexdigest()
        verifier_output=lambda executed: canonical_json({"result":"pass","protocol_manifest":{"aggregate_sha256":manifest["aggregate_sha256"]},
            "retrieval_calibration":{"semantic":{"executed":executed}}})
        test_count=sum(1 for line in Path("tests/test_evaluation_protocol.py").read_text().splitlines() if line.lstrip().startswith("def test_"))
        test_count += sum(1 for path in Path("tests").glob("test_*.py") if path.name != "test_evaluation_protocol.py"
            for line in path.read_text().splitlines() if line.lstrip().startswith("def test_"))
        gate_times=iter((("13:00:00","13:01:00"),("13:01:00","13:02:00"),("13:02:00","13:03:00")))
        def gate(command,implementation,stdout,stderr=""):
            combined=stdout+stderr; started,completed=next(gate_times)
            return {"command":command,"exit_status":0,"result":"pass","stdout":stdout,
                "stdout_sha256":hashlib.sha256(stdout.encode()).hexdigest(),"implementation_sha256":implementation,
                "stderr":stderr,"stderr_sha256":hashlib.sha256(stderr.encode()).hexdigest(),
                "combined_output_policy":"stdout_bytes_then_stderr_bytes","combined_output":combined,
                "combined_output_sha256":hashlib.sha256(combined.encode()).hexdigest(),
                "started_at_utc":f"2026-07-15T{started}Z","completed_at_utc":f"2026-07-15T{completed}Z",
                "duration_seconds":60.0}
        value={"schema_version":1,"evidence_id":"stage3-verification-v1-test","status":"pass",
            "capture_runner_sha256":runner_sha,
            "protocol_normative_sha256":manifest["protocol_normative_sha256"],"protocol_aggregate_sha256":manifest["aggregate_sha256"],
            "protocol_manifest_sha256":manifest["manifest_sha256"],
            "candidate_identity_observed_at_utc":"2026-07-15T12:59:00Z",
            "environment":{"python":platform.python_version(),"platform":platform.platform(),"uv":"uv 0.11.28",
                "packages":{name:package_version(name) for name in ("jsonschema","rapidfuzz","torch","transformers")}},
            "ordinary_verifier":gate("uv run --frozen python scripts/verify_evaluation_protocol.py",verifier_sha,verifier_output(False)),
            "semantic_verifier":gate("uv run --frozen python scripts/verify_evaluation_protocol.py --semantic",verifier_sha,verifier_output(True)),
            "full_test_suite":gate("uv run --frozen python -m unittest discover -s tests",tests_sha,"",f"Ran {test_count} tests in 1.0s\n\nOK\n"),
            "created_at_utc":"2026-07-15T13:03:00Z"}
        self.assertEqual(validate_stage3_verification_evidence(value)["result"],"pass")
        for mutate in (
            lambda broken: broken.__setitem__("capture_runner_sha256",digest),
            lambda broken: broken["semantic_verifier"].__setitem__("implementation_sha256",digest),
            lambda broken: broken["semantic_verifier"].__setitem__("started_at_utc","2000-01-01T00:00:00Z"),
            lambda broken: broken["semantic_verifier"].__setitem__("completed_at_utc","2999-01-01T00:00:00Z"),
            lambda broken: broken.__setitem__("candidate_identity_observed_at_utc","2999-01-01T00:00:00Z"),
            lambda broken: broken.__setitem__("candidate_identity_observed_at_utc","2026-07-15T12:59:00+00:00"),
            lambda broken: broken["semantic_verifier"].__setitem__("duration_seconds",0),
            lambda broken: broken["full_test_suite"].update({
                "stderr":"Ran 999 tests in 1.0s\n\nOK\n",
                "stderr_sha256":hashlib.sha256(b"Ran 999 tests in 1.0s\n\nOK\n").hexdigest(),
                "combined_output":"Ran 999 tests in 1.0s\n\nOK\n",
                "combined_output_sha256":hashlib.sha256(b"Ran 999 tests in 1.0s\n\nOK\n").hexdigest(),
            }),
            lambda broken: broken["ordinary_verifier"].__setitem__("combined_output","substituted"),
        ):
            with self.subTest(mutation=repr(mutate)):
                broken=copy.deepcopy(value); mutate(broken)
                with self.assertRaises(ContractError): validate_stage3_verification_evidence(broken)

    def test_stage3_capture_runner_keeps_stdout_and_stderr_as_distinct_evidence(self):
        completed=subprocess.CompletedProcess([],0,stdout=b'{"result":"pass"}\n',stderr=b"diagnostic\n")
        with (
            patch("scripts.capture_stage3_verification.subprocess.run",return_value=completed) as execute,
            patch("scripts.capture_stage3_verification.time.monotonic",side_effect=[10.0,11.5]),
            patch("scripts.capture_stage3_verification.utc_now",side_effect=["2026-07-15T13:00:00Z","2026-07-15T13:00:01.5Z"]),
        ):
            record=run_gate(STAGE3_CAPTURE_COMMANDS["ordinary_verifier"],"a"*64)
        self.assertEqual(record["stdout"],'{"result":"pass"}\n')
        self.assertEqual(record["stderr"],"diagnostic\n")
        self.assertEqual(record["combined_output"],record["stdout"]+record["stderr"])
        self.assertEqual(record["duration_seconds"],1.5)
        self.assertEqual(execute.call_args.args[0],["uv","run","--frozen","python","scripts/verify_evaluation_protocol.py"])

    def test_complete_cross_cutting_quota_fixture_passes(self):
        result = validate_heldout_records(heldout_records())
        self.assertEqual(result["prompt_count"], 60)
        self.assertEqual(result["observed"]["reporting_slice"]["cross_domain"], 15)

    def test_schema_cross_field_rules_and_quota_drift_fail(self):
        records = heldout_records()
        broken = copy.deepcopy(records)
        broken[0]["robustness_role"] = "format_pressure"
        with self.assertRaises(ContractError):
            validate_heldout_records(broken)

        broken = copy.deepcopy(records)
        broken[9]["robustness_role"] = "behaviour_pressure"
        broken[22]["robustness_role"] = "format_pressure"
        with self.assertRaises(ContractError):
            validate_heldout_records(broken)

        broken = copy.deepcopy(records)
        broken[16]["important_constraints"] = ["quietly hidden"]
        with self.assertRaises(ContractError):
            validate_heldout_records(broken)

        broken = copy.deepcopy(records)
        broken[-1]["prompt_id"] = "heldout-v1-061"
        with self.assertRaises(ContractError):
            validate_heldout_records(broken)
        broken = copy.deepcopy(records)
        broken[9]["robustness_role"], broken[58]["robustness_role"] = (
            broken[58]["robustness_role"], broken[9]["robustness_role"]
        )
        with self.assertRaises(ContractError):
            validate_heldout_records(broken)
        broken = copy.deepcopy(records)
        broken[0]["input_form"] = "statement_or_fragment"
        with self.assertRaises(ContractError):
            validate_heldout_records(broken)

    def test_normalized_duplicates_fail(self):
        records = heldout_records()
        records[1]["prompt"] = "  UNIQUE PROTOCOL TEST PROMPT 1\n"
        with self.assertRaises(ContractError):
            validate_heldout_records(records)

    def test_wilson_interval_examples_and_errors(self):
        low, high = wilson_interval(30, 60)
        self.assertAlmostEqual(low, 0.377, places=3)
        self.assertAlmostEqual(high, 0.623, places=3)
        with self.assertRaises(ContractError):
            wilson_interval(1, 0)
        with self.assertRaises(ContractError):
            wilson_interval(1.0, 2)

    def test_paired_bootstrap_and_weighted_kappa_contracts(self):
        binary = [
            {"prompt_id":f"heldout-v1-{index:03d}", "B":0, "C":1 if index <= 30 else 0}
            for index in range(1, 61)
        ]
        result = paired_bootstrap_interval(binary, "paired_rate_difference", resamples=100)
        self.assertEqual(result["paired_prompt_count"], 60)
        self.assertAlmostEqual(result["estimate"], 0.5)
        continuous = paired_bootstrap_interval(
            [{"prompt_id":"heldout-v1-001","B":2.0,"C":3.0}],
            "paired_mean_difference", resamples=10,
        )
        self.assertEqual(continuous["estimate"], 1.0)
        with self.assertRaises(ContractError):
            paired_bootstrap_interval(binary[:-1], "paired_rate_difference", resamples=10)
        self.assertAlmostEqual(weighted_cohens_kappa([(1,1),(2,2),(3,3)])["kappa"], 1.0)
        self.assertEqual(weighted_cohens_kappa([("unable_to_assess", 2)])["undefined_reason"], "no_resolved_pairs")

    def test_judgment_batch_enforces_distinct_pair_ids_and_frozen_provenance(self):
        evidence=judgment_evidence_v4()
        result=validate_judgment_records(
            evidence[0], evidence[1], heldout_records=evidence[2], run_records=evidence[3], generation_manifest=evidence[4]
        )
        self.assertEqual(result["pairwise_count"],75)
        broken=list(copy.deepcopy(evidence)); broken[1][0]["protocol_sha256"]="0"*64
        with self.assertRaises(ContractError):
            validate_judgment_records(
                broken[0], broken[1], heldout_records=broken[2], run_records=broken[3], generation_manifest=broken[4]
            )
        broken=list(copy.deepcopy(evidence)); broken[1]=broken[1][1:]
        with self.assertRaises(ContractError):
            validate_judgment_records(
                broken[0], broken[1], heldout_records=broken[2], run_records=broken[3], generation_manifest=broken[4]
            )

        # The aggregate must be built from the complete canonical 4 x 60 inventory.
        broken=list(copy.deepcopy(evidence)); broken[3]=broken[3][:-1]
        with self.assertRaises(ContractError):
            validate_judgment_records(
                broken[0], broken[1], heldout_records=broken[2], run_records=broken[3], generation_manifest=broken[4]
            )

        # Attempt order comes from the inspected harness schedule; callers cannot
        # manufacture a different complete-looking schedule.
        shuffled=list(copy.deepcopy(evidence))
        for record in shuffled[3]: record["attempt_index"]=239-record["attempt_index"]
        with self.assertRaises(ContractError):
            build_evaluation_generation_manifest(shuffled[2],shuffled[3],
                source_harness_manifest_path=shuffled[4]["source_harness_manifest_path"])

        # The manifest path, source digest, system prompt/config identities, and
        # output population are all non-callable facts from one contained run.
        for mutate in (
            lambda value:value[4].__setitem__("source_harness_manifest_path","tests/fixtures/missing/manifest.json"),
            lambda value:value[4].__setitem__("source_harness_manifest_sha256","0"*64),
            lambda value:value[4]["systems"][0].__setitem__("prompt_asset_sha256","0"*64),
            lambda value:value[4]["systems"][1].__setitem__("generation_config_sha256","0"*64),
            lambda value:value[4]["systems"][2].__setitem__("adapter_enabled",False),
        ):
            broken=list(copy.deepcopy(evidence)); mutate(broken)
            with self.assertRaises(ContractError):
                validate_judgment_records(broken[0],broken[1],heldout_records=broken[2],
                    run_records=broken[3],generation_manifest=broken[4])

        harness_path=Path(evidence[4]["source_harness_manifest_path"]); original=harness_path.read_bytes()
        for mutate in (
            lambda value:value["system_set"]["systems"][0]["prompt_asset"].__setitem__("source_sha256","0"*64),
            lambda value:value["configuration"]["inference"]["values"]["runtime"].__setitem__("quantization",True),
            lambda value:value["model"].__setitem__("weights_sha256","0"*64),
            lambda value:value["timing"].__setitem__("batch_size",2),
            lambda value:value["adapter"]["provenance"].__setitem__("base_model_revision","0"*40),
        ):
            altered,_=read_strict_json(harness_path); mutate(altered); harness_path.write_bytes(canonical_line(altered))
            try:
                with self.assertRaises(ContractError):
                    evaluation_run_records_from_harness(evidence[2],evidence[4]["source_harness_manifest_path"])
            finally:
                harness_path.write_bytes(original)

        # A coherent alternative can keep the v3 label, five-example count,
        # paired B/D bytes, system-set links, and all substituted digests
        # internally consistent. It is still not the selected five-shot-v3.
        substitute_source=Path("tests/fixtures/coherent-substitute-five-shot-v3.json")
        with self.assertRaises(ContractError):
            validate_five_shot_prompt_v3(substitute_source)
        substitute,substitute_raw=read_strict_json(substitute_source)
        alternate_dir=GENERATED_HARNESS_ROOT/"coherent-substitute-treatment"
        alternate_dir.mkdir(parents=True,exist_ok=True)
        alternate_prompt=alternate_dir/"five-shot-v3.json"
        alternate_prompt.write_bytes(substitute_raw)
        alternate_system=alternate_dir/"evaluation-abcd-v1.json"
        alternate_system_value={"schema_version":1,"systems":[
            {"adapter_enabled":False,"prompt_asset_path":"../../../config/prompts/minimal-v1.json","system_id":"A"},
            {"adapter_enabled":False,"prompt_asset_path":"five-shot-v3.json","system_id":"B"},
            {"adapter_enabled":True,"prompt_asset_path":"../../../config/prompts/minimal-v1.json","system_id":"C"},
            {"adapter_enabled":True,"prompt_asset_path":"five-shot-v3.json","system_id":"D"},
        ]}
        alternate_system.write_bytes(canonical_line(alternate_system_value))
        altered,_=read_strict_json(harness_path)
        altered["system_set"]["source_path"]=alternate_system.as_posix()
        altered["system_set"]["source_sha256"]=hashlib.sha256(alternate_system.read_bytes()).hexdigest()
        for system in altered["system_set"]["systems"]:
            if system["system_id"] in "BD":
                system["prompt_asset"]={
                    **substitute,"source_path":alternate_prompt.as_posix(),
                    "source_sha256":hashlib.sha256(substitute_raw).hexdigest(),
                }
        harness_path.write_bytes(canonical_line(altered))
        try:
            with self.assertRaises(ContractError):
                evaluation_run_records_from_harness(evidence[2],evidence[4]["source_harness_manifest_path"])
        finally:
            harness_path.write_bytes(original)

        other=judgment_evidence_v4("ABC")
        mixed=list(copy.deepcopy(evidence)); mixed[3][0]=copy.deepcopy(other[3][0])
        with self.assertRaises(ContractError):
            validate_judgment_records(mixed[0],mixed[1],heldout_records=mixed[2],
                run_records=mixed[3],generation_manifest=mixed[4])

        # A complete-looking splice of 240 unrelated runs is not one formal generation run.
        broken=list(copy.deepcopy(evidence))
        for index,record in enumerate(broken[3]): record["run_id"]=f"spliced-run-{index:03d}"
        with self.assertRaises(ContractError):
            validate_judgment_records(broken[0],broken[1],heldout_records=broken[2],run_records=broken[3],generation_manifest=broken[4])
        broken=list(copy.deepcopy(evidence)); broken[3][0]["system_configuration_sha256"]="0"*64
        with self.assertRaises(ContractError):
            validate_judgment_records(broken[0],broken[1],heldout_records=broken[2],run_records=broken[3],generation_manifest=broken[4])

        # Neither a held-out prompt nor immutable generated bytes can be substituted.
        broken=list(copy.deepcopy(evidence)); broken[2][0]["prompt"]="Substituted held-out prompt"
        with self.assertRaises(ContractError):
            validate_judgment_records(
                broken[0], broken[1], heldout_records=broken[2], run_records=broken[3], generation_manifest=broken[4]
            )
        broken=list(copy.deepcopy(evidence)); broken[3][0]["raw_output"]="not json"
        broken[3][0]["response_sha256"]=hashlib.sha256(b"not json").hexdigest()
        with self.assertRaises(ContractError):
            validate_judgment_records(
                broken[0], broken[1], heldout_records=broken[2], run_records=broken[3], generation_manifest=broken[4]
            )

        uta=list(copy.deepcopy(evidence)); primary=next(item for item in uta[0] if item["judgment_round"]=="primary")
        primary["scores"]={"underlying_answer_quality":3,"metaphorical_coherence":3,"recipe_style_execution":"unable_to_assess"}; primary["resolution_status"]="pending_second"
        second=copy.deepcopy(primary); second.update({"judgment_id":"qual-v1-second-test","judgment_round":"second",
            "prior_judgment_id":primary["judgment_id"],"judge_identity":"judge-second","judge_session_id":"fresh-second-session",
            "scores":{"underlying_answer_quality":3,"metaphorical_coherence":3,"recipe_style_execution":3},"resolution_status":"resolved"})
        uta[0].append(second)
        self.assertEqual(validate_judgment_records(
            uta[0], uta[1], heldout_records=uta[2], run_records=uta[3], generation_manifest=uta[4]
        )["unresolved_count"],0)
        second["judge_session_id"]=primary["judge_session_id"]
        with self.assertRaises(ContractError):
            validate_judgment_records(
                uta[0], uta[1], heldout_records=uta[2], run_records=uta[3], generation_manifest=uta[4]
            )
        orphan=list(copy.deepcopy(evidence)); orphan_second=copy.deepcopy(orphan[0][0]); orphan_second.update({"judgment_id":"qual-v1-orphan",
            "judgment_round":"second","prior_judgment_id":"qual-v1-missing","judge_identity":"judge-second","judge_session_id":"fresh",
            "scores":{"underlying_answer_quality":3,"metaphorical_coherence":3,"recipe_style_execution":3},"resolution_status":"resolved"})
        orphan[0].append(orphan_second)
        with self.assertRaises(ContractError):
            validate_judgment_records(
                orphan[0], orphan[1], heldout_records=orphan[2], run_records=orphan[3], generation_manifest=orphan[4]
            )

    def test_judgment_human_calibration_shortfall_is_deterministic_and_executable(self):
        # Only canonically schema-valid responses may enter calibration. The
        # selector fills every available quota deterministically and reports a
        # shortfall rather than fabricating judgments for invalid outputs.
        one_system=judgment_evidence_v4(valid_systems="A")
        result=validate_judgment_records(
            one_system[0], one_system[1], heldout_records=one_system[2], run_records=one_system[3], generation_manifest=one_system[4]
        )
        self.assertEqual(result["human_response_achieved"],6)
        self.assertEqual(result["human_response_shortfall"],18)
        self.assertEqual(result["human_pair_achieved"],0)
        self.assertEqual(result["human_pair_shortfall"],15)

        comparison_systems=judgment_evidence_v4(valid_systems="BC")
        result=validate_judgment_records(
            comparison_systems[0], comparison_systems[1],
            heldout_records=comparison_systems[2], run_records=comparison_systems[3], generation_manifest=comparison_systems[4],
        )
        self.assertEqual(result["human_response_achieved"],12)
        self.assertEqual(result["human_response_shortfall"],12)
        self.assertEqual(result["human_pair_achieved"],15)
        self.assertEqual(result["human_pair_shortfall"],0)

    def test_response_similarity_aggregate_recomputes_and_requires_complete_coverage(self):
        evidence=response_similarity_evidence()
        def validate(items):
            return validate_response_similarity_records(*items[:4],heldout_records=items[4])
        result=validate(evidence)
        self.assertEqual(result["response_count"],240)
        broken=list(copy.deepcopy(evidence)); broken[2][0]["response_text_view_sha256"]="0"*64
        with self.assertRaises(ContractError): validate(broken)
        broken=list(copy.deepcopy(evidence)); broken[2]=broken[2][1:]
        with self.assertRaises(ContractError): validate(broken)
        broken=list(copy.deepcopy(evidence)); exact=next(item for item in broken[2] if item["exact_text_view_match"])
        exact["decision"]="no_concern"
        with self.assertRaises(ContractError): validate(broken)
        broken=list(copy.deepcopy(evidence)); broken[2][0]["exposure_status"]="exposed"
        with self.assertRaises(ContractError): validate(broken)
        broken=list(copy.deepcopy(evidence)); broken[3]["responses_sha256"]="0"*64
        with self.assertRaises(ContractError): validate(broken)
        broken=list(copy.deepcopy(evidence)); broken[3]["model_revision"]="0"*40
        with self.assertRaises(ContractError): validate(broken)
        broken=list(copy.deepcopy(evidence)); broken[3]["verifier_implementation_sha256"]="0"*64
        with self.assertRaises(ContractError): validate(broken)
        # Caller-controlled evidence cannot become authoritative by changing
        # every score and synchronising the reviews and captured hash/output.
        broken=list(copy.deepcopy(evidence))
        for record in broken[3]["records"]:
            for neighbour in record["neighbours"]:
                neighbour["semantic_score"]=-0.777
        for review in broken[2]:
            if review["semantic_score"] is not None:
                review["semantic_score"]=-0.777
        rewrite_semantic_stdout(broken[3],"response_similarity","records")
        with self.assertRaises(ContractError): validate(broken)
        broken=list(copy.deepcopy(evidence)); target=broken[3]["records"][0]
        target["response_pre_truncation_wordpieces"] += 1
        for review in broken[2]:
            if review["response_id"]==target["response_id"] and review["reference_collection"]==target["reference_collection"]:
                review["response_pre_truncation_wordpieces"] += 1
        rewrite_semantic_stdout(broken[3],"response_similarity","records")
        with self.assertRaises(ContractError): validate(broken)
        broken=list(copy.deepcopy(evidence)); broken[0]=broken[0][1:]
        with self.assertRaises(ContractError): validate(broken)
        broken=list(copy.deepcopy(evidence)); broken[0][0]["raw_output"]="not json"
        with self.assertRaises(ContractError): validate(broken)
        broken=list(copy.deepcopy(evidence)); broken[1]["training_responses"]=[]
        with self.assertRaises(ContractError): validate(broken)

    def test_versioned_evaluation_record_schemas_are_closed_and_executable(self):
        digest = "0" * 64
        records = {
            "schemas/evaluation-generation-manifest-v1.schema.json": {
                "schema_version":1,"manifest_id":"evaluation-generation-manifest-v1-test","run_id":"run-test",
                "source_harness_manifest_path":"experiments/runs/run-test/manifest.json",
                "source_harness_manifest_sha256":digest,"source_harness_prompts_sha256":digest,
                "source_harness_responses_sha256":digest,"source_harness_inspection_sha256":digest,
                "heldout_records_sha256":digest,
                "run_configuration_sha256":digest,"systems":[{"system_id":system,"adapter_enabled":system in "CD",
                    "prompt_asset_sha256":digest,"model_sha256":digest,"generation_config_sha256":digest,
                    "adapter_sha256":digest if system in "CD" else None,
                    "system_configuration_sha256":digest} for system in "ABCD"],"scheduled_attempt_count":240,
                "attempts_sha256":digest,"run_records_sha256":digest,
            },
            "schemas/prompt-overlap-review-v1.schema.json": {
                "record_schema_version":1,"review_id":"prompt-review-v1-001","matrix_prompt_id":"heldout-v1-001",
                "candidate_id":"candidate-1","candidate_original_sha256":digest,"candidate_normalized_sha256":digest,
                "candidate_pre_truncation_wordpieces":8,"candidate_semantic_input_truncated":False,
                "candidate_complete_text_reviewed":True,"review_scope":"selection",
                "review_round":"primary","trigger":"routine","reviewer_type":"llm_agent","reviewer_identity":"judge-v1",
                "blind_to_prior_decision":False,"prior_review_ids":[],"searched_source_identity_ids":[],
                "retrieval_coverage":[],"decision":"allow","neighbours":[],
                "rationale":"No duplicated scenario was found.","reviewed_at_utc":"2026-07-15T14:00:00Z"
            },
            "schemas/response-similarity-review-v1.schema.json": {
                "record_schema_version":1,"review_id":"response-review-v1-001","system_id":"C","response_id":"response-1",
                "response_original_sha256":digest,"response_text_view_sha256":digest,
                "response_pre_truncation_wordpieces":12,"response_semantic_input_truncated":False,
                "reference_collection":"training_responses","reference_id":"train-1","exposure_status":"exposed",
                "reference_original_sha256":digest,"reference_text_view_sha256":digest,
                "reference_pre_truncation_wordpieces":10,"reference_semantic_input_truncated":False,
                "retrieval_signals":["lexical","semantic"],"exact_text_view_match":False,
                "lexical_rank":1,"lexical_score":40,"semantic_rank":1,"semantic_score":0.3,
                "complete_text_reviewed":True,
                "decision":"no_concern","rationale":"Only generic overlap.","reviewer_type":"llm_agent","reviewer_identity":"judge-v1"
            },
            "schemas/qualitative-judgment-v1.schema.json": {
                "record_schema_version": 1, "judgment_id": "qual-v1-001", "protocol_sha256": digest,
                "heldout_records_sha256":digest,"run_records_sha256":digest,"generation_manifest_sha256":digest,
                "rubric_sha256": digest, "judge_manifest_sha256":digest,"instruction_sha256":digest,"packet_sha256":digest,
                "packet_id":"qual-packet-v1-000000000000000000000000",
                "prompt_id": "heldout-v1-001", "response_id": "response-1",
                "blinded_label": "candidate-001", "judge_role": "llm", "judge_identity": "judge-v1",
                "judge_session_id":"session-1","exposed_model_id":"GPT-5",
                "judgment_round": "primary","prior_judgment_id":None,"resolution_status":"pending_second",
                "scores": {"underlying_answer_quality": 2,
                "metaphorical_coherence": 2, "recipe_style_execution": "unable_to_assess"},
                "rationales": {"underlying_answer_quality": "Useful.", "metaphorical_coherence": "Coherent.",
                "recipe_style_execution": "Insufficient evidence."}, "recorded_at_utc": "2026-07-15T14:00:00Z"
            },
            "schemas/pairwise-judgment-v1.schema.json": {
                "record_schema_version": 1, "judgment_id": "pair-v1-001", "protocol_sha256": digest,
                "heldout_records_sha256":digest,"run_records_sha256":digest,"generation_manifest_sha256":digest,
                "judge_manifest_sha256":digest,"instruction_sha256":digest,"packet_sha256":digest,"renderer_id":"chatgnt-pairwise-json-v1",
                "packet_id":"pair-packet-v1-000000000000000000000000",
                "prompt_id": "heldout-v1-001", "response_a_id": "response-1", "response_b_id": "response-2",
                "order_schedule_sha256": digest, "judge_role": "human", "judge_identity": "reviewer-1",
                "judge_session_id":"session-1","exposed_model_id":None,
                "judgment_round": "human_calibration","prior_judgment_id":None,"resolution_status":"resolved",
                "choice": "tie", "rationale": "No meaningful advantage.",
                "recorded_at_utc": "2026-07-15T14:00:00Z"
            },
            "schemas/heldout-replacement-v1.schema.json": {
                "record_schema_version": 1, "replacement_record_id": "replace-v1-001",
                "matrix_prompt_id": "heldout-v1-001", "candidate_id": "candidate-1",
                "candidate_prompt":"Repeated prompt.","candidate_metadata":{
                    "intent_family":"advice_decision_support","reporting_slice":"target_use","input_form":"question",
                    "complexity":"standard","complexity_sources":[],"constraint_bearing":False,"robustness_role":None,
                    "withheld_domain":None,"topic":"work","user_goal":"choose","requested_task_or_artefact":"advice",
                    "scenario_summary":"Choosing between options.","important_constraints":[]},
                "original_sha256": digest, "normalized_sha256": digest, "reason": "exact_collision",
                "rationale": "Normalized prompt matches training.","source_identity_ids":["source-v1-training"],
                "retrieved_reference_ids":["train-1"],"retrieval_report_sha256":digest,
                "review_ids": ["prompt-review-v1-001","prompt-review-v1-002"],"replacement_status":"replaced",
                "replacement_candidate_id": "candidate-2", "author_identity": "author-1",
                "decision_identity": "reviewer-1", "recorded_at_utc": "2026-07-15T14:00:00Z"
            },
        }
        for relative_path, record in records.items():
            schema, _ = read_strict_json(Path(relative_path))
            validator = Draft202012Validator(schema, format_checker=FormatChecker())
            self.assertEqual(list(validator.iter_errors(record)), [], relative_path)
            with_unknown = copy.deepcopy(record)
            with_unknown["unknown"] = True
            self.assertTrue(list(validator.iter_errors(with_unknown)), relative_path)

    @patch("chatgnt.evaluation_protocol.validate_protocol_manifest", side_effect=frozen_manifest_test_result)
    def test_stage5_bundle_cross_record_contract_passes_and_detects_drift(self, _manifest):
        evidence = stage5_evidence()
        result = validate_stage5_freeze_bundle(*evidence)
        self.assertEqual(result["accepted_audit_count"], 6)
        broken = list(copy.deepcopy(evidence))
        broken[8]["prompt_reviews_sha256"] = "0" * 64
        with self.assertRaises(ContractError):
            validate_stage5_freeze_bundle(*broken)
        broken = list(copy.deepcopy(evidence))
        broken[1] = [item for item in broken[1] if item.get("trigger") != "accepted_audit"]
        broken[8]["prompt_reviews_sha256"] = canonical_records_sha256(broken[1])
        with self.assertRaises(ContractError):
            validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[4]["source-v1-training"][0]["text"]="tampered"
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); primary=next(item for item in broken[1] if item["candidate_id"]=="rejected-001" and item["review_round"]=="primary")
        primary["decision"]="allow"; broken[8]["prompt_reviews_sha256"]=canonical_records_sha256(broken[1])
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); neighbour=next(item for item in broken[1][0]["neighbours"] if "lexical" in item["retrieval_signals"])
        neighbour["lexical_score"] += 1; broken[8]["prompt_reviews_sha256"]=canonical_records_sha256(broken[1])
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[1][0]["retrieval_coverage"][0]["withheld_domain_checked"]=False
        broken[8]["prompt_reviews_sha256"]=canonical_records_sha256(broken[1])
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); audit=next(item for item in broken[1] if item.get("trigger")=="accepted_audit")
        audit["candidate_id"]="heldout-v1-001"; audit["candidate_original_sha256"]=text_identity(broken[0][0]["prompt"])["original_sha256"]
        audit["candidate_normalized_sha256"]=text_identity(broken[0][0]["prompt"])["normalized_sha256"]
        broken[8]["prompt_reviews_sha256"]=canonical_records_sha256(broken[1])
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[2][0]["replacement_candidate_id"]="rejected-001"
        broken[8]["replacement_log_sha256"]=canonical_records_sha256(broken[2])
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[6]["candidate_attestations"][0]["natural"]=False
        broken[8]["semantic_review_artifact_sha256"]=hashlib.sha256(canonical_json(broken[6]).encode()).hexdigest()
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[6]["embedding_model_revision"]="0"*40
        broken[8]["semantic_review_artifact_sha256"]=hashlib.sha256(canonical_json(broken[6]).encode()).hexdigest()
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[6]["verifier_implementation_sha256"]="0"*64
        broken[8]["semantic_review_artifact_sha256"]=hashlib.sha256(canonical_json(broken[6]).encode()).hexdigest()
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence))
        for record in broken[6]["retrieval_evidence"]:
            for neighbour in record["neighbours"]:
                neighbour["semantic_score"]=-0.777
        for review in broken[1]:
            for neighbour in review["neighbours"]:
                if neighbour["semantic_score"] is not None:
                    neighbour["semantic_score"]=-0.777
        rewrite_semantic_stdout(broken[6],"stage5","retrieval_evidence")
        broken[8]["prompt_reviews_sha256"]=canonical_records_sha256(broken[1])
        broken[8]["semantic_review_artifact_sha256"]=hashlib.sha256(canonical_json(broken[6]).encode()).hexdigest()
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); target=broken[6]["retrieval_evidence"][0]
        target["candidate_pre_truncation_wordpieces"] += 1
        for review in broken[1]:
            if review["candidate_id"]==target["candidate_id"]:
                review["candidate_pre_truncation_wordpieces"] += 1
        rewrite_semantic_stdout(broken[6],"stage5","retrieval_evidence")
        broken[8]["prompt_reviews_sha256"]=canonical_records_sha256(broken[1])
        broken[8]["semantic_review_artifact_sha256"]=hashlib.sha256(canonical_json(broken[6]).encode()).hexdigest()
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[4]["source-v1-training"][0]["metadata"]["topic"]=3
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[5][0]["notes"]="Substituted attestation notes."
        broken[8]["withheld_domain_checks_sha256"]=canonical_records_sha256(broken[5])
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[8]["frozen_at_utc"]="2999-01-01T00:00:00Z"
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[1][0]["reviewed_at_utc"]="2999-01-01T00:00:00Z"
        broken[8]["prompt_reviews_sha256"]=canonical_records_sha256(broken[1])
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[7]=broken[7][1:]
        # Even a caller who renumbers and rehashes the visible tail cannot erase a replacement-log attempt.
        previous=None
        for index,item in enumerate(broken[7]):
            item["authoring_index"]=index; item["previous_entry_sha256"]=previous
            base={key:item[key] for key in ("authoring_index","attempt_index_within_slot","matrix_prompt_id","candidate_id","final_for_slot","recorded_at_utc","previous_entry_sha256")}
            item["entry_sha256"]=hashlib.sha256(canonical_json(base).encode()).hexdigest(); previous=item["entry_sha256"]
        broken[8]["authoring_schedule_sha256"]=canonical_records_sha256(broken[7])
        broken[8]["authoring_ledger_entry_count"]=len(broken[7]); broken[8]["authoring_ledger_final_entry_sha256"]=previous
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)

    @patch("chatgnt.evaluation_protocol.validate_protocol_manifest", side_effect=frozen_manifest_test_result)
    def test_stage5_selection_only_rejection_requires_independent_confirmation_and_same_slot_replacement(self, _manifest):
        evidence=stage5_evidence(selection_only=True)
        self.assertEqual(validate_stage5_freeze_bundle(*evidence)["rejected_candidate_count"],1)
        broken=list(copy.deepcopy(evidence)); broken[1]=[item for item in broken[1] if item.get("trigger")!="selection_rejection"]
        broken[8]["prompt_reviews_sha256"]=canonical_records_sha256(broken[1])
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
        broken=list(copy.deepcopy(evidence)); broken[2][0]["matrix_prompt_id"]="heldout-v1-002"
        broken[8]["replacement_log_sha256"]=canonical_records_sha256(broken[2])
        with self.assertRaises(ContractError): validate_stage5_freeze_bundle(*broken)
