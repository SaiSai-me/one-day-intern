from __future__ import annotations

import copy
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


engine = module("workflow", "state-tool.py")
diary = module("diary", "render-diary.py")
validator = module("validator", "validate-skill.py")
builder = module("builder", "build-release.py")
NOW = "2026-09-17T09:00:00+08:00"
LATER = "2026-09-18T09:00:00+08:00"
EXPIRY = "2026-09-19T09:00:00+08:00"


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.state = engine.new_state("pm-one-day-test", "ou_player", NOW)
        self.call("lease-acquire", {"expires_at": EXPIRY})
        self.call("patch", {"resources": {key: {"id": "id_" + key, "url": "https://example.test/" + key,
                                                "ready": True} for key in engine.RESOURCE_TYPES}})

    def call(self, command, data=None, at=NOW, owner="runner"):
        engine.mutate(self.state, command, data or {}, owner, at)

    def obs(self, kind="message", resource="company", text="叫我阿宁，没写过 PRD。我看明白邀请流程了。",
            origin="player", **overrides):
        item = {"key": "event-" + str(len(self.state["observations"]) + 1), "kind": kind,
                "resource_id": "id_" + resource, "origin": origin, "content": {"text": text}}
        if origin == "player":
            item["actor_id"] = "ou_player"
        if kind in {"message", "card", "reaction"}:
            item["occurred_at"] = NOW
        item.update(overrides)
        self.call("observe", item)
        return self.state["observations"][-1]["id"]

    def decide(self, key, ids):
        self.call("decide", {"key": key, "evidence_ids": ids, "reason": "依据所引用的真实内容"})

    def receipt(self, key):
        self.call("receipt", {"key": key, "status": "pending", "params": {"target": key}})
        self.call("receipt", {"key": key, "status": "done", "params": {"target": key},
                              "result": {"verified": True, "id": key}})

    def onboard(self):
        self.receipt("landing.shared")
        shared = self.obs(text="入组说明链接已发送", origin="agent")
        self.decide("landing_shared", [shared])
        intro = self.obs()
        self.call("introduce", {"evidence_id": intro, "fields": {"preferred_name": "阿宁", "stated_background": "没写过 PRD"}})
        self.decide("landing_understood", [intro])
        self.call("advance")
        return intro

    def ready_for_review(self):
        intro = self.onboard()
        seed = [self.obs("document", "prd", "草案 R03：待确认", "seed"),
                self.obs("whiteboard", "prototype", "P03 待设计", "seed"),
                self.obs("base", "feedback", "F02 请先让我确认", "seed"),
                self.obs("task", "task", "待提交", "seed")]
        self.decide("materials_ready", seed)
        self.decide("initial_judgment", [intro])
        self.call("advance")
        decision = self.obs(text="没有接受不能展示。O0 是待确认版本，Aria 修订。")
        self.decide("conflict_resolved", [decision])
        self.call("advance")
        board = self.obs("whiteboard", "prototype", "P03 未加入；拒绝后不允许重复发送", "unknown")
        doc = self.obs("document", "prd", "R03 接受后展示；R05 拒绝后未加入；重复只建一次；失效不建立；O1 Aria 负责", "unknown")
        self.decide("design_updated", [board, decision])
        self.decide("rules_updated", [doc, decision])
        self.call("advance")
        request = self.obs(text="请评审这版")
        self.decide("submission", [request])
        self.call("advance")

    def review(self, passed=True):
        ids = {k: self.state["snapshots"][k]["evidence_id"] for k in ("prd", "prototype")}
        self.call("review", {"snapshot_ids": ids, "checks": [
            {"criterion": c, "passed": passed, "reason": "依据实际规则和原型核对", "location": "R03 / P03",
             "quote": "接受后展示", "evidence_ids": [ids["prd"], ids["prototype"]]} for c in sorted(engine.CRITERIA)]})

    def test_no_modes_deadlines_or_one_turn_budgets(self):
        self.call("pause", at=LATER)
        self.call("resume", at=LATER)
        self.assertEqual(self.state["stage"], "S01")
        self.assertNotIn("mode", self.state)
        self.assertNotIn("checkpoint_budget", self.state)
        for patch in ({"mode": "live_demo"}, {"runtime": {"session_deadline_at": EXPIRY}}):
            with self.assertRaises(ValueError):
                self.call("patch", patch, at=LATER)

    def test_no_default_introduction_and_no_silent_advancement(self):
        with self.assertRaises(ValueError):
            self.call("advance")
        self.assertIsNone(self.state["player"]["introduction"])
        self.assertEqual(self.state["stage"], "S01")

    def test_intro_persists_across_memory_rotation_and_reload(self):
        self.onboard()
        for n in range(20):
            self.call("patch", {"memory": [f"最近第 {n} 轮"]})
        restored = json.loads(json.dumps(self.state))
        engine.validate(restored)
        self.assertEqual(restored["player"]["name"], "阿宁")
        self.assertIn("没写过 PRD", restored["player"]["introduction"]["text"])

    def test_intro_corrections_keep_original_and_require_explicit_words(self):
        self.onboard()
        correction = self.obs(text="后面叫我宁宁")
        self.call("introduce", {"evidence_id": correction, "correction": True, "fields": {"preferred_name": "宁宁"}})
        self.assertEqual(self.state["player"]["name"], "宁宁")
        self.assertEqual(self.state["player"]["introduction"]["fields"]["preferred_name"], "阿宁")
        with self.assertRaises(ValueError):
            self.call("introduce", {"evidence_id": correction, "correction": True, "fields": {"stated_background": "高级设计师"}})

    def test_explicit_intro_opt_out(self):
        eid = self.obs(text="我不想介绍自己，叫实习生就好")
        self.call("introduce", {"evidence_id": eid, "skipped": True, "fields": {}})
        self.assertTrue(self.state["player"]["introduction"]["skipped"])

    def test_replayed_original_intro_cannot_undo_correction(self):
        original = self.onboard()
        corrected = self.obs(text="以后叫宁宁")
        self.call("introduce", {"evidence_id": corrected, "correction": True, "fields": {"preferred_name": "宁宁"}})
        self.call("introduce", {"evidence_id": original, "fields": {"preferred_name": "阿宁", "stated_background": "没写过 PRD"}})
        self.assertEqual(self.state["player"]["name"], "宁宁")

    def test_paused_callbacks_not_replayed_on_resume(self):
        self.call("pause")
        self.call("resume", at=LATER)
        with self.assertRaises(ValueError):
            self.call("observe", {"key": "late", "kind": "message", "origin": "player", "actor_id": "ou_player",
                "resource_id": "id_company", "occurred_at": "2026-09-17T10:00:00+08:00", "content": {"text": "请评审"}}, at=LATER)
        self.assertEqual(self.state["observations"], [])

    def test_wrong_player_wrong_room_and_bot_intro_rejected(self):
        with self.assertRaises(ValueError):
            self.obs(actor_id="ou_other")
        eid = self.obs(origin="agent")
        with self.assertRaises(ValueError):
            self.call("introduce", {"evidence_id": eid})
        eid = self.obs(resource="mentor_dm")
        with self.assertRaises(ValueError):
            self.call("introduce", {"evidence_id": eid})

    def test_out_of_scope_and_old_messages_rejected(self):
        with self.assertRaises(ValueError):
            self.obs(resource_id="oc_unrelated")
        with self.assertRaises(ValueError):
            self.obs(occurred_at="2026-09-16T09:00:00+08:00")
        self.assertEqual(self.state["observations"], [])

    def test_duplicate_event_idempotency_and_collision(self):
        self.obs(key="stable")
        item = {k: v for k, v in self.state["observations"][0].items() if k in {
            "key", "kind", "resource_id", "origin", "content", "actor_id", "occurred_at"}}
        self.call("observe", item)
        self.assertEqual(len(self.state["observations"]), 1)
        item["content"] = {"text": "different"}
        with self.assertRaises(ValueError):
            self.call("observe", item)

    def test_revision_only_is_not_content_change(self):
        self.obs("document", "prd", "同一正文", "seed", revision=1)
        eid = self.obs("document", "prd", "同一正文", "unknown", revision=2)
        self.assertFalse(self.state["observations"][-1]["changed"])
        msg = self.obs(text="我改过了")
        with self.assertRaises(ValueError):
            self.decide("rules_updated", [eid, msg])

    def test_out_of_order_document_revision_rejected(self):
        self.obs("document", "prd", "第二版", "unknown", revision=2)
        with self.assertRaises(ValueError):
            self.obs("document", "prd", "旧版本", "unknown", revision=1)
        self.assertEqual(self.state["snapshots"]["prd"]["revision"], 2)

    def test_reverting_content_is_a_new_change_not_duplicate(self):
        self.obs("whiteboard", "prototype", "A", "seed")
        self.obs("whiteboard", "prototype", "B", "unknown")
        self.obs("whiteboard", "prototype", "A", "unknown")
        self.assertEqual([o["changed"] for o in self.state["observations"]], [False, True, True])

    def test_unknown_whiteboard_author_not_credited_to_player(self):
        self.obs("whiteboard", "prototype", "草图", "seed")
        changed = self.obs("whiteboard", "prototype", "未加入", "unknown")
        with self.assertRaises(ValueError):
            self.decide("design_updated", [changed])
        comment = self.obs("comment", "prd", "P03 改为未加入，这是我的决定")
        self.decide("design_updated", [changed, comment])
        self.assertEqual(self.state["observations"][changed - 1]["origin"], "unknown")

    def test_card_scope_versions_and_actions(self):
        self.call("patch", {"cards": {"om_card": {"chat_id": "id_company", "version": "1", "active": True,
                                                   "purpose": "review", "actions": ["request_review"]}}})
        payload = {"message_id": "om_card", "version": "1", "action": "request_review"}
        self.obs("card", content=payload)
        with self.assertRaises(ValueError):
            self.decide("landing_understood", [self.state["observations"][-1]["id"]])
        for invalid in ({**payload, "version": "0"}, {**payload, "action": "accept_all"}, {**payload, "message_id": "om_elsewhere"}):
            with self.assertRaises(ValueError):
                self.obs("card", content=invalid)

    def test_rule_change_invalidates_invitation_sample(self):
        self.obs("document", "prd", "规则一", "seed")
        self.call("patch", {"cards": {"om_sample": {"chat_id": "id_company", "version": "1", "active": True,
            "purpose": "invitation_sample", "actions": ["accept"], "rule_digest": self.state["snapshots"]["prd"]["digest"]}}})
        self.obs("document", "prd", "规则二", "unknown")
        self.assertFalse(self.state["cards"]["om_sample"]["active"])
        with self.assertRaises(ValueError):
            self.obs("card", content={"message_id": "om_sample", "version": "1", "action": "accept"})

    def test_reaction_is_not_understanding_or_submission(self):
        eid = self.obs("reaction", text="👍")
        for key in ("landing_understood", "submission"):
            with self.assertRaises(ValueError):
                self.decide(key, [eid])

    def test_pause_stops_work_but_retains_progress(self):
        self.onboard()
        self.call("pause")
        with self.assertRaises(ValueError):
            self.obs()
        self.call("resume", at=LATER)
        self.assertEqual(self.state["stage"], "S02")
        self.assertEqual(self.state["player"]["name"], "阿宁")

    def test_failed_mutation_is_atomic(self):
        before = copy.deepcopy(self.state)
        with self.assertRaises(ValueError):
            self.call("patch", {"resources": {"prd": {"url": "new"}}, "runtime": {"story_deadline_at": NOW}})
        self.assertEqual(self.state, before)

    def test_lease_exclusion_and_expiration(self):
        with self.assertRaises(PermissionError):
            self.call("lease-acquire", {"expires_at": EXPIRY}, owner="other")
        with self.assertRaises(PermissionError):
            self.call("pause", at=EXPIRY)

    def test_resource_id_cannot_change(self):
        with self.assertRaises(ValueError):
            self.call("patch", {"resources": {"prd": {"id": "another_doc"}}})

    def test_receipts_pending_before_done_and_idempotent(self):
        with self.assertRaises(ValueError):
            self.call("receipt", {"key": "x", "status": "done", "params": {}, "result": {"id": "1"}})
        self.receipt("x")
        with self.assertRaises(ValueError):
            self.call("receipt", {"key": "x", "status": "pending", "params": {"target": "x"}})

    def test_unlimited_real_review_iterations(self):
        self.ready_for_review()
        for _ in range(4):
            self.review(False)
        self.assertEqual(self.state["review"]["round"], 4)
        with self.assertRaises(ValueError):
            self.call("advance")
        self.review(True)
        self.call("advance")
        self.assertEqual(self.state["stage"], "S07")

    def test_task_done_does_not_pass_review(self):
        done = self.obs("task", "task", origin="unknown", content={"status": "done"})
        self.decide("submission", [done])
        self.assertEqual(self.state["review"]["state"], "not_started")
        with self.assertRaises(ValueError):
            self.call("finalize", {"outcome": "completed"})

    def test_current_version_changes_invalidate_pass(self):
        self.ready_for_review()
        self.review()
        self.call("advance")
        eid = self.obs(text="已交接评审版", origin="agent")
        self.decide("handoff", [eid])
        self.obs("whiteboard", "prototype", "改了 P03", "unknown")
        self.assertEqual(self.state["review"]["state"], "stale")
        self.assertNotIn("handoff", self.state["decisions"])
        with self.assertRaises(ValueError):
            self.call("finalize", {"outcome": "completed"})

    def test_review_cannot_invent_quotes_or_use_old_snapshots(self):
        self.ready_for_review()
        ids = {k: self.state["snapshots"][k]["evidence_id"] for k in ("prd", "prototype")}
        checks = [{"criterion": c, "passed": True, "reason": "reason", "location": "R03",
                   "quote": "并不存在的内容", "evidence_ids": [ids["prd"]]} for c in engine.CRITERIA]
        with self.assertRaises(ValueError):
            self.call("review", {"snapshot_ids": ids, "checks": checks})
        ids["prd"] = 1
        with self.assertRaises(ValueError):
            self.call("review", {"snapshot_ids": ids, "checks": checks})

    def test_full_workflow_and_cleanup_recovery(self):
        self.ready_for_review()
        self.review()
        self.call("advance")
        eid = self.obs(text="按这版交接，Aria 接活动说明", origin="agent")
        self.decide("handoff", [eid])
        self.call("finalize", {"outcome": "completed"})
        with self.assertRaises(ValueError):
            self.call("finish")
        self.assertEqual(self.state["status"], "finalizing")
        for key in ("final.diary", "final.notify", "final.stop"):
            self.receipt(key)
        self.call("finish")
        self.assertEqual(self.state["status"], "completed")
        self.assertIsNone(self.state["runtime"]["lease"]["owner_id"])
        with self.assertRaises(ValueError):
            self.call("pause")

    def test_early_exit_is_not_success(self):
        self.call("finalize", {"outcome": "aborted"})
        for key in ("final.diary", "final.notify", "final.stop"):
            self.receipt(key)
        self.call("finish")
        self.assertEqual(self.state["status"], "aborted")
        self.assertFalse(engine.review_current(self.state))

    def test_historical_save_not_rewritten(self):
        before = {"schema_version": 4, "mode": "live_demo"}
        with self.assertRaises(ValueError):
            engine.mutate(before, "pause", {}, "runner", NOW)
        self.assertEqual(before, {"schema_version": 4, "mode": "live_demo"})

    def test_cli_disk_roundtrip_and_failed_write(self):
        with tempfile.TemporaryDirectory() as tmp:
            run = Path(tmp) / "run"
            cmd = [sys.executable, str(ROOT / "scripts/state-tool.py")]
            created = subprocess.run(cmd + ["init", "--run-dir", str(run), "--run-id", "pm-one-day-cli",
                "--player-open-id", "ou_me", "--at", NOW], capture_output=True, text=True)
            self.assertEqual(created.returncode, 0, created.stderr)
            state_path = run / "state.json"
            before = state_path.read_bytes()
            failed = subprocess.run(cmd + ["advance", "--state", str(state_path), "--owner-id", "other", "--at", NOW], capture_output=True)
            self.assertNotEqual(failed.returncode, 0)
            self.assertEqual(state_path.read_bytes(), before)


class PackagingAndDiaryTests(unittest.TestCase):
    def test_prototype_has_editable_text_and_no_external_images(self):
        svg = ET.fromstring((ROOT / "assets/prototype.svg").read_text())
        ns = {"s": "http://www.w3.org/2000/svg"}
        self.assertIsNotNone(svg.find("s:text[@id='p03-rejection-state']", ns))
        self.assertGreater(len(svg.findall("s:text", ns)), 20)
        for tag in ("script", "image", "foreignObject", "mask", "clipPath"):
            self.assertEqual(svg.findall(".//s:" + tag, ns), [])

    def test_active_skill_and_deterministic_release(self):
        validator.validate_skill(ROOT)
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / "a.zip", Path(tmp) / "b.zip"
            builder.build(ROOT, a)
            builder.build(ROOT, b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            validator.validate_zip(ROOT, a)

    def test_diary_escapes_text_without_interpreting_player_placeholders(self):
        data = {key: "value" for key in diary.REQUIRED_SCALARS}
        data.update(player_name='<script>{{run_id}}</script>', highlights=["<img onerror=x>"], outcome="未完成", ending="无推断")
        result = diary.render((ROOT / "assets/diary-template.html").read_text(), data)
        self.assertIn("&lt;script&gt;{{run_id}}&lt;/script&gt;", result)
        self.assertNotIn("<script>", result)


if __name__ == "__main__":
    unittest.main()
