"use client";

import { useEffect, useRef, useState, useCallback } from "react";


const BUZZWORDS = "对齐 ▸ 抓手 ▸ 闭环 ▸ 颗粒度 ▸ 拉通 ▸ 赋能 ▸ 组合拳 ▸ 护城河 ▸ 双月OKR ▸ 向上管理 ▸ 降本增效 ▸ 底层逻辑 ▸ 用户心智 ▸ 价值沉淀 ▸ ";
const BASE_PATH = process.env.NEXT_PUBLIC_BASE_PATH || "";
const publicPath = (path: string) => `${BASE_PATH}${path}`;

/* ===== SVG Icons ===== */
function CloudSVG({ w = 120, h = 48 }: { w?: number; h?: number }) {
  return (
    <svg width={w} height={h} viewBox="0 0 30 12" shapeRendering="crispEdges">
      <rect x="4" y="4" width="22" height="6" fill="#fff" />
      <rect x="8" y="1" width="10" height="4" fill="#fff" />
      <rect x="2" y="6" width="26" height="4" fill="#fff" />
    </svg>
  );
}

function LockIcon() {
  return (
    <svg width="42" height="42" viewBox="0 0 32 32" aria-hidden="true">
      <path d="M9 14V9a7 7 0 0 1 14 0v5" fill="none" stroke="#fff" strokeWidth="3" strokeLinecap="square" />
      <rect x="6" y="13" width="20" height="14" fill="#fff" />
      <rect x="14" y="18" width="4" height="6" fill="#6b7280" />
    </svg>
  );
}

/* Quest icons (pixel SVG) */
const QUESTS = [
  {
    no: 1, name: "被 AI 派活", final: false,
    icon: (
      <svg width="36" height="36" viewBox="0 0 16 16" shapeRendering="crispEdges">
        <rect x="7" y="0" width="2" height="3" fill="#ff5d5d" /><rect x="6" y="2" width="1" height="1" fill="#ff5d5d" /><rect x="9" y="2" width="1" height="1" fill="#ff5d5d" />
        <rect x="2" y="5" width="12" height="9" fill="#0b2a6b" /><rect x="3" y="6" width="10" height="7" fill="#fff" />
        <rect x="4" y="7" width="1" height="1" fill="#0b2a6b" /><rect x="11" y="7" width="1" height="1" fill="#0b2a6b" />
        <rect x="5" y="8" width="1" height="1" fill="#0b2a6b" /><rect x="10" y="8" width="1" height="1" fill="#0b2a6b" />
        <rect x="6" y="9" width="1" height="1" fill="#0b2a6b" /><rect x="9" y="9" width="1" height="1" fill="#0b2a6b" />
        <rect x="7" y="10" width="2" height="1" fill="#0b2a6b" />
      </svg>
    ),
  },
  {
    no: 2, name: "建立日程", final: false,
    icon: (
      <svg width="36" height="36" viewBox="0 0 16 16" shapeRendering="crispEdges">
        <rect x="2" y="3" width="12" height="11" fill="#0b2a6b" /><rect x="3" y="4" width="10" height="3" fill="#2f6bff" />
        <rect x="5" y="1" width="1" height="3" fill="#0b2a6b" /><rect x="10" y="1" width="1" height="3" fill="#0b2a6b" />
        <rect x="3" y="7" width="10" height="6" fill="#fff" />
        <rect x="5" y="8" width="1" height="1" fill="#0b2a6b" /><rect x="7" y="8" width="1" height="1" fill="#0b2a6b" /><rect x="9" y="8" width="1" height="1" fill="#0b2a6b" />
        <rect x="5" y="10" width="1" height="1" fill="#0b2a6b" /><rect x="7" y="10" width="1" height="1" fill="#ffd23e" /><rect x="9" y="10" width="1" height="1" fill="#0b2a6b" />
      </svg>
    ),
  },
  {
    no: 3, name: "被拉进群", final: false,
    icon: (
      <svg width="36" height="36" viewBox="0 0 16 16" shapeRendering="crispEdges">
        <rect x="3" y="2" width="4" height="1" fill="#0b2a6b" /><rect x="3" y="3" width="4" height="3" fill="#ffe3c9" /><rect x="2" y="7" width="6" height="5" fill="#2f6bff" />
        <rect x="9" y="4" width="4" height="1" fill="#0b2a6b" /><rect x="9" y="5" width="4" height="3" fill="#ffe3c9" /><rect x="8" y="9" width="6" height="5" fill="#7cc4ff" />
      </svg>
    ),
  },
  {
    no: 4, name: "开会吵架", final: false,
    icon: (
      <svg width="36" height="36" viewBox="0 0 16 16" shapeRendering="crispEdges">
        <rect x="1" y="1" width="8" height="6" fill="#0b2a6b" /><rect x="2" y="2" width="6" height="4" fill="#fff" />
        <rect x="3" y="7" width="1" height="1" fill="#0b2a6b" />
        <rect x="3" y="3" width="1" height="2" fill="#2f6bff" /><rect x="5" y="3" width="1" height="2" fill="#2f6bff" />
        <rect x="7" y="8" width="8" height="6" fill="#0b2a6b" /><rect x="8" y="9" width="6" height="4" fill="#ff5d5d" />
        <rect x="12" y="14" width="1" height="1" fill="#0b2a6b" />
        <rect x="10" y="9" width="1" height="3" fill="#fff" /><rect x="10" y="12" width="1" height="1" fill="#fff" opacity=".6" />
      </svg>
    ),
  },
  {
    no: 5, name: "评审被怼", final: false,
    icon: (
      <svg width="36" height="36" viewBox="0 0 16 16" shapeRendering="crispEdges">
        <rect x="3" y="3" width="10" height="10" fill="#0b2a6b" /><rect x="4" y="4" width="8" height="8" fill="#ffd23e" />
        <rect x="5" y="6" width="2" height="2" fill="#0b2a6b" /><rect x="9" y="6" width="2" height="2" fill="#0b2a6b" />
        <rect x="6" y="10" width="4" height="1" fill="#0b2a6b" />
        <rect x="5" y="9" width="1" height="1" fill="#ff9d9d" /><rect x="10" y="9" width="1" height="1" fill="#ff9d9d" />
        <rect x="13" y="2" width="2" height="2" fill="#7cc4ff" /><rect x="13" y="4" width="1" height="1" fill="#7cc4ff" />
      </svg>
    ),
  },
  {
    no: 6, name: "摸鱼划水", final: false,
    icon: (
      <svg width="36" height="36" viewBox="0 0 16 16" shapeRendering="crispEdges">
        <rect x="3" y="6" width="8" height="5" fill="#0b2a6b" /><rect x="4" y="7" width="6" height="3" fill="#7cc4ff" />
        <rect x="11" y="5" width="2" height="2" fill="#0b2a6b" /><rect x="11" y="10" width="2" height="2" fill="#0b2a6b" /><rect x="12" y="7" width="1" height="3" fill="#0b2a6b" />
        <rect x="5" y="8" width="1" height="1" fill="#0b2a6b" />
        <rect x="13" y="2" width="1" height="1" fill="#7cc4ff" /><rect x="14" y="4" width="1" height="1" fill="#7cc4ff" />
        <rect x="1" y="12" width="14" height="1" fill="#7cc4ff" opacity=".5" />
      </svg>
    ),
  },
  {
    no: 7, name: "生成实习日记", final: true,
    icon: (
      <svg width="36" height="36" viewBox="0 0 16 16" shapeRendering="crispEdges">
        <rect x="3" y="2" width="10" height="12" fill="#0b2a6b" /><rect x="4" y="3" width="8" height="10" fill="#2f6bff" />
        <rect x="4" y="3" width="2" height="10" fill="#0b2a6b" />
        <rect x="7" y="5" width="4" height="4" fill="#fff" /><rect x="8" y="6" width="2" height="1" fill="#0b2a6b" /><rect x="8" y="8" width="2" height="1" fill="#0b2a6b" />
        <rect x="13" y="1" width="1" height="1" fill="#ffd23e" /><rect x="14" y="3" width="1" height="1" fill="#ffd23e" />
      </svg>
    ),
  },
];

/* Player avatars */
function Avatar01() {
  return (
    <svg className="avatar" viewBox="0 0 16 16" shapeRendering="crispEdges">
      <rect x="4" y="1" width="8" height="3" fill="#5a3b1e" /><rect x="4" y="3" width="8" height="4" fill="#ffe3c9" />
      <rect x="5" y="4" width="2" height="2" fill="#0b2a6b" /><rect x="9" y="4" width="2" height="2" fill="#0b2a6b" />
      <rect x="3" y="7" width="10" height="5" fill="#7cc4ff" /><rect x="7" y="8" width="2" height="2" fill="#fff" />
      <rect x="5" y="12" width="2" height="3" fill="#0b2a6b" /><rect x="9" y="12" width="2" height="3" fill="#0b2a6b" />
      <rect x="12" y="2" width="2" height="2" fill="#ffd23e" /><rect x="13" y="1" width="1" height="1" fill="#ffd23e" />
    </svg>
  );
}
function Avatar02() {
  return (
    <svg className="avatar" viewBox="0 0 16 16" shapeRendering="crispEdges">
      <rect x="4" y="1" width="8" height="3" fill="#0b2a6b" /><rect x="4" y="3" width="8" height="4" fill="#ffe3c9" />
      <rect x="5" y="4" width="2" height="1" fill="#0b2a6b" /><rect x="9" y="4" width="2" height="1" fill="#0b2a6b" />
      <rect x="5" y="5" width="2" height="1" fill="#ff5d5d" /><rect x="9" y="5" width="2" height="1" fill="#ff5d5d" />
      <rect x="3" y="7" width="10" height="5" fill="#2f6bff" /><rect x="6" y="8" width="4" height="2" fill="#0b2a6b" />
      <rect x="5" y="12" width="2" height="3" fill="#0b2a6b" /><rect x="9" y="12" width="2" height="3" fill="#0b2a6b" />
      <rect x="1" y="3" width="2" height="1" fill="#ff5d5d" /><rect x="13" y="6" width="2" height="1" fill="#ff5d5d" />
    </svg>
  );
}
function Avatar03() {
  return (
    <svg className="avatar" viewBox="0 0 16 16" shapeRendering="crispEdges">
      <rect x="4" y="1" width="8" height="3" fill="#8a5a2b" /><rect x="4" y="3" width="8" height="4" fill="#ffe3c9" />
      <rect x="4" y="4" width="3" height="2" fill="#0b2a6b" opacity=".9" /><rect x="9" y="4" width="3" height="2" fill="#0b2a6b" opacity=".9" /><rect x="7" y="4" width="2" height="1" fill="#0b2a6b" />
      <rect x="3" y="7" width="10" height="5" fill="#ffd23e" /><rect x="7" y="8" width="2" height="3" fill="#2f6bff" />
      <rect x="5" y="12" width="2" height="3" fill="#0b2a6b" /><rect x="9" y="12" width="2" height="3" fill="#0b2a6b" />
      <rect x="13" y="2" width="1" height="3" fill="#2f6bff" /><rect x="12" y="3" width="3" height="1" fill="#2f6bff" />
    </svg>
  );
}

const PLAYERS = [
  {
    name: "迷雾小白", role: "PLAYER 01 · 没进过互联网大厂的新手村玩家",
    avatar: <Avatar01 />,
    body: "对实习岗位一头雾水：「大厂实习到底怎么上班、群里怎么说话、会怎么开」完全没概念，好奇又没门路预体验。正经训练营/课程太重、太贵、太严肃，只想先轻松地感受一下。",
    say: "「在家抠脚，好想实习！」怎么办？", act: "打开一日实习生，当场上班。",
    tags: [{ text: "一头雾水", debuff: true }, { text: "没有门路", debuff: true }, { text: "课程太贵", debuff: true }],
  },
  {
    name: "上班上美了", role: "PLAYER 02 · 想让别人也体验一下的大厂打工人",
    avatar: <Avatar02 />,
    body: "想让别人也体验一下自己正在上什么班。制作自己的一日实习日记，将日常工作记录下来，沉淀成一个「实习包」——方便自己复盘，也把经验分享给别人。",
    say: "「实习结束了，我来复盘一下，顺便分享个人经验。」怎么办？", act: "打开一日实习生，开始创作（开始夹带私货）。",
    tags: [{ text: "精神状态美丽", debuff: true }, { text: "想分享", debuff: false }, { text: "想复盘", debuff: false }],
  },
  {
    name: "职场段子手", role: "PLAYER 03 · 传播职业内容的专业创作者",
    avatar: <Avatar03 />,
    body: "有一肚子职场段子和岗位经验，但把它变成一段「能让 AI 演出来」的体验，从零写剧本门槛极高——缺一个把创作变简单的工具。",
    say: "「大家关注一下我的一日实习生账号，以后持续给大家产出高质量的产品经理实习包！」", act: "打开一日实习生，涨粉恰饭两不误。",
    tags: [{ text: "满肚子素材", debuff: false }, { text: "剧本门槛高", debuff: true }, { text: "缺工具", debuff: true }],
  },
];



/** 像素城市天际线 */
function CitySkyline() {
  return (
    <svg viewBox="0 0 960 240" className="w-full block" shapeRendering="crispEdges" aria-hidden>
      <rect x="812" y="24" width="48" height="48" fill="var(--yellow)" stroke="var(--ink)" strokeWidth="4" />
      <g fill="var(--white)" stroke="var(--ink)" strokeWidth="3">
        <rect x="80" y="40" width="90" height="22" />
        <rect x="110" y="26" width="46" height="18" />
        <rect x="420" y="30" width="100" height="22" />
        <rect x="452" y="16" width="48" height="18" />
        <rect x="660" y="52" width="80" height="20" />
      </g>
      <g stroke="var(--ink)" strokeWidth="4">
        <rect x="60" y="90" width="120" height="150" fill="#bfe0ff" />
        <rect x="88" y="64" width="64" height="26" fill="#bfe0ff" />
        <rect x="116" y="40" width="8" height="24" fill="var(--ink)" stroke="none" />
        <rect x="230" y="120" width="70" height="120" fill="var(--sky)" />
        <rect x="316" y="104" width="70" height="136" fill="var(--sky)" />
        <rect x="300" y="150" width="16" height="14" fill="var(--ink)" stroke="none" />
        <rect x="440" y="140" width="150" height="100" fill="#bfe0ff" />
        <rect x="470" y="110" width="90" height="30" fill="#bfe0ff" />
        <rect x="640" y="84" width="90" height="156" fill="var(--blue)" />
        <rect x="770" y="130" width="130" height="110" fill="var(--sky)" />
      </g>
      <g fill="var(--yellow)">
        {[0,1,2,3].map(r => [0,1,2].map(c => (
          <rect key={`a${r}${c}`} x={78+c*32} y={104+r*32} width="14" height="14" />
        )))}
        {[0,1,2].map(r => <rect key={`b${r}`} x={658} y={100+r*40} width="14" height="14" />)}
        <rect x="700" y="140" width="14" height="14" />
        <rect x="700" y="220" width="14" height="14" fill="var(--white)" />
        {[0,1].map(r => [0,1,2].map(c => (
          <rect key={`c${r}${c}`} x={460+c*44} y={156+r*40} width="16" height="16" fill={(r+c)%2 ? "var(--yellow)" : "var(--white)"} />
        )))}
      </g>
      <g fontFamily="inherit" fill="var(--ink)" fontSize="13">
        <text x="70" y="82" fontSize="12">跳动大厂</text>
        <text x="782" y="124">厂里厂气</text>
      </g>
      <rect x="0" y="236" width="960" height="4" fill="var(--ink)" />
    </svg>
  );
}

export default function Home() {
  const [questsDone, setQuestsDone] = useState<Set<number>>(new Set());
  const [selectedPlayer, setSelectedPlayer] = useState<number | null>(null);
  const [toastMsg, setToastMsg] = useState("");
  const [toastShow, setToastShow] = useState(false);
  const toastTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const revealRefs = useRef<(HTMLElement | null)[]>([]);

  const showToast = useCallback((msg: string) => {
    setToastMsg(msg);
    setToastShow(true);
    if (toastTimer.current) clearTimeout(toastTimer.current);
    toastTimer.current = setTimeout(() => setToastShow(false), 2200);
  }, []);


  /* Reveal on scroll */
  useEffect(() => {
    const io = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          e.target.classList.add("on");
          io.unobserve(e.target);
        }
      });
    }, { threshold: 0.12 });
    revealRefs.current.forEach(el => { if (el) io.observe(el); });
    return () => io.disconnect();
  }, []);

  const toggleQuest = (idx: number, name: string) => {
    setQuestsDone(prev => {
      const next = new Set(prev);
      if (next.has(idx)) { next.delete(idx); } else { next.add(idx); }
      if (next.size === QUESTS.length) showToast("★ 一天通关！实习日记已生成（假装） ★");
      else if (next.has(idx)) showToast("✓ 打卡成功：" + name);
      return next;
    });
  };

  const selectPlayer = (idx: number, name: string) => {
    setSelectedPlayer(idx);
    showToast("▶ PLAYER SELECTED：" + name);
  };

  const addRevealRef = (el: HTMLElement | null) => {
    if (el && !revealRefs.current.includes(el)) revealRefs.current.push(el);
  };

  return (
    <div>
      {/* ============ HERO 头图（index.html像素风） ============ */}
      <section id="hero" className="concept-hero">
        <div className="hero-photo" style={{ backgroundImage: `url("${publicPath("/intern-hero.jpg")}")` }} aria-hidden />
        <div className="pixel-cloud" style={{ top:70, animationDuration:"34s" }}><CloudSVG w={120} h={48} /></div>
        <div className="pixel-cloud" style={{ top:160, animationDuration:"48s", animationDelay:"-20s" }}><CloudSVG w={90} h={36} /></div>
        <div className="pixel-cloud" style={{ top:110, animationDuration:"40s", animationDelay:"-33s" }}><CloudSVG w={150} h={60} /></div>

        <div className="px-badge-accent floaty">★ 游戏化实习模拟skill ★</div>
        <h1 className="text-5xl sm:text-7xl tracking-[6px] mb-1 font-black text-white" style={{ textShadow:"4px 4px 0 var(--sky),8px 8px 0 rgba(47,107,255,.3)" }}>
          一日实习生
        </h1>
      </section>

      {/* ============ 内容开始锚点 ============ */}
      <div id="content-start" />

      {/* ============ 大厂黑话跑马灯 ============ */}
      <div className="marquee-wrap" aria-hidden>
        <div className="marquee-inner">{BUZZWORDS.repeat(2)}{BUZZWORDS.repeat(2)}</div>
      </div>

      {/* ============ Skill 实习包下载 ============ */}
      <section className="max-w-5xl mx-auto px-4 py-10">
        <div className="stage-head">
          <span className="stage-tag">SKILL PACK</span>
          <h2>Skill实习包点击下载</h2>
          <div className="stage-line" />
        </div>
        <div className="skill-pack-grid">
          <article className="px-card px-card-hover skill-pack-card">
            <h3>产品经理</h3>
            <p className="text-xs leading-5 text-[var(--ink)]/70">人人都搞产品经理</p>
            <a href={publicPath("/one-day-intern-player-v1.0.0.zip")} download className="px-btn px-btn-blue !text-xs text-center">⬇️ 点击下载</a>
          </article>
          <article className="px-card px-card-hover skill-pack-card skill-card-locked" aria-disabled="true">
            <h3>产品运营</h3>
            <p className="text-xs leading-5 text-[var(--ink)]/70">人人都搞产品运营</p>
            <button type="button" disabled className="px-btn !text-xs cursor-not-allowed">已锁定</button>
            <div className="skill-lock-overlay"><LockIcon /></div>
          </article>
          <article className="px-card px-card-hover skill-pack-card skill-card-locked" aria-disabled="true">
            <h3>体验设计</h3>
            <p className="text-xs leading-5 text-[var(--ink)]/70">人人都搞体验设计</p>
            <button type="button" disabled className="px-btn !text-xs cursor-not-allowed">已锁定</button>
            <div className="skill-lock-overlay"><LockIcon /></div>
          </article>
        </div>
        <div id="start" className="skill-quick-start">
          <div className="skill-quick-heading">
            <span className="skill-quick-arrow" aria-hidden="true">▶</span>
            <h3 className="skill-quick-title">三步开工</h3>
            <div className="skill-quick-divider" aria-hidden="true" />
          </div>
          <div className="skill-step-grid">
            {[
              ["①", "下载体验包", "拿到 zip，解压成独立文件夹。"],
              ["②", "打开文件夹", "用 Codex 打开项目目录。"],
              ["③", "一句话开玩", "说“开始实习”，让 AI 在飞书里拉你上班。"],
            ].map(([number, title, detail]) => (
              <div key={title} className="skill-step">
                <span className="skill-step-number">{number}</span>
                <span className="skill-step-copy"><span className="skill-step-title">{title}</span><span className="skill-step-detail">{detail}</span></span>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section className="max-w-5xl mx-auto px-4 pb-8">
        <div className="skill-config-card">
          <h3 className="skill-config-title">需要配置：</h3>
          <div className="skill-config-list">
            <div className="skill-config-item"><span>飞书 CLI</span><a className="skill-config-link" href="https://www.feishu.cn/feishu-cli" target="_blank" rel="noreferrer">点击跳转官网配置 ↗</a></div>
            <div className="skill-config-item"><span>飞书个人账号授权</span></div>
          </div>
        </div>
      </section>

      {/* ============ 产品概念讲解区 ============ */}

      {/* --- Concept Main --- */}
      <main className="concept-main">

        {/* STAGE 1 概念介绍 */}
        <section id="stage1" className="concept-section">
          <div className="stage-head reveal" ref={addRevealRef}>
            <span className="stage-tag">STAGE 1</span>
            <h2>创意名称 + 创意介绍</h2>
            <div className="stage-line" />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-[1.4fr_1fr] gap-5">
            <div className="px-card-deep reveal" ref={addRevealRef}>
              <div className="inner">
                <h3>这是个什么游戏？</h3>
                <p>一个<span className="text-hl">基于飞书和本地 Agent 的游戏化实习模拟器开源网站平台</span>。用户下载一个「一日实习包」副本，接上自己本地的 AI Agent，接入个人飞书，就可以沉浸式地在一家虚构公司上一天班。</p>
                <p>下班时自动生成一份可截图分享的搞笑<span className="text-hl">「实习日记」</span>。记录、创作、体验、复盘，全程由 AI 驱动。</p>
                <div className="formula-row">
                  <span className="formula-f">本地 Agent</span><span className="formula-plus">＋</span>
                  <span className="formula-f">飞书开放平台</span><span className="formula-plus">＋</span>
                  <span className="formula-f">在线平台</span><span className="formula-eq">＝</span>
                  <span className="formula-result">人人可玩、可造的实习模拟器</span>
                </div>
              </div>
            </div>

            <div className="px-card-deep reveal" ref={addRevealRef}>
              <div className="inner">
                <h3>产品出发点</h3>
                <p>实习本来就是一种<span className="text-hl">探索不同工作体验</span>的方式，而实习的要求却越来越高，垂直经验显得格外重要——这似乎打破了实习的初衷。</p>
                <p><span className="text-hl">为什么不可以随意到处实习呢？</span></p>
                <p>秉承开源精神，开源实习模拟器诞生了。它与普通职业模拟器的区别：用户可基于飞书开放接口<span className="text-hl">创建自己的「一日实习浓缩包」</span>并上传平台，也可以下载体验别人的实习包，水灵灵地体验多个岗位。多种岗位，多种风格，自由开放的生态平台。</p>
              </div>
            </div>
          </div>

          {/* 一天任务链 */}
          <div className="reveal mt-6" ref={addRevealRef}>
            <div className="stage-head" style={{ marginBottom:14 }}>
              <span className="stage-tag" style={{ background:"var(--blue)" }}>SIDE QUEST</span>
              <h2 style={{ fontSize:18 }}>你的一天 · 任务链（点击打卡）</h2>
              <div className="stage-line" />
            </div>
            <div className="quest-grid">
              {QUESTS.map((q, i) => (
                <div key={q.no}
                     className={`quest-item ${questsDone.has(i) ? "done" : ""} ${q.final ? "final" : ""}`}
                     onClick={() => toggleQuest(i, q.name)}>
                  <span className="qno">{q.no}</span>
                  <span className="qicon">{q.icon}</span>
                  <span className="qname">{q.name}</span>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* STAGE 2 目标用户 */}
        <section id="stage2" className="concept-section">
          <div className="stage-head reveal" ref={addRevealRef}>
            <span className="stage-tag">STAGE 2</span>
            <h2>目标用户及痛点 · SELECT PLAYER</h2>
            <div className="stage-line" />
          </div>

          <div className="player-grid">
            {PLAYERS.map((p, i) => (
              <div key={p.name}
                   className={`player-card reveal ${selectedPlayer === i ? "selected" : ""}`}
                   ref={addRevealRef}
                   onClick={() => selectPlayer(i, p.name)}>
                {p.avatar}
                <h3>{p.name}</h3>
                <div className="role">{p.role}</div>
                <p>{p.body}</p>
                <div className="player-quote">
                  <span className="say">{p.say}</span>
                  <span className="act">{p.act}</span>
                </div>
                <div className="debuff-row">
                  {p.tags.map(t => (
                    <span key={t.text} className={t.debuff ? "debuff-tag" : "buff-tag"}>{t.text}</span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* FINAL 总结 */}
        <section className="concept-section">
          <div className="stage-head reveal" ref={addRevealRef}>
            <span className="stage-tag">FINAL</span>
            <h2>总结一句话</h2>
            <div className="stage-line" />
          </div>
          <div className="final-banner reveal" ref={addRevealRef}>
            <div className="small">— MISSION STATEMENT —</div>
            <p>本地 Agent <span className="hl2">＋</span> 飞书开放平台 <span className="hl2">＋</span> 在线平台，<br/>
              第一次做成一个<span className="hl2">人人可玩、可造</span>的消费级娱乐实习模拟器。</p>
          </div>
        </section>

        {/* CTA：看完概念后引导开始 */}
        <section className="cta-after-concept reveal" ref={addRevealRef}>
          <h2 className="px-h2 mb-6">▶ READY PLAYER ONE</h2>
          <p className="text-sm leading-7 max-w-xl mx-auto text-[var(--ink)]/80 mb-8">
            看完介绍了？准备好开始你的第一份（虚构的）工作了吗？<br/>
            先下载实习包，然后花 5 分钟配置环境——上班！
          </p>
        </section>

      </main>
      {/* ============ Footer ============ */}
      <footer className="border-t-4 border-[var(--ink)] text-center py-5 text-[13px] tracking-[1px]"
              style={{ background:"var(--ink)", color:"var(--sky)" }}>
        © 2026 一日实习生 ONE-DAY INTERN · 开源实习模拟器 · MADE WITH{" "}
        <span className="text-[var(--red)]" style={{ animation:"blink 1s steps(2) infinite" }}>♥</span>{" "}
        AND PIXELS
      </footer>

      {/* Toast */}
      <div className={`pixel-toast ${toastShow ? "show" : ""}`}>{toastMsg}</div>
    </div>
  );
}
