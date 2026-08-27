"use client";

import { useEffect, useState } from "react";
import { isCollected, toggleCollect } from "@/lib/collection";

export default function CollectButton({
  packId,
  size = "normal",
  onChange,
}: {
  packId: string;
  size?: "normal" | "small";
  onChange?: (on: boolean) => void;
}) {
  const [on, setOn] = useState(false);
  useEffect(() => setOn(isCollected(packId)), [packId]);

  function handle(e: React.MouseEvent) {
    e.preventDefault();
    e.stopPropagation();
    const next = toggleCollect(packId);
    setOn(next);
    onChange?.(next);
  }

  if (size === "small") {
    return (
      <button
        onClick={handle}
        title={on ? "移出我的实习" : "加入我的实习"}
        className="px-tag !cursor-pointer"
        style={{ background: on ? "var(--red)" : "var(--white)", color: on ? "var(--white)" : "var(--ink)" }}
      >
        {on ? "♥" : "♡"}
      </button>
    );
  }
  return (
    <button onClick={handle} className="px-btn !text-sm" style={{ background: on ? "var(--red)" : "var(--yellow)", color: on ? "var(--white)" : "var(--ink)" }}>
      {on ? "♥ 已在我的实习" : "♡ 加入我的实习"}
    </button>
  );
}
