"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { supabase, type InternPack } from "@/lib/supabase";
import { getCollection } from "@/lib/collection";
import PackCard from "@/components/PackCard";

export default function MyPage() {
  const [packs, setPacks] = useState<InternPack[] | null>(null);

  useEffect(() => {
    const ids = getCollection();
    if (ids.length === 0) {
      setPacks([]);
      return;
    }
    supabase
      .from("intern_packs")
      .select("*")
      .in("id", ids)
      .returns<InternPack[]>()
      .then(({ data }) => setPacks(data ?? []));
  }, []);

  return (
    <div className="max-w-5xl mx-auto px-4 py-8">
      <h1 className="px-h2">🎒 我的实习</h1>
      <p className="text-xs text-[var(--ink)]/70 mt-3 mb-8">
        你的工牌收藏夹。收藏在本机保存,登录体系上线后自动同步。
      </p>

      {packs === null ? (
        <div className="px-card p-6 text-sm">翻工牌中…</div>
      ) : packs.length === 0 ? (
        <div className="px-card p-8 text-center">
          <div className="text-3xl mb-3">🪪</div>
          <div className="text-sm mb-2">工牌夹还是空的</div>
          <p className="text-xs text-[var(--ink)]/70 mb-5">
            去集市逛逛,点卡片右上角的 ♡ 收藏你想上的班
          </p>
          <Link href="/market" className="px-btn px-btn-blue !text-sm">
            🏬 去实习集市
          </Link>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6 mb-10">
            {packs.map((pack) => (
              <PackCard key={pack.id} pack={pack} />
            ))}
          </div>
          <div className="px-card p-5 text-xs leading-6">
            <span className="px-badge-yellow !text-[11px] mr-2">怎么开工?</span>
            下载实习包后,打开你的本地 AI(如 Claude Code)说:「加载 &lt;包名&gt;,开始上班!」——剧情将在你的飞书里展开。
          </div>
        </>
      )}
    </div>
  );
}
