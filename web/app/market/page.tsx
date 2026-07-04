"use client";

import { useEffect, useMemo, useState } from "react";
import { supabase, type InternPack } from "@/lib/supabase";
import PackCard from "@/components/PackCard";

// 部门筛选:按 role/tags 关键词匹配(MVP 客户端过滤,包多了再上服务端)
const DEPARTMENTS = [
  { key: "全部", match: [] },
  { key: "产品部", match: ["产品", "PM"] },
  { key: "技术部", match: ["程序", "开发", "工程", "技术"] },
  { key: "设计部", match: ["设计", "UI", "UX", "交互"] },
  { key: "运营部", match: ["运营", "市场", "营销", "增长"] },
  { key: "人事部", match: ["HR", "人事", "行政"] },
] as const;

export default function MarketPage() {
  const [packs, setPacks] = useState<InternPack[] | null>(null);
  const [dept, setDept] = useState("全部");
  const [q, setQ] = useState("");

  useEffect(() => {
    supabase
      .from("intern_packs")
      .select("*")
      .order("downloads", { ascending: false })
      .returns<InternPack[]>()
      .then(({ data }) => setPacks(data ?? []));
  }, []);

  const filtered = useMemo(() => {
    if (!packs) return [];
    const d = DEPARTMENTS.find((x) => x.key === dept);
    return packs.filter((p) => {
      const hay = `${p.name} ${p.role} ${p.tagline} ${p.company} ${(p.tags ?? []).join(" ")}`;
      const deptOk = !d || d.match.length === 0 || d.match.some((m) => hay.includes(m));
      const qOk = !q || hay.toLowerCase().includes(q.toLowerCase());
      return deptOk && qOk;
    });
  }, [packs, dept, q]);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <div className="flex items-end justify-between flex-wrap gap-3 mb-6">
        <div>
          <h1 className="px-h2">🏬 实习集市</h1>
          <p className="text-xs text-[var(--ink)]/70 mt-3">
            全网的班都在货架上,总有一款适合你上。
          </p>
        </div>
        <input
          className="px-input !w-56 !text-xs"
          placeholder="🔍 搜岗位 / 公司 / 标签…"
          value={q}
          onChange={(e) => setQ(e.target.value)}
        />
      </div>

      {/* 部门筛选 */}
      <div className="flex flex-wrap gap-2 mb-8">
        {DEPARTMENTS.map((d) => (
          <button
            key={d.key}
            className={`px-chip ${dept === d.key ? "active" : ""}`}
            onClick={() => setDept(d.key)}
          >
            {d.key}
          </button>
        ))}
      </div>

      {packs === null ? (
        <div className="px-card p-6 text-sm">货架整理中…</div>
      ) : filtered.length === 0 ? (
        <div className="px-card p-6 text-sm">
          这个部门还没有实习包。
          {dept !== "全部" && "换个部门看看,或者——"}
          <a href="/create" className="text-[var(--blue)] underline">自己造一个?</a>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
          {filtered.map((pack) => (
            <PackCard key={pack.id} pack={pack} />
          ))}
        </div>
      )}
    </div>
  );
}
