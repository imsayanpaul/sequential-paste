import type { ReactNode } from "react";
import { Reveal } from "./Motion";

const PLACES = ["Web forms", "Excel", "Google Sheets", "CRM records", "Sign-up pages", "Outlook", "Admin panels", "Notepad", "Job portals", "VS Code", "Chat apps", "Invoices"];

export function Marquee() {
  return (
    <div className="relative mt-16 overflow-hidden border-y border-line py-[18px]" aria-label="Works anywhere you can paste">
      <div className="absolute inset-y-0 left-0 z-10 hidden items-center bg-paper pl-6 pr-6 font-mono text-[12px] uppercase tracking-[.08em] text-ink-3 shadow-[18px_0_18px_rgb(var(--paper))] md:flex">
        Works anywhere you can paste
      </div>
      <div className="flex w-max animate-marquee gap-11 hover:[animation-play-state:paused] motion-reduce:animate-none md:pl-[270px]">
        {[...PLACES, ...PLACES].map((p, i) => (
          <span
            key={i}
            aria-hidden={i >= PLACES.length}
            className="inline-flex items-center gap-11 whitespace-nowrap text-[22px] font-semibold tracking-[-.02em] text-ink-2"
          >
            {p}
            <i className="h-[7px] w-[7px] rotate-45 rounded-[2px] bg-marker" />
          </span>
        ))}
      </div>
    </div>
  );
}

function SectionHead({ eyebrow, title, lede }: { eyebrow: string; title: string; lede?: string }) {
  return (
    <>
      <div className="eyebrow">{eyebrow}</div>
      <Reveal><h2 className="h2">{title}</h2></Reveal>
      {lede && <Reveal delay={0.05}><p className="lede">{lede}</p></Reveal>}
    </>
  );
}

const Chip = ({ children, first }: { children: ReactNode; first?: boolean }) => (
  <span className={`whitespace-nowrap rounded border px-[7px] py-[5px] font-mono text-[12px] leading-none ${first ? "border-transparent bg-marker text-marker-ink" : "border-line bg-paper-2"}`}>
    {children}
  </span>
);

const MODES: { title: string; input: ReactNode; out: string[]; text: string }[] = [
  { title: "Lines", input: "Priya Sharma\nBengaluru\n98450 12345", out: ["Priya Sharma", "Bengaluru", "98450…"], text: "Each line is one item. The default." },
  { title: "Commas", input: "red, green, blue", out: ["red", "green", "blue"], text: "Comma-separated values, tags, lists." },
  {
    title: "Spreadsheet cells",
    input: (
      <table className="border-collapse">
        <tbody>
          {[["Priya", "Pune", "31"], ["Arjun", "", "27"]].map((r, i) => (
            <tr key={i}>{r.map((c, j) => <td key={j} className="border border-line-2 px-1.5 py-px">{c}</td>)}</tr>
          ))}
        </tbody>
      </table>
    ),
    out: ["Priya", "Pune", "31", "Arjun", "·"],
    text: "Row by row. Empty cells are kept, so fields stay lined up.",
  },
  { title: "Sentences", input: "Hi Dr. Rao. It\nshipped. Thanks!", out: ["Hi Dr. Rao.", "It shipped.", "Thanks!"], text: "Knows Mr., Dr., decimals, URLs. Also । 。 ؟" },
  { title: "Paragraphs", input: "Hi Priya,\n\nYour order…", out: ["Hi Priya,", "Your order…"], text: "Split at blank lines, for longer blocks of text." },
];

export function Modes() {
  return (
    <section id="modes" className="wrap mt-24 sm:mt-28">
      <SectionHead
        eyebrow="Split copied text into"
        title="Whatever you copy, it finds the pieces."
        lede="Pick how a copy gets split. Change it any time, and the list you already copied is split again."
      />
      <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-5">
        {MODES.map((m, i) => (
          <Reveal key={m.title} delay={0.05 * i}>
          <div className="card flex h-full flex-col gap-3.5 p-[18px] transition hover:-translate-y-1 hover:border-line-2 hover:shadow-soft">
            <h3 className="m-0 text-[19px] font-bold tracking-[-.01em]">{m.title}</h3>
            <div className="min-h-[74px] overflow-hidden whitespace-pre rounded-md border border-dashed border-line-2 bg-tape px-2.5 py-2 font-mono text-[12.5px] leading-relaxed text-ink-2">
              {m.input}
            </div>
            <div className="flex flex-wrap gap-[5px]">
              {m.out.map((o, j) => <Chip key={j} first={j === 0}>{o}</Chip>)}
            </div>
            <p className="m-0 text-[14px] text-ink-2">{m.text}</p>
          </div>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

function Tile({ className = "", children, delay = 0 }: { className?: string; children: ReactNode; delay?: number }) {
  return (
    <Reveal delay={delay} className={`relative flex flex-col overflow-hidden rounded-[20px] border p-6 ${className}`}>
      {children}
    </Reveal>
  );
}

const MINI_FORM = [
  ["Full name", "Priya Sharma"],
  ["City", "Bengaluru"],
  ["Phone", "98450 12345"],
  ["Email", "priya@example.com"],
];

export function Bento() {
  return (
    <section id="features" className="wrap mt-24 sm:mt-28">
      <SectionHead
        eyebrow="Small app, careful details"
        title="Built for the 40th field, not just the first."
        lede="The basics are simple. These are the parts that make it pleasant on a long form."
      />
      <div className="grid gap-3.5 md:grid-cols-2 lg:auto-rows-[minmax(210px,auto)] lg:grid-cols-6">
        <Tile className="border-ink bg-ink text-paper md:col-span-2 lg:col-span-4 lg:row-span-2">
          <h3 className="mb-1.5 text-[22px] font-bold leading-tight tracking-[-.02em] sm:text-[26px]">Fill a whole form without touching the mouse</h3>
          <p className="max-w-[440px] text-[15px] text-paper/70">Set it to press Tab after each item, then keep pressing Ctrl+Shift+V. Every press lands in the next field.</p>
          <div className="mt-auto pt-6">
            <div className="grid gap-3 sm:grid-cols-2">
              {MINI_FORM.map(([label, value], i) => (
                <div
                  key={label}
                  className="anim-ring rounded-[10px] border border-paper/15 bg-paper/[.07] px-3 pb-3 pt-2.5"
                  style={{ animationDelay: `${i * 1.2}s` }}
                >
                  <small className="mb-2 block font-mono text-[11px] uppercase tracking-[.06em] opacity-55">{label}</small>
                  <span className="anim-fill block overflow-hidden whitespace-nowrap font-mono text-[15px]" style={{ animationDelay: `${i * 1.2}s` }}>
                    {value}
                  </span>
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap items-center gap-2 font-mono text-[12px] opacity-80">
              {["Ctrl", "Shift", "V"].map(k => <kbd key={k} className="rounded-md border border-paper/25 px-2 py-1.5 font-semibold" style={{ borderBottomWidth: 3 }}>{k}</kbd>)}
              then <kbd className="rounded-md border border-paper/25 px-2 py-1.5 font-semibold" style={{ borderBottomWidth: 3 }}>Tab</kbd>, four times
            </div>
          </div>
        </Tile>

        <Tile className="card lg:col-span-2" delay={0.05}>
          <h3 className="mb-1.5 text-[21px] font-bold tracking-[-.02em]">Types where paste is blocked</h3>
          <p className="text-[15px] text-ink-2">Switch to typing and it types each item out, key by key. Hold Esc to stop.</p>
          <div className="relative mt-auto rounded-[10px] border border-line-2 bg-paper px-3.5 py-3 font-mono text-[15px]">
            <span className="absolute -top-2.5 right-2.5 rounded-full border border-line-2 bg-card px-2 py-1 text-[10.5px] font-semibold uppercase leading-none tracking-wide text-ink-3">paste blocked</span>
            <span className="anim-type inline-block overflow-hidden whitespace-nowrap align-bottom">ACC-4417-0093-21</span>
            <span className="inline-block h-[18px] w-[1.5px] animate-blink bg-ink align-[-3px]" />
          </div>
        </Tile>

        <Tile className="card lg:col-span-2" delay={0.1}>
          <h3 className="mb-1.5 text-[21px] font-bold tracking-[-.02em]">Stays out of your way</h3>
          <p className="text-[15px] text-ink-2">No list loaded? The shortcut does what it always did.</p>
          <div className="mt-auto flex flex-wrap items-center gap-1.5 pt-5">
            {["Ctrl", "Shift", "V"].map(k => <kbd key={k} className="kbd">{k}</kbd>)}
            <span className="ml-1.5 font-mono text-[12px] text-ink-3">→ goes to <b className="text-ink">your browser</b></span>
          </div>
        </Tile>

        <Tile className="card lg:col-span-2" delay={0.05}>
          <h3 className="mb-1.5 text-[21px] font-bold tracking-[-.02em]">Your clipboard comes back</h3>
          <p className="text-[15px] text-ink-2">After each paste, what you had copied is put back, untouched.</p>
          <div className="mt-auto flex flex-wrap items-center gap-2 pt-5 font-mono text-[12.5px]">
            <Chip first>your copy</Chip><span className="text-ink-3">→</span><Chip>item 3</Chip><span className="text-ink-3">→</span><Chip first>your copy</Chip>
          </div>
        </Tile>

        <Tile className="card lg:col-span-2" delay={0.1}>
          <h3 className="mb-1.5 text-[21px] font-bold tracking-[-.02em]">Skip, go back, start over</h3>
          <p className="text-[15px] text-ink-2">Missed a field? Step back one item, skip one, or restart the list.</p>
          <div className="mt-auto flex items-center gap-1.5 pt-5">
            {["N", "B", "R"].map(k => <kbd key={k} className="kbd">{k}</kbd>)}
            <span className="ml-1.5 font-mono text-[12px] text-ink-3">with Ctrl+Shift</span>
          </div>
        </Tile>

        <Tile className="card lg:col-span-2" delay={0.15}>
          <h3 className="mb-1.5 text-[21px] font-bold tracking-[-.02em]">Nothing leaves your PC</h3>
          <p className="text-[15px] text-ink-2">No account, no internet, no tracking.</p>
          <div className="mt-auto pt-4">
            <b className="block text-[76px] font-extrabold leading-[.9] tracking-[-.05em]">0</b>
            <small className="mt-1.5 block font-mono text-[12px] uppercase tracking-[.04em] text-ink-3">network requests</small>
          </div>
        </Tile>
      </div>
    </section>
  );
}

export function Shortcuts() {
  const rows = [
    ["V", "Paste the next item"],
    ["N", "Skip the next item"],
    ["B", "Go back one item"],
    ["R", "Start over from the first"],
  ];
  return (
    <section id="shortcuts" className="wrap mt-24 sm:mt-28">
      <SectionHead eyebrow="Shortcuts" title="Four shortcuts. One you'll use." />
      <div className="grid gap-3.5 sm:grid-cols-2 lg:grid-cols-4">
        {rows.map(([k, text], i) => (
          <Reveal key={k} delay={0.05 * i} className="card flex flex-col gap-3.5 p-[18px]">
            <div className="flex gap-1.5">
              <kbd className="kbd">Ctrl</kbd><kbd className="kbd">Shift</kbd><kbd className="kbd">{k}</kbd>
            </div>
            <span className="text-[15px] text-ink-2">{text}</span>
          </Reveal>
        ))}
      </div>
    </section>
  );
}

export { SectionHead };
