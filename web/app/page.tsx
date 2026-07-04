import Link from "next/link";
import { supabase, type InternPack } from "@/lib/supabase";

export const revalidate = 30;

export default async function Home() {
  const { data: packs, error } = await supabase
    .from("intern_packs")
    .select("*")
    .order("downloads", { ascending: false })
    .returns<InternPack[]>();

  return (
    <div>
      <section className="px-card p-6 mb-10 relative overflow-hidden">
        <div className="px-badge-yellow text-xs mb-3">🎮 开源实习模拟器平台</div>
        <h1 className="text-2xl leading-relaxed mb-2">
          你好!我是今天的<span className="text-[var(--blue)]">一日实习生</span>酱~
        </h1>
        <p className="text-sm leading-7 text-[var(--ink)]/80 max-w-2xl">
          下载一个「实习包」,接上你本地的 AI Agent 和个人飞书,
          就能沉浸式地在一家虚构公司上一天班:被派活、开会吵架、评审被怼、摸鱼划水,
          下班还送一份可以发朋友圈的搞笑实习日记。
        </p>
        <p className="text-xs mt-3 text-[var(--blue)]">
          在家抠脚,好想实习!→ 当场上班 ↓
        </p>
      </section>

      <h2 className="px-h2 mb-6">▶ 实习包市场</h2>

      {error && (
        <div className="px-card p-4 text-sm text-[var(--red)]">
          加载失败:{error.message}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mt-2">
        {(packs ?? []).map((pack) => (
          <Link key={pack.id} href={`/packs/${pack.id}`}>
            <article className="px-card px-card-hover p-5 h-full flex flex-col gap-3">
              <header className="flex items-start justify-between gap-2">
                <h3 className="text-lg leading-snug">{pack.name}</h3>
                <span className="px-tag shrink-0 !bg-[var(--yellow)]">
                  ⬇ {pack.downloads}
                </span>
              </header>
              <p className="text-xs leading-6 text-[var(--ink)]/75 flex-1">
                {pack.tagline}
              </p>
              <div className="flex flex-wrap gap-2">
                {pack.tags?.map((t) => (
                  <span key={t} className="px-tag">
                    {t}
                  </span>
                ))}
              </div>
              <footer className="text-[11px] text-[var(--blue)] flex justify-between pt-1 border-t-2 border-dashed border-[var(--sky)]">
                <span>🏢 {pack.company}</span>
                <span>by {pack.author}</span>
              </footer>
            </article>
          </Link>
        ))}
        {(packs ?? []).length === 0 && !error && (
          <div className="px-card p-6 text-sm">
            还没有实习包,点右上角「+ 上传实习包」成为第一个创作者!
          </div>
        )}
      </div>
    </div>
  );
}
