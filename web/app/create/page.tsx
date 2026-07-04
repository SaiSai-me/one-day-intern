"use client";

import { useState } from "react";
import Link from "next/link";

const CREATE_PROMPT = `帮我创作一个「一日实习生」实习包(格式规范 pack-spec v2):
- 岗位:(比如:游戏策划实习生)
- 虚构公司:(起个梗名,比如:鹅厂平替)
- 我想让玩家体验的名场面:(比如:周五下午五点被拉进需求评审)
- 同事人设:(老板/导师/损友…各自什么梗)
- 风格:(搞笑/写实/恐怖上班文学…)
请按 pack.json + company.md + personas/ + timeline.md(幕索引)+ beats/(每幕一个文件,含判定规则)
的结构生成,每个 choice 幕都要有 timeout_fallback,最后打包成 zip。`;

const STEPS = [
  {
    icon: "📐",
    title: "① 想清楚你要复刻哪一天班",
    body: "一个好实习包 = 一个岗位 + 一家有梗的虚构公司 + 3~5 个名场面(被派活/评审被怼/排期扯皮…)+ 4~5 个同事人设。骨架你写死,细节 AI 即兴——你是在写剧本杀的主持人手册,不是台词本。",
  },
  {
    icon: "🤖",
    title: "② 让你的 AI 替你写(推荐)",
    body: "打开你的本地 AI(如 Claude Code),粘贴下面的创作指令,像接受访谈一样回答它的问题,几分钟就能生成整包。它会自动校验幕跳转闭合、每个选择都有兜底。",
    prompt: true,
  },
  {
    icon: "🧪",
    title: "③ 本地试跑一遍",
    body: "对 AI 说「加载我的实习包,开始上班(压缩模式)」,在自己的飞书里走一遍剧情。重点检查:选择分支都能走通、评审怼得够不够狠、日记好不好笑。",
  },
  {
    icon: "🚀",
    title: "④ 打包上架",
    body: "把实习包目录压成 zip,填好名字和标签,发布到集市。上架后所有玩家都能下载你的班,下载数和直播场次都会记在你的作品上。",
    upload: true,
  },
];

export default function CreatePage() {
  const [copied, setCopied] = useState(false);

  async function copy() {
    await navigator.clipboard.writeText(CREATE_PROMPT);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="max-w-3xl mx-auto px-4 py-8">
      <h1 className="px-h2">🛠 创建实习包</h1>
      <p className="text-xs text-[var(--ink)]/70 mt-3 mb-8 leading-6">
        上班上美了?把你的日常做成实习包,让全世界替你上班。
        实习包是<b>纯数据剧本</b>(Markdown + JSON),不用写一行代码。
      </p>

      <div className="flex flex-col gap-5">
        {STEPS.map((s) => (
          <section key={s.title} className="px-card p-6">
            <div className="flex items-center gap-3 mb-2">
              <span className="text-2xl">{s.icon}</span>
              <h2 className="text-sm">{s.title}</h2>
            </div>
            <p className="text-xs leading-6 text-[var(--ink)]/80">{s.body}</p>

            {s.prompt && (
              <div className="mt-4">
                <pre className="text-[11px] leading-5 bg-[var(--paper)] border-2 border-dashed border-[var(--sky)] p-4 whitespace-pre-wrap">
                  {CREATE_PROMPT}
                </pre>
                <button onClick={copy} className="px-btn !text-xs mt-3">
                  {copied ? "✓ 已复制,去粘给你的 AI" : "📋 复制创作指令"}
                </button>
              </div>
            )}

            {s.upload && (
              <Link href="/upload" className="px-btn px-btn-blue !text-sm mt-4 inline-block">
                🚀 去上架我的实习包
              </Link>
            )}
          </section>
        ))}
      </div>

      <div className="px-card p-5 mt-8 text-[11px] leading-6 text-[var(--ink)]/70">
        <span className="px-badge-yellow !text-[11px] mr-2">创作守则</span>
        包内禁止:可执行脚本、任何人的真实信息、真实公司名(用梗名平替)。
        人设卡必须写「即兴红线」(不辱骂、不涉真人)。违规包会被下架。
      </div>
    </div>
  );
}
