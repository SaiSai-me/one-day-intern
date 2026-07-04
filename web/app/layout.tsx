import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "一日实习生 One-Day Intern",
  description: "下载实习包,接上你的本地 AI Agent 和飞书,沉浸式上一天班。",
};

const NAV = [
  { href: "/market", label: "实习集市" },
  { href: "/my", label: "我的实习" },
  { href: "/dashboard", label: "实习看板" },
] as const;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN" className="h-full">
      <body className="min-h-full flex flex-col">
        <header className="border-b-4 border-[var(--ink)] bg-[var(--white)] sticky top-0 z-50">
          <div className="max-w-5xl mx-auto px-4 py-3 flex items-center justify-between flex-wrap gap-3">
            <Link href="/" className="text-lg font-bold tracking-wide">
              ■ 一日实习生{" "}
              <span className="text-[var(--blue)] hidden sm:inline">One-Day Intern</span>
            </Link>
            <nav className="flex gap-4 text-sm items-center">
              {NAV.map((n) => (
                <Link key={n.href} href={n.href} className="hover:text-[var(--blue)]">
                  {n.label}
                </Link>
              ))}
              <Link href="/create" className="px-btn px-btn-blue !py-1 !px-3 !text-sm">
                + 创建实习包
              </Link>
            </nav>
          </div>
        </header>
        <main className="flex-1 w-full">{children}</main>
        <footer className="border-t-4 border-[var(--ink)] bg-[var(--white)] py-4 text-center text-xs text-[var(--blue)]">
          ■ 人人可玩、可造的消费级娱乐实习模拟器 · 本地 Agent + 飞书开放平台 + 开源生态 ■
        </footer>
      </body>
    </html>
  );
}
