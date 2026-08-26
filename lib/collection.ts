// 「我的实习」收藏库 —— MVP 用 localStorage,后续接账号体系时替换为服务端
const KEY = "odi_collection";

export function getCollection(): string[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(KEY) ?? "[]");
  } catch {
    return [];
  }
}

export function isCollected(packId: string): boolean {
  return getCollection().includes(packId);
}

export function toggleCollect(packId: string): boolean {
  const list = getCollection();
  const idx = list.indexOf(packId);
  if (idx >= 0) list.splice(idx, 1);
  else list.push(packId);
  localStorage.setItem(KEY, JSON.stringify(list));
  return idx < 0;
}
