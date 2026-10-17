#!/usr/bin/env python3
"""Atomic, evidence-based state for the single coauthor-invitation scenario.

The director reads Lark and supplies normalized observations; this helper never
claims to have contacted Lark or to infer semantic correctness by keywords.
"""
from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

SCHEMA_VERSION = 5
STAGES = tuple(f"S{i:02d}" for i in range(1, 8))
STATUSES = {"initializing", "running", "finalizing", "completed", "aborted"}
RESOURCE_TYPES = {"company": "chat", "mentor_dm": "chat", "boss_dm": "chat",
                  "landing": "document", "prd": "document", "prototype": "whiteboard",
                  "feedback": "base", "task": "task"}
KINDS = {"message", "card", "reaction", "document", "whiteboard", "comment", "base", "task"}
ORIGINS = {"seed", "player", "agent", "unknown"}
CRITERIA = {"consent", "accept", "reject", "idempotency", "unavailable", "consistency", "handoff"}
DECISIONS = {
    "landing_shared": {"message"}, "landing_understood": {"message", "card"},
    "materials_ready": {"document", "whiteboard", "base", "task"},
    "initial_judgment": {"message", "comment", "base"},
    "conflict_resolved": {"message", "comment", "document"},
    "design_updated": {"whiteboard", "comment"}, "rules_updated": {"document"},
    "submission": {"message", "card", "task"}, "handoff": {"message", "document", "comment"},
}
GATES = {"S01": ("landing_shared", "landing_understood"),
         "S02": ("materials_ready", "initial_judgment"),
         "S03": ("conflict_resolved",), "S04": ("design_updated", "rules_updated"),
         "S05": ("submission",), "S06": (), "S07": ("handoff",)}


def time(value):
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None:
        raise ValueError("timestamps must include a timezone")
    return result


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode()).hexdigest()


def atomic_write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def save(path, state):
    atomic_write(path, json.dumps(state, ensure_ascii=False, indent=2) + "\n")


@contextmanager
def lock(path):
    with Path(str(path) + ".lock").open("a+") as handle:
        fcntl.flock(handle, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle, fcntl.LOCK_UN)


def new_state(run_id, player_id, at):
    time(at)
    state = {
        "schema_version": SCHEMA_VERSION, "scenario": "coauthor-invitation",
        "run_id": run_id, "status": "initializing", "stage": "S01", "paused": False,
        "started_at": at, "updated_at": at, "requested_final_status": None,
        "player": {"open_id": player_id, "name": "实习生", "introduction": None, "corrections": []},
        "resources": {key: {"type": typ, "id": None, "url": None, "ready": False}
                      for key, typ in RESOURCE_TYPES.items()},
        "actors": {"hr": "company", "mentor": "mentor_dm", "boss": "boss_dm",
                   "designer": "company", "backend": "company", "operations": "company"},
        "cards": {}, "receipts": {}, "observations": [], "snapshots": {}, "decisions": {},
        "review": {"round": 0, "state": "not_started", "history": []},
        "conflict_started": False, "memory": [], "cursors": {},
        "runtime": {"heartbeat_id": None, "lease": {"owner_id": None, "expires_at": None},
                    "capabilities": {}, "last_poll_at": None, "paused_at": None, "pause_intervals": []},
    }
    validate(state)
    return state


def evidence(state, ids):
    if not isinstance(ids, list) or not ids or any(type(i) is not int for i in ids):
        raise ValueError("nonempty evidence_ids required")
    by_id = {item["id"]: item for item in state["observations"]}
    if any(i not in by_id for i in ids):
        raise ValueError("unknown evidence ID")
    return [by_id[i] for i in ids]


def review_current(state):
    review = state["review"]
    if review["state"] != "accepted" or not review["history"]:
        return False
    last = review["history"][-1]
    return all(state["snapshots"].get(key, {}).get("digest") == last["fingerprints"].get(key)
               for key in ("prd", "prototype"))


def validate(state):
    if state.get("schema_version") != 5 or state.get("scenario") != "coauthor-invitation":
        raise ValueError("historical save: retained read-only; no automatic scenario migration")
    if "mode" in state or "pacing" in state or "checkpoint_budget" in state:
        raise ValueError("only one scenario, without mode or checkpoint budgets")
    if any(state["runtime"].get(k) is not None for k in ("session_deadline_at", "story_deadline_at", "wait_deadline_at")):
        raise ValueError("no gameplay deadlines")
    if not state["run_id"].startswith("pm-one-day-") or not state["player"]["open_id"]:
        raise ValueError("run ID and player identity required")
    if state["stage"] not in STAGES or state["status"] not in STATUSES:
        raise ValueError("invalid lifecycle")
    if time(state["updated_at"]) < time(state["started_at"]):
        raise ValueError("update precedes start")
    if type(state["paused"]) is not bool:
        raise ValueError("paused must be boolean")
    if len(state["memory"]) > 12:
        raise ValueError("short-term memory limit is 12; introduction is stored separately")
    for key, typ in RESOURCE_TYPES.items():
        resource = state["resources"][key]
        if resource["type"] != typ or type(resource["ready"]) is not bool:
            raise ValueError("invalid resource")
        if resource["ready"] and (not resource["id"] or not resource["url"]):
            raise ValueError("ready resource needs verified ID and URL")
    registered = [r["id"] for r in state["resources"].values() if r["id"]]
    if len(set(registered)) != len(registered):
        raise ValueError("resources must have distinct IDs")
    observations = state["observations"]
    if [o["id"] for o in observations] != list(range(1, len(observations) + 1)):
        raise ValueError("evidence sequence is not contiguous")
    if len({o["key"] for o in observations}) != len(observations):
        raise ValueError("duplicate evidence keys")
    if state["review"]["round"] != len(state["review"]["history"]):
        raise ValueError("invalid review history")
    if state["review"]["state"] == "accepted" and not review_current(state):
        raise ValueError("accepted review must match current work")
    if state["status"] in {"completed", "aborted"}:
        if state["requested_final_status"] != state["status"]:
            raise ValueError("final outcome mismatch")
        if any(state["receipts"].get(k, {}).get("status") != "done"
               for k in ("final.diary", "final.notify", "final.stop")):
            raise ValueError("finalization receipts missing")
        if state["runtime"]["heartbeat_id"] or state["runtime"]["lease"]["owner_id"]:
            raise ValueError("final state must stop heartbeat and release lease")
    if state["status"] == "completed" and (state["stage"] != "S07" or not review_current(state)
                                           or "handoff" not in state["decisions"]):
        raise ValueError("completion requires current accepted review and handoff")


def assert_lease(state, owner, at):
    lease = state["runtime"]["lease"]
    if lease["owner_id"] != owner or not lease["expires_at"] or time(lease["expires_at"]) <= time(at):
        raise PermissionError("acquire a valid runner lease first")


def configure(state, patch):
    if set(patch) - {"resources", "cards", "runtime", "cursors", "memory"}:
        raise ValueError("use evidence/lifecycle commands for protected state")
    for key, value in patch.get("resources", {}).items():
        if key not in RESOURCE_TYPES or not isinstance(value, dict):
            raise ValueError("unknown resource")
        if set(value) & {"type"}:
            raise ValueError("resource type is fixed")
        old = state["resources"][key]
        if old["id"] and "id" in value and value["id"] != old["id"]:
            raise ValueError("cannot replace a registered resource")
        old.update(value)
    for mid, card in patch.get("cards", {}).items():
        if not card.get("actions") or card.get("chat_id") not in {
                state["resources"][k]["id"] for k in ("company", "mentor_dm", "boss_dm")}:
            raise ValueError("card must belong to a registered chat with action whitelist")
        if not card.get("version") or type(card.get("active")) is not bool:
            raise ValueError("card version and active flag required")
        state["cards"][mid] = card
    runtime = patch.get("runtime", {})
    if set(runtime) - {"heartbeat_id", "capabilities", "last_poll_at"}:
        raise ValueError("runtime patch cannot change lease or introduce deadlines")
    state["runtime"].update(runtime)
    state["cursors"].update(patch.get("cursors", {}))
    if "memory" in patch:
        state["memory"] = patch["memory"]


def observe(state, item, at):
    item = copy.deepcopy(item)
    if not item.get("key") or item.get("kind") not in KINDS or item.get("origin") not in ORIGINS:
        raise ValueError("observation requires stable key, supported kind and origin")
    if not isinstance(item.get("content"), dict):
        raise ValueError("normalized content object required")
    existing = next((o for o in state["observations"] if o["key"] == item["key"]), None)
    if existing:
        if existing["input_digest"] != digest(item):
            raise ValueError("same evidence key has different content")
        return existing["id"]
    rid = item.get("resource_id")
    resource_key = next((k for k, r in state["resources"].items() if r["id"] and r["id"] == rid), None)
    if resource_key is None:
        raise ValueError("out-of-run resource")
    kind, origin = item["kind"], item["origin"]
    expected = {"message": "chat", "card": "chat", "reaction": "chat", "comment": "document"}.get(kind, kind)
    if state["resources"][resource_key]["type"] != expected:
        raise ValueError("observation kind does not match resource")
    if origin == "player" and item.get("actor_id") != state["player"]["open_id"]:
        raise ValueError("player attribution requires verified current player ID")
    if origin == "seed" and kind not in {"document", "whiteboard", "base", "task"}:
        raise ValueError("seed is a material snapshot, not player input")
    if item.get("occurred_at"):
        if not time(state["started_at"]) <= time(item["occurred_at"]) <= time(at):
            raise ValueError("input time outside current run")
        if kind in {"message", "card", "reaction"} and any(
                time(interval["start"]) <= time(item["occurred_at"]) < time(interval["end"])
                for interval in state["runtime"]["pause_intervals"]):
            raise ValueError("interactive input occurred while paused; do not replay it as new work")
    elif kind in {"message", "card", "reaction"}:
        raise ValueError("interactive input needs actual source timestamp")
    if kind == "card":
        content = item["content"]
        card = state["cards"].get(content.get("message_id"), {})
        if (origin != "player" or not card.get("active") or card.get("chat_id") != rid
                or content.get("version") != card.get("version")
                or content.get("action") not in card.get("actions", [])):
            raise ValueError("unregistered, stale, or invalid card action")
        if card.get("purpose") == "invitation_sample" and card.get("rule_digest") != state["snapshots"].get("prd", {}).get("digest"):
            raise ValueError("sample no longer matches PRD")
    record = dict(item, id=len(state["observations"]) + 1, input_digest=digest(item),
                  observed_at=at, resource_key=resource_key, changed=False)
    if kind in {"document", "whiteboard", "base", "task"}:
        fingerprint = digest(item["content"])
        previous = state["snapshots"].get(resource_key)
        if (kind == "document" and previous and type(previous.get("revision")) is int
                and type(item.get("revision")) is int and item["revision"] < previous["revision"]):
            raise ValueError("stale document revision; reread instead of rolling back the snapshot")
        record["changed"] = previous is not None and previous["digest"] != fingerprint
        record["before_digest"] = previous["digest"] if previous else None
        record["digest"] = fingerprint
        state["snapshots"][resource_key] = {"digest": fingerprint, "evidence_id": record["id"],
                                               "revision": item.get("revision"), "observed_at": at}
        if record["changed"] and resource_key in {"prd", "prototype"}:
            if state["review"]["state"] == "accepted":
                state["review"]["state"] = "stale"
            state["decisions"].pop("handoff", None)
            if resource_key == "prd":
                for card in state["cards"].values():
                    if card.get("purpose") == "invitation_sample":
                        card["active"] = False
    state["observations"].append(record)
    return record["id"]


def introduce(state, data, at):
    item = evidence(state, [data["evidence_id"]])[0]
    if item["kind"] != "message" or item["origin"] != "player" or item["resource_key"] != "company":
        raise ValueError("introduction requires player's real company-chat message")
    text = item["content"].get("text", "").strip()
    if not text:
        raise ValueError("introduction source is empty")
    fields = data.get("fields", {})
    allowed = {"preferred_name", "stated_background", "learning_goal", "help_preference"}
    if set(fields) - allowed or any(not isinstance(v, str) or not v.strip() or v not in text for v in fields.values()):
        raise ValueError("introduction fields must quote explicitly stated information")
    player = state["player"]
    entry = {"evidence_id": item["id"], "text": text, "fields": fields,
             "skipped": bool(data.get("skipped", False)), "saved_at": at}
    if player["introduction"] is None:
        player["introduction"] = entry
    elif player["introduction"]["evidence_id"] != item["id"]:
        if not data.get("correction"):
            raise ValueError("use correction=true to amend fixed introduction memory")
        existing = next((c for c in player["corrections"] if c["evidence_id"] == item["id"]), None)
        if existing:
            if existing["fields"] != fields:
                raise ValueError("cannot rewrite a saved correction")
            return
        player["corrections"].append(entry)
    else:
        if fields != player["introduction"]["fields"]:
            raise ValueError("cannot rewrite original introduction")
        return
    if fields.get("preferred_name"):
        player["name"] = fields["preferred_name"]


def decide(state, data, at):
    key = data.get("key")
    if key not in DECISIONS or not data.get("reason", "").strip():
        raise ValueError("decision needs known key and reason")
    items = evidence(state, data.get("evidence_ids"))
    if not any(i["kind"] in DECISIONS[key] for i in items):
        raise ValueError("decision lacks relevant evidence kind")
    if key in {"landing_understood", "initial_judgment", "conflict_resolved"} and not any(i["origin"] == "player" for i in items):
        raise ValueError("understanding/judgment requires player evidence")
    if key == "landing_understood" and not any(i["origin"] == "player" and (
            (i["kind"] == "message" and i["content"].get("text", "").strip()) or
            (i["kind"] == "card" and isinstance(i["content"].get("form_value"), dict)
             and any(isinstance(v, str) and v.strip() for v in i["content"]["form_value"].values()))) for i in items):
        raise ValueError("opening a link or clicking a button is not evidence of understanding")
    if key == "landing_shared" and (not state["resources"]["landing"]["ready"] or
                                     state["receipts"].get("landing.shared", {}).get("status") != "done"):
        raise ValueError("Landing must be accessible and actually shared")
    if key == "materials_ready" and not all(r["ready"] for r in state["resources"].values()):
        raise ValueError("work objects are not ready")
    if key in {"design_updated", "rules_updated"}:
        target = "prototype" if key == "design_updated" else "prd"
        if not any(i["resource_key"] == target and i["changed"] for i in items):
            raise ValueError("actual content change required, not just a revision number")
        if not any(i["origin"] == "player" for i in items):
            raise ValueError("include player's decision/comment as well as unassigned snapshot changes")
    if key == "submission":
        if not any((i["origin"] == "player" and i["kind"] == "message") or
                   (i["kind"] == "card" and i["content"].get("action") == "request_review") or
                   (i["kind"] == "task" and i["content"].get("status") == "done") for i in items):
            raise ValueError("explicit review request or confirmed task completion required")
    if key == "handoff" and not review_current(state):
        raise ValueError("handoff requires current accepted review")
    state["decisions"][key] = dict(data, at=at)


def advance(state):
    stage = state["stage"]
    missing = [key for key in GATES[stage] if key not in state["decisions"]]
    if stage == "S01" and state["player"]["introduction"] is None:
        missing.append("introduction or explicit opt-out")
    if missing:
        raise ValueError("unmet work dependencies: " + ", ".join(missing))
    if stage == "S06" and not review_current(state):
        raise ValueError("review must pass on current work")
    if stage == "S07":
        raise ValueError("use finalize after handoff")
    state["stage"] = STAGES[STAGES.index(stage) + 1]
    state["status"] = "running"
    if state["stage"] == "S03":
        state["conflict_started"] = True


def review(state, data, at):
    if state["stage"] not in {"S06", "S07"} or "submission" not in state["decisions"]:
        raise ValueError("review requires a submitted work version")
    checks = data.get("checks", [])
    if len(checks) != len(CRITERIA) or {c.get("criterion") for c in checks} != CRITERIA:
        raise ValueError("review must cover all seven criteria exactly once")
    ids = data.get("snapshot_ids", {})
    for key in ("prd", "prototype"):
        snapshot = state["snapshots"].get(key)
        if not snapshot or ids.get(key) != snapshot["evidence_id"]:
            raise ValueError("review must reference latest PRD and prototype snapshots")
    for check in checks:
        if type(check.get("passed")) is not bool or not check.get("reason") or not check.get("location"):
            raise ValueError("criterion requires boolean outcome, reason and location")
        items = evidence(state, check.get("evidence_ids"))
        if check["criterion"] == "consistency" and not {"prd", "prototype"}.issubset({i["resource_key"] for i in items}):
            raise ValueError("consistency must compare both PRD and prototype")
        quote = check.get("quote", "")
        if not quote or not any(quote in json.dumps(i["content"], ensure_ascii=False) for i in items):
            raise ValueError("criterion must quote real saved content, including failed criteria")
        if any(i["resource_key"] in {"prd", "prototype"} and i["id"] != ids[i["resource_key"]] for i in items):
            raise ValueError("criterion cites stale work")
    result = dict(data, at=at, fingerprints={k: state["snapshots"][k]["digest"] for k in ("prd", "prototype")})
    state["review"]["history"].append(result)
    state["review"]["round"] += 1
    state["review"]["state"] = "accepted" if all(c["passed"] for c in checks) else "changes_requested"


def receipt(state, data, at):
    key, status = data.get("key"), data.get("status")
    if not key or status not in {"pending", "done"} or not isinstance(data.get("params"), dict):
        raise ValueError("receipt needs stable key, status and params")
    if status == "done" and not data.get("result"):
        raise ValueError("done receipt needs verified result")
    old = state["receipts"].get(key)
    if old:
        if old["params"] != data["params"] or (old["status"] == "done" and
                (status != "done" or old["result"] != data.get("result"))):
            raise ValueError("cannot reuse action key with different parameters/result")
    elif status == "done":
        raise ValueError("persist pending before external mutation")
    state["receipts"][key] = dict(data, at=at)


def _mutate(state, command, data, owner, at):
    validate(state)
    if not owner:
        raise ValueError("runner owner required")
    if time(at) < time(state["updated_at"]):
        raise ValueError("clock moved backwards")
    if state["status"] in {"completed", "aborted"}:
        raise ValueError("finished save is immutable")
    if command == "lease-acquire":
        lease = state["runtime"]["lease"]
        if time(data["expires_at"]) <= time(at):
            raise ValueError("lease expiry must be in the future")
        if lease["owner_id"] not in (None, owner) and time(lease["expires_at"]) > time(at):
            raise PermissionError("another runner holds the lease")
        lease.update(owner_id=owner, expires_at=data["expires_at"])
    else:
        assert_lease(state, owner, at)
        if state["paused"] and command not in {"resume", "pause", "finalize", "patch", "receipt", "lease-release", "finish"}:
            raise ValueError("paused: retain source cursor and read controls only")
        if state["status"] == "finalizing" and command not in {"receipt", "patch", "finish", "lease-release"}:
            raise ValueError("finalizing: finish cleanup, do not advance story")
        if command == "lease-release":
            state["runtime"]["lease"] = {"owner_id": None, "expires_at": None}
        elif command == "patch":
            configure(state, data)
        elif command == "observe":
            observe(state, data, at)
        elif command == "introduce":
            introduce(state, data, at)
        elif command == "decide":
            decide(state, data, at)
        elif command == "advance":
            advance(state)
        elif command == "review":
            review(state, data, at)
        elif command == "receipt":
            receipt(state, data, at)
        elif command in {"pause", "resume"}:
            if command == "pause" and not state["paused"]:
                state["runtime"]["paused_at"] = at
                state["paused"] = True
            elif command == "resume" and state["paused"]:
                state["runtime"]["pause_intervals"].append({"start": state["runtime"]["paused_at"], "end": at})
                state["runtime"]["paused_at"] = None
                state["paused"] = False
        elif command == "finalize":
            outcome = data.get("outcome")
            if outcome not in {"completed", "aborted"}:
                raise ValueError("invalid outcome")
            if outcome == "completed" and (state["stage"] != "S07" or not review_current(state)
                                             or "handoff" not in state["decisions"]):
                raise ValueError("cannot complete without current acceptance and handoff")
            state.update(status="finalizing", requested_final_status=outcome, paused=False)
        elif command == "finish":
            if state["status"] != "finalizing":
                raise ValueError("not finalizing")
            state["status"] = state["requested_final_status"]
            state["runtime"]["lease"] = {"owner_id": None, "expires_at": None}
        else:
            raise ValueError("unsupported command")
    state["updated_at"] = at
    validate(state)


def mutate(state, command, data, owner, at):
    candidate = copy.deepcopy(state)
    _mutate(candidate, command, data, owner, at)
    state.clear()
    state.update(candidate)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init")
    for arg in ("run-dir", "run-id", "player-open-id", "at"):
        init.add_argument("--" + arg, required=True)
    for name in ("validate", "export-log"):
        p = sub.add_parser(name)
        p.add_argument("--state", required=True)
        if name == "export-log":
            p.add_argument("--output", required=True)
    for name in ("lease-acquire", "lease-release", "patch", "observe", "introduce", "decide",
                 "advance", "review", "receipt", "pause", "resume", "finalize", "finish"):
        p = sub.add_parser(name)
        for arg in ("state", "owner-id", "at"):
            p.add_argument("--" + arg, required=True)
        if name == "lease-acquire":
            p.add_argument("--expires-at", required=True)
        elif name == "finalize":
            p.add_argument("--outcome", choices=["completed", "aborted"], required=True)
        elif name in {"patch", "observe", "introduce", "decide", "review", "receipt"}:
            p.add_argument("--input-json", required=True, help="JSON object or @path")
    args = parser.parse_args()
    try:
        if args.command == "init":
            state = new_state(args.run_id, args.player_open_id, args.at)
            run_dir = Path(args.run_dir)
            run_dir.mkdir(parents=True, exist_ok=False)
            save(run_dir / "state.json", state)
            print(json.dumps({"state": str(run_dir / "state.json"), "schema_version": 5}))
            return 0
        path = Path(args.state)
        with lock(path):
            state = json.loads(path.read_text(encoding="utf-8"))
            validate(state)
            if args.command == "export-log":
                # No identity IDs or raw card payloads in narrative export.
                rows = [{"t": o["observed_at"], "kind": o["kind"], "who": o["origin"],
                         "text": o["content"].get("text", ""),
                         "data": {"evidence_id": o["id"], "resource": o["resource_key"], "changed": o["changed"]}}
                        for o in state["observations"]]
                if Path(args.output).resolve() == path.resolve():
                    raise ValueError("export must not overwrite state")
                atomic_write(args.output, "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows))
            elif args.command != "validate":
                data = {}
                if hasattr(args, "input_json"):
                    raw = args.input_json
                    data = json.loads(Path(raw[1:]).read_text(encoding="utf-8") if raw.startswith("@") else raw)
                    if not isinstance(data, dict):
                        raise ValueError("input must be a JSON object")
                if hasattr(args, "expires_at"):
                    data["expires_at"] = args.expires_at
                if hasattr(args, "outcome"):
                    data["outcome"] = args.outcome
                mutate(state, args.command, data, args.owner_id, args.at)
                save(path, state)
        print(json.dumps({"ok": True, "stage": state["stage"], "status": state["status"],
                          "evidence_count": len(state["observations"])}, ensure_ascii=False))
        return 0
    except (ValueError, KeyError, TypeError, OSError) as exc:
        parser.exit(1, f"state error: {exc}\n")


if __name__ == "__main__":
    raise SystemExit(main())
