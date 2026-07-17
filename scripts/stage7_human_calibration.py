"""Collect and seal the one required project-author Stage 7 calibration sample."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from chatgnt.evaluation_protocol import read_jsonl, validate_judgment_records  # noqa: E402
from chatgnt.records import ContractError, canonical_line, strict_json_loads  # noqa: E402


def _choice(prompt: str, allowed: set[str]) -> str:
    while True:
        value = input(prompt).strip().lower()
        if value in allowed: return value
        print(f"Enter one of: {', '.join(sorted(allowed))}")


def collect(packets_path: Path, output: Path) -> None:
    packets = read_jsonl(packets_path)
    existing = read_jsonl(output) if output.exists() else []
    completed = {item["packet_id"] for item in existing}
    mode = "ab" if output.exists() else "xb"
    with output.open(mode) as handle:
        for number, packet in enumerate(packets, 1):
            if packet["packet_id"] in completed: continue
            print("\n" + "=" * 78)
            print(f"CALIBRATION {number}/{len(packets)} — {packet['kind']}")
            print("=" * 78 + "\n" + packet["packet_text"])
            if packet["kind"] == "qualitative":
                scores = {
                    "underlying_answer_quality": int(_choice("Underlying answer quality [1/2/3]: ", {"1", "2", "3"})),
                    "metaphorical_coherence": int(_choice("Metaphorical coherence [1/2/3]: ", {"1", "2", "3"})),
                    "recipe_style_execution": int(_choice("Recipe style execution [1/2/3]: ", {"1", "2", "3"})),
                }
                rationale = input("Brief reason: ").strip() or "Project-author assessment."
                decision = {"packet_id": packet["packet_id"], "kind": "qualitative", "scores": scores,
                            "rationale": rationale, "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds")}
            else:
                choice = _choice("Better response [a/b/tie]: ", {"a", "b", "tie"})
                rationale = input("Brief reason: ").strip() or "Project-author assessment."
                decision = {"packet_id": packet["packet_id"], "kind": "pairwise",
                            "choice": {"a": "response_a", "b": "response_b", "tie": "tie"}[choice],
                            "rationale": rationale, "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds")}
            handle.write(canonical_line(decision)); handle.flush()
    print(f"Complete: {len(read_jsonl(output))}/{len(packets)} decisions in {output}")


def seal(evaluation_dir: Path, heldout_path: Path, raw_path: Path) -> None:
    derived = evaluation_dir / "derived"; judging = evaluation_dir / "judging"
    decisions = {item["packet_id"]: item for item in read_jsonl(raw_path)}
    selected = read_jsonl(derived / "human-calibration-packets.jsonl")
    if set(decisions) != {item["packet_id"] for item in selected}:
        raise ContractError("human decisions do not exactly cover the deterministic calibration sample")
    q_primary = read_jsonl(judging / "qualitative-judgments-llm.jsonl")
    p_primary = read_jsonl(judging / "pairwise-judgments-llm.jsonl")
    q_by = {item["packet_id"]: item for item in q_primary}; p_by = {item["packet_id"]: item for item in p_primary}
    q_human = []; p_human = []
    for packet in selected:
        decision = decisions[packet["packet_id"]]
        if packet["kind"] == "qualitative":
            item = dict(q_by[packet["packet_id"]]); item.update({
                "judgment_id": f"qual-v1-human-{item['packet_id'].removeprefix('qual-packet-v1-')}",
                "judge_role": "human", "judge_identity": "project-author",
                "judge_session_id": "project-author-stage7-calibration-v1", "exposed_model_id": None,
                "judgment_round": "human_calibration", "scores": decision["scores"],
                "rationales": {key: decision["rationale"] for key in decision["scores"]},
                "recorded_at_utc": decision["recorded_at_utc"],
            }); q_human.append(item)
        else:
            item = dict(p_by[packet["packet_id"]]); item.update({
                "judgment_id": f"pair-v1-human-{item['packet_id'].removeprefix('pair-packet-v1-')}",
                "judge_role": "human", "judge_identity": "project-author",
                "judge_session_id": "project-author-stage7-calibration-v1", "exposed_model_id": None,
                "judgment_round": "human_calibration", "choice": decision["choice"],
                "rationale": decision["rationale"], "recorded_at_utc": decision["recorded_at_utc"],
            }); p_human.append(item)
    heldout = read_jsonl(heldout_path); runs = read_jsonl(derived / "run-records.jsonl")
    manifest = strict_json_loads((derived / "generation-manifest.json").read_text())
    report = validate_judgment_records(q_primary + q_human, p_primary + p_human,
                                       heldout_records=heldout, run_records=runs, generation_manifest=manifest)
    for name, records in (("qualitative-judgments-human.jsonl", q_human), ("pairwise-judgments-human.jsonl", p_human)):
        path = judging / name
        if path.exists(): raise ContractError(f"refusing to replace sealed human judgments: {path}")
        path.write_bytes(b"".join(canonical_line(item) for item in records))
    print(report)


def main() -> int:
    parser = argparse.ArgumentParser(); sub = parser.add_subparsers(dest="command", required=True)
    c = sub.add_parser("collect"); c.add_argument("--packets", type=Path, required=True); c.add_argument("--output", type=Path, required=True)
    s = sub.add_parser("seal"); s.add_argument("--evaluation-dir", type=Path, required=True); s.add_argument("--heldout", type=Path, required=True); s.add_argument("--raw", type=Path, required=True)
    args = parser.parse_args()
    if args.command == "collect": collect(args.packets, args.output)
    else: seal(args.evaluation_dir, args.heldout, args.raw)
    return 0


if __name__ == "__main__": raise SystemExit(main())
