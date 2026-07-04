import { createClient } from "@supabase/supabase-js";

const url = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

export const supabase = createClient(url, anonKey);

export const BUCKET = "intern-packs";

export type InternPack = {
  id: string;
  name: string;
  tagline: string;
  role: string;
  company: string;
  author: string;
  version: string;
  difficulty: string;
  tags: string[];
  stats: { events?: number; choices?: number; npcs?: number };
  requires: { domains?: string[]; optional?: string[] };
  downloads: number;
  storage_path: string | null;
  created_at: string;
};

export function packZipUrl(pack: InternPack): string | null {
  if (!pack.storage_path) return null;
  return `${url}/storage/v1/object/public/${BUCKET}/${pack.storage_path}`;
}

export type Run = {
  id: string;
  pack_id: string;
  player_alias: string;
  mode: string;
  status: "running" | "done" | "aborted";
  current_beat: string | null;
  stats: Record<string, number>;
  diary_url: string | null;
  started_at: string;
  updated_at: string;
};

export type RunEvent = {
  id: number;
  run_id: string;
  t: string;
  kind: string;
  title: string;
  detail: string;
};
