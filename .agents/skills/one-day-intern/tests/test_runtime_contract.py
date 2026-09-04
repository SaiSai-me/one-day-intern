from __future__ import annotations

import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).resolve().parents[1]


class RuntimeContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.skill = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
        cls.contract = (SKILL_DIR / "references/lark-cli-contract.md").read_text(encoding="utf-8")
        cls.adapter = (SKILL_DIR / "references/artifact-adapters.md").read_text(encoding="utf-8")
        cls.dashboard = (SKILL_DIR / "references/data-dashboard.md").read_text(encoding="utf-8")
        cls.permissions = (SKILL_DIR / "references/permission-setup.md").read_text(encoding="utf-8")

    def test_permission_setup_covers_user_bot_and_recovery(self) -> None:
        for text in (
            "missing_scopes",
            "console_url",
            "lark-cli auth login",
            "im.message.receive_v1",
            "创建和管理群聊",
            "云文档评论",
            "继续实习",
        ):
            self.assertIn(text, self.permissions)
        self.assertIn("permission-setup.md", self.skill)
        self.assertIn("permission-setup.md", self.contract)

    def test_three_entry_and_single_bot_contract(self) -> None:
        for room in ("company", "mentor_dm", "boss_dm"):
            self.assertIn(room, self.contract)
        self.assertIn("同一 bot", self.skill)
        self.assertIn("chat_type", self.contract)

    def test_document_task_submission_contract(self) -> None:
        for command in (
            "docs +create",
            "task +create",
            "task tasks get",
            "docs +fetch",
            "drive +add-comment",
            "task +reopen",
            "task +complete",
        ):
            self.assertIn(command, self.contract)
        self.assertIn("点击完成即提交", self.contract)
        self.assertIn("permission_grant.status", self.adapter)

    def test_adapter_contract_and_runtime_limits(self) -> None:
        for operation in (
            "create_template",
            "capture_revision",
            "fetch_for_review",
            "locate_feedback_target",
            "write_feedback",
            "has_changed",
        ):
            self.assertIn(f"`{operation}`", self.adapter)
        compression = (SKILL_DIR / "references/runtime-compression.md").read_text(encoding="utf-8")
        self.assertIn("runtime.session_deadline_at", compression)
        self.assertIn("30 分钟", self.skill)
        self.assertIn("不得再重开任务", self.adapter)

    def test_checkpoint_and_deadline_contract(self) -> None:
        for checkpoint in (
            "onboarding",
            "problem_metric",
            "evidence_scope",
            "first_submit",
            "micro_revision",
            "final_decision",
        ):
            self.assertIn(checkpoint, self.skill)
        self.assertIn("session_deadline_at", self.skill)
        self.assertIn("15 秒", self.skill)
        self.assertIn("2 秒", self.skill)

    def test_outbound_text_forbids_visible_newline_escapes(self) -> None:
        self.assertIn("单行纯文本", self.contract)
        self.assertIn("禁止先把正文序列化为 JSON", self.contract)
        self.assertIn("拆成两次 `messages-send`", self.contract)
        beat = (SKILL_DIR / "references/beat-e01.md").read_text(encoding="utf-8")
        onboarding = next(line for line in beat.splitlines() if "现在轮到你啦" in line)
        self.assertNotIn("\\n", onboarding)
        self.assertNotIn("\\r", onboarding)
        self.assertNotIn("\\\\n", onboarding)
        self.assertNotIn("\\\\r", onboarding)
        for path in (SKILL_DIR / "references").glob("beat-e*.md"):
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("\\n", text, path.name)
            self.assertNotIn("\\r", text, path.name)

    def test_e01_is_landing_before_assignment(self) -> None:
        beat = (SKILL_DIR / "references/beat-e01.md").read_text(encoding="utf-8")
        landing = (SKILL_DIR / "references/landing-orientation.md").read_text(encoding="utf-8")
        self.assertIn("E01 · Landing", beat)
        self.assertIn("https://wqua64v2akt.feishu.cn/docx/TCwtdW1EKoWtOUxtySbc9JJtnQb", beat)
        for actor in ("【人事】Chloe", "【Mentor】kris姐", "【产品总监】Vincent", "【技术负责人】Ethan", "【运营】Aria"):
            self.assertIn(actor, beat)
        self.assertIn("不得创建旧版 `lobby`", beat)
        self.assertIn("玩家完成 Landing 确认后", beat)
        self.assertIn("不创建 PRD 文档、飞书任务或日程", beat)
        self.assertLess(beat.index("阶段一：Landing 与团队见面"), beat.index("阶段二：创建工作对象"))
        self.assertIn("第一份玩家可见材料", landing)
        self.assertIn("后台 `docs +fetch` 成功不等于玩家已经看过", landing)
        self.assertIn("E01 是唯一例外", self.skill)

    def test_e02_uses_verified_dashboard_instead_of_kpi_messages(self) -> None:
        beat = (SKILL_DIR / "references/beat-e02.md").read_text(encoding="utf-8")
        self.assertIn("data-dashboard.md", beat)
        self.assertIn('artifacts.data_dashboard.status="ready"', beat)
        self.assertIn("不在 Chat 中复述 41%、47% 或 18%", beat)
        for command in (
            "sheets +workbook-create",
            "sheets +chart-create",
            "+workbook-info",
            "+csv-get",
            "+chart-list",
            "+revision-get",
        ):
            self.assertIn(command, self.dashboard)
        self.assertIn("三个指标的分母不同", self.dashboard)
        self.assertIn("不得退回聊天逐条发送 KPI", self.dashboard)


if __name__ == "__main__":
    unittest.main()
