// Generates a deterministic colored avatar with the customer's initials.
const PALETTE = [
  '#e60028', '#f97316', '#eab308', '#22c55e', '#3b82f6',
  '#8b5cf6', '#ec4899', '#14b8a6', '#f59e0b', '#06b6d4',
];

function hashStr(s: string): number {
  let h = 0;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) | 0;
  return Math.abs(h);
}

function initials(name: string): string {
  if (!name) return '··';
  const parts = name.trim().split(/\s+/).filter(Boolean);
  if (parts.length === 0) return '··';
  if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
  return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
}

export function CustomerAvatar({ name, id, size = 44 }: { name: string; id: string; size?: number }) {
  const seed = hashStr(id || name);
  const color = PALETTE[seed % PALETTE.length];
  const text = initials(name);
  return (
    <div
      style={{
        width: size,
        height: size,
        background: `linear-gradient(135deg, ${color} 0%, ${color}cc 100%)`,
        fontSize: Math.round(size * 0.36),
      }}
      className="rounded-lg flex items-center justify-center text-white font-semibold shrink-0 shadow-md"
      aria-hidden
    >
      {text}
    </div>
  );
}
