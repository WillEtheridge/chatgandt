"""Verify the frozen Stage 3 evaluation protocol."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from chatgnt.evaluation_protocol import (
    CALIBRATION_PATH,
    RESPONSE_CALIBRATION_PATH,
    embed_texts_with_diagnostics,
    lexical_neighbours,
    load_protocol,
    read_jsonl,
    response_similarity_text_view,
    semantic_neighbours,
    validate_calibration_records,
    validate_judge_calibration,
    validate_judge_manifest,
    validate_protocol_manifest,
    validate_response_similarity_calibration,
)
from chatgnt.records import ContractError, read_strict_json
from jsonschema import Draft202012Validator


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--semantic", action="store_true", help="download/load the pinned embedding model and exercise semantic retrieval")
    arguments = parser.parse_args()
    try:
        protocol, protocol_digest = load_protocol()
        calibration = validate_calibration_records()
        judge_calibration = validate_judge_calibration()
        judge_manifest, judge_manifest_digest = validate_judge_manifest()
        response_calibration = validate_response_similarity_calibration()
        records = read_jsonl(CALIBRATION_PATH)
        corpus = [{"record_id": item["existing_id"], "text": item["existing_prompt"]} for item in records]
        lexical_hits = 0
        for item in records:
            neighbours = lexical_neighbours(item["candidate_prompt"], corpus, top_k=5)
            lexical_hits += int(item["existing_id"] in {value["record_id"] for value in neighbours})
        semantic_result = {"executed": False, "expected_match_recall_at_5": None}
        if arguments.semantic:
            selected = protocol["contamination"]["semantic"]
            texts = [item["existing_prompt"] for item in records] + [item["candidate_prompt"] for item in records]
            vectors, diagnostics = embed_texts_with_diagnostics(texts, selected["model_id"], selected["revision"])
            split = len(records)
            corpus_vectors = [(records[index]["existing_id"], vectors[index]) for index in range(split)]
            hits = 0
            for index, item in enumerate(records):
                neighbours = semantic_neighbours(vectors[split + index], corpus_vectors, top_k=5)
                hits += int(item["existing_id"] in {value["record_id"] for value in neighbours})
            long_index = next(
                index for index, item in enumerate(records)
                if item["case_type"] == "supplied_text_over_256_wordpieces"
            )
            long_diagnostics = {
                "existing": diagnostics[long_index],
                "candidate": diagnostics[split + long_index],
            }
            if not all(value["semantic_input_truncated"] for value in long_diagnostics.values()):
                raise ContractError("over-256-wordpiece calibration case did not exercise truncation")
            semantic_result = {
                "executed": True,
                "expected_match_recall_at_5": hits / len(records),
                "long_supplied_text_diagnostic": long_diagnostics,
            }
            response_records = read_jsonl(RESPONSE_CALIBRATION_PATH)
            response_cases = []
            for case in response_records:
                texts = [response_similarity_text_view("", case["query_response"])] + [
                    response_similarity_text_view("", item["response"]) for item in case["references"]
                ]
                response_vectors, response_diagnostics = embed_texts_with_diagnostics(
                    texts, selected["model_id"], selected["revision"]
                )
                ranked = semantic_neighbours(
                    response_vectors[0],
                    [(item["reference_id"], response_vectors[index + 1]) for index, item in enumerate(case["references"])],
                    top_k=5,
                )
                ranked_ids = [item["record_id"] for item in ranked]
                if (
                    case["expected_target_id"] not in ranked_ids
                    or case["hard_distractor_id"] not in ranked_ids
                    or ranked_ids.index(case["expected_target_id"]) >= ranked_ids.index(case["hard_distractor_id"])
                ):
                    raise ContractError("response calibration target did not outrank its hard distractor semantically")
                response_cases.append({
                    "case_id":case["case_id"], "ranked_reference_ids":ranked_ids,
                    "tokenization_diagnostics":response_diagnostics,
                })
            semantic_result["response_similarity_calibration"] = response_cases
        protocol_manifest = validate_protocol_manifest()
        paths = {
            "protocol": PROJECT_ROOT / "config" / "evaluation-protocol-v1.json",
            "protocol_schema": PROJECT_ROOT / protocol["protocol_schema_path"],
            "evaluation_generation_manifest_schema": PROJECT_ROOT / protocol["evaluation_generation_manifest_schema_path"],
            "rubric": PROJECT_ROOT / protocol["qualitative_rubric_path"],
            "judge_manifest": PROJECT_ROOT / protocol["judge_manifest_path"],
            "judge_calibration": PROJECT_ROOT / protocol["judge_calibration_path"],
            "heldout_prompt_schema": PROJECT_ROOT / protocol["heldout_prompt_schema_path"],
            "prompt_overlap_review_schema": PROJECT_ROOT / protocol["prompt_overlap_review_schema_path"],
            "response_similarity_review_schema": PROJECT_ROOT / protocol["response_similarity_review_schema_path"],
            "response_similarity_evidence_schema": PROJECT_ROOT / protocol["response_similarity_evidence_schema_path"],
            "source_identity_schema": PROJECT_ROOT / protocol["source_identity_schema_path"],
            "review_artifact_schema": PROJECT_ROOT / protocol["review_artifact_schema_path"],
            "withheld_domain_check_schema": PROJECT_ROOT / protocol["withheld_domain_check_schema_path"],
            "heldout_freeze_bundle_schema": PROJECT_ROOT / protocol["heldout_freeze_bundle_schema_path"],
            "stage5_semantic_review_schema": PROJECT_ROOT / protocol["stage5_semantic_review_schema_path"],
            "stage3_verification_evidence_schema": PROJECT_ROOT / protocol["stage3_verification_evidence_schema_path"],
            "qualitative_judgment_schema": PROJECT_ROOT / protocol["qualitative_judgment_schema_path"],
            "pairwise_judgment_schema": PROJECT_ROOT / protocol["pairwise_judgment_schema_path"],
            "heldout_replacement_schema": PROJECT_ROOT / protocol["heldout_replacement_schema_path"],
            "contamination_calibration": PROJECT_ROOT / protocol["contamination_calibration_path"],
            "response_similarity_calibration": PROJECT_ROOT / protocol["response_similarity_calibration_path"],
        }
        for name, path in paths.items():
            if not path.is_file() or path.stat().st_size == 0:
                raise ContractError(f"protocol asset missing or empty: {name}")
        for name in ("protocol_schema","evaluation_generation_manifest_schema","heldout_prompt_schema","prompt_overlap_review_schema",
            "response_similarity_review_schema","response_similarity_evidence_schema","source_identity_schema","heldout_freeze_bundle_schema","stage5_semantic_review_schema","stage3_verification_evidence_schema",
            "review_artifact_schema","withheld_domain_check_schema",
            "qualitative_judgment_schema","pairwise_judgment_schema","heldout_replacement_schema"):
            schema, _ = read_strict_json(paths[name])
            Draft202012Validator.check_schema(schema)
        if lexical_hits != len(records):
            raise ContractError("lexical calibration expected-match recall@5 is below 1.0")
        result = {
            "result": "pass",
            "status": protocol["status"],
            "protocol_id": protocol["protocol_id"],
            "protocol_sha256": protocol_digest,
            "protocol_manifest": protocol_manifest,
            "judge_manifest_sha256": judge_manifest_digest,
            "asset_sha256": {key: file_digest(path) for key, path in paths.items()},
            "calibration": calibration,
            "judge_calibration": judge_calibration,
            "response_similarity_calibration": response_calibration,
            "retrieval_calibration": {
                "case_count": len(records),
                "lexical_expected_match_recall_at_5": lexical_hits / len(records),
                "semantic": semantic_result,
                "interpretation": "retrieval recall is a diagnostic; semantic collision decisions remain human-readable judgments",
            },
        }
    except (ContractError, OSError, ValueError) as exc:
        print(json.dumps({"result": "fail", "error": str(exc)}, sort_keys=True), file=sys.stderr)
        return 1
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
