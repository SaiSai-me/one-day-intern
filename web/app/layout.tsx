import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "一日实习生 One-Day Intern",
  description: "下载实习包,接上你的本地 AI Agent 和飞书,沉浸式上一天班。",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full">
      <body className="min-h-full flex flex-col">
        <header className="border-b-4 border-[var(--ink)] bg-[var(--white)]">
          <div className="max-w-5xl mx-auto px-4 py-4 flex items-center justify-between flex-wrap gap-3">
            <Link href="/" className="text-xl font-bold tracking-wide">
              ■ 一日实习生{" "}
              <span className="text-[var(--blue)]">One-Day Intern</span>
            </Link>
            <nav className="flex gap-4 text-sm items-center">
              <Link href="/" className="hover:text-[var(--blue)]">
                实习包市场
              </Link>
              <Link href="/upload" className="px-btn px-btn-blue !py-1 !px-3 !text-sm">
                + 上传实习包
              </Link>
            </nav>
          </div>
        </header>
        <main className="flex-1 max-w-5xl mx-auto w-full px-4 py-8">
          {children}
        </main>
        <footer className="border-t-4 border-[var(--ink)] bg-[var(--white)] py-4 text-center text-xs text-[var(--blue)]">
          ■ 人人可玩、可造的消费级娱乐实习模拟器 · 本地 Agent + 飞书开放平台 + 开源生态 ■
        </footer>
      </body>
    </html>
  );
}
