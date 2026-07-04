import Link from "next/link";
import type { InternPack } from "@/lib/supabase";
import CollectButton from "./CollectButton";

export default function PackCard({ pack }: { pack: InternPack }) {
  return (
    <Link href={`/packs/${pack.id}`}>
      <article className="px-card px-card-hover p-5 h-full flex flex-col gap-3">
        <header className="flex items-start justify-between gap-2">
          <h3 className="text-lg leading-snug">{pack.name}</h3>
          <span className="flex gap-1 shrink-0 items-start">
            <span className="px-tag !bg-[var(--yellow)]">⬇ {pack.downloads}</span>
            <CollectButton packId={pack.id} size="small" />
          </span>
        </header>
        <p className="text-xs leading-6 text-[var(--ink)]/75 flex-1">{pack.tagline}</p>
        <div className="flex flex-wrap gap-2">
          {pack.tags?.map((t) => (
            <span key={t} className="px-tag">{t}</span>
          ))}
        </div>
        <footer className="text-[11px] text-[var(--blue)] flex justify-between pt-1 border-t-2 border-dashed border-[var(--sky)]">
          <span>🏢 {pack.company}</span>
          <span>by {pack.author}</span>
        </footer>
      </article>
    </Link>
  );
}
