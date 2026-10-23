"use client";

import { AnimatePresence, motion, useMotionValueEvent, useScroll, useSpring } from "framer-motion";
import { useEffect, useState } from "react";
import { DOWNLOADS, NAV_LINKS, REPO_URL, VERSION, formatCount } from "@/lib/site";
import { GitHubIcon, MenuIcon, StarIcon } from "./Icons";
import { Logo, Wordmark } from "./Logo";

function StarButton({ stars, compact = false }: { stars: number | null; compact?: boolean }) {
  return (
    <a
      href={REPO_URL}
      target="_blank"
      rel="noopener"
      aria-label="Star Sequential Paste on GitHub"
      className="group/star inline-flex items-stretch overflow-hidden rounded-[10px] border border-line-2 bg-card text-[14px] font-semibold transition-colors hover:border-ink-3"
    >
      <span className="inline-flex items-center gap-1.5 px-2.5 py-[7px]">
        <GitHubIcon />
        <StarIcon className="h-[15px] w-[15px] fill-transparent stroke-current transition-all duration-300 ease-[cubic-bezier(.3,1.6,.5,1)] group-hover/star:rotate-[72deg] group-hover/star:scale-110 group-hover/star:fill-marker group-hover/star:stroke-marker-ink" />
        {!compact && <span>Star</span>}
      </span>
      {stars !== null && (
        <span className="inline-flex items-center border-l border-line-2 bg-paper px-2.5 font-mono text-[12.5px] font-semibold tabular-nums">
          {formatCount(stars)}
        </span>
      )}
    </a>
  );
}

export function Nav({ stars }: { stars: number | null }) {
  const [scrolled, setScrolled] = useState(false);
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState<string | null>(null);

  const { scrollY, scrollYProgress } = useScroll();
  const progress = useSpring(scrollYProgress, { stiffness: 200, damping: 30, restDelta: 0.001 });
  useMotionValueEvent(scrollY, "change", y => setScrolled(y > 24));

  // Highlight the section in the middle of the screen
  useEffect(() => {
    const ids = NAV_LINKS.map(l => l.href.slice(1));
    const spy = new IntersectionObserver(
      entries => entries.forEach(e => e.isIntersecting && setActive(e.target.id)),
      { rootMargin: "-45% 0px -50% 0px" },
    );
    ids.forEach(id => {
      const el = document.getElementById(id);
      if (el) spy.observe(el);
    });
    return () => spy.disconnect();
  }, []);

  // Close the mobile menu on Escape
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && setOpen(false);
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <motion.header
      className="fixed left-1/2 z-40 -translate-x-1/2"
      initial={false}
      animate={{
        top: scrolled ? 10 : 14,
        width: scrolled ? "min(980px, calc(100% - 24px))" : "min(1112px, calc(100% - 24px))",
      }}
      transition={{ type: "spring", stiffness: 260, damping: 30 }}
    >
      <nav
        aria-label="Main"
        className={`relative flex items-center gap-1.5 rounded-2xl border border-line/80 bg-card/75 px-2.5 backdrop-blur-xl backdrop-saturate-150 transition-[padding,box-shadow] duration-300 sm:pl-4 ${
          scrolled ? "py-1.5 shadow-lift" : "py-2 shadow-soft"
        }`}
      >
        <a href="#top" className="group mr-auto inline-flex items-center gap-2.5" aria-label="Sequential Paste, back to top">
          <Logo />
          <span className="hidden min-[360px]:inline"><Wordmark /></span>
        </a>

        <div className="hidden items-center gap-0.5 lg:flex">
          {NAV_LINKS.map(l => {
            const isActive = active === l.href.slice(1);
            return (
              <a
                key={l.href}
                href={l.href}
                className={`relative rounded-[9px] px-3 py-[7px] text-[14.5px] transition-colors ${isActive ? "text-ink" : "text-ink-2 hover:bg-ink/[.06] hover:text-ink"}`}
              >
                {isActive && (
                  <motion.span
                    layoutId="nav-active"
                    className="absolute inset-0 -z-10 rounded-[9px] bg-marker/60"
                    transition={{ type: "spring", stiffness: 380, damping: 32 }}
                  />
                )}
                {l.label}
              </a>
            );
          })}
        </div>

        <div className="ml-1 hidden sm:block"><StarButton stars={stars} /></div>
        <div className="sm:hidden"><StarButton stars={stars} compact /></div>

        <a
          href="#download"
          className="hidden items-center gap-2 rounded-[10px] bg-ink py-2 pl-3.5 pr-2 text-[14.5px] font-semibold text-paper transition-transform hover:-translate-y-px sm:inline-flex"
        >
          Download
          <span className="rounded-md bg-marker px-1.5 py-1 font-mono text-[11px] font-medium leading-none text-marker-ink">v{VERSION.split(".").slice(0, 2).join(".")}</span>
        </a>

        <button
          type="button"
          onClick={() => setOpen(o => !o)}
          aria-expanded={open}
          aria-controls="mobile-menu"
          aria-label={open ? "Close menu" : "Open menu"}
          className="grid h-[38px] w-[38px] place-items-center rounded-[10px] border border-line-2 bg-card lg:hidden"
        >
          <MenuIcon open={open} />
        </button>

        <span className="pointer-events-none absolute inset-x-4 -bottom-px h-[2px] overflow-hidden rounded-full">
          <motion.span className="block h-full origin-left bg-marker" style={{ scaleX: progress }} />
        </span>
      </nav>

      <AnimatePresence>
        {open && (
          <motion.div
            id="mobile-menu"
            initial={{ opacity: 0, y: -8, scale: 0.98 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -8, scale: 0.98 }}
            transition={{ duration: 0.18 }}
            className="mt-2 origin-top rounded-2xl border border-line bg-card p-2 shadow-lift lg:hidden"
          >
            {NAV_LINKS.map((l, i) => (
              <motion.a
                key={l.href}
                href={l.href}
                onClick={() => setOpen(false)}
                initial={{ opacity: 0, x: -6 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.03 * i }}
                className="flex items-center justify-between rounded-xl px-4 py-3 text-[17px] font-semibold hover:bg-ink/[.05]"
              >
                {l.label}
                <span className="font-mono text-[12px] text-ink-3">0{i + 1}</span>
              </motion.a>
            ))}
            <a
              href={DOWNLOADS.installer.url}
              className="mt-2 flex items-center justify-center gap-2 rounded-xl bg-green px-4 py-3.5 text-[16px] font-semibold text-green-ink"
            >
              Download for Windows
              <span className="font-mono text-[12px] opacity-80">{DOWNLOADS.installer.size}</span>
            </a>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.header>
  );
}
