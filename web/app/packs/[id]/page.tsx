import Link from "next/link";
import { notFound } from "next/navigation";
import { supabase, type InternPack } from "@/lib/supabase";
import DownloadButton from "./DownloadButton";

export const revalidate = 30;

export default async function PackDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const { data: pack } = await supabase
    .from("intern_packs")
    .select("*")
    .eq("id", id)
    .single<InternPack>();

  if (!pack) notFound();

  const stats = pack.stats ?? {};
  const requires = pack.requires ?? {};

  return (
    <div className="max-w-3xl mx-auto">
      <Link href="/" className="text-xs text-[var(--blue)] hover:underline">
        ← 返回实习包市场
      </Link>

      <article className="px-card p-7 mt-4">
        <div className="px-badge-yellow text-xs mb-4">
          📦 {pack.id} · v{pack.version}
        </div>
        <h1 className="text-2xl mb-2">{pack.name}</h1>
        <p className="text-sm text-[var(--ink)]/75 mb-5">{pack.tagline}</p>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
          {[
            ["岗位", pack.role],
            ["公司", pack.company],
            ["难度", pack.difficulty],
            ["下载", `${pack.downloads} 次`],
          ].map(([k, v]) => (
            <div key={k} className="border-3 border-[var(--ink)] p-3 text-center" style={{ borderWidth: 3, boxShadow: "4px 4px 0 var(--ink)" }}>
              <div className="text-[11px] text-[var(--blue)] mb-1">{k}</div>
              <div className="text-sm">{v}</div>
            </div>
          ))}
        </div>

        <div className="flex flex-wrap gap-2 mb-6">
          {pack.tags?.map((t) => (
            <span key={t} className="px-tag">{t}</span>
          ))}
        </div>

        <div className="text-xs leading-7 mb-6 border-2 border-dashed border-[var(--sky)] p-4 bg-[var(--paper)]">
          <div>🎬 剧情事件 {stats.events ?? "?"} 个 · 分支选择 {stats.choices ?? "?"} 处 · NPC {stats.npcs ?? "?"} 位</div>
          <div>
            🔌 需要飞书权限域:{(requires.domains ?? []).join(" / ") || "无"}
            {requires.optional?.length ? `(可选:${requires.optional.join(" / ")})` : ""}
          </div>
          <div>✍️ 作者:{pack.author}</div>
        </div>

        <DownloadButton pack={pack} />

        <section className="mt-8 text-xs leading-7 text-[var(--ink)]/80">
          <h2 className="px-h2 !text-xs mb-3">▶ 怎么玩?</h2>
          <ol className="list-decimal list-inside space-y-1">
            <li>下载实习包 zip,解压到本地 <code className="bg-[var(--paper)] px-1">packs/</code> 目录</li>
            <li>安装飞书 CLI:<code className="bg-[var(--paper)] px-1">npx @larksuite/cli@latest install</code> 并完成 <code className="bg-[var(--paper)] px-1">config init</code> + <code className="bg-[var(--paper)] px-1">auth login</code></li>
            <li>打开你的本地 AI Agent(如 Claude Code),安装 one-day-intern 引擎技能</li>
            <li>对 Agent 说:「加载 {pack.id} 实习包,开始上班!」</li>
          </ol>
        </section>
      </article>
    </div>
  );
}
