"""Collect one pipeline run from Claude Code transcripts.

Reads the main session transcript and its subagent transcripts, then writes:

  <out>/messages/NNN-<from>-to-<to>-<type>.md  one file per message (sanitized, public)
  <out>/messages.jsonl                          the same messages, one JSON per line
  <out>/flow.md                                 Mermaid sequence diagram of the messages
  <out>/usage.csv                               one row per API call
  <out>/agents.csv                              totals per agent instance
  <out>/edges.csv                               size of each message
  <out>/summary.md                              run totals and API-equivalent cost
  <out>/transcripts/                            raw JSONL copies (private, git-ignored)

Usage:
  uv run python research/tools/collect.py --session <id> --out research/runs/F1/auto/r1
  uv run python research/tools/collect.py --worktree <path> --out ...   (latest session there)
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import shutil
import sys
from collections import defaultdict
from collections.abc import Callable
from dataclasses import asdict, dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sanitize import find_leaks, sanitize

REPO = Path(__file__).resolve().parents[2]
PRICING = json.loads((REPO / "research/config/pricing.json").read_text(encoding="utf-8"))["models"]
DEFAULT_PROJECTS = Path.home() / ".claude" / "projects"

FIX_ROLES = {"implementer", "test-writer"}
REVIEW_ROLES = {"reviewer", "qa", "security"}
TOKEN_FIELDS = ("input", "cache_write_5m", "cache_write_1h", "cache_read", "output", "thinking")


# ---------------------------------------------------------------- transcript reading


def read_jsonl(path: Path) -> list[dict]:
    records = []
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return records


def text_of(content) -> str:
    """Plain text of a message content (string or list of blocks); '' for tool results."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(
        b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text"
    )


def is_tool_result(content) -> bool:
    return isinstance(content, list) and any(
        isinstance(b, dict) and b.get("type") == "tool_result" for b in content
    )


@dataclass
class Call:
    """One API call (deduplicated by message id)."""

    agent: str
    agent_type: str
    turn: int
    model: str
    timestamp: str
    input: int = 0
    cache_write_5m: int = 0
    cache_write_1h: int = 0
    cache_read: int = 0
    output: int = 0
    thinking: int = 0

    def cost(self) -> float | None:
        price = PRICING.get(self.model)
        if not price:
            return None
        return (
            self.input * price["input"]
            + self.cache_write_5m * price["cache_write_5m"]
            + self.cache_write_1h * price["cache_write_1h"]
            + self.cache_read * price["cache_read"]
            + self.output * price["output"]
        ) / 1_000_000


def calls_from(
    records: list[dict], agent: str, agent_type: str, turn_of: Callable[[int], int]
) -> list[Call]:
    """Build one Call per assistant message id. A response is written as several records
    (one per content block) that repeat the same usage, so the last record of an id wins."""
    by_id: dict[str, tuple[int, dict]] = {}
    for idx, rec in enumerate(records):
        if rec.get("type") != "assistant":
            continue
        msg = rec.get("message") or {}
        if not msg.get("usage"):
            continue
        key = msg.get("id") or rec.get("requestId") or rec.get("uuid")
        by_id[key] = (idx, rec)
    calls = []
    for idx, rec in sorted(by_id.values(), key=lambda t: t[0]):
        msg = rec["message"]
        usage = msg["usage"]
        cache = usage.get("cache_creation") or {}
        cw_5m = cache.get("ephemeral_5m_input_tokens")
        cw_1h = cache.get("ephemeral_1h_input_tokens")
        if cw_5m is None and cw_1h is None:
            cw_5m, cw_1h = usage.get("cache_creation_input_tokens", 0), 0
        calls.append(
            Call(
                agent=agent,
                agent_type=agent_type,
                turn=turn_of(idx),
                model=msg.get("model", ""),
                timestamp=rec.get("timestamp", ""),
                input=usage.get("input_tokens", 0),
                cache_write_5m=cw_5m or 0,
                cache_write_1h=cw_1h or 0,
                cache_read=usage.get("cache_read_input_tokens", 0),
                output=usage.get("output_tokens", 0),
                thinking=(usage.get("output_tokens_details") or {}).get("thinking_tokens", 0),
            )
        )
    return calls


# ---------------------------------------------------------------- messages


@dataclass
class Message:
    seq: int = 0
    sender: str = ""
    receiver: str = ""
    type: str = ""
    timestamp: str = ""
    agent: str = ""
    agent_id: str = ""
    turn: int = 0
    reply_to: int | None = None
    chars: int = 0
    tokens_est: int = 0
    wait_s: float | None = None  # human inputs: seconds since the main session's last reply
    text: str = field(default="", repr=False)


def estimate_tokens(text: str) -> int:
    """Rough estimate: about 4 ASCII chars per token, about 1 token per non-ASCII char."""
    ascii_chars = sum(1 for ch in text if ord(ch) < 128)
    return round(ascii_chars / 4 + (len(text) - ascii_chars))


def classify_prompt(role: str, turn: int) -> str:
    if turn == 1:
        return "T-TASK"
    if role in FIX_ROLES:
        return "T-FIX"
    if role == "tester":
        return "T-RERUN"
    if role in REVIEW_ROLES:
        return "T-REREVIEW"
    return "T-FOLLOWUP"


def classify_report(role: str, text: str) -> str:
    if role == "tester":
        return "R-FAIL" if re.search(r"결과\s*[:：]\s*\**\s*FAIL", text) else "R-DONE"
    if role in REVIEW_ROLES:
        return "R-FINDINGS"
    return "R-DONE"


def seconds_between(start: str, end: str) -> float | None:
    from datetime import datetime

    try:
        a = datetime.fromisoformat(start)
        b = datetime.fromisoformat(end)
    except ValueError:
        return None
    return round((b - a).total_seconds(), 1)


def human_inputs(main_records: list[dict]) -> list[Message]:
    msgs = []
    last_reply_ts = ""
    for rec in main_records:
        if rec.get("type") == "assistant" and not rec.get("isSidechain"):
            last_reply_ts = rec.get("timestamp", last_reply_ts)
            continue
        if rec.get("type") != "user" or rec.get("isSidechain") or rec.get("isMeta"):
            continue
        content = (rec.get("message") or {}).get("content")
        if is_tool_result(content):
            continue
        text = text_of(content).strip()
        if not text or "<task-notification>" in text or text.startswith("<local-command"):
            continue
        msgs.append(
            Message(
                sender="human",
                receiver="main",
                type="H-INPUT",
                timestamp=rec.get("timestamp", ""),
                wait_s=seconds_between(last_reply_ts, rec.get("timestamp", ""))
                if last_reply_ts
                else None,
                text=text,
            )
        )
    return msgs


# A SendMessage continuation is written into the subagent transcript as a meta user
# record with this header, followed by the message text.
CONTINUATION_RE = re.compile(r"^The coordinator sent a message while you were working:\s*")


def turn_text(rec: dict) -> str | None:
    """Text of a user record that starts a turn, or None if the record does not."""
    if rec.get("type") != "user":
        return None
    content = (rec.get("message") or {}).get("content")
    if is_tool_result(content):
        return None
    text = text_of(content).strip()
    if not text:
        return None
    if rec.get("isMeta"):
        match = CONTINUATION_RE.match(text)
        return text[match.end() :].strip() if match else None
    return text


def agent_turns(records: list[dict]) -> tuple[list[tuple[int, dict]], Callable[[int], int]]:
    """User records that start a turn (the spawn prompt, then each continuation message),
    and a function mapping a record index to its turn number."""
    starts = [(idx, rec) for idx, rec in enumerate(records) if turn_text(rec) is not None]
    start_idx = [i for i, _ in starts]

    def turn_of(i: int) -> int:
        return max(sum(1 for s in start_idx if s <= i), 1)

    return starts, turn_of


def turn_report(records: list[dict]) -> tuple[str, str]:
    """Final report of one turn: the last SubagentHandback message if the harness uses
    hand-back (desktop app), otherwise the last assistant text."""
    handback, text = ("", ""), ("", "")
    for r in records:
        if r.get("type") != "assistant":
            continue
        content = (r.get("message") or {}).get("content") or []
        ts = r.get("timestamp", "")
        for block in content if isinstance(content, list) else []:
            if block.get("type") == "tool_use" and block.get("name") == "SubagentHandback":
                handback = ((block.get("input") or {}).get("message", "").strip(), ts)
        t = text_of(content).strip()
        if t:
            text = (t, ts)
    return handback if handback[0] else text


def system_prompt_chars(records: list[dict]) -> int | None:
    """Size of the first recorded system prompt snapshot (the fixed prompt layer)."""
    for r in records:
        att = r.get("attachment") or {}
        if r.get("type") == "attachment" and att.get("type") == "prompt_snapshot":
            return sum(len(part) for part in att.get("systemPrompt") or [])
    return None


# ---------------------------------------------------------------- main


def find_session(args) -> Path:
    projects = Path(args.projects_dir)
    if args.session:
        hits = list(projects.glob(f"*/{args.session}.jsonl"))
        if not hits:
            sys.exit(f"session transcript not found: {args.session}")
        return hits[0]
    slug = re.sub(r"[^A-Za-z0-9-]", "-", str(Path(args.worktree).resolve()))
    folder = projects / slug
    sessions = sorted(folder.glob("*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not sessions:
        sys.exit(f"no sessions in {folder}")
    return sessions[-1]


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_-]", "_", name)


def first_timestamp(path: Path) -> str:
    records = read_jsonl(path)
    return records[0].get("timestamp", "") if records else ""


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--session", help="main session id")
    src.add_argument("--worktree", help="project folder; uses its most recent session")
    ap.add_argument("--out", required=True, help="run folder to write into")
    ap.add_argument("--projects-dir", default=str(DEFAULT_PROJECTS))
    ap.add_argument("--no-copy", action="store_true", help="do not copy raw transcripts")
    args = ap.parse_args()

    main_path = find_session(args)
    out = Path(args.out)
    main_records = read_jsonl(main_path)
    session_id = main_path.stem

    # Agent tool calls in the main transcript (tool_use id -> input), used as a fallback role.
    spawn_inputs: dict[str, dict] = {}
    for rec in main_records:
        for block in (rec.get("message") or {}).get("content") or []:
            if (
                isinstance(block, dict)
                and block.get("type") == "tool_use"
                and block.get("name") in ("Agent", "Task")
            ):
                spawn_inputs[block["id"]] = block.get("input", {})

    calls = calls_from(main_records, "main", "main", lambda i: 0)
    messages = human_inputs(main_records)

    sub_dir = main_path.with_suffix("") / "subagents"
    agent_files = (
        sorted(sub_dir.glob("agent-*.jsonl"), key=first_timestamp) if sub_dir.exists() else []
    )
    name_count: dict[str, int] = defaultdict(int)
    agent_rows = []
    for path in agent_files:
        agent_id = path.stem.removeprefix("agent-")
        meta_path = path.with_suffix(".meta.json")
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        role = (
            meta.get("agentType")
            or spawn_inputs.get(meta.get("toolUseId"), {}).get("subagent_type")
            or "agent"
        )
        name_count[role] += 1
        name = role if name_count[role] == 1 else f"{role}#{name_count[role]}"
        records = read_jsonl(path)
        starts, turn_of = agent_turns(records)
        calls.extend(calls_from(records, name, role, turn_of))

        for turn, (start, rec) in enumerate(starts, start=1):
            end = starts[turn][0] if turn < len(starts) else len(records)
            messages.append(
                Message(
                    sender="main",
                    receiver=name,
                    type=classify_prompt(role, turn),
                    timestamp=rec.get("timestamp", ""),
                    agent=name,
                    agent_id=agent_id,
                    turn=turn,
                    text=turn_text(rec) or "",
                )
            )
            report, report_ts = turn_report(records[start + 1 : end])
            if report:
                messages.append(
                    Message(
                        sender=name,
                        receiver="main",
                        type=classify_report(role, report),
                        timestamp=report_ts,
                        agent=name,
                        agent_id=agent_id,
                        turn=turn,
                        text=report,
                    )
                )
        agent_rows.append(
            {
                "agent": name,
                "agent_type": role,
                "agent_id": agent_id,
                "description": meta.get("description", ""),
                "turns": len(starts),
                "system_prompt_chars": system_prompt_chars(records),
            }
        )

    # Order, number, sanitize, and link each report to the prompt it answers.
    messages.sort(key=lambda m: m.timestamp)
    last_prompt: dict[tuple[str, int], int] = {}
    for seq, m in enumerate(messages, start=1):
        m.seq = seq
        m.text = sanitize(m.text)
        m.chars = len(m.text)
        m.tokens_est = estimate_tokens(m.text)
        if m.sender == "main" and m.agent:
            last_prompt[(m.agent, m.turn)] = seq
        elif m.receiver == "main" and m.agent:
            m.reply_to = last_prompt.get((m.agent, m.turn))

    leaks = [f"#{m.seq}: {leak}" for m in messages for leak in find_leaks(m.text)]
    if leaks:
        print("Personal data still present after sanitizing; nothing written:")
        print("\n".join(f"  {leak}" for leak in leaks))
        return 2

    write_outputs(
        out, session_id, main_path, agent_files, messages, calls, agent_rows, args.no_copy
    )
    print(
        f"session {session_id}: {len(messages)} messages, {len(agent_rows)} subagents, "
        f"{len(calls)} API calls -> {out}"
    )
    return 0


# ---------------------------------------------------------------- outputs


def write_outputs(out, session_id, main_path, agent_files, messages, calls, agent_rows, no_copy):
    main_prompt_chars = system_prompt_chars(read_jsonl(main_path))
    msg_dir = out / "messages"
    if msg_dir.exists():
        shutil.rmtree(msg_dir)
    msg_dir.mkdir(parents=True)

    for m in messages:
        fname = f"{m.seq:03d}-{safe_name(m.sender)}-to-{safe_name(m.receiver)}-{m.type}.md"
        front = {k: v for k, v in asdict(m).items() if k != "text"}
        lines = ["---"]
        lines += [f"{k}: {json.dumps(v, ensure_ascii=False)}" for k, v in front.items()]
        lines += ["---", "", m.text, ""]
        (msg_dir / fname).write_text("\n".join(lines), encoding="utf-8")

    with (out / "messages.jsonl").open("w", encoding="utf-8") as fh:
        for m in messages:
            fh.write(json.dumps(asdict(m), ensure_ascii=False) + "\n")

    with (out / "edges.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            ["seq", "from", "to", "type", "turn", "reply_to", "chars", "tokens_est", "timestamp"]
        )
        for m in messages:
            w.writerow(
                [
                    m.seq,
                    m.sender,
                    m.receiver,
                    m.type,
                    m.turn,
                    m.reply_to or "",
                    m.chars,
                    m.tokens_est,
                    m.timestamp,
                ]
            )

    with (out / "usage.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        if calls:
            w.writerow(list(asdict(calls[0]).keys()) + ["cost_usd"])
        for c in calls:
            cost = c.cost()
            w.writerow(list(asdict(c).values()) + ["" if cost is None else f"{cost:.6f}"])

    totals: dict[str, dict] = {}
    for c in calls:
        t = totals.setdefault(
            c.agent, {"calls": 0, "cost_usd": 0.0, "model": c.model, **{k: 0 for k in TOKEN_FIELDS}}
        )
        t["calls"] += 1
        if c.model and c.model not in t["model"].split("+"):
            t["model"] = f"{t['model']}+{c.model}" if t["model"] else c.model
        for k in TOKEN_FIELDS:
            t[k] += getattr(c, k)
        t["cost_usd"] += c.cost() or 0.0
    info = {r["agent"]: r for r in agent_rows}
    order = ["main"] + [r["agent"] for r in agent_rows]

    with (out / "agents.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(
            [
                "agent",
                "agent_type",
                "model",
                "turns",
                "system_prompt_chars",
                "calls",
                *TOKEN_FIELDS,
                "cost_usd",
            ]
        )
        for a in order:
            t = totals.get(a)
            if not t:
                continue
            r = info.get(
                a, {"agent_type": "main", "turns": "", "system_prompt_chars": main_prompt_chars}
            )
            w.writerow(
                [
                    a,
                    r["agent_type"],
                    t["model"],
                    r["turns"],
                    r["system_prompt_chars"] or "",
                    t["calls"],
                    *(t[k] for k in TOKEN_FIELDS),
                    f"{t['cost_usd']:.4f}",
                ]
            )

    write_flow(out / "flow.md", messages)
    write_human_log(out / "human-log.md", messages)
    write_summary(out / "summary.md", session_id, messages, totals, order)

    if not no_copy:
        raw = out / "transcripts"
        if raw.exists():
            shutil.rmtree(raw)
        (raw / "subagents").mkdir(parents=True)
        shutil.copy2(main_path, raw / main_path.name)
        for p in agent_files:
            shutil.copy2(p, raw / "subagents" / p.name)
            meta = p.with_suffix(".meta.json")
            if meta.exists():
                shutil.copy2(meta, raw / "subagents" / meta.name)


def write_flow(path: Path, messages: list[Message]) -> None:
    def pid(name: str) -> str:
        return {"human": "Human", "main": "Main"}.get(name, safe_name(name))

    participants: list[str] = []
    for m in messages:
        for p in (m.sender, m.receiver):
            if p not in participants:
                participants.append(p)
    lines = ["# 메시지 흐름", "", "```mermaid", "sequenceDiagram"]
    lines += [f"    participant {pid(p)} as {p}" for p in participants]
    for m in messages:
        arrow = "-->>" if m.receiver == "main" and m.sender != "human" else "->>"
        lines.append(
            f"    {pid(m.sender)}{arrow}{pid(m.receiver)}: #{m.seq} {m.type} (~{m.tokens_est} tok)"
        )
    lines += ["```", ""]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_human_log(path: Path, messages: list[Message]) -> None:
    """Human interventions, derived from the transcript. Researchers may add notes below."""
    humans = [m for m in messages if m.sender == "human"]
    total_wait = sum(m.wait_s or 0 for m in humans)
    lines = [
        "# 사람 개입 기록",
        "",
        f"- 사람 메시지: {len(humans)}개",
        f"- 메인의 직전 응답부터 사람 입력까지 걸린 시간 합계: {total_wait / 60:.1f}분",
        "",
        "| # | 시각 | 대기(분) | 글자 수 | 첫 줄 |",
        "|---|---|---|---|---|",
    ]
    for m in humans:
        first = m.text.strip().splitlines()[0][:80].replace("|", r"\|") if m.text.strip() else ""
        wait = f"{m.wait_s / 60:.1f}" if m.wait_s is not None else ""
        lines.append(f"| {m.seq} | {m.timestamp} | {wait} | {m.chars} | {first} |")
    lines += [
        "",
        "## 연구자 메모",
        "",
        "(개입 시점 H1~H4 구분, 결정 내용 등을 여기에 덧붙입니다.)",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


def write_summary(path: Path, session_id, messages, totals, order) -> None:
    def fmt(n: float) -> str:
        return f"{int(n):,}"

    grand = {"calls": 0, "cost_usd": 0.0, **{k: 0 for k in TOKEN_FIELDS}}
    for t in totals.values():
        for k in grand:
            grand[k] += t[k]
    comm = sum(m.tokens_est for m in messages if "human" not in (m.sender, m.receiver))
    lines = [
        "# 실행 요약",
        "",
        f"- 메인 세션: `{session_id}`",
        f"- 메시지: {len(messages)}개 (에이전트 간 메시지 토큰 추정 합계 ~{fmt(comm)})",
        f"- API 호출: {fmt(grand['calls'])}회",
        f"- API 환산 비용: ${grand['cost_usd']:.4f}",
        "",
        "## 에이전트별 토큰",
        "",
        "| 에이전트 | 모델 | 호출 | input | cache write | cache read | output | 비용(USD) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for a in order:
        t = totals.get(a)
        if not t:
            continue
        cw = t["cache_write_5m"] + t["cache_write_1h"]
        lines.append(
            f"| {a} | {t['model']} | {fmt(t['calls'])} | {fmt(t['input'])} | {fmt(cw)} | "
            f"{fmt(t['cache_read'])} | {fmt(t['output'])} | {t['cost_usd']:.4f} |"
        )
    cw = grand["cache_write_5m"] + grand["cache_write_1h"]
    lines.append(
        f"| **합계** | | {fmt(grand['calls'])} | {fmt(grand['input'])} | {fmt(cw)} | "
        f"{fmt(grand['cache_read'])} | {fmt(grand['output'])} | {grand['cost_usd']:.4f} |"
    )
    lines += [
        "",
        "메시지 토큰은 글자 수 기반 추정치입니다. API 호출 토큰은 트랜스크립트의 usage 값입니다.",
        "",
    ]
    path.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())
