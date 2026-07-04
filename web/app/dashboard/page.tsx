"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { supabase, type Run } from "@/lib/supabase";

const STATUS: Record<string, { label: string; color: string }> = {
  running: { label: "● 上班中", color: "var(--green)" },
  done: { label: "■ 已下班", color: "var(--blue)" },
  aborted: { label: "✕ 提前跑路", color: "var(--red)" },
};

export default function DashboardPage() {
  const [runs, setRuns] = useState<Run[] | null>(null);

  async function load() {
    const { data } = await supabase
      .from("runs")
      .select("*")
      .order("updated_at", { ascending: false })
      .limit(30)
      .returns<Run[]>();
    setRuns(data ?? []);
  }

  // 看板每 10s 轮询;有人在上班时保持直播感
  useEffect(() => {
    load();
    const t = setInterval(load, 10000);
    return () => clearInterval(t);
  }, []);

  const total = runs?.length ?? 0;
  const running = runs?.filter((r) => r.status === "running").length ?? 0;
  const done = runs?.filter((r) => r.status === "done").length ?? 0;
  const totalFights = runs?.reduce((s, r) => s + (r.stats?.["吵架次数"] ?? 0), 0) ?? 0;

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="px-h2">📺 实习看板</h1>
      <p className="text-xs text-[var(--ink)]/70 mt-3 mb-8">
        全平台的上班实况。数据由玩家本地引擎自愿上报,点击任意一场进入直播间。
      </p>

      {/* 总览仪表 */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-10">
        {[
          ["总实习场次", total, "var(--ink)"],
          ["正在上班", running, "var(--green)"],
          ["顺利下班", done, "var(--blue)"],
          ["累计职场吵架", totalFights, "var(--red)"],
        ].map(([label, val, color]) => (
          <div key={label as string} className="px-card p-4 text-center">
            <div className="text-2xl mb-1" style={{ color: color as string }}>{val}</div>
            <div className="text-[11px] text-[var(--ink)]/70">{label}</div>
          </div>
        ))}
      </div>

      <h2 className="px-h2 !text-sm mb-5">▶ 实况列表</h2>
      {runs === null ? (
        <div className="px-card p-6 text-sm">打卡机启动中…</div>
      ) : runs.length === 0 ? (
        <div className="px-card p-8 text-center text-sm">
          还没有人来上班。<Link href="/market" className="text-[var(--blue)] underline">去领一份实习?</Link>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          {runs.map((r) => {
            const st = STATUS[r.status] ?? STATUS.running;
            return (
              <Link key={r.id} href={`/runs/${r.id}`}>
                <div className="px-card px-card-hover p-4 flex items-center justify-between gap-3 flex-wrap text-xs">
                  <div className="flex items-center gap-3">
                    <span style={{ color: st.color }} className={r.status === "running" ? "blink" : ""}>
                      {st.label}
                    </span>
                    <span className="text-sm">{r.player_alias}</span>
                    <span className="text-[var(--blue)]">@ {r.pack_id}</span>
                  </div>
                  <div className="flex items-center gap-3 text-[11px] text-[var(--ink)]/70">
                    <span>进度 {r.current_beat ?? "开场"}</span>
                    {Object.entries(r.stats ?? {}).slice(0, 3).map(([k, v]) => (
                      <span key={k} className="px-tag !text-[10px]">{k} {v}</span>
                    ))}
                    <span>{new Date(r.updated_at).toLocaleString("zh-CN", { month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit" })}</span>
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
