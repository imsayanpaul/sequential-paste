/**
 * Three stacked strips of tape, the next one pulled out in highlighter yellow.
 * Same geometry as assets/icon.ico (tools/make_logo.py); colours follow the theme.
 */
export function Logo({ className = "h-[30px] w-[30px]" }: { className?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={`group/logo shrink-0 ${className}`} aria-hidden="true">
      <rect width="64" height="64" rx="15" className="fill-ink" />
      <rect x="15" y="40" width="34" height="8" rx="4" className="fill-paper" opacity=".32" />
      <rect x="15" y="28" width="34" height="8" rx="4" className="fill-paper" opacity=".62" />
      <rect
        x="21" y="15" width="34" height="9" rx="4.5"
        className="fill-marker transition-transform duration-300 ease-[cubic-bezier(.3,1.6,.5,1)] group-hover:-translate-x-1"
      />
    </svg>
  );
}

export function Wordmark() {
  return (
    <span className="whitespace-nowrap text-[17px] tracking-[-.02em]">
      <b className="font-extrabold">Sequential</b> <span className="font-medium">Paste</span>
    </span>
  );
}
