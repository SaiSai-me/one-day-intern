#!/usr/bin/env python3
"""Atomic state, receipt, lease, log, and migration helper for one-day-intern."""

from __future__ import annotations

import argparse
import copy
import fcntl
import json
import os
import tempfile
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Iterator


SCHEMA_VERSION = 4
ACTIVE_STATUSES = {"initializing", "running", "finalizing"}
FINAL_STATUSES = {"completed", "aborted"}
ALL_STATUSES = ACTIVE_STATUSES | FINAL_STATUSES
ROOM_LAYOUTS = {"company_with_role_rooms", "legacy_four_room"}
ROOM_KEYS = ("company", "mentor_dm", "boss_dm")
LEGACY_ROOM_KEYS = ("lobby", "mentor", "research", "review")
CHECKPOINT_KEYS = ("onboarding", "problem_metric", "evidence_scope", "first_submit", "micro_revision", "final_decision")


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def parse_object(value: str, label: str) -> dict[str, Any]:
    parsed = json.loads(value)
    if not isinstance(parsed, dict):
        raise ValueError(f"{label} must be a JSON object")
    return parsed


def atomic_write_json(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=False)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        directory_fd = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def state_lock(state_path: Path) -> Iterator[None]:
    lock_path = state_path.with_suffix(state_path.suffix + ".lock")
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def validate_state(state: dict[str, Any]) -> None:
    errors: list[str] = []
    if state.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    if state.get("status") not in ALL_STATUSES:
        errors.append("status is invalid")
    if state.get("requested_final_status") not in (None, *FINAL_STATUSES):
        errors.append("requested_final_status is invalid")
    if not isinstance(state.get("run_id"), str) or not state["run_id"].startswith("pm-one-day-"):
        errors.append("run_id must start with pm-one-day-")
    if state.get("current_beat") not in {f"E{i:02d}" for i in range(1, 11)}:
        errors.append("current_beat must be E01..E10")
    room_layout = state.get("room_layout")
    if room_layout not in ROOM_LAYOUTS:
        errors.append("room_layout is invalid")
    rooms = state.get("rooms")
    if room_layout == "company_with_role_rooms":
        if not isinstance(rooms, dict) or any(key not in rooms for key in ROOM_KEYS):
            errors.append("rooms must contain company/mentor_dm/boss_dm")
    chat_ids = state.get("chat_ids")
    if room_layout == "legacy_four_room":
        if not isinstance(chat_ids, dict) or any(key not in chat_ids for key in LEGACY_ROOM_KEYS):
            errors.append("legacy chat_ids must contain lobby/mentor/research/review")
    actors = state.get("actors")
    if not isinstance(actors, dict):
        errors.append("actors must be an object")
    else:
        for persona, actor in actors.items():
            if not isinstance(actor, dict):
                errors.append(f"actors.{persona} must be an object")
                continue
            if actor.get("room_key") not in (*ROOM_KEYS, *LEGACY_ROOM_KEYS):
                errors.append(f"actors.{persona}.room_key is invalid")
            if not isinstance(actor.get("memory", []), list):
                errors.append(f"actors.{persona}.memory must be an array")
    cursors = state.get("last_message_time_by_chat")
    expected_cursor_keys = ROOM_KEYS if room_layout == "company_with_role_rooms" else LEGACY_ROOM_KEYS
    if not isinstance(cursors, dict) or any(key not in cursors for key in expected_cursor_keys):
        errors.append("last_message_time_by_chat must contain layout room keys")
    artifacts = state.get("artifacts")
    if not isinstance(artifacts, dict):
        errors.append("artifacts must be an object")
    else:
        for key in ("task_progress", "action_receipts", "finalization"):
            if not isinstance(artifacts.get(key), dict):
                errors.append(f"artifacts.{key} must be an object")
        data_dashboard = artifacts.get("data_dashboard")
        if not isinstance(data_dashboard, dict):
            errors.append("artifacts.data_dashboard must be an object")
        else:
            if data_dashboard.get("type") != "sheet":
                errors.append("artifacts.data_dashboard.type must be sheet")
            if data_dashboard.get("status") not in {"not_created", "ready"}:
                errors.append("artifacts.data_dashboard.status is invalid")
            if not isinstance(data_dashboard.get("chart_ids"), list):
                errors.append("artifacts.data_dashboard.chart_ids must be an array")
            if data_dashboard.get("status") == "ready":
                for key in ("token", "url", "sheet_id"):
                    if not isinstance(data_dashboard.get(key), str) or not data_dashboard[key]:
                        errors.append(f"ready data dashboard requires {key}")
                if not data_dashboard.get("chart_ids"):
                    errors.append("ready data dashboard requires chart_ids")
                if data_dashboard.get("revision") is None:
                    errors.append("ready data dashboard requires revision")
        finalization = artifacts.get("finalization", {})
        for key in ("diary_written", "hr_notified", "heartbeat_stopped"):
            if not isinstance(finalization.get(key), bool):
                errors.append(f"artifacts.finalization.{key} must be boolean")
        work_item = artifacts.get("work_item")
        if not isinstance(work_item, dict):
            errors.append("artifacts.work_item must be an object")
        else:
            if work_item.get("status") not in {"unassigned", "assigned", "submitted", "changes_requested", "accepted"}:
                errors.append("artifacts.work_item.status is invalid")
            document = work_item.get("document")
            if not isinstance(document, dict) or document.get("type") not in {"docx", "sheet"}:
                errors.append("artifacts.work_item.document must declare docx or sheet")
            review = work_item.get("review")
            if not isinstance(review, dict):
                errors.append("artifacts.work_item.review must be an object")
            else:
                if review.get("round") not in {0, 1, 2}:
                    errors.append("review.round must be 0, 1, or 2")
                if review.get("state") not in {"not_started", "reviewing", "changes_requested", "accepted", "closed"}:
                    errors.append("review.state is invalid")
                if not isinstance(review.get("comment_ids"), list):
                    errors.append("review.comment_ids must be an array")
                if review.get("round") == 2 and review.get("state") == "changes_requested":
                    errors.append("second review cannot request another revision")
    runtime = state.get("runtime")
    if not isinstance(runtime, dict) or not isinstance(runtime.get("lease"), dict):
        errors.append("runtime.lease must be an object")
    if not isinstance(state.get("processed_message_ids"), list):
        errors.append("processed_message_ids must be an array")
    if len(state.get("processed_message_ids", [])) > 100:
        errors.append("processed_message_ids exceeds 100")
    if not isinstance(state.get("memory"), list) or len(state.get("memory", [])) > 12:
        errors.append("memory must be an array with at most 12 entries")
    if not isinstance(state.get("processed_task_event_ids"), list):
        errors.append("processed_task_event_ids must be an array")
    if len(state.get("processed_task_event_ids", [])) > 100:
        errors.append("processed_task_event_ids exceeds 100")
    checkpoint_budget = state.get("checkpoint_budget")
    if not isinstance(checkpoint_budget, dict) or any(key not in checkpoint_budget for key in CHECKPOINT_KEYS):
        errors.append("checkpoint_budget must contain all checkpoints")
    elif any(value not in {0, 1} for value in checkpoint_budget.values()):
        errors.append("checkpoint_budget values must be 0 or 1")
    session_deadline = state.get("runtime", {}).get("session_deadline_at")
    if not session_deadline:
        errors.append("runtime.session_deadline_at is required")
    else:
        try:
            started_at = parse_time(state.get("started_at", session_deadline))
            deadline_at = parse_time(session_deadline)
            if deadline_at <= started_at:
                errors.append("session deadline must be after started_at")
            paused_duration = timedelta()
            previous_end = started_at
            for interval in state.get("runtime", {}).get("pause_intervals", []):
                pause_start = parse_time(interval["start"])
                pause_end = parse_time(interval["end"])
                if pause_start < previous_end or pause_end < pause_start or pause_end > parse_time(state["updated_at"]):
                    errors.append("pause intervals must be ordered, non-overlapping and in the past")
                paused_duration += max(pause_end - pause_start, timedelta())
                previous_end = pause_end
            if deadline_at > started_at + timedelta(minutes=30) + paused_duration:
                errors.append("session deadline cannot exceed 30 minutes")
        except (TypeError, ValueError, KeyError):
            errors.append("runtime.session_deadline_at must be ISO-8601")
    story_deadline = state.get("runtime", {}).get("story_deadline_at")
    if not story_deadline:
        errors.append("runtime.story_deadline_at is required")
    else:
        try:
            story_deadline_at = parse_time(story_deadline)
            if story_deadline_at > parse_time(session_deadline):
                errors.append("story deadline cannot exceed session deadline")
        except (TypeError, ValueError):
            errors.append("runtime.story_deadline_at must be ISO-8601")
    if state.get("status") in FINAL_STATUSES:
        finalization = state.get("artifacts", {}).get("finalization", {})
        if not all(finalization.get(key) is True for key in ("diary_written", "hr_notified", "heartbeat_stopped")):
            errors.append("final state requires all finalization receipts")
        if state.get("runtime", {}).get("heartbeat_id") is not None:
            errors.append("final state must clear heartbeat_id")
        if state.get("runtime", {}).get("lease", {}).get("owner_id") is not None:
            errors.append("final state must release runner lease")
        if state.get("requested_final_status") != state.get("status"):
            errors.append("final state must match requested_final_status")
    if state.get("status") == "finalizing":
        if state.get("requested_final_status") not in FINAL_STATUSES:
            errors.append("finalizing state requires requested_final_status")
        if state.get("current_beat") != "E10":
            errors.append("finalizing state requires current_beat E10")
    if errors:
        raise ValueError("; ".join(errors))


def new_state(args: argparse.Namespace) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": args.run_id,
        "status": "initializing",
        "requested_final_status": None,
        "current_beat": "E01",
        "beat_phase": "opening",
        "entered_beat_at": args.started_at,
        "beat_actions_done": False,
        "room_layout": "company_with_role_rooms",
        "rooms": {key: None for key in ROOM_KEYS},
        "chat_ids": {},
        "active_room": "company",
        "actors": {
            "hr": {"room_key": "company", "memory": []},
            "mentor": {"room_key": "mentor_dm", "memory": []},
            "boss": {"room_key": "boss_dm", "memory": []},
            "backend": {"room_key": "company", "memory": []},
            "slacker": {"room_key": "company", "memory": []},
        },
        "player": {"open_id": args.player_open_id, "name": args.player_name},
        "counters": {"boss_affinity": 0, "slack": 0, "fights": 0, "tasks_completed": 0},
        "flags": {},
        "artifacts": {
            "review_brief": "",
            "task_id": None,
            "task_progress": {},
            "calendar_event_ids": [],
            "data_dashboard": {
                "type": "sheet",
                "status": "not_created",
                "token": None,
                "url": None,
                "sheet_id": None,
                "chart_ids": [],
                "revision": None,
            },
            "action_receipts": {},
            "work_item": {
                "task_guid": None,
                "task_url": None,
                "status": "unassigned",
                "document": {"type": "docx", "token": None, "url": None, "revision": None, "owner_identity": None},
                "review": {
                    "round": 0,
                    "state": "not_started",
                    "comment_ids": [],
                    "last_reviewed_revision": None,
                    "feedback_block_id": None,
                },
            },
            "finalization": {"diary_written": False, "hr_notified": False, "heartbeat_stopped": False},
        },
        "memory": [],
        "processed_message_ids": [],
        "processed_task_event_ids": [],
        "last_message_time_by_chat": {key: None for key in ROOM_KEYS},
        "checkpoint_budget": {key: 1 for key in CHECKPOINT_KEYS},
        "paused": False,
        "runtime": {
            "heartbeat_id": None,
            "wait_started_at": None,
            "wait_deadline_at": None,
            "last_runner_wakeup_at": None,
            "story_deadline_at": (parse_time(args.started_at) + timedelta(minutes=27)).isoformat(),
            "session_deadline_at": args.session_deadline_at,
            "lease": {"owner_id": None, "expires_at": None},
        },
        "started_at": args.started_at,
        "updated_at": args.started_at,
    }


def migrate_state(state: dict[str, Any], at: str) -> dict[str, Any]:
    migrated = copy.deepcopy(state)
    flags = migrated.setdefault("flags", {})
    original_schema = migrated.get("schema_version", 1)
    if "chat_ids" not in migrated:
        migrated["chat_ids"] = {key: None for key in LEGACY_ROOM_KEYS}
        if migrated.get("chat_id"):
            migrated["chat_ids"]["lobby"] = migrated["chat_id"]
            flags["legacy_single_chat"] = True
    migrated.setdefault("requested_final_status", None)
    migrated.setdefault("beat_phase", "opening")
    if original_schema <= 3:
        migrated["room_layout"] = "legacy_four_room"
        migrated.setdefault("rooms", {key: None for key in ROOM_KEYS})
        migrated.setdefault("active_room", "lobby")
        legacy_actor_rooms = {"hr": "lobby", "mentor": "mentor", "boss": "review", "backend": "review", "slacker": "lobby"}
        migrated.setdefault("actors", {persona: {"room_key": room, "memory": []} for persona, room in legacy_actor_rooms.items()})
    else:
        migrated.setdefault("room_layout", "company_with_role_rooms")
        migrated.setdefault("rooms", {key: None for key in ROOM_KEYS})
        migrated.setdefault("active_room", "company")
        migrated.setdefault("actors", {})
    migrated.setdefault("processed_message_ids", [])
    migrated.setdefault("processed_task_event_ids", [])
    migrated.setdefault("memory", [])
    migrated.setdefault("paused", False)
    cursor_keys = LEGACY_ROOM_KEYS if migrated["room_layout"] == "legacy_four_room" else ROOM_KEYS
    migrated.setdefault("last_message_time_by_chat", {key: None for key in cursor_keys})
    for key in cursor_keys:
        migrated["chat_ids"].setdefault(key, None)
        migrated["last_message_time_by_chat"].setdefault(key, None)
    artifacts = migrated.setdefault("artifacts", {})
    if "review_brief" not in artifacts and "prd_text" in artifacts:
        artifacts["review_brief"] = artifacts["prd_text"]
    artifacts.setdefault("review_brief", "")
    artifacts.setdefault("task_id", None)
    artifacts.setdefault("task_progress", {})
    artifacts.setdefault("calendar_event_ids", [])
    artifacts.setdefault(
        "data_dashboard",
        {
            "type": "sheet",
            "status": "not_created",
            "token": None,
            "url": None,
            "sheet_id": None,
            "chart_ids": [],
            "revision": None,
        },
    )
    artifacts.setdefault("action_receipts", {})
    artifacts.setdefault(
        "work_item",
        {
            "task_guid": artifacts.get("task_id"),
            "task_url": None,
            "status": "assigned" if artifacts.get("task_id") else "unassigned",
            "document": {"type": "docx", "token": None, "url": None, "revision": None, "owner_identity": None},
            "review": {"round": 0, "state": "not_started", "comment_ids": [], "last_reviewed_revision": None, "feedback_block_id": None},
        },
    )
    if migrated.get("status") in FINAL_STATUSES:
        artifacts["finalization"] = {"diary_written": True, "hr_notified": True, "heartbeat_stopped": True}
        flags["legacy_finalization_assumed"] = True
        migrated["requested_final_status"] = migrated["status"]
    else:
        artifacts.setdefault("finalization", {"diary_written": False, "hr_notified": False, "heartbeat_stopped": False})
    runtime = migrated.setdefault("runtime", {})
    runtime.setdefault("heartbeat_id", None)
    runtime.setdefault("wait_started_at", None)
    runtime.setdefault("wait_deadline_at", None)
    runtime.setdefault("last_runner_wakeup_at", None)
    runtime.setdefault("story_deadline_at", at)
    runtime.setdefault("session_deadline_at", at)
    runtime.setdefault("lease", {"owner_id": None, "expires_at": None})
    if migrated.get("status") in FINAL_STATUSES:
        runtime["heartbeat_id"] = None
        runtime["lease"] = {"owner_id": None, "expires_at": None}
    migrated.setdefault("started_at", at)
    if parse_time(runtime["session_deadline_at"]) <= parse_time(migrated["started_at"]):
        runtime["session_deadline_at"] = (parse_time(migrated["started_at"]) + timedelta(minutes=30)).isoformat()
    if parse_time(runtime["story_deadline_at"]) <= parse_time(migrated["started_at"]):
        runtime["story_deadline_at"] = (parse_time(migrated["started_at"]) + timedelta(minutes=27)).isoformat()
    migrated.setdefault("checkpoint_budget", {key: 1 for key in CHECKPOINT_KEYS})
    migrated["updated_at"] = at
    migrated["schema_version"] = SCHEMA_VERSION
    return migrated


def assert_lease(state: dict[str, Any], owner_id: str, at: str) -> None:
    lease = state.get("runtime", {}).get("lease", {})
    if lease.get("owner_id") != owner_id:
        raise PermissionError("runner does not own the lease")
    expires_at = lease.get("expires_at")
    if not expires_at or parse_time(expires_at) <= parse_time(at):
        raise PermissionError("runner lease has expired")


def deep_merge(target: dict[str, Any], patch: dict[str, Any]) -> None:
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            deep_merge(target[key], value)
        else:
            target[key] = value


def command_init(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    state_path = run_dir / "state.json"
    log_path = run_dir / "log.jsonl"
    run_dir.mkdir(parents=True, exist_ok=False)
    state = new_state(args)
    validate_state(state)
    atomic_write_json(state_path, state)
    atomic_write_text(log_path, "")
    print(state_path)


def command_validate(args: argparse.Namespace) -> None:
    state = load_json(Path(args.state))
    validate_state(state)
    print("state valid")


def command_migrate(args: argparse.Namespace) -> None:
    path = Path(args.state)
    with state_lock(path):
        state = migrate_state(load_json(path), args.at)
        validate_state(state)
        atomic_write_json(path, state)
    print("state migrated")


def command_lease_acquire(args: argparse.Namespace) -> None:
    path = Path(args.state)
    if parse_time(args.expires_at) <= parse_time(args.at):
        raise ValueError("expires-at must be later than at")
    with state_lock(path):
        state = load_json(path)
        lease = state["runtime"]["lease"]
        active_other = (
            lease.get("owner_id")
            and lease.get("owner_id") != args.owner_id
            and lease.get("expires_at")
            and parse_time(lease["expires_at"]) > parse_time(args.at)
        )
        if active_other:
            raise PermissionError(f"lease held by {lease['owner_id']} until {lease['expires_at']}")
        lease.update({"owner_id": args.owner_id, "expires_at": args.expires_at})
        state["updated_at"] = args.at
        validate_state(state)
        atomic_write_json(path, state)
    print("lease acquired")


def command_lease_release(args: argparse.Namespace) -> None:
    path = Path(args.state)
    with state_lock(path):
        state = load_json(path)
        lease = state["runtime"]["lease"]
        if lease.get("owner_id") not in (None, args.owner_id):
            raise PermissionError("cannot release another runner's lease")
        lease.update({"owner_id": None, "expires_at": None})
        state["updated_at"] = args.at
        validate_state(state)
        atomic_write_json(path, state)
    print("lease released")


def command_patch(args: argparse.Namespace) -> None:
    path = Path(args.state)
    patch = parse_object(args.patch_json, "patch-json")
    with state_lock(path):
        state = load_json(path)
        assert_lease(state, args.owner_id, args.at)
        deep_merge(state, patch)
        state["updated_at"] = args.at
        state["processed_message_ids"] = state.get("processed_message_ids", [])[-100:]
        state["processed_task_event_ids"] = state.get("processed_task_event_ids", [])[-100:]
        state["memory"] = state.get("memory", [])[-12:]
        validate_state(state)
        atomic_write_json(path, state)
    print("state patched")


def command_receipt_begin(args: argparse.Namespace) -> None:
    path = Path(args.state)
    params = parse_object(args.params_json, "params-json")
    with state_lock(path):
        state = load_json(path)
        assert_lease(state, args.owner_id, args.at)
        receipts = state["artifacts"]["action_receipts"]
        existing = receipts.get(args.key)
        if existing and existing.get("status") == "done":
            print("receipt already done")
            return
        if existing and existing.get("params") != params:
            raise ValueError("pending receipt parameters cannot change")
        if existing and existing.get("idempotency_key") != args.idempotency_key:
            raise ValueError("pending receipt idempotency key cannot change")
        receipt = existing or {}
        receipt.update({"status": "pending", "params": params, "recorded_at": receipt.get("recorded_at", args.at)})
        if args.idempotency_key:
            receipt["idempotency_key"] = args.idempotency_key
        receipts[args.key] = receipt
        state["updated_at"] = args.at
        validate_state(state)
        atomic_write_json(path, state)
    print("receipt pending")


def command_receipt_done(args: argparse.Namespace) -> None:
    path = Path(args.state)
    result = parse_object(args.result_json, "result-json")
    with state_lock(path):
        state = load_json(path)
        assert_lease(state, args.owner_id, args.at)
        receipt = state["artifacts"]["action_receipts"].get(args.key)
        if not receipt:
            raise ValueError("receipt must be pending before it can be completed")
        if receipt.get("status") == "done":
            print("receipt already done")
            return
        receipt.update(result)
        receipt.update({"status": "done", "completed_at": args.at})
        state["updated_at"] = args.at
        validate_state(state)
        atomic_write_json(path, state)
    print("receipt done")


def command_log_append(args: argparse.Namespace) -> None:
    state_path = Path(args.state)
    entry = parse_object(args.entry_json, "entry-json")
    required = {"t", "beat", "kind", "who", "text", "data"}
    if not required.issubset(entry):
        raise ValueError(f"log entry missing: {sorted(required - set(entry))}")
    serialized = json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n"
    with state_lock(state_path):
        state = load_json(state_path)
        assert_lease(state, args.owner_id, args.at)
        log_path = Path(args.log)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8") as handle:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            handle.write(serialized)
            handle.flush()
            os.fsync(handle.fileno())
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
    print("log appended")


def command_task_event_record(args: argparse.Namespace) -> None:
    path = Path(args.state)
    with state_lock(path):
        state = load_json(path)
        assert_lease(state, args.owner_id, args.at)
        event_ids = state["processed_task_event_ids"]
        if args.event_id in event_ids:
            print("task event already processed")
            return
        event_ids.append(args.event_id)
        state["processed_task_event_ids"] = event_ids[-100:]
        state["updated_at"] = args.at
        validate_state(state)
        atomic_write_json(path, state)
    print("task event recorded")


def command_checkpoint_consume(args: argparse.Namespace) -> None:
    if args.checkpoint not in CHECKPOINT_KEYS:
        raise ValueError(f"unknown checkpoint: {args.checkpoint}")
    path = Path(args.state)
    with state_lock(path):
        state = load_json(path)
        assert_lease(state, args.owner_id, args.at)
        if state["checkpoint_budget"][args.checkpoint] == 0:
            print("checkpoint already consumed")
            return
        state["checkpoint_budget"][args.checkpoint] = 0
        state["updated_at"] = args.at
        validate_state(state)
        atomic_write_json(path, state)
    print("checkpoint consumed")


def command_write_text(args: argparse.Namespace) -> None:
    state_path = Path(args.state)
    with state_lock(state_path):
        state = load_json(state_path)
        assert_lease(state, args.owner_id, args.at)
        atomic_write_text(Path(args.path), args.text)
    print("text written")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--run-dir", required=True)
    init.add_argument("--run-id", required=True)
    init.add_argument("--started-at", required=True)
    init.add_argument("--player-open-id", required=True)
    init.add_argument("--player-name", required=True)
    init.add_argument("--session-deadline-at", required=True)
    init.set_defaults(handler=command_init)

    validate = commands.add_parser("validate")
    validate.add_argument("--state", required=True)
    validate.set_defaults(handler=command_validate)

    migrate = commands.add_parser("migrate")
    migrate.add_argument("--state", required=True)
    migrate.add_argument("--at", required=True)
    migrate.set_defaults(handler=command_migrate)

    acquire = commands.add_parser("lease-acquire")
    acquire.add_argument("--state", required=True)
    acquire.add_argument("--owner-id", required=True)
    acquire.add_argument("--at", required=True)
    acquire.add_argument("--expires-at", required=True)
    acquire.set_defaults(handler=command_lease_acquire)

    release = commands.add_parser("lease-release")
    release.add_argument("--state", required=True)
    release.add_argument("--owner-id", required=True)
    release.add_argument("--at", required=True)
    release.set_defaults(handler=command_lease_release)

    patch = commands.add_parser("patch")
    patch.add_argument("--state", required=True)
    patch.add_argument("--owner-id", required=True)
    patch.add_argument("--at", required=True)
    patch.add_argument("--patch-json", required=True)
    patch.set_defaults(handler=command_patch)

    begin = commands.add_parser("receipt-begin")
    begin.add_argument("--state", required=True)
    begin.add_argument("--owner-id", required=True)
    begin.add_argument("--at", required=True)
    begin.add_argument("--key", required=True)
    begin.add_argument("--params-json", required=True)
    begin.add_argument("--idempotency-key")
    begin.set_defaults(handler=command_receipt_begin)

    done = commands.add_parser("receipt-done")
    done.add_argument("--state", required=True)
    done.add_argument("--owner-id", required=True)
    done.add_argument("--at", required=True)
    done.add_argument("--key", required=True)
    done.add_argument("--result-json", required=True)
    done.set_defaults(handler=command_receipt_done)

    log = commands.add_parser("log-append")
    log.add_argument("--state", required=True)
    log.add_argument("--owner-id", required=True)
    log.add_argument("--at", required=True)
    log.add_argument("--log", required=True)
    log.add_argument("--entry-json", required=True)
    log.set_defaults(handler=command_log_append)

    task_event = commands.add_parser("task-event-record")
    task_event.add_argument("--state", required=True)
    task_event.add_argument("--owner-id", required=True)
    task_event.add_argument("--at", required=True)
    task_event.add_argument("--event-id", required=True)
    task_event.set_defaults(handler=command_task_event_record)

    checkpoint = commands.add_parser("checkpoint-consume")
    checkpoint.add_argument("--state", required=True)
    checkpoint.add_argument("--owner-id", required=True)
    checkpoint.add_argument("--at", required=True)
    checkpoint.add_argument("--checkpoint", required=True)
    checkpoint.set_defaults(handler=command_checkpoint_consume)

    text = commands.add_parser("write-text")
    text.add_argument("--state", required=True)
    text.add_argument("--owner-id", required=True)
    text.add_argument("--at", required=True)
    text.add_argument("--path", required=True)
    text.add_argument("--text", required=True)
    text.set_defaults(handler=command_write_text)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.handler(args)
    except (ValueError, PermissionError, json.JSONDecodeError, OSError) as exc:
        print(f"error: {exc}", file=os.sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
