from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "demo-cues.py"


class DemoCueTests(unittest.TestCase):
    def base_state(self) -> dict:
        return {
            "mode": "live_demo",
            "status": "running",
            "paused": False,
            "demo": {
                "stage": "alignment",
                "pacing": "cue",
                "live_started_at": "2026-09-14T01:00:00+08:00",
                "resumed_at": "2026-09-14T01:00:00+08:00",
                "stage_entered_at": "2026-09-14T01:00:00+08:00",
            },
            "artifacts": {"action_receipts": {}},
        }

    def cue_run(self, state: dict, at: str) -> dict | None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state.json"
            path.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--state", str(path), "--at", at],
                capture_output=True, text=True, check=True,
            )
            return json.loads(result.stdout)

    def test_cues_arrive_in_order_and_pause_suppresses_them(self) -> None:
        state = self.base_state()
        first = self.cue_run(state, "2026-09-14T01:00:01+08:00")
        self.assertEqual(first["key"], "demo.cue.alignment.0")
        state["artifacts"]["action_receipts"][first["key"]] = {"status": "done"}
        self.assertEqual(self.cue_run(state, "2026-09-14T01:00:03+08:00")["key"], "demo.cue.alignment.1")
        state["paused"] = True
        self.assertIsNone(self.cue_run(state, "2026-09-14T01:00:30+08:00"))

    def test_pending_cue_requires_reconciliation(self) -> None:
        state = self.base_state()
        state["artifacts"]["action_receipts"]["demo.cue.alignment.0"] = {"status": "pending"}
        result = self.cue_run(state, "2026-09-14T01:00:10+08:00")
        self.assertTrue(result["reconcile"])

    def test_prepared_or_wrong_mode_is_quiet(self) -> None:
        state = self.base_state()
        state["status"] = "initializing"
        self.assertIsNone(self.cue_run(state, "2026-09-14T01:00:30+08:00"))
        state["status"] = "running"
        state["mode"] = "full"
        self.assertIsNone(self.cue_run(state, "2026-09-14T01:00:30+08:00"))


if __name__ == "__main__":
    unittest.main()
