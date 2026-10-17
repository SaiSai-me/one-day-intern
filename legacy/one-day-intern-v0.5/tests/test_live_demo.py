"""Behavioral checks for short-mode isolation and evidence-driven transitions.

Fixtures are synthetic. These tests make no Lark calls and are not live rehearsals.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path


TOOL = Path(__file__).resolve().parents[1] / "scripts" / "state-tool.py"
SPEC = importlib.util.spec_from_file_location("demo_state", TOOL)
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class LiveDemoTests(unittest.TestCase):
    def setUp(self):
        self.created = datetime(2026, 9, 13, 10, tzinfo=timezone.utc)
        self.start = self.created + timedelta(days=2)
        self.state = MODULE.new_state(Namespace(
            mode="live_demo", purpose="rehearsal", run_id="pm-one-day-test-demo",
            started_at=self.created.isoformat(), session_deadline_at=None,
            player_open_id="ou_player", player_name="实习生"))

    def transition(self, action, seconds=0, evidence=None):
        proposed = deepcopy(self.state)
        at = (self.start + timedelta(seconds=seconds)).isoformat()
        MODULE.demo_transition(proposed, action, at, evidence or {})
        proposed["updated_at"] = at
        MODULE.validate_state(proposed)
        self.state = proposed

    def prepare(self):
        self.state["rooms"] = {key: "oc_" + key for key in MODULE.ROOM_KEYS}
        artifacts = self.state["artifacts"]
        artifacts["task_id"] = "guid_one"
        work = artifacts["work_item"]
        work.update(task_guid="guid_one", task_url="https://example.test/task", status="changes_requested")
        work["document"].update(token="doc_one", url="https://example.test/doc", revision=3)
        work["review"].update(round=1, state="changes_requested", comment_ids=["comment_one"],
                              feedback_block_id="block_metric", last_reviewed_revision=3)
        receipts = {f"demo.chat.{room}": {"chat_id": chat} for room, chat in self.state["rooms"].items()}
        receipts.update({
            "demo.document": {"document_token": "doc_one"},
            "demo.task": {"task_guid": "guid_one"},
            "demo.seed.submit": {"task_guid": "guid_one", "task_status": "done"},
            "demo.seed.review": {"score": 2, "revision": 3, "document_token": "doc_one"},
            "demo.seed.comment": {"comment_id": "comment_one", "block_id": "block_metric"},
            "demo.seed.reopen": {"task_guid": "guid_one", "task_status": "todo"},
            **{f"demo.drama.{role}": {"message_id": "om_" + role} for role in ("boss", "backend", "mentor")},
        })
        artifacts["action_receipts"] = {key: {"status": "done", **value} for key, value in receipts.items()}
        self.transition("ready")

    def decision(self, judgment="protect"):
        return {"message_id": "om_decision", "chat_id": "oc_boss_dm", "sender_id": "ou_player",
                "created_at": (self.start + timedelta(seconds=5)).isoformat(),
                "observed_at": (self.start + timedelta(seconds=6)).isoformat(),
                "text": "先做最小验证，其他功能放下一轮。", "judgment": judgment,
                "reason": "明确保护本期目标并分期。"}

    def submission(self, passing=True):
        return {"task_guid": "guid_one", "task_status": "done", "document_token": "doc_one",
                "completed_at": (self.start + timedelta(seconds=20)).isoformat(),
                "observed_at": (self.start + timedelta(seconds=21)).isoformat(), "revision": 4,
                "text": "问题 用户 指标 范围 风险",
                "rubric": [{"score": 1 if passing or i < 2 else 0, "quote": quote,
                            "reason": "按正文评价", "source": "seed" if i < 2 else "live_revision"}
                           for i, quote in enumerate(("问题", "用户", "指标", "范围", "风险"))]}

    def live(self):
        self.prepare()
        self.transition("start")
        self.transition("decision", 10, self.decision())

    def cleanup(self, passed=True):
        self.state["artifacts"]["finalization"] = dict.fromkeys(("diary_written", "hr_notified", "heartbeat_stopped"), True)
        self.state["runtime"]["heartbeat_id"] = None
        receipts = self.state["artifacts"]["action_receipts"]
        receipts["demo.final.task"] = {"status": "done", "task_guid": "guid_one", "task_status": "done"}
        receipts["demo.final.snapshot"] = {"status": "done", "task_guid": "guid_one"}
        receipts["demo.final.review-message"] = {"status": "done", "message_id": "om_final_review"}
        if passed:
            receipts["demo.final.comment"] = {"status": "done", "comment_id": "comment_one", "resolved": True}

    def test_preparation_waits_days_without_clock_or_inputs(self):
        self.prepare()
        self.state["updated_at"] = (self.start + timedelta(days=1)).isoformat()
        MODULE.validate_state(self.state)
        self.assertIsNone(self.state["runtime"]["session_deadline_at"])
        with self.assertRaisesRegex(ValueError, "cannot time out"):
            self.transition("timeout", 86400)
        with self.assertRaisesRegex(ValueError, "stage"):
            self.transition("decision", 10, self.decision())
        self.assertFalse(any(self.state["checkpoint_budget"].values()))

    def test_missing_or_wrong_preparation_receipts_block_ready(self):
        self.prepare()
        prepared = deepcopy(self.state)
        for key in prepared["artifacts"]["action_receipts"]:
            with self.subTest(key=key):
                self.state = deepcopy(prepared)
                self.state["demo"]["stage"] = "preparing"
                del self.state["artifacts"]["action_receipts"][key]
                with self.assertRaises(ValueError):
                    self.transition("ready")
        self.state = deepcopy(prepared)
        self.state["demo"]["stage"] = "preparing"
        self.state["artifacts"]["action_receipts"]["demo.seed.reopen"]["task_guid"] = "another_task"
        with self.assertRaisesRegex(ValueError, "mismatched"):
            self.transition("ready")

    def test_start_retry_and_resume_preserve_clock_and_objects(self):
        self.prepare()
        original = deepcopy(self.state["rooms"])
        self.transition("start")
        runtime = deepcopy(self.state["runtime"])
        self.transition("start", 90)
        self.assertEqual(self.state["runtime"], runtime)
        self.assertEqual(self.state["rooms"], original)
        self.assertEqual(self.state["demo"]["live_started_at"], self.start.isoformat())

    def test_wrong_chat_sender_and_prerun_input_rejected(self):
        self.prepare()
        self.transition("start")
        for key, value in (("chat_id", "oc_company"), ("sender_id", "ou_other"),
                           ("created_at", self.created.isoformat())):
            with self.subTest(key=key):
                evidence = self.decision()
                evidence[key] = value
                with self.assertRaises(ValueError):
                    self.transition("decision", 10, evidence)
        self.assertIsNone(self.state["demo"]["decision"])

    def test_semantic_judgments_preserved_not_forced_to_success(self):
        self.prepare()
        self.transition("start")
        self.transition("decision", 10, self.decision("accept_all"))
        self.assertEqual(self.state["flags"]["scope_response"], "accept_all")
        self.assertEqual(self.state["counters"]["tasks_completed"], 0)

    def test_duplicate_input_and_submission_do_not_repeat_review(self):
        self.live()
        self.transition("decision", 11, self.decision())
        self.assertEqual(self.state["processed_message_ids"], ["om_decision"])
        self.transition("submit", 25, self.submission())
        self.transition("submit", 26, self.submission())
        self.assertEqual(self.state["artifacts"]["work_item"]["review"]["round"], 2)
        other = self.submission()
        other["revision"] = 5
        with self.assertRaisesRegex(ValueError, "already consumed"):
            self.transition("submit", 27, other)

    def test_task_done_without_document_change_does_not_consume_revision(self):
        self.live()
        same = self.submission()
        same["revision"] = 3
        with self.assertRaisesRegex(ValueError, "尚未检测到修改"):
            self.transition("submit", 25, same)
        self.assertIsNone(self.state["demo"]["submission"])
        self.assertEqual(self.state["demo"]["stage"], "revision")
        self.transition("submit", 26, self.submission())

    def test_unverified_or_wrong_object_or_invented_quote_rejected(self):
        self.live()
        for key, value in (("task_status", "open"), ("task_guid", "other"),
                           ("document_token", "other"), ("completed_at", self.created.isoformat()),
                           ("text", "not the quoted text")):
            with self.subTest(key=key):
                evidence = self.submission()
                evidence[key] = value
                with self.assertRaises(ValueError):
                    self.transition("submit", 25, evidence)
        self.assertEqual(self.state["artifacts"]["work_item"]["review"]["round"], 1)

    def test_acceptance_waits_for_remote_cleanup_receipts(self):
        self.live()
        self.transition("submit", 25, self.submission())
        self.assertEqual(self.state["counters"]["tasks_completed"], 0)
        self.assertEqual(self.state["artifacts"]["work_item"]["review"]["state"], "reviewing")
        with self.assertRaisesRegex(ValueError, "cleanup"):
            self.transition("finish", 30)
        self.cleanup()
        self.transition("finish", 35)
        self.assertEqual(self.state["status"], "completed")
        self.assertEqual(self.state["counters"]["tasks_completed"], 1)
        self.transition("finish", 36)
        self.assertEqual(self.state["counters"]["tasks_completed"], 1)

    def test_failed_second_review_closes_without_acceptance(self):
        self.live()
        self.transition("submit", 25, self.submission(False))
        self.cleanup(False)
        self.transition("finish", 35)
        self.assertEqual(self.state["status"], "completed")
        self.assertEqual(self.state["artifacts"]["work_item"]["review"]["state"], "closed")
        self.assertEqual(self.state["counters"]["tasks_completed"], 0)

    def test_missing_comment_resolution_or_review_message_blocks_acceptance(self):
        self.live()
        self.transition("submit", 25, self.submission())
        self.cleanup()
        finalizing = deepcopy(self.state)
        for key in ("demo.final.comment", "demo.final.review-message", "demo.final.snapshot", "demo.final.task"):
            self.state = deepcopy(finalizing)
            del self.state["artifacts"]["action_receipts"][key]
            with self.assertRaisesRegex(ValueError, "receipt"):
                self.transition("finish", 35)
            self.assertEqual(self.state["status"], "finalizing")
            self.assertEqual(self.state["counters"]["tasks_completed"], 0)

    def test_timeout_never_fabricates_submission_or_success(self):
        self.live()
        with self.assertRaisesRegex(ValueError, "window ended"):
            self.transition("submit", 210, self.submission())
        self.transition("timeout", 210)
        self.cleanup(False)
        self.transition("finish", 215)
        self.assertEqual(self.state["status"], "aborted")
        self.assertIsNone(self.state["demo"]["submission"])
        self.assertEqual(self.state["counters"]["tasks_completed"], 0)

    def test_pause_cannot_extend_live_budget(self):
        self.live()
        self.state["paused"] = True
        with self.assertRaisesRegex(ValueError, "paused"):
            self.transition("submit", 25, self.submission())
        invalid = deepcopy(self.state)
        invalid["runtime"]["session_deadline_at"] = (self.start + timedelta(minutes=5)).isoformat()
        with self.assertRaisesRegex(ValueError, "four minutes"):
            MODULE.validate_state(invalid)
        self.transition("timeout", 210)

    def test_full_legacy_state_and_demo_are_isolated(self):
        full = MODULE.new_state(Namespace(run_id="pm-one-day-full", started_at=self.created.isoformat(),
                                         session_deadline_at=None, player_open_id="ou_player", player_name="实习生"))
        self.assertNotIn("mode", full)
        MODULE.validate_state(full)
        with self.assertRaisesRegex(ValueError, "full run"):
            MODULE.demo_transition(full, "start", self.start.isoformat(), {})
        self.state["current_beat"] = "E10"
        with self.assertRaisesRegex(ValueError, "DEMO"):
            MODULE.validate_state(self.state)

    def test_cli_atomic_retries_logs_lease_and_patch_guards(self):
        self.prepare()
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "state.json"
            self.state["runtime"]["lease"] = {"owner_id": "runner", "expires_at": (self.start + timedelta(seconds=90)).isoformat()}
            path.write_text(json.dumps(self.state))
            def cli(*args, owner="runner"):
                return subprocess.run([sys.executable, str(TOOL), *args, "--state", str(path),
                                       "--owner-id", owner, "--at", self.start.isoformat()],
                                      capture_output=True, text=True)
            self.assertNotEqual(cli("demo", "start", owner="wrong").returncode, 0)
            self.assertEqual(cli("demo", "start").returncode, 0)
            self.assertEqual(cli("demo", "start").returncode, 0)
            self.assertEqual(len(path.with_name("log.jsonl").read_text().splitlines()), 1)
            for patch in ({"mode": "full"}, {"demo": {"stage": "prepared"}},
                          {"runtime": {"session_deadline_at": None}}):
                self.assertNotEqual(cli("patch", "--patch-json", json.dumps(patch)).returncode, 0)
            saved = json.loads(path.read_text())
            self.assertEqual(saved["demo"]["stage"], "decision")
            MODULE.validate_state(saved)


if __name__ == "__main__":
    unittest.main()
