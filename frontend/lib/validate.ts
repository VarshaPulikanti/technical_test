export function isYouTubeUrl(url: string): boolean {
  const u = url.toLowerCase();
  return u.includes("youtube.com/") || u.includes("youtu.be/");
}

export function isInstagramReelUrl(url: string): boolean {
  const u = url.toLowerCase();
  return u.includes("instagram.com/reel") || u.includes("instagram.com/reels") || u.includes("instagram.com/p/");
}
