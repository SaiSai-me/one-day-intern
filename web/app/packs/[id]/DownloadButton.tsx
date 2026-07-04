"use client";

import { useState } from "react";
import { supabase, packZipUrl, type InternPack } from "@/lib/supabase";

export default function DownloadButton({ pack }: { pack: InternPack }) {
  const [count, setCount] = useState(pack.downloads);
  const zipUrl = packZipUrl(pack);

  if (!zipUrl) {
    return <div className="px-btn opacity-50 cursor-not-allowed">暂无下载文件</div>;
  }

  async function handleDownload() {
    setCount((c) => c + 1);
    try {
      // 等计数落库再跳转,否则请求会被页面跳转取消;失败也不阻塞下载
      await supabase.rpc("increment_pack_downloads", { pack_id: pack.id });
    } catch {
      /* 计数失败不影响下载 */
    }
    window.location.href = zipUrl!;
  }

  return (
    <button onClick={handleDownload} className="px-btn px-btn-blue text-base w-full sm:w-auto">
      ⬇ 下载实习包(已被下载 {count} 次)
    </button>
  );
}
