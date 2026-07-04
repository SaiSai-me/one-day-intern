"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { supabase, BUCKET } from "@/lib/supabase";

const KEBAB = /^[a-z0-9]+(-[a-z0-9]+)*$/;

export default function UploadPage() {
  const router = useRouter();
  const [form, setForm] = useState({
    id: "",
    name: "",
    tagline: "",
    role: "",
    company: "",
    author: "",
    difficulty: "轻松搞笑",
    tags: "",
  });
  const [file, setFile] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const [msg, setMsg] = useState<{ ok: boolean; text: string } | null>(null);

  function set(k: keyof typeof form, v: string) {
    setForm((f) => ({ ...f, [k]: v }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setMsg(null);

    if (!KEBAB.test(form.id)) {
      setMsg({ ok: false, text: "包 ID 必须是 kebab-case(如 pm-one-day)" });
      return;
    }
    if (!file || !file.name.endsWith(".zip")) {
      setMsg({ ok: false, text: "请选择实习包 zip 文件" });
      return;
    }

    setBusy(true);
    try {
      const storagePath = `${form.id}-${Date.now()}.zip`;
      const { error: upErr } = await supabase.storage
        .from(BUCKET)
        .upload(storagePath, file, { contentType: "application/zip" });
      if (upErr) throw new Error(`上传失败:${upErr.message}`);

      const { error: dbErr } = await supabase.from("intern_packs").insert({
        id: form.id,
        name: form.name,
        tagline: form.tagline,
        role: form.role,
        company: form.company,
        author: form.author || "匿名创作者",
        difficulty: form.difficulty,
        tags: form.tags.split(/[,,\s]+/).filter(Boolean),
        storage_path: storagePath,
      });
      if (dbErr) throw new Error(`保存失败:${dbErr.message}(包 ID 是否已存在?)`);

      setMsg({ ok: true, text: "上传成功!正在跳转…" });
      setTimeout(() => router.push(`/packs/${form.id}`), 800);
    } catch (err) {
      setMsg({ ok: false, text: err instanceof Error ? err.message : String(err) });
    } finally {
      setBusy(false);
    }
  }

  const fields: Array<[keyof typeof form, string, string, boolean]> = [
    ["id", "包 ID(kebab-case)", "pm-one-day", true],
    ["name", "实习包名称", "产品经理·一日实习", true],
    ["tagline", "一句话简介", "在跳动大厂当一天 PM,活着下班就算赢", false],
    ["role", "岗位", "产品经理实习生", true],
    ["company", "虚构公司", "跳动大厂", true],
    ["author", "作者", "你的创作者昵称", false],
    ["tags", "标签(逗号分隔)", "产品经理, 大厂, 搞笑", false],
  ];

  return (
    <div className="max-w-2xl mx-auto">
      <h1 className="px-h2 mb-3">▶ 上传实习包</h1>
      <p className="text-xs leading-6 mb-6 text-[var(--ink)]/75">
        把你的实习体验做成实习包分享给全世界。包格式见项目文档
        <code className="bg-[var(--white)] px-1">docs/pack-spec.md</code>
        ,或直接让你的 AI Agent 用「创作模式」帮你生成。
      </p>

      <form onSubmit={handleSubmit} className="px-card p-6 flex flex-col gap-4">
        {fields.map(([key, label, placeholder, required]) => (
          <label key={key} className="text-xs">
            <span className="block mb-1">
              {label}
              {required && <span className="text-[var(--red)]"> *</span>}
            </span>
            <input
              className="px-input"
              value={form[key]}
              placeholder={placeholder}
              required={required}
              onChange={(e) => set(key, e.target.value)}
            />
          </label>
        ))}

        <label className="text-xs">
          <span className="block mb-1">
            实习包文件(.zip)<span className="text-[var(--red)]"> *</span>
          </span>
          <input
            type="file"
            accept=".zip"
            required
            className="px-input !p-2"
            onChange={(e) => setFile(e.target.files?.[0] ?? null)}
          />
        </label>

        {msg && (
          <div
            className={`text-xs border-2 p-3 ${
              msg.ok
                ? "border-[var(--green)] text-[var(--green)]"
                : "border-[var(--red)] text-[var(--red)]"
            }`}
          >
            {msg.text}
          </div>
        )}

        <button type="submit" disabled={busy} className="px-btn px-btn-blue disabled:opacity-50">
          {busy ? "上传中…" : "🚀 发布实习包"}
        </button>
      </form>
    </div>
  );
}
