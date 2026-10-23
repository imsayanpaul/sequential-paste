"use client";

import { motion } from "framer-motion";
import { Logo } from "./Logo";
import { Reveal } from "./Motion";
import { SectionHead } from "./Sections";

/** The tray menu, rebuilt in HTML so it follows the page's light/dark theme */
function TrayMenu() {
  const Row = ({ label, keys, check, chevron, dim, bold }: {
    label: string; keys?: string; check?: boolean; chevron?: boolean; dim?: boolean; bold?: boolean;
  }) => (
    <div className={`grid grid-cols-[18px_1fr_auto] items-center gap-1 rounded-[5px] px-2 py-[5px] ${dim ? "text-ink-3" : "hover:bg-ink/[.06]"}`}>
      <span className="text-[11px]">{check ? "✓" : ""}</span>
      <span className={`truncate ${bold ? "font-bold" : ""}`}>{label}</span>
      <span className="flex items-center gap-1 pl-4 text-ink-2">
        {keys}
        {chevron && <span aria-hidden="true">›</span>}
      </span>
    </div>
  );
  const Sep = () => <div className="mx-2 my-1 h-px bg-line" />;

  return (
    <div className="w-full max-w-[320px] rounded-xl border border-line bg-card p-1 text-[13px] shadow-lift" role="img" aria-label="The Sequential Paste tray menu">
      <Row label="Open Sequential Paste…" bold />
      <Sep />
      <Row label="3 of 7 pasted" dim />
      <Row label="Paste next: “Arjun Mehta”" keys="Ctrl+Shift+V" dim />
      <Sep />
      <Row label="Skip next item" keys="Ctrl+Shift+N" />
      <Row label="Previous item" keys="Ctrl+Shift+B" />
      <Row label="Start over" keys="Ctrl+Shift+R" />
      <Sep />
      <Row label="Split copied text into" keys="Lines" chevron />
      <Row label="Insert items by" keys="Pasting" chevron />
      <Row label="After each item" keys="Press Tab" chevron />
      <Sep />
      <Row label="Show notifications" />
      <Row label="Beep when a list is finished" check />
      <Row label="Start with Windows" check />
      <Sep />
      <Row label="Pause shortcuts" />
      <Row label="Quit Sequential Paste" />
    </div>
  );
}

export function Showcase() {
  return (
    <section id="app" className="wrap mt-24 sm:mt-28">
      <SectionHead
        eyebrow="The app"
        title="Lives in your tray. Explains itself."
        lede="Click the tray icon for the app window. Hover any setting and it acts out what it does on a sample form."
      />
      <div className="grid items-start gap-7 lg:grid-cols-[minmax(0,1fr)_320px]">
        <Reveal>
          <figure className="m-0 overflow-hidden rounded-2xl border border-line bg-card shadow-lift">
            <div className="flex h-[38px] items-center gap-2.5 border-b border-line px-3.5 text-[13px] text-ink-2">
              <Logo className="h-4 w-4" />
              Sequential Paste
              <span className="ml-auto flex gap-4 font-mono text-ink-3" aria-hidden="true">– □ ×</span>
            </div>
            {/* eslint-disable-next-line @next/next/no-img-element -- animated GIF, no optimisation wanted */}
            <img
              src="/media/app-preview.gif"
              alt="The app window: hovering each setting plays a preview of what it does"
              width={737}
              height={475}
              loading="lazy"
              className="block h-auto w-full"
            />
          </figure>
        </Reveal>
        <Reveal delay={0.1} className="flex flex-col gap-3.5 sm:flex-row sm:items-start lg:flex-col">
          <motion.div whileHover={{ y: -3 }} className="w-full max-w-[320px]">
            <TrayMenu />
          </motion.div>
          <p className="text-[14px] text-ink-2">
            <b className="text-ink">Right-click the tray icon</b> for the same controls: what&apos;s next, skip or go back,
            and every setting.
          </p>
        </Reveal>
      </div>
    </section>
  );
}
