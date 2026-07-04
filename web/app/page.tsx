import Link from "next/link";

const BUZZWORDS = "对齐 ▸ 抓手 ▸ 闭环 ▸ 颗粒度 ▸ 拉通 ▸ 赋能 ▸ 组合拳 ▸ 护城河 ▸ 双月OKR ▸ 向上管理 ▸ 降本增效 ▸ 底层逻辑 ▸ 用户心智 ▸ 价值沉淀 ▸ ";

/** 像素城市天际线:互联网大厂园区 */
function CitySkyline() {
  return (
    <svg
      viewBox="0 0 960 240"
      className="w-full block"
      shapeRendering="crispEdges"
      aria-hidden
    >
      {/* 太阳(打工人的 kpi 一样准时升起) */}
      <rect x="812" y="24" width="48" height="48" fill="var(--yellow)" stroke="var(--ink)" strokeWidth="4" />
      {/* 像素云 */}
      <g fill="var(--white)" stroke="var(--ink)" strokeWidth="3">
        <rect x="80" y="40" width="90" height="22" />
        <rect x="110" y="26" width="46" height="18" />
        <rect x="420" y="30" width="100" height="22" />
        <rect x="452" y="16" width="48" height="18" />
        <rect x="660" y="52" width="80" height="20" />
      </g>
      {/* 楼群 */}
      <g stroke="var(--ink)" strokeWidth="4">
        {/* 跳动大厂总部 */}
        <rect x="60" y="90" width="120" height="150" fill="#bfe0ff" />
        <rect x="88" y="64" width="64" height="26" fill="#bfe0ff" />
        <rect x="116" y="40" width="8" height="24" fill="var(--ink)" stroke="none" />
        {/* 鹅厂双子楼 */}
        <rect x="230" y="120" width="70" height="120" fill="var(--sky)" />
        <rect x="316" y="104" width="70" height="136" fill="var(--sky)" />
        <rect x="300" y="150" width="16" height="14" fill="var(--ink)" stroke="none" />
        {/* 猫厂园区 */}
        <rect x="440" y="140" width="150" height="100" fill="#bfe0ff" />
        <rect x="470" y="110" width="90" height="30" fill="#bfe0ff" />
        {/* 加班中的写字楼 */}
        <rect x="640" y="84" width="90" height="156" fill="var(--blue)" />
        {/* 厂牌楼 */}
        <rect x="770" y="130" width="130" height="110" fill="var(--sky)" />
      </g>
      {/* 窗户(亮灯的都是在加班) */}
      <g fill="var(--yellow)">
        {[0, 1, 2, 3].map((r) =>
          [0, 1, 2].map((c) => (
            <rect key={`a${r}${c}`} x={78 + c * 32} y={104 + r * 32} width="14" height="14" />
          ))
        )}
        {[0, 1, 2].map((r) => (
          <rect key={`b${r}`} x={658} y={100 + r * 40} width="14" height="14" />
        ))}
        <rect x="700" y="140" width="14" height="14" />
        <rect x="700" y="220" width="14" height="14" fill="var(--white)" />
        {[0, 1].map((r) =>
          [0, 1, 2].map((c) => (
            <rect key={`c${r}${c}`} x={460 + c * 44} y={156 + r * 40} width="16" height="16" fill={(r + c) % 2 ? "var(--yellow)" : "var(--white)"} />
          ))
        )}
        {[0, 1].map((r) =>
          [0, 1].map((c) => (
            <rect key={`d${r}${c}`} x={246 + c * 30} y={140 + r * 44} width="14" height="14" fill="var(--white)" />
          ))
        )}
        {[0, 1].map((r) =>
          [0, 1].map((c) => (
            <rect key={`e${r}${c}`} x={332 + c * 30} y={124 + r * 44} width="14" height="14" />
          ))
        )}
      </g>
      {/* 楼顶招牌 */}
      <g fontFamily="inherit" fill="var(--ink)" fontSize="13">
        <text x="70" y="82" fontSize="12">跳动大厂</text>
        <text x="782" y="124">厂里厂气</text>
      </g>
      {/* 地面 */}
      <rect x="0" y="236" width="960" height="4" fill="var(--ink)" />
    </svg>
  );
}

const SECTIONS = [
  { href: "/market", icon: "🏬", title: "实习集市", desc: "按部门逛遍全网实习包,总有一款班适合你上" },
  { href: "/my", icon: "🎒", title: "我的实习", desc: "收藏的实习包都在工牌里,随时开工" },
  { href: "/dashboard", icon: "📺", title: "实习看板", desc: "上班实况直播:进度、量表、名场面" },
  { href: "/create", icon: "🛠", title: "创建实习包", desc: "把你的班做成剧本,让全世界替你上" },
] as const;

export default function Home() {
  return (
    <div>
      {/* ============ Hero:像素大厂 City ============ */}
      <section className="hero-sky relative overflow-hidden">
        <div className="max-w-5xl mx-auto px-4 pt-14 pb-0 text-center relative z-10">
          <div className="px-badge-yellow text-xs mb-5">🎮 游戏化实习模拟器 · 开源平台</div>
          <h1 className="text-5xl sm:text-6xl leading-tight mb-3 tracking-widest">
            一日实习生
          </h1>
          <div className="text-sm text-[var(--blue)] tracking-[0.35em] mb-5">ONE-DAY INTERN</div>
          <p className="text-sm leading-7 max-w-xl mx-auto text-[var(--ink)]/80 mb-8">
            接上你的 AI 和飞书,今天就去一家虚构大厂上班:
            被派活、开会吵架、评审被怼、摸鱼划水——
            下班还送一份能发朋友圈的实习日记。
          </p>
          <div className="flex gap-4 justify-center flex-wrap mb-4">
            <Link href="/market" className="px-btn px-btn-blue px-btn-big">
              ▶ 开始游玩
            </Link>
            <Link href="/create" className="px-btn px-btn-big">
              🛠 我要造班
            </Link>
          </div>
          <div className="text-[11px] text-[var(--blue)] mb-6">
            <span className="blink">●</span> 在家抠脚,好想实习!→ 当场上班
          </div>
        </div>
        <CitySkyline />
      </section>

      {/* ============ 大厂黑话跑马灯 ============ */}
      <div className="marquee-wrap" aria-hidden>
        <div className="marquee-inner">{BUZZWORDS.repeat(2)}{BUZZWORDS.repeat(2)}</div>
      </div>

      {/* ============ 四大板块 ============ */}
      <section className="max-w-5xl mx-auto px-4 py-12">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
          {SECTIONS.map((s) => (
            <Link key={s.href} href={s.href}>
              <div className="px-card px-card-hover p-5 h-full text-center flex flex-col gap-2">
                <div className="text-3xl">{s.icon}</div>
                <div className="text-base">{s.title}</div>
                <div className="text-[11px] leading-5 text-[var(--ink)]/70">{s.desc}</div>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ============ 怎么玩 ============ */}
      <section className="max-w-5xl mx-auto px-4 pb-14">
        <h2 className="px-h2 mb-6">▶ 三步上岗</h2>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5 text-xs leading-6">
          {[
            ["①", "领实习包", "去实习集市挑一个岗位,下载实习包"],
            ["②", "喊 AI 开机", "打开你的本地 AI(如 Claude Code):「加载实习包,开始上班!」"],
            ["③", "去飞书上班", "剧情全在你的飞书里发生,下班领实习日记"],
          ].map(([n, t, d]) => (
            <div key={t as string} className="px-card p-5">
              <div className="text-2xl mb-2 text-[var(--blue)]">{n}</div>
              <div className="text-sm mb-1">{t}</div>
              <div className="text-[var(--ink)]/70">{d}</div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
