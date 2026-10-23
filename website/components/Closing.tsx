"use client";

import { AnimatePresence, motion } from "framer-motion";
import { useState, type ReactNode } from "react";
import { DOWNLOADS, REPO_URL, VERSION } from "@/lib/site";
import { DownloadIcon, FileIcon, GitHubIcon } from "./Icons";
import { Logo, Wordmark } from "./Logo";
import { Reveal } from "./Motion";
import { SectionHead } from "./Sections";

function DownloadRow({ href, icon, title, sub, meta, primary }: {
  href: string; icon: ReactNode; title: string; sub: string; meta: string; primary?: boolean;
}) {
  return (
    <motion.a
      href={href}
      whileHover={{ y: -2 }}
      transition={{ type: "spring", stiffness: 400, damping: 28 }}
      className={`grid grid-cols-[40px_minmax(0,1fr)_auto] items-center gap-3.5 rounded-[14px] border p-3.5 sm:grid-cols-[44px_minmax(0,1fr)_auto] sm:px-[18px] sm:py-4 ${
        primary ? "border-marker bg-marker text-marker-ink" : "border-paper/15 bg-paper/[.07] hover:bg-paper/[.12]"
      }`}
    >
      <span className={`grid h-10 w-10 place-items-center rounded-[10px] sm:h-11 sm:w-11 ${primary ? "bg-marker-ink/10" : "bg-paper/10"}`}>{icon}</span>
      <span className="min-w-0">
        <b className="block text-[17px]">{title}</b>
        <small className="hidden break-all font-mono text-[12.5px] opacity-70 sm:block">{sub}</small>
      </span>
      <span className="font-mono text-[13px] opacity-75">{meta}</span>
    </motion.a>
  );
}

export function Download() {
  return (
    <div className="wrap">
      <Reveal>
        <div
          id="download"
          className="relative mt-24 grid items-center gap-12 overflow-hidden rounded-[22px] bg-ink px-5 py-9 text-paper sm:mt-32 sm:rounded-[28px] sm:px-14 sm:py-16 lg:grid-cols-[minmax(0,1.2fr)_minmax(0,1fr)]"
        >
          <div
            aria-hidden="true"
            className="pointer-events-none absolute inset-0 [background-image:radial-gradient(rgb(var(--paper)/.1)_1.2px,transparent_1.4px)] [background-size:22px_22px] [mask-image:linear-gradient(110deg,transparent_40%,#000)]"
          />
          <div className="relative">
            <div className="font-mono text-[12.5px] uppercase tracking-[.08em] text-paper/55">Download</div>
            <h2 className="h2 mt-3 text-paper">Get it in under a minute.</h2>
            <p className="text-paper/70">
              Free and open source. Installs for your account only, no admin rights needed, with an option to start
              with Windows.
            </p>
            <p className="mt-4 text-[14px] text-paper/70">
              Windows may show a SmartScreen warning because the app isn&apos;t code-signed yet. Choose{" "}
              <b className="text-paper">More info</b>, then <b className="text-paper">Run anyway</b>. The full source is on GitHub.
            </p>
          </div>
          <div className="relative grid gap-3">
            <DownloadRow primary href={DOWNLOADS.installer.url} icon={<DownloadIcon className="h-[22px] w-[22px]" />} title="Installer" sub={DOWNLOADS.installer.file} meta={DOWNLOADS.installer.size} />
            <DownloadRow href={DOWNLOADS.portable.url} icon={<FileIcon />} title="Portable" sub={`${DOWNLOADS.portable.file} · no install`} meta={DOWNLOADS.portable.size} />
            <DownloadRow href={REPO_URL} icon={<GitHubIcon className="h-[22px] w-[22px]" />} title="Source code" sub="github.com/imsayanpaul/sequential-paste" meta="MIT" />
          </div>
        </div>
      </Reveal>
    </div>
  );
}

const FAQS: [string, string][] = [
  ["Does it send my clipboard anywhere?", "No. It never connects to the internet. Your text stays in memory on your PC and is gone when you copy something else."],
  ["Will it break Ctrl+Shift+V in my browser?", "No. The shortcuts only act while you have a list of two or more items loaded. Otherwise they go to the app you're using as normal. You can also pause them from the tray."],
  ["A site won't let me paste. Now what?", "Switch \"Insert items by\" to Typing it out. It types each item as keystrokes, which works on most paste-blocked fields."],
  ["Why does Windows warn me when I run it?", "The app isn't code-signed, which costs money every year, so SmartScreen doesn't recognise it yet. Choose More info, then Run anyway. You can read every line of the source on GitHub."],
  ["What does it need?", "Windows 10 or 11. The app window uses Microsoft Edge WebView2, which Windows 11 and current Windows 10 already have. Without it, everything still works from the tray menu."],
  ["How do I uninstall it?", "Settings, then Apps, then Sequential Paste, then Uninstall. The portable version is just one file you can delete."],
];

function FaqItem({ q, a }: { q: string; a: string }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="border-t border-line">
      <button
        type="button"
        onClick={() => setOpen(o => !o)}
        aria-expanded={open}
        className="flex w-full items-center justify-between gap-4 py-[18px] text-left text-[17px] font-semibold sm:text-[18px]"
      >
        {q}
        <motion.span animate={{ rotate: open ? 45 : 0 }} className="font-mono text-[20px] font-normal text-ink-3" aria-hidden="true">+</motion.span>
      </button>
      <AnimatePresence initial={false}>
        {open && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: "auto", opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.2, 0.8, 0.2, 1] }}
            className="overflow-hidden"
          >
            <p className="pb-5 text-[16px] text-ink-2">{a}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export function Faq() {
  return (
    <section id="faq" className="wrap mt-24 sm:mt-28">
      <SectionHead eyebrow="Questions" title="Good to know." />
      <div className="grid gap-x-12 md:grid-cols-2">
        <div>{FAQS.slice(0, 3).map(([q, a]) => <FaqItem key={q} q={q} a={a} />)}</div>
        <div>{FAQS.slice(3).map(([q, a]) => <FaqItem key={q} q={q} a={a} />)}</div>
      </div>
    </section>
  );
}

const COLUMNS: { title: string; links: [string, string][] }[] = [
  { title: "Product", links: [["Installer", DOWNLOADS.installer.url], ["Portable exe", DOWNLOADS.portable.url], ["The app window", "#app"]] },
  { title: "Learn", links: [["Live demo", "#demo"], ["Split modes", "#modes"], ["Shortcuts", "#shortcuts"], ["FAQ", "#faq"]] },
  { title: "Project", links: [["GitHub", REPO_URL], ["Report a problem", `${REPO_URL}/issues`], ["MIT license", `${REPO_URL}/blob/main/LICENSE`]] },
];

export function Footer() {
  return (
    <footer className="mt-28 border-t border-line sm:mt-32">
      <div className="wrap flex flex-wrap items-center justify-between gap-8 py-12 sm:py-14">
        <h3 className="m-0 max-w-[620px] text-[clamp(28px,3.6vw,44px)] font-[750] leading-[1.02] tracking-[-.035em]">
          Stop copying one thing at a time. <span className="marker">Copy the whole list.</span>
        </h3>
        <a href={DOWNLOADS.installer.url} className="inline-flex items-center gap-2.5 rounded-xl bg-ink px-5 py-3.5 font-semibold text-paper transition hover:-translate-y-px">
          <DownloadIcon /> Download for Windows
        </a>
      </div>
      <div className="wrap grid grid-cols-2 gap-8 border-t border-dashed border-line-2 py-9 md:grid-cols-[1.6fr_repeat(3,1fr)]">
        <div className="col-span-2 md:col-span-1">
          <a href="#top" className="group inline-flex items-center gap-2.5"><Logo /><Wordmark /></a>
          <p className="mt-3.5 max-w-[300px] text-[15px] text-ink-2">A small, free Windows utility that turns a copied list into a paste queue.</p>
        </div>
        {COLUMNS.map(c => (
          <div key={c.title}>
            <h4 className="mb-4 mt-1.5 font-mono text-[12px] font-medium uppercase tracking-[.08em] text-ink-3">{c.title}</h4>
            <ul className="m-0 grid list-none gap-2.5 p-0">
              {c.links.map(([label, href]) => (
                <li key={label}><a href={href} className="text-[15px] text-ink-2 hover:text-ink hover:underline hover:underline-offset-[3px]">{label}</a></li>
              ))}
            </ul>
          </div>
        ))}
      </div>
      <div className="wrap flex flex-wrap justify-between gap-4 font-mono text-[12.5px] text-ink-3">
        <span>Made by Sayan Paul</span>
        <span>v{VERSION} · Windows 10 and 11</span>
      </div>
      <div
        aria-hidden="true"
        className="select-none whitespace-nowrap pb-[.12em] pt-6 text-center text-[clamp(34px,12.4vw,172px)] font-extrabold leading-none tracking-[-.035em] text-ink/[.07]"
      >
        sequential paste
      </div>
    </footer>
  );
}
