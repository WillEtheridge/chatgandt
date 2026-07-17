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


RULE = "─" * 78


def _amount(value: object) -> str:
    """Render JSON numbers naturally without changing the recorded response."""
    return f"{value:g}" if isinstance(value, float) else str(value)


def _render_response(response: dict[str, object]) -> str:
    ingredients = response["ingredients"]
    method = response["method"]
    assert isinstance(ingredients, list)
    assert isinstance(method, list)

    lines = [str(response["title"]), "", "Ingredients"]
    for ingredient in ingredients:
        assert isinstance(ingredient, dict)
        lines.append(
            f"  • {_amount(ingredient['amount'])} {ingredient['unit']} {ingredient['name']}"
        )
    lines.extend(["", "Method"])
    for step, instruction in enumerate(method, 1):
        lines.append(f"  {step}. {instruction}")
    lines.extend(["", f"Garnish\n  {response['garnish']}"])
    return "\n".join(lines)


def _load_display_packets(packets_path: Path, selected: list[dict[str, object]]) -> dict[str, dict[str, object]]:
    """Load the structured counterparts and prove they are the selected blind packets."""
    derived = packets_path.parent
    qualitative = {
        item["packet_id"]: item for item in read_jsonl(derived / "qualitative-packets.jsonl")
    }
    pairwise = {
        item["packet_id"]: item for item in read_jsonl(derived / "pairwise-packets.jsonl")
    }
    display_packets: dict[str, dict[str, object]] = {}
    for selected_packet in selected:
        source = (qualitative if selected_packet["kind"] == "qualitative" else pairwise).get(
            selected_packet["packet_id"]
        )
        if source is None:
            raise ContractError("calibration packet is missing its structured display record")
        if any(source[key] != selected_packet[key] for key in ("packet_id", "packet_sha256", "packet_text")):
            raise ContractError("structured display record does not match the selected blind packet")
        display_packet = dict(source)
        display_packet["kind"] = selected_packet["kind"]
        display_packets[str(selected_packet["packet_id"])] = display_packet
    return display_packets


def _render_packet(packet: dict[str, object], number: int, total: int) -> str:
    """Present a blind evaluation packet as a readable recipe card, not raw JSON."""
    header = f"CALIBRATION {number}/{total} · " + (
        "ONE CANDIDATE RESPONSE" if packet["kind"] == "qualitative" else "A OR B COMPARISON"
    )
    lines = ["", RULE, header, RULE, "", "User prompt", str(packet["user_prompt"]), ""]
    if packet["kind"] == "qualitative":
        response = packet["response"]
        assert isinstance(response, dict)
        lines.extend(["Candidate response", _render_response(response), "", RULE])
        lines.extend(
            [
                "Score each dimension: 1 = fails, 2 = usable but imperfect, 3 = strong.",
                "• Answer quality — useful, accurate answer to the prompt",
                "• Metaphor — recipe elements meaningfully express that answer",
                "• Recipe style — natural cocktail voice and a method that progresses it",
            ]
        )
    else:
        response_a = packet["response_a"]
        response_b = packet["response_b"]
        assert isinstance(response_a, dict)
        assert isinstance(response_b, dict)
        lines.extend(
            [
                "Response A",
                _render_response(response_a),
                "",
                RULE,
                "Response B",
                _render_response(response_b),
                "",
                RULE,
                "Choose the response that better answers the prompt as a coherent cocktail recipe.",
                "Choose tie only when neither is meaningfully better.",
            ]
        )
    return "\n".join(lines)


def collect(packets_path: Path, output: Path) -> None:
    packets = read_jsonl(packets_path)
    display_packets = _load_display_packets(packets_path, packets)
    existing = read_jsonl(output) if output.exists() else []
    completed = {item["packet_id"] for item in existing}
    mode = "ab" if output.exists() else "xb"
    with output.open(mode) as handle:
        for number, packet in enumerate(packets, 1):
            if packet["packet_id"] in completed: continue
            display_packet = display_packets[packet["packet_id"]]
            print(_render_packet(display_packet, number, len(packets)))
            if packet["kind"] == "qualitative":
                scores = {
                    "underlying_answer_quality": int(_choice("Answer quality [1/2/3]: ", {"1", "2", "3"})),
                    "metaphorical_coherence": int(_choice("Metaphor [1/2/3]: ", {"1", "2", "3"})),
                    "recipe_style_execution": int(_choice("Recipe style [1/2/3]: ", {"1", "2", "3"})),
                }
                rationale = input("Optional note (Enter to skip): ").strip() or "Project-author assessment."
                decision = {"packet_id": packet["packet_id"], "kind": "qualitative", "scores": scores,
                            "rationale": rationale, "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds")}
            else:
                choice = _choice("Preferred response [a/b/tie]: ", {"a", "b", "tie"})
                rationale = input("Optional note (Enter to skip): ").strip() or "Project-author assessment."
                decision = {"packet_id": packet["packet_id"], "kind": "pairwise",
                            "choice": {"a": "response_a", "b": "response_b", "tie": "tie"}[choice],
                            "rationale": rationale, "recorded_at_utc": datetime.now(timezone.utc).isoformat(timespec="microseconds")}
            handle.write(canonical_line(decision)); handle.flush()
            print(f"Saved {number}/{len(packets)} decisions.")
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
