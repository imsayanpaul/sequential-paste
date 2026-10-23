"use client";

import { motion } from "framer-motion";
import { DOWNLOADS, VERSION } from "@/lib/site";
import { Demo } from "./Demo";
import { DownloadIcon } from "./Icons";

const LINES = [
  ["Copy", "once."],
  ["Paste", "one", "at", "a", "time."],
];

const STATS = [
  { n: "1", label: "shortcut to learn" },
  { n: "5", label: "ways to split" },
  { n: "0", label: "accounts" },
];

export function Hero() {
  let w = 0;
  return (
    <div id="top" className="relative isolate">
      <div
        aria-hidden="true"
        className="dot-grid absolute inset-x-0 top-0 -z-10 h-[900px] [mask-image:radial-gradient(ellipse_70%_60%_at_50%_30%,#000_30%,transparent_75%)]"
      />
      <header id="try" className="wrap pb-10 pt-[120px] sm:pt-[148px]">
        <motion.a
          href="#app"
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="group inline-flex max-w-full items-center gap-2.5 rounded-full border border-line bg-card py-1 pl-1 pr-3 text-[14px] text-ink-2 shadow-soft transition-colors hover:border-ink-3 hover:text-ink"
        >
          <span className="rounded-full bg-ink px-2 py-1 font-mono text-[11px] font-semibold uppercase leading-none tracking-wider text-paper">New</span>
          <span className="truncate">An app window that shows what every setting does</span>
          <span className="transition-transform group-hover:translate-x-0.5">→</span>
        </motion.a>

        <h1
          aria-label="Copy once. Paste one at a time."
          className="mb-7 mt-7 text-[clamp(50px,8.6vw,116px)] font-extrabold leading-[.9] tracking-[-.05em]"
        >
          {LINES.map((line, li) => (
            <span key={li} className="block" aria-hidden="true">
              {line.map(word => {
                const delay = 0.08 * w++ + (li ? 0.2 : 0);
                return (
                  <motion.span
                    key={word}
                    className={`mr-[.22em] inline-block ${word === "one" ? "marker" : ""}`}
                    initial={{ opacity: 0, y: "0.3em", rotate: 2 }}
                    animate={{ opacity: 1, y: 0, rotate: 0 }}
                    transition={{ type: "spring", stiffness: 300, damping: 24, delay }}
                  >
                    {word}
                  </motion.span>
                );
              })}
            </span>
          ))}
        </h1>

        <div className="grid items-end gap-10 lg:grid-cols-[minmax(0,1fr)_auto]">
          <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.5, duration: 0.6 }}>
            <p className="mb-8 max-w-[600px] text-[18px] text-ink-2 sm:text-[21px]">
              Sequential Paste turns anything you copy into a queue. Each press of{" "}
              <span className="font-mono">Ctrl+Shift+V</span> pastes the next line, value or spreadsheet cell, so you
              can fill forms without flipping between windows.
            </p>
            <div className="flex flex-wrap items-center gap-3">
              <a
                href={DOWNLOADS.installer.url}
                className="inline-flex items-center gap-2.5 rounded-xl bg-green px-5 py-3.5 text-[16px] font-semibold text-green-ink transition hover:-translate-y-px hover:shadow-lift"
              >
                <DownloadIcon /> Download for Windows
              </a>
              <a
                href="#demo"
                className="inline-flex items-center rounded-xl border border-line-2 px-5 py-3.5 text-[16px] font-semibold transition hover:-translate-y-px hover:border-ink-3"
              >
                Try it right here
              </a>
            </div>
            <p className="mt-4 font-mono text-[13px] text-ink-3">
              v{VERSION} · {DOWNLOADS.installer.size} · Windows 10 and 11 · open source, MIT
            </p>
          </motion.div>

          <motion.dl
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8, duration: 0.6 }}
            className="flex gap-7 pb-1.5"
          >
            {STATS.map(s => (
              <div key={s.label}>
                <dt className="sr-only">{s.label}</dt>
                <dd className="m-0">
                  <b className="block text-[34px] font-extrabold leading-none tracking-[-.04em] sm:text-[40px]">{s.n}</b>
                  <span className="font-mono text-[11.5px] uppercase tracking-[.06em] text-ink-3">{s.label}</span>
                </dd>
              </div>
            ))}
          </motion.dl>
        </div>

        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.7, duration: 0.8, ease: [0.2, 0.8, 0.2, 1] }}>
          <Demo />
        </motion.div>
      </header>
    </div>
  );
}
