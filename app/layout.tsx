import type { Metadata } from "next";
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
      <body className="min-h-full flex flex-col">{children}</body>
    </html>
  );
}
