"""Build and validate the frozen Stage 7 response-similarity audit."""

from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatgnt.evaluation_protocol import (  # noqa: E402
    canonical_records_sha256,
    lexical_neighbours,
    read_jsonl,
    response_similarity_text_view,
    validate_response_similarity_records,
)
from chatgnt.records import canonical_json, canonical_line, strict_json_loads  # noqa: E402


def _json_response(value: dict[str, Any]) -> str:
    return canonical_json(value)


def inputs(run_records: Path) -> tuple[list[dict[str, Any]], dict[str, list[dict[str, Any]]]]:
    responses = [
        {key: item[key] for key in ("response_id", "prompt_id", "system_id", "raw_output", "parsed_response")}
        for item in read_jsonl(run_records)
    ]
    worked = strict_json_loads((ROOT / "data/prompt-engineering/worked-examples-v1.json").read_text())
    training = read_jsonl(ROOT / "data/dataset-v1/frozen-v1.2/train.jsonl")
    references = {
        "worked_example_responses": [
            {"reference_id": item["example_id"], "raw_output": _json_response(item["assistant_response"]),
             "parsed_response": item["assistant_response"]}
            for item in worked["worked_examples"]
        ],
        "training_responses": [
            {"reference_id": item["example_id"], "raw_output": _json_response(item["assistant_response"]),
             "parsed_response": item["assistant_response"]}
            for item in training
        ],
    }
    return responses, references


def prepare_bundle(run_records: Path, output: Path) -> None:
    responses, references = inputs(run_records)
    now = datetime.now(timezone.utc).isoformat(timespec="microseconds")
    bundle = {
        "artifact_id": "response-similarity-evidence-v1-heldout-evaluation-v1-20260717-run01",
        "verifier_identity": "canonical-stage7-semantic-verifier",
        "started_at_utc": now,
        "verified_at_utc": now,
        "responses": responses,
        "references": references,
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(bundle, indent=2, sort_keys=True) + "\n")


def build_queue(run_records: Path, evidence_path: Path, output: Path) -> None:
    responses, references = inputs(run_records)
    evidence = strict_json_loads(evidence_path.read_text())
    evidence_by_pair = {(item["response_id"], item["reference_collection"]): item for item in evidence["records"]}
    views = {item["response_id"]: response_similarity_text_view(item["raw_output"], item["parsed_response"])
             for item in responses}
    queue = []
    for response in responses:
        collections = {
            **references,
            "heldout_system_responses": [
                {"reference_id": item["response_id"], "raw_output": item["raw_output"],
                 "parsed_response": item["parsed_response"]}
                for item in responses
                if item["system_id"] == response["system_id"] and item["response_id"] != response["response_id"]
            ],
        }
        response_view = views[response["response_id"]]
        for collection, records in collections.items():
            corpus = [{"record_id": item["reference_id"],
                       "text": response_similarity_text_view(item["raw_output"], item["parsed_response"])}
                      for item in records]
            lexical = lexical_neighbours(response_view, corpus, 5)
            semantic = evidence_by_pair[(response["response_id"], collection)]["neighbours"]
            exact = {item["record_id"] for item in corpus if item["text"] == response_view}
            ids = sorted({item["record_id"] for item in lexical} | {item["reference_id"] for item in semantic} | exact)
            by_id = {item["record_id"]: item["text"] for item in corpus}
            for reference_id in ids:
                key = hashlib.sha256(f"{response['response_id']}|{collection}|{reference_id}".encode()).hexdigest()[:20]
                queue.append({
                    "review_key": f"similarity-{key}",
                    "response_id": response["response_id"],
                    "reference_collection": collection,
                    "reference_id": reference_id,
                    "exact_text_view_match": reference_id in exact,
                    "text_a": response_view,
                    "text_b": by_id[reference_id],
                })
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(b"".join(canonical_line(item) for item in queue))
    print(canonical_json({"result": "complete", "review_count": len(queue), "queue_sha256": canonical_records_sha256(queue)}))


def assemble(run_records: Path, evidence_path: Path, queue_path: Path, decisions_path: Path,
             heldout_path: Path, output: Path) -> None:
    responses, references = inputs(run_records)
    evidence = strict_json_loads(evidence_path.read_text())
    queue = read_jsonl(queue_path)
    decisions = {item["review_key"]: item for item in read_jsonl(decisions_path)}
    evidence_by_pair = {(item["response_id"], item["reference_collection"]): item for item in evidence["records"]}
    response_by_id = {item["response_id"]: item for item in responses}
    reference_by_collection = {name: {item["reference_id"]: item for item in records} for name, records in references.items()}
    for response in responses:
        reference_by_collection.setdefault("heldout_system_responses", {})
        reference_by_collection["heldout_system_responses"].update({
            item["response_id"]: {"reference_id": item["response_id"], "raw_output": item["raw_output"],
                                  "parsed_response": item["parsed_response"]}
            for item in responses if item["system_id"] == response["system_id"]
        })
    exposure = {"A": set(), "B": {"worked_example_responses"}, "C": {"training_responses"},
                "D": {"worked_example_responses", "training_responses"}}
    reviews = []
    for item in queue:
        response = response_by_id[item["response_id"]]
        reference = reference_by_collection[item["reference_collection"]][item["reference_id"]]
        evidence_item = evidence_by_pair[(item["response_id"], item["reference_collection"])]
        response_view = response_similarity_text_view(response["raw_output"], response["parsed_response"])
        reference_view = response_similarity_text_view(reference["raw_output"], reference["parsed_response"])
        corpus = [{"record_id": record["reference_id"],
                   "text": response_similarity_text_view(record["raw_output"], record["parsed_response"])}
                  for record in (references[item["reference_collection"]]
                                 if item["reference_collection"] != "heldout_system_responses" else
                                 [{"reference_id": r["response_id"], "raw_output": r["raw_output"],
                                   "parsed_response": r["parsed_response"]} for r in responses
                                  if r["system_id"] == response["system_id"] and r["response_id"] != response["response_id"]])]
        lexical = {v["record_id"]: (rank, v["lexical_score"])
                   for rank, v in enumerate(lexical_neighbours(response_view, corpus, 5), 1)}
        semantic = {v["reference_id"]: v for v in evidence_item["neighbours"]}
        diagnostic = {v["reference_id"]: v for v in evidence_item["reference_diagnostics"]}[item["reference_id"]]
        signals = (["exact"] if item["exact_text_view_match"] else [])
        if item["reference_id"] in lexical: signals.append("lexical")
        if item["reference_id"] in semantic: signals.append("semantic")
        decision = decisions[item["review_key"]]
        within = item["reference_collection"] == "heldout_system_responses"
        if item["exact_text_view_match"]:
            verdict = "generic_collapse_flag" if within else "exact_project_response"
            rationale = "The complete canonical response text is an exact match."
        else:
            verdict, rationale = decision["decision"], decision["rationale"]
        lex = lexical.get(item["reference_id"]); sem = semantic.get(item["reference_id"])
        reviews.append({
            "record_schema_version": 1, "review_id": f"response-review-v1-{item['review_key']}",
            "system_id": response["system_id"], "response_id": response["response_id"],
            "response_original_sha256": hashlib.sha256(response["raw_output"].encode()).hexdigest(),
            "response_text_view_sha256": hashlib.sha256(response_view.encode()).hexdigest(),
            "response_pre_truncation_wordpieces": evidence_item["response_pre_truncation_wordpieces"],
            "response_semantic_input_truncated": evidence_item["response_semantic_input_truncated"],
            "reference_collection": item["reference_collection"], "reference_id": item["reference_id"],
            "reference_original_sha256": hashlib.sha256(reference["raw_output"].encode()).hexdigest(),
            "reference_text_view_sha256": hashlib.sha256(reference_view.encode()).hexdigest(),
            "reference_pre_truncation_wordpieces": diagnostic["reference_pre_truncation_wordpieces"],
            "reference_semantic_input_truncated": diagnostic["reference_semantic_input_truncated"],
            "exposure_status": "within_system_diversity" if within else
                ("exposed" if item["reference_collection"] in exposure[response["system_id"]] else "diagnostic_not_exposed"),
            "retrieval_signals": signals, "exact_text_view_match": item["exact_text_view_match"],
            "lexical_rank": lex[0] if lex else None, "lexical_score": lex[1] if lex else None,
            "semantic_rank": sem["semantic_rank"] if sem else None,
            "semantic_score": sem["semantic_score"] if sem else None,
            "complete_text_reviewed": True, "decision": verdict, "rationale": rationale,
            "reviewer_type": "llm_agent", "reviewer_identity": "openai-codex-cli-gpt-5.6-terra-batched-blind-review",
        })
    heldout = read_jsonl(heldout_path)
    report = validate_response_similarity_records(responses, references, reviews, evidence, heldout_records=heldout)
    output.write_bytes(b"".join(canonical_line(item) for item in reviews))
    by_system = {}
    for system in "ABCD":
        records = [item for item in reviews if item["system_id"] == system]
        by_system[system] = {
            "review_count": len(records),
            "decisions": dict(sorted(Counter(item["decision"] for item in records).items())),
            "by_exposure_status": {
                status: dict(sorted(Counter(item["decision"] for item in records if item["exposure_status"] == status).items()))
                for status in ("exposed", "diagnostic_not_exposed", "within_system_diversity")
            },
        }
    summary = {"schema_version": 1, **report, "systems": by_system,
               "overall_decisions": dict(sorted(Counter(item["decision"] for item in reviews).items())),
               "responses_with_flags": len({item["response_id"] for item in reviews if item["decision"] != "no_concern"})}
    output.with_name("summary.json").write_bytes(canonical_line(summary))
    print(canonical_json(summary))


def main() -> int:
    parser = argparse.ArgumentParser()
    subs = parser.add_subparsers(dest="command", required=True)
    p = subs.add_parser("prepare-bundle"); p.add_argument("run_records", type=Path); p.add_argument("output", type=Path)
    q = subs.add_parser("build-queue"); q.add_argument("run_records", type=Path); q.add_argument("evidence", type=Path); q.add_argument("output", type=Path)
    a = subs.add_parser("assemble"); a.add_argument("run_records", type=Path); a.add_argument("evidence", type=Path); a.add_argument("queue", type=Path); a.add_argument("decisions", type=Path); a.add_argument("heldout", type=Path); a.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.command == "prepare-bundle": prepare_bundle(args.run_records, args.output)
    elif args.command == "build-queue": build_queue(args.run_records, args.evidence, args.output)
    else: assemble(args.run_records, args.evidence, args.queue, args.decisions, args.heldout, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
