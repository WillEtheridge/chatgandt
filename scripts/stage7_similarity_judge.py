"""Run bounded, blinded batch review over the Stage 7 similarity queue."""

from __future__ import annotations

import argparse
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from stage7_similarity import read_jsonl
from chatgnt.records import ContractError, canonical_line, strict_json_loads

ROOT = Path(__file__).resolve().parents[1]
SCHEMA = ROOT / "schemas/stage7-similarity-batch-decision-v1.schema.json"
MODEL = "gpt-5.6-terra"


def invoke(batch_id: str, groups: list[list[dict]], schema: Path) -> dict:
    sections = []
    expected = []
    for group_number, group in enumerate(groups, 1):
        sections.append(f"QUERY {group_number}:\n{group[0]['text_a']}")
        for item in group:
            expected.append(item["review_key"])
            sections.append(f"REFERENCE {item['review_key']}:\n{item['text_b']}")
    prompt = """You are performing a blinded response-similarity audit. For every reference, compare the COMPLETE query and reference texts. Return review_flag only when there is distinctive substantive copying, an unusually reusable sequence or wording, or (between generated outputs) clear generic template collapse. Shared JSON/cocktail structure, ordinary advice, broad concepts, common ingredient quantities, and generic cocktail metaphors are not concerns. Otherwise return no_concern. Do not infer identities or exposure. Use each supplied review_key exactly once. Keep each rationale to one short sentence. Do not use tools or outside information.\n\n""" + "\n\n".join(sections)
    with tempfile.TemporaryDirectory(prefix="chatgnt-similarity-") as directory:
        output = Path(directory) / "decision.json"
        command = ["codex", "exec", "--ephemeral", "--ignore-user-config", "--ignore-rules",
                   "--sandbox", "read-only", "--skip-git-repo-check", "--json", "-C", directory,
                   "--model", MODEL, "-c", 'model_reasoning_effort="low"',
                   "--output-schema", str(schema), "--output-last-message", str(output), "-"]
        completed = subprocess.run(command, input=prompt, text=True, capture_output=True)
        if completed.returncode:
            raise ContractError(f"similarity batch {batch_id} failed: {completed.stderr[-1000:]}")
        value = strict_json_loads(output.read_text())
        decisions = value["decisions"]
        actual = [item["review_key"] for item in decisions]
        if len(actual) != len(set(actual)) or set(actual) != set(expected):
            raise ContractError(f"similarity batch {batch_id} returned incomplete or extra keys")
        thread_id = None
        for line in completed.stdout.splitlines():
            try: event = json.loads(line)
            except json.JSONDecodeError: continue
            if event.get("type") == "thread.started": thread_id = event.get("thread_id")
        if not thread_id:
            raise ContractError(f"similarity batch {batch_id} lacks a thread ID")
        return {"batch_id": batch_id, "thread_id": thread_id,
                "stdout_sha256": hashlib.sha256(completed.stdout.encode()).hexdigest(),
                "decisions": decisions}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("queue", type=Path); parser.add_argument("output", type=Path)
    parser.add_argument("--workers", type=int, default=4); parser.add_argument("--responses-per-context", type=int, default=2)
    parser.add_argument("--references-per-context", type=int, default=12)
    args = parser.parse_args()
    queue = read_jsonl(args.queue)
    groups_by_response = defaultdict(list)
    exact_decisions = []
    for item in queue:
        if item["exact_text_view_match"]:
            exact_decisions.append({"review_key": item["review_key"], "decision": "review_flag",
                                    "rationale": "The complete canonical texts are exactly identical."})
        else:
            groups_by_response[item["response_id"]].append(item)
    raw_path = args.output.with_suffix(".raw.jsonl")
    existing = read_jsonl(raw_path) if raw_path.exists() else []
    completed_keys = {decision["review_key"] for item in existing for decision in item["decisions"]}
    response_groups = [[item for item in groups_by_response[key] if item["review_key"] not in completed_keys]
                       for key in sorted(groups_by_response)]
    response_groups = [group[index:index + args.references_per_context]
                       for group in response_groups if group
                       for index in range(0, len(group), args.references_per_context)]
    batches = [response_groups[index:index + args.responses_per_context]
               for index in range(0, len(response_groups), args.responses_per_context)]
    jobs = []
    for batch in batches:
        keys = sorted(item["review_key"] for group in batch for item in group)
        batch_id = "similarity-batch-" + hashlib.sha256("|".join(keys).encode()).hexdigest()[:16]
        jobs.append((batch_id, batch))
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {executor.submit(invoke, batch_id, batch, SCHEMA): batch_id for batch_id, batch in jobs}
        failures = []
        for future in as_completed(futures):
            try:
                result = future.result()
            except BaseException as exc:
                failures.append({"batch_id": futures[future], "error": str(exc)})
                print(json.dumps({"incomplete": futures[future]}), flush=True)
                continue
            with raw_path.open("ab") as handle: handle.write(canonical_line(result))
            print(json.dumps({"completed": result["batch_id"]}), flush=True)
    if failures:
        print(json.dumps({"result": "incomplete", "failed_contexts": len(failures)}))
    raw = read_jsonl(raw_path)
    if len({item["thread_id"] for item in raw}) != len(raw):
        raise ContractError("similarity review lacks complete fresh batch contexts")
    first_decision = {}
    for batch in raw:
        for decision in batch["decisions"]:
            first_decision.setdefault(decision["review_key"], decision)
    decisions = exact_decisions + list(first_decision.values())
    if len(decisions) != len(queue) or {item["review_key"] for item in decisions} != {item["review_key"] for item in queue}:
        raise ContractError("similarity decisions do not cover the queue exactly")
    by_queue = {item["review_key"]: index for index, item in enumerate(queue)}
    decisions.sort(key=lambda item: by_queue[item["review_key"]])
    args.output.write_bytes(b"".join(canonical_line(item) for item in decisions))
    print(json.dumps({"result": "complete", "contexts": len(raw), "decisions": len(decisions),
                      "flags": sum(item["decision"] == "review_flag" for item in decisions)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
