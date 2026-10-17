#!/usr/bin/env python3

from __future__ import annotations

import importlib.util
import json
import subprocess
import tempfile
import unittest
from argparse import Namespace
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]
STATE_TOOL = SKILL_DIR / "scripts" / "state-tool.py"
SPEC = importlib.util.spec_from_file_location("state_tool", STATE_TOOL)
STATE_TOOL_MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(STATE_TOOL_MODULE)


class StateToolV4Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.started = datetime(2026, 8, 27, 10, 0, tzinfo=timezone(timedelta(hours=8)))
        self.started_at = self.started.isoformat()
        self.deadline_at = (self.started + timedelta(minutes=30)).isoformat()
        self.state = STATE_TOOL_MODULE.new_state(
            Namespace(
                run_id="pm-one-day-20260827-100000",
                started_at=self.started_at,
                session_deadline_at=self.deadline_at,
                player_open_id="ou_player",
                player_name="玩家",
            )
        )

    def test_new_state_uses_three_role_rooms_and_docx_work_item(self) -> None:
        STATE_TOOL_MODULE.validate_state(self.state)
        self.assertEqual(self.state["schema_version"], 4)
        self.assertEqual(set(self.state["rooms"]), {"company", "mentor_dm", "boss_dm"})
        self.assertEqual(self.state["actors"]["mentor"]["room_key"], "mentor_dm")
        self.assertEqual(self.state["actors"]["boss"]["room_key"], "boss_dm")
        self.assertEqual(self.state["artifacts"]["work_item"]["document"]["type"], "docx")
        self.assertEqual(
            self.state["artifacts"]["data_dashboard"],
            {"type": "sheet", "status": "not_created", "token": None, "url": None, "sheet_id": None, "chart_ids": [], "revision": None},
        )
        self.assertEqual(self.state["runtime"]["story_deadline_at"], (self.started + timedelta(minutes=27)).isoformat())

    def test_session_deadline_cannot_exceed_thirty_minutes(self) -> None:
        invalid = deepcopy(self.state)
        invalid["runtime"]["session_deadline_at"] = (self.started + timedelta(minutes=31)).isoformat()
        with self.assertRaisesRegex(ValueError, "cannot exceed 30 minutes"):
            STATE_TOOL_MODULE.validate_state(invalid)

    def test_v3_active_run_migrates_without_creating_new_rooms(self) -> None:
        legacy = deepcopy(self.state)
        legacy["schema_version"] = 3
        legacy.pop("room_layout")
        legacy.pop("rooms")
        legacy.pop("actors")
        legacy.pop("processed_task_event_ids")
        legacy.pop("checkpoint_budget")
        legacy["chat_ids"] = {"lobby": "oc_1", "mentor": "oc_2", "research": "oc_3", "review": "oc_4"}
        legacy["active_room"] = "mentor"
        legacy["last_message_time_by_chat"] = {key: None for key in legacy["chat_ids"]}
        legacy["artifacts"].pop("work_item")
        legacy["artifacts"].pop("data_dashboard")
        legacy["runtime"].pop("story_deadline_at")
        legacy["runtime"].pop("session_deadline_at")

        migrated = STATE_TOOL_MODULE.migrate_state(legacy, self.started_at)

        STATE_TOOL_MODULE.validate_state(migrated)
        self.assertEqual(migrated["room_layout"], "legacy_four_room")
        self.assertEqual(migrated["chat_ids"]["review"], "oc_4")
        self.assertTrue(all(value is None for value in migrated["rooms"].values()))
        self.assertEqual(migrated["artifacts"]["data_dashboard"]["status"], "not_created")

    def test_ready_data_dashboard_requires_verified_artifacts(self) -> None:
        invalid = deepcopy(self.state)
        invalid["artifacts"]["data_dashboard"]["status"] = "ready"
        with self.assertRaisesRegex(ValueError, "ready data dashboard requires"):
            STATE_TOOL_MODULE.validate_state(invalid)

        ready = deepcopy(self.state)
        ready["artifacts"]["data_dashboard"].update(
            {
                "status": "ready",
                "token": "shtcn_dashboard",
                "url": "https://example.feishu.cn/sheets/shtcn_dashboard",
                "sheet_id": "sheet_1",
                "chart_ids": ["chart_1"],
                "revision": 7,
            }
        )
        STATE_TOOL_MODULE.validate_state(ready)

    def test_second_review_cannot_request_another_revision(self) -> None:
        invalid = deepcopy(self.state)
        review = invalid["artifacts"]["work_item"]["review"]
        review.update({"round": 2, "state": "changes_requested"})
        with self.assertRaisesRegex(ValueError, "second review"):
            STATE_TOOL_MODULE.validate_state(invalid)

    def test_task_event_and_checkpoint_commands_are_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            state_path = run_dir / "state.json"
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--run-id",
                self.state["run_id"],
                "--started-at",
                self.started_at,
                "--session-deadline-at",
                self.deadline_at,
                "--player-open-id",
                "ou_player",
                "--player-name",
                "玩家",
            )
            lease_expiry = (self.started + timedelta(seconds=90)).isoformat()
            self._run("lease-acquire", "--state", str(state_path), "--owner-id", "runner", "--at", self.started_at, "--expires-at", lease_expiry)
            first = self._run("task-event-record", "--state", str(state_path), "--owner-id", "runner", "--at", self.started_at, "--event-id", "evt_1")
            second = self._run("task-event-record", "--state", str(state_path), "--owner-id", "runner", "--at", self.started_at, "--event-id", "evt_1")
            self.assertIn("recorded", first.stdout)
            self.assertIn("already processed", second.stdout)
            self._run("checkpoint-consume", "--state", str(state_path), "--owner-id", "runner", "--at", self.started_at, "--checkpoint", "onboarding")
            repeated = self._run("checkpoint-consume", "--state", str(state_path), "--owner-id", "runner", "--at", self.started_at, "--checkpoint", "onboarding")
            self.assertIn("already consumed", repeated.stdout)
            saved = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(saved["processed_task_event_ids"], ["evt_1"])
            self.assertEqual(saved["checkpoint_budget"]["onboarding"], 0)

    def test_comment_receipt_recovery_preserves_identity(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            run_dir = Path(temporary) / "run"
            state_path = run_dir / "state.json"
            self._run(
                "init",
                "--run-dir",
                str(run_dir),
                "--run-id",
                self.state["run_id"],
                "--started-at",
                self.started_at,
                "--session-deadline-at",
                self.deadline_at,
                "--player-open-id",
                "ou_player",
                "--player-name",
                "玩家",
            )
            lease_expiry = (self.started + timedelta(seconds=90)).isoformat()
            self._run("lease-acquire", "--state", str(state_path), "--owner-id", "runner", "--at", self.started_at, "--expires-at", lease_expiry)
            args = ("receipt-begin", "--state", str(state_path), "--owner-id", "runner", "--at", self.started_at, "--key", "review.comment.1", "--params-json", '{"block_id":"blk_1"}', "--idempotency-key", "review-comment-1")
            self._run(*args)
            self._run(*args)
            saved = json.loads(state_path.read_text(encoding="utf-8"))
            receipt = saved["artifacts"]["action_receipts"]["review.comment.1"]
            self.assertEqual(receipt["status"], "pending")
            self.assertEqual(receipt["idempotency_key"], "review-comment-1")

    def test_final_state_still_requires_complete_finalization(self) -> None:
        invalid = deepcopy(self.state)
        invalid.update({"status": "completed", "requested_final_status": "completed"})
        with self.assertRaisesRegex(ValueError, "final state requires"):
            STATE_TOOL_MODULE.validate_state(invalid)

    def _run(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["python3", str(STATE_TOOL), *args],
            check=True,
            capture_output=True,
            text=True,
        )


if __name__ == "__main__":
    unittest.main()
