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
DEMO_STAGES = {"preparing", "prepared", "alignment", "decision", "handoff", "revision", "finalizing", "finished"}


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


def validate_demo_state(state: dict[str, Any], errors: list[str]) -> None:
    demo = state.get("demo", {})
    runtime = state.get("runtime", {})
    stage = demo.get("stage")
    cue = demo.get("pacing", "timed") == "cue"
    if demo.get("pacing", "timed") not in {"cue", "timed"}:
        errors.append("invalid demo pacing")
    if stage not in DEMO_STAGES or state.get("current_beat") != "DEMO":
        errors.append("demo requires a valid stage and current_beat DEMO")
    if demo.get("purpose") not in {"live", "rehearsal"}:
        errors.append("demo purpose must be live or rehearsal")
    if state.get("room_layout") != "company_with_role_rooms":
        errors.append("demo requires three role rooms")
    if any(state.get("checkpoint_budget", {}).values()):
        errors.append("demo must not consume full-mode checkpoints")
    expected_status = {"preparing": "initializing", "prepared": "initializing",
                       "alignment": "running", "decision": "running", "handoff": "running", "revision": "running", "finalizing": "finalizing"}
    if stage in expected_status and state.get("status") != expected_status[stage]:
        errors.append("demo stage and status disagree")
    if stage == "finished" and state.get("status") not in FINAL_STATUSES:
        errors.append("finished demo requires final status")
    start = demo.get("live_started_at")
    if start is None:
        if stage in {"alignment", "decision", "handoff", "revision"}:
            errors.append("live demo requires live_started_at")
        if any(runtime.get(key) is not None for key in ("story_deadline_at", "session_deadline_at", "wait_started_at", "wait_deadline_at", "heartbeat_id")):
            errors.append("prepared demo must have no clock or heartbeat")
    else:
        try:
            started = parse_time(start)
            if started < parse_time(state["started_at"]) or started > parse_time(state["updated_at"]):
                errors.append("demo start must be between creation and update")
            if cue and any(runtime.get(k) is not None for k in ("story_deadline_at", "session_deadline_at")):
                errors.append("cue pacing must not have countdown deadlines")
            if not cue and parse_time(runtime["session_deadline_at"]) != started + timedelta(minutes=4):
                errors.append("demo hard deadline must remain four minutes after live start")
            if not cue and parse_time(runtime["story_deadline_at"]) != started + timedelta(seconds=210):
                errors.append("demo story deadline must remain 210 seconds after live start")
        except (TypeError, ValueError, KeyError):
            errors.append("invalid demo clock")
    if stage in {"preparing", "prepared"} and (start or demo.get("decision") or demo.get("submission")):
        errors.append("preparation cannot contain live input")
    if stage == "revision" and not demo.get("decision"):
        errors.append("revision stage requires candidate decision")
    if cue:
        if stage in {"decision", "handoff", "revision"} and not demo.get("alignment"):
            errors.append("cue decision requires team alignment")
        if stage == "handoff" and not demo.get("decision"):
            errors.append("handoff requires boss decision")
        if stage == "revision" and not demo.get("handoff"):
            errors.append("revision requires team handoff")
        if state.get("status") == "completed" and (not demo.get("alignment") or not demo.get("handoff")):
            errors.append("cue completion requires three conversations")
    if state.get("status") == "completed":
        if not demo.get("decision") or not demo.get("submission"):
            errors.append("completed demo requires decision and valid submission")
    if state.get("counters", {}).get("tasks_completed") == 1:
        submission = demo.get("submission") or {}
        if sum(item.get("score", 0) for item in submission.get("rubric", [])) < 3:
            errors.append("demo task completion requires passing rubric")
        if stage != "finished" or state.get("status") != "completed":
            errors.append("demo task completion requires finished cleanup")


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
    mode = state.get("mode", "full")
    if mode not in {"full", "live_demo"}:
        errors.append("mode must be full or live_demo")
    if mode == "live_demo":
        validate_demo_state(state, errors)
    elif state.get("current_beat") not in {f"E{i:02d}" for i in range(1, 11)}:
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
    if mode == "live_demo":
        pass  # Preparation has no clock; the live clock is validated separately.
    elif not session_deadline:
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
    if mode == "live_demo":
        pass
    elif not story_deadline:
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
        if mode != "live_demo" and state.get("current_beat") != "E10":
            errors.append("finalizing state requires current_beat E10")
    if errors:
        raise ValueError("; ".join(errors))


def new_state(args: argparse.Namespace) -> dict[str, Any]:
    state = {
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
            "session_deadline_at": args.session_deadline_at or (parse_time(args.started_at) + timedelta(minutes=30)).isoformat(),
            "lease": {"owner_id": None, "expires_at": None},
        },
        "started_at": args.started_at,
        "updated_at": args.started_at,
    }
    if getattr(args, "mode", "full") == "live_demo":
        state.update({"mode": "live_demo", "current_beat": "DEMO", "beat_phase": "preparing"})
        state["demo"] = {"stage": "preparing", "purpose": getattr(args, "purpose", "live"),
                         "live_started_at": None, "decision": None, "submission": None}
        if getattr(args, "pacing", "timed") == "cue":
            state["demo"].update(pacing="cue", alignment=None, handoff=None, resumed_at=None, paused_at=None)
        state["checkpoint_budget"] = {key: 0 for key in CHECKPOINT_KEYS}
        state["runtime"].update({"story_deadline_at": None, "session_deadline_at": None})
    return state


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
    state = new_state(args)
    validate_state(state)
    run_dir.mkdir(parents=True, exist_ok=False)
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
        existing = load_json(path)
        state = existing if existing.get("mode") == "live_demo" else migrate_state(existing, args.at)
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
        if "mode" in patch and patch["mode"] != state.get("mode", "full"):
            raise ValueError("cannot change a run's mode")
        if state.get("mode") == "live_demo":
            if state["demo"].get("pacing") == "cue" and "paused" in patch:
                raise ValueError("use demo pause/resume for cue controls")
            if "demo" in patch or any(key in patch for key in ("status", "current_beat", "requested_final_status")):
                raise ValueError("use demo commands for lifecycle changes")
            if any(key in patch.get("runtime", {}) for key in ("story_deadline_at", "session_deadline_at")):
                raise ValueError("demo deadlines cannot be patched")
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


def demo_receipt(state: dict[str, Any], key: str, **expected: Any) -> None:
    receipt = state["artifacts"]["action_receipts"].get(key, {})
    if receipt.get("status") != "done" or any(receipt.get(k) != v for k, v in expected.items()):
        raise ValueError(f"missing or mismatched receipt: {key}")


def validate_demo_message(state: dict[str, Any], evidence: dict[str, Any], at: str, room: str) -> None:
    demo = state["demo"]
    if evidence.get("chat_id") != state["rooms"][room] or evidence.get("sender_id") != state["player"]["open_id"]:
        raise ValueError("conversation requires candidate in the expected chat")
    if not evidence.get("message_id") or not evidence.get("text", "").strip():
        raise ValueError("conversation requires real message and text")
    if evidence["message_id"] in state["processed_message_ids"]:
        raise ValueError("message already consumed by another conversation")
    if not parse_time(demo["resumed_at"]) <= parse_time(evidence["created_at"]) <= parse_time(evidence["observed_at"]) <= parse_time(at):
        raise ValueError("conversation predates resume or has invalid timestamps")


def demo_transition(state: dict[str, Any], action: str, at: str, evidence: dict[str, Any]) -> None:
    """Apply a transition to a copy; callers validate and atomically commit it.

    Evidence must be normalized from fresh Lark reads by the runner. This helper
    validates identity/version/phase, not network authenticity or semantic grades.
    """
    if state.get("mode") != "live_demo":
        raise ValueError("demo command cannot operate on a full run")
    demo = state["demo"]
    cue = demo.get("pacing", "timed") == "cue"
    stage = demo["stage"]
    runtime = state["runtime"]
    work = state["artifacts"]["work_item"]
    review = work["review"]
    now = parse_time(at)
    if action == "ready":
        if stage == "prepared":
            return
        if stage != "preparing":
            raise ValueError("only preparation can become ready")
        if cue:
            for room in ROOM_KEYS:
                if not state["rooms"][room]:
                    raise ValueError("missing demo room")
                demo_receipt(state, f"demo.chat.{room}", chat_id=state["rooms"][room])
            if not work["document"]["url"] or not work["task_url"] or state["artifacts"]["task_id"] != work["task_guid"]:
                raise ValueError("missing or mismatched work objects")
            demo_receipt(state, "demo.prepared.document", document_token=work["document"]["token"], revision=review["last_reviewed_revision"])
            demo_receipt(state, "demo.prepared.task", task_guid=work["task_guid"], task_status="todo")
            demo_receipt(state, "demo.prepared.scene")
            if not state["artifacts"]["action_receipts"]["demo.prepared.scene"].get("message_id"):
                raise ValueError("scene requires real message")
            demo["stage"] = "prepared"
            state["paused"] = True
            state["beat_phase"] = "prepared"
            return
        for room in ROOM_KEYS:
            if not state["rooms"][room]:
                raise ValueError("missing demo room")
            demo_receipt(state, f"demo.chat.{room}", chat_id=state["rooms"][room])
        if not work["task_guid"] or not work["task_url"] or not work["document"]["url"]:
            raise ValueError("missing demo work objects")
        if not work["document"]["token"]:
            raise ValueError("missing document identity")
        if state["artifacts"]["task_id"] != work["task_guid"]:
            raise ValueError("demo task identities differ")
        if review["round"] != 1 or review["state"] != "changes_requested" or work["status"] != "changes_requested":
            raise ValueError("first review must really request changes")
        if len(review["comment_ids"]) != 1 or not review["feedback_block_id"] or review["last_reviewed_revision"] is None:
            raise ValueError("preparation requires one localized comment and revision")
        demo_receipt(state, "demo.seed.submit", task_guid=work["task_guid"], task_status="done")
        demo_receipt(state, "demo.document", document_token=work["document"]["token"])
        demo_receipt(state, "demo.task", task_guid=work["task_guid"])
        demo_receipt(state, "demo.seed.review", score=2, revision=review["last_reviewed_revision"], document_token=work["document"]["token"])
        demo_receipt(state, "demo.seed.comment", comment_id=review["comment_ids"][0], block_id=review["feedback_block_id"])
        reopen_receipt = state["artifacts"]["action_receipts"].get("demo.seed.reopen", {})
        if reopen_receipt.get("status") != "done" or reopen_receipt.get("task_guid") != work["task_guid"] or reopen_receipt.get("task_status") not in {"open", "todo"}:
            raise ValueError("mismatched receipt: demo.seed.reopen")
        for role in ("boss", "backend", "mentor"):
            demo_receipt(state, f"demo.drama.{role}")
            if not state["artifacts"]["action_receipts"][f"demo.drama.{role}"].get("message_id"):
                raise ValueError("drama requires real message IDs")
        demo["stage"] = "prepared"
    elif action in {"start", "resume"}:
        if action == "resume" and cue and stage in {"alignment", "decision", "handoff", "revision"}:
            if state["paused"]:
                if demo.get("paused_at") and demo.get("stage_entered_at"):
                    demo["stage_entered_at"] = (parse_time(demo["stage_entered_at"]) + (now - parse_time(demo["paused_at"]))).isoformat()
                state["paused"] = False
                demo.update(resumed_at=at, paused_at=None)
            return
        if stage in {"alignment", "decision", "handoff", "revision", "finalizing", "finished"}:
            return  # Resume/start never resets a running clock.
        if stage != "prepared":
            raise ValueError("demo must be prepared before start")
        demo.update({"stage": "alignment" if cue else "decision", "live_started_at": at})
        state["status"] = "running"
        state["active_room"] = "company" if cue else "boss_dm"
        state["paused"] = False
        if cue:
            demo.update(resumed_at=at, paused_at=None)
        else:
            runtime.update({"story_deadline_at": (now + timedelta(seconds=210)).isoformat(),
                            "session_deadline_at": (now + timedelta(minutes=4)).isoformat()})
    elif action == "pause":
        if not cue:
            raise ValueError("cue pause requires cue pacing")
        if stage not in {"prepared", "alignment", "decision", "handoff", "revision"}:
            raise ValueError("cannot pause this stage")
        if not state["paused"]:
            state["paused"] = True
            demo["paused_at"] = at
        runtime["heartbeat_id"] = None
        runtime.update(wait_started_at=None, wait_deadline_at=None)
    elif action in {"alignment", "handoff"}:
        if not cue:
            raise ValueError("team conversation requires cue pacing")
        if demo.get(action) == evidence:
            return
        if demo.get(action):
            raise ValueError("live input already consumed")
        if stage != action or state["paused"]:
            raise ValueError("conversation stage mismatch or paused")
        validate_demo_message(state, evidence, at, "company")
        if not evidence.get("reason"):
            raise ValueError("conversation requires semantic assessment")
        demo[action] = evidence
        state["processed_message_ids"] = (state["processed_message_ids"] + [evidence["message_id"]])[-100:]
        demo["stage"] = "decision" if action == "alignment" else "revision"
        state["active_room"] = "boss_dm" if action == "alignment" else "company"
    elif action in {"decision", "submit"}:
        existing = demo.get("decision" if action == "decision" else "submission")
        if existing is not None:
            if existing == evidence:
                return
            raise ValueError("live input already consumed")
        if state["paused"]:
            raise ValueError("demo is paused")
        if stage != ("decision" if action == "decision" else "revision"):
            raise ValueError("input does not match demo stage")
        if not cue and now >= parse_time(runtime["story_deadline_at"]):
            raise ValueError("demo input window ended; finalize honestly")
        observed = parse_time(evidence["observed_at"])
        if not parse_time(demo["live_started_at"]) <= observed <= now:
            raise ValueError("input must be observed during live session")
        if action == "decision":
            if cue:
                validate_demo_message(state, evidence, at, "boss_dm")
            if evidence.get("chat_id") != state["rooms"]["boss_dm"] or evidence.get("sender_id") != state["player"]["open_id"]:
                raise ValueError("decision must come from candidate in boss chat")
            if not parse_time(demo["live_started_at"]) <= parse_time(evidence["created_at"]) <= observed:
                raise ValueError("pre-run messages are not live input")
            if not evidence.get("message_id") or not evidence.get("text", "").strip() or not evidence.get("reason", "").strip():
                raise ValueError("decision requires message, text and semantic reason")
            if evidence.get("judgment") not in {"protect", "evidence", "accept_all", "reject_only", "unclear"}:
                raise ValueError("invalid scope judgment")
            demo["decision"] = evidence
            demo["stage"] = "handoff" if cue else "revision"
            state["active_room"] = "company"
            state["processed_message_ids"] = (state["processed_message_ids"] + [evidence["message_id"]])[-100:]
            state["flags"]["scope_response"] = evidence["judgment"]
        else:
            if evidence.get("task_guid") != work["task_guid"] or evidence.get("task_status") != "done":
                raise ValueError("submission requires the same task confirmed done")
            if evidence.get("document_token") != work["document"]["token"]:
                raise ValueError("wrong document")
            if not parse_time(demo["live_started_at"]) <= parse_time(evidence["completed_at"]) <= observed:
                raise ValueError("task completion must be from live session")
            if cue and parse_time(evidence["completed_at"]) < parse_time(demo["resumed_at"]):
                raise ValueError("submission predates resume")
            if cue and (not evidence.get("baseline_text") or evidence.get("text") == evidence["baseline_text"]):
                raise ValueError("document body must change, not only its revision")
            revision = evidence.get("revision")
            if not isinstance(revision, int) or isinstance(revision, bool) or revision <= int(review["last_reviewed_revision"]):
                raise ValueError("尚未检测到修改")
            text = evidence.get("text", "")
            rubric = evidence.get("rubric", [])
            if not text.strip() or len(rubric) != 5:
                raise ValueError("submission needs document text and five rubric items")
            for item in rubric:
                if type(item.get("score")) is not int or item["score"] not in {0, 1} or not item.get("reason"):
                    raise ValueError("invalid rubric score or reason")
                if item.get("source") not in {"seed", "live_revision", "presenter_script", "existing_document"}:
                    raise ValueError("rubric must distinguish seed from live revision")
                if item["score"] and (not item.get("quote") or item["quote"] not in text):
                    raise ValueError("scored evidence must quote the document")
            demo["submission"] = evidence
            passed = sum(item["score"] for item in rubric) >= 3
            review.update({"round": 2, "state": "reviewing", "last_reviewed_revision": revision})
            work["document"]["revision"] = revision
            state["flags"]["review_passed"] = passed
            demo["stage"] = "finalizing"
            state.update({"status": "finalizing", "requested_final_status": "completed"})
    elif action in {"timeout", "stop"}:
        if stage in {"finalizing", "finished"}:
            return
        if action == "timeout" and (cue or not demo["live_started_at"] or now < parse_time(runtime["story_deadline_at"])):
            raise ValueError("prepared or unexpired demo cannot time out")
        demo.update({"stage": "finalizing", "stop_reason": "timeout" if action == "timeout" else "presenter_stopped"})
        state.update({"status": "finalizing", "requested_final_status": "aborted"})
        review["state"] = "closed"
    elif action == "finish":
        if stage == "finished":
            return
        if stage != "finalizing":
            raise ValueError("demo must be finalizing")
        if not all(state["artifacts"]["finalization"].values()) or runtime["heartbeat_id"] is not None:
            raise ValueError("demo cleanup is incomplete")
        if demo["submission"]:
            passed = state["flags"].get("review_passed") is True
            demo_receipt(state, "demo.final.task", task_guid=work["task_guid"], task_status="done")
            demo_receipt(state, "demo.final.snapshot", task_guid=work["task_guid"])
            demo_receipt(state, "demo.final.review-message")
            if not state["artifacts"]["action_receipts"]["demo.final.review-message"].get("message_id"):
                raise ValueError("final review message requires real message ID")
            if passed:
                if review["comment_ids"]:
                    demo_receipt(state, "demo.final.comment", comment_id=review["comment_ids"][0], resolved=True)
                work["status"] = "accepted"
                state["counters"]["tasks_completed"] = 1
            else:
                work["status"] = "submitted"  # Closed review is not acceptance.
            review["state"] = "accepted" if passed else "closed"
        state["status"] = state["requested_final_status"]
        demo["stage"] = "finished"
        runtime["lease"] = {"owner_id": None, "expires_at": None}
    else:
        raise ValueError("unknown demo action")
    if cue and demo["stage"] != stage:
        demo["stage_entered_at"] = at
    state["beat_phase"] = demo["stage"]


def command_demo(args: argparse.Namespace) -> None:
    path = Path(args.state)
    evidence = load_json(Path(args.evidence_file)) if args.evidence_file else {}
    with state_lock(path):
        original = load_json(path)
        # Final retries do not need to reacquire the released lease.
        if original.get("demo", {}).get("stage") == "finished" and args.action in {"finish", "start", "timeout", "stop"}:
            print("demo already finished")
            return
        assert_lease(original, args.owner_id, args.at)
        state = copy.deepcopy(original)
        demo_transition(state, args.action, args.at, evidence)
        state["updated_at"] = args.at
        validate_state(state)
        if state.get("demo") != original.get("demo"):
            # Persist the log before the state. A crash may repeat this identical
            # event; diary readers deduplicate event_id and never infer acceptance.
            entry = {"t": args.at, "beat": "DEMO", "kind": "review" if args.action == "submit" else "control",
                     "who": "player" if args.action in {"alignment", "decision", "handoff", "submit"} else "engine",
                     "text": evidence.get("text", f"demo {args.action}"),
                     "data": {"source": ("presenter_script" if state["flags"].get("presenter_scripted") else "presenter_live") if args.action in {"alignment", "decision", "handoff"} else ("submitted_document" if args.action == "submit" else "runtime"), "evidence": evidence},
                     "event_id": f"{state['run_id']}:demo:{args.action}" + (f":{args.at}" if args.action in {"pause", "resume"} else "")}
            with path.with_name("log.jsonl").open("a", encoding="utf-8") as log:
                log.write(json.dumps(entry, ensure_ascii=False) + "\n")
                log.flush()
                os.fsync(log.fileno())
        atomic_write_json(path, state)
    print(f"demo {state['demo']['stage']}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init")
    init.add_argument("--run-dir", required=True)
    init.add_argument("--run-id", required=True)
    init.add_argument("--started-at", required=True)
    init.add_argument("--player-open-id", required=True)
    init.add_argument("--player-name", required=True)
    init.add_argument("--session-deadline-at")
    init.add_argument("--mode", choices=("full", "live_demo"), default="full")
    init.add_argument("--purpose", choices=("live", "rehearsal"), default="live")
    init.add_argument("--pacing", choices=("cue", "timed"), default="cue")
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
    demo = commands.add_parser("demo", help="Guarded live-demo lifecycle; no Lark requests")
    demo.add_argument("action", choices=("ready", "start", "pause", "resume", "alignment", "decision", "handoff", "submit", "timeout", "stop", "finish"))
    demo.add_argument("--state", required=True)
    demo.add_argument("--owner-id", required=True)
    demo.add_argument("--at", required=True)
    demo.add_argument("--evidence-file", help="Normalized fresh Lark read plus semantic assessment")
    demo.set_defaults(handler=command_demo)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        args.handler(args)
    except (ValueError, PermissionError, json.JSONDecodeError, OSError, KeyError, TypeError) as exc:
        print(f"error: {exc}", file=os.sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
