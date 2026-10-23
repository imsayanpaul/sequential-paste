export const REPO = "imsayanpaul/sequential-paste";
export const REPO_URL = `https://github.com/${REPO}`;
export const VERSION = "1.0.0";

export const DOWNLOADS = {
  installer: {
    url: `${REPO_URL}/raw/main/installer/SequentialPaste_Setup_v${VERSION}.exe`,
    file: `SequentialPaste_Setup_v${VERSION}.exe`,
    size: "34.4 MB",
  },
  portable: {
    url: `${REPO_URL}/raw/main/dist/SequentialPaste.exe`,
    file: "SequentialPaste.exe",
    size: "32.7 MB",
  },
};

export const NAV_LINKS = [
  { href: "#try", label: "Try it" },
  { href: "#modes", label: "Split modes" },
  { href: "#features", label: "Features" },
  { href: "#app", label: "The app" },
  { href: "#faq", label: "FAQ" },
];

/** Star count, refreshed at most once an hour (no token, so keep it rare) */
export async function getStars(): Promise<number | null> {
  try {
    const res = await fetch(`https://api.github.com/repos/${REPO}`, {
      headers: { Accept: "application/vnd.github+json" },
      next: { revalidate: 3600 },
    });
    if (!res.ok) return null;
    const data = (await res.json()) as { stargazers_count?: unknown };
    return typeof data.stargazers_count === "number" ? data.stargazers_count : null;
  } catch {
    return null;
  }
}

export function formatCount(n: number): string {
  if (n < 1000) return String(n);
  return `${(n / 1000).toFixed(n >= 10000 ? 0 : 1)}k`;
}
