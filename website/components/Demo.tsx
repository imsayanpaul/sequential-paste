"use client";

import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import { Fragment, useCallback, useEffect, useRef, useState } from "react";

type Mode = "line" | "comma" | "tab" | "sentence" | "paragraph";
type Insert = "paste" | "type";
type After = "tab" | "none";

const MODES: { id: Mode; label: string }[] = [
  { id: "line", label: "Lines" },
  { id: "comma", label: "Commas" },
  { id: "tab", label: "Cells" },
  { id: "sentence", label: "Sentences" },
  { id: "paragraph", label: "Paragraphs" },
];

/** What "you copied" for each mode, and the form it gets pasted into */
const SAMPLES: Record<Mode, { text: string; labels: string[] }> = {
  line: { text: "Priya Sharma\nBengaluru\n98450 12345\npriya@example.com", labels: ["Name", "City", "Phone", "Email"] },
  comma: { text: "Priya Sharma, Bengaluru, 98450 12345, priya@example.com", labels: ["Name", "City", "Phone", "Email"] },
  tab: { text: "Priya Sharma\tBengaluru\n98450 12345\tpriya@example.com", labels: ["Name", "City", "Phone", "Email"] },
  sentence: { text: "Hi Priya. Your order has shipped. It arrives on Friday. Thanks!", labels: ["Line 1", "Line 2", "Line 3", "Line 4"] },
  paragraph: { text: "Hi Priya,\n\nYour order has shipped and arrives on Friday.\n\nThanks, Arjun", labels: ["Greeting", "Message", "Sign-off"] },
};

const MAX_ITEMS = 8;
const TYPE_DELAY = 38;
const spring = { type: "spring" as const, stiffness: 420, damping: 34 };

/** A simplified version of the app's splitting rules (clipboard_manager.py) */
function split(text: string, mode: Mode): string[] {
  const t = text.replace(/\r/g, "");
  let parts: string[];
  switch (mode) {
    case "comma": parts = t.split(","); break;
    case "tab": parts = t.split("\n").filter(r => r.trim()).flatMap(r => r.split("\t")); break;
    case "sentence": parts = t.split(/(?<=[.!?।。؟])\s+/); break;
    case "paragraph": parts = t.split(/\n\s*\n/); break;
    default: parts = t.split("\n");
  }
  const items = parts.map(s => s.trim());
  // Spreadsheet mode keeps empty cells so fields stay lined up
  return (mode === "tab" ? items : items.filter(Boolean)).slice(0, MAX_ITEMS);
}

/** Separator shown between items when the copy is displayed as raw text */
const JOIN: Record<Exclude<Mode, "tab">, string> = { line: "\n", comma: ", ", sentence: " ", paragraph: "\n\n" };

function Segmented<T extends string>({ value, options, onChange, label }: {
  value: T; options: { id: T; label: string }[]; onChange: (v: T) => void; label: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <span className="hidden font-mono text-[11.5px] uppercase tracking-[.08em] text-ink-3 sm:inline">{label}</span>
      <div role="group" aria-label={label} className="relative flex rounded-[10px] border border-line-2 bg-paper p-0.5">
        {options.map(o => (
          <button
            key={o.id}
            type="button"
            aria-pressed={value === o.id}
            onClick={() => onChange(o.id)}
            className={`relative whitespace-nowrap rounded-lg px-1 py-1.5 text-[12px] min-[400px]:px-[7px] min-[400px]:text-[12.5px] font-semibold transition-colors sm:px-2.5 sm:text-[13px] ${value === o.id ? "text-paper" : "text-ink-2 hover:text-ink"}`}
          >
            {value === o.id && (
              <motion.span layoutId={`seg-${label}`} className="absolute inset-0 rounded-lg bg-ink" transition={{ type: "spring", stiffness: 500, damping: 36 }} />
            )}
            <span className="relative">{o.label}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

export function Demo() {
  const [mode, setMode] = useState<Mode>("line");
  const [text, setText] = useState(SAMPLES.line.text);
  const [custom, setCustom] = useState(false);
  const [insert, setInsert] = useState<Insert>("paste");
  const [after, setAfter] = useState<After>("tab");
  const [index, setIndex] = useState(0);
  const [focus, setFocus] = useState(0);
  const [typed, setTyped] = useState<Record<number, string>>({});
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [pressed, setPressed] = useState(false);
  const [tabFlash, setTabFlash] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const items = split(text, mode);
  const labels = custom ? [] : SAMPLES[mode].labels;
  const done = index >= items.length;

  // Refs so fast repeated presses and timers always see current values
  const indexRef = useRef(0);
  const typingRef = useRef(false);
  const timers = useRef<number[]>([]);
  const live = useRef({ items, insert, after });
  live.current = { items, insert, after };

  const clearTimers = () => {
    timers.current.forEach(t => window.clearTimeout(t));
    timers.current = [];
  };
  const later = (fn: () => void, ms: number) => {
    timers.current.push(window.setTimeout(fn, ms));
  };
  const flash = (set: (v: boolean) => void, ms: number) => {
    set(true);
    window.setTimeout(() => set(false), ms);
  };

  const reset = useCallback(() => {
    clearTimers();
    typingRef.current = false;
    indexRef.current = 0;
    setIndex(0);
    setFocus(0);
    setTyped({});
  }, []);

  useEffect(() => () => clearTimers(), []);

  const moveOn = (next: number) => {
    if (live.current.after === "tab") {
      flash(setTabFlash, 320);
      setFocus(next);
    } else {
      // "Do nothing": the caret stays put until you'd click the next field
      setFocus(-1);
      later(() => setFocus(f => (f === -1 ? next : f)), 500);
    }
  };

  const pasteNext = useCallback(() => {
    flash(setPressed, 140);
    const { items: list, insert: how } = live.current;
    const i = indexRef.current;
    // Like the app: presses while an item is still being typed are ignored
    if (i >= list.length || typingRef.current) return;
    const next = i + 1;

    if (how === "paste") {
      indexRef.current = next;
      setIndex(next);
      moveOn(next);
      return;
    }

    // Typing: the item is used up straight away, its text appears key by key
    typingRef.current = true;
    indexRef.current = next;
    setIndex(next);
    setFocus(i);
    const value = list[i];
    for (let c = 1; c <= value.length; c++) {
      later(() => setTyped(t => ({ ...t, [i]: value.slice(0, c) })), c * TYPE_DELAY);
    }
    later(() => {
      typingRef.current = false;
      moveOn(next);
    }, value.length * TYPE_DELAY + 120);
  }, []);

  const chooseMode = (m: Mode) => {
    setMode(m);
    if (!custom) setText(SAMPLES[m].text);
    setEditing(false);
    reset();
  };

  const chooseInsert = (v: Insert) => {
    setInsert(v);
    reset();
  };

  const applyDraft = useCallback(() => {
    setEditing(false);
    if (draft.trim()) {
      setText(draft);
      setCustom(draft !== SAMPLES[mode].text);
    }
    reset();
  }, [draft, mode, reset]);

  const startEditing = () => {
    setDraft(text);
    setEditing(true);
    window.setTimeout(() => textareaRef.current?.select(), 0);
  };

  const useSample = () => {
    setCustom(false);
    setText(SAMPLES[mode].text);
    setEditing(false);
    reset();
  };

  // Ctrl+Shift+V (Cmd+Shift+V on a Mac) pastes the next item, right on this page
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!(e.ctrlKey || e.metaKey) || !e.shiftKey) return;
      const k = e.key.toLowerCase();
      if (k === "v") {
        if (editing && document.activeElement === textareaRef.current) return;
        e.preventDefault();
        if (editing) applyDraft();
        else pasteNext();
      } else if (k === "r" && indexRef.current > 0) {
        e.preventDefault();
        reset();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [editing, pasteNext, applyDraft, reset]);

  /** One piece of the copied text: highlighted when next, struck through once used */
  const segment = (value: string, i: number) => {
    const used = i < index;
    const next = i === index;
    const flies = insert === "paste";
    const shown = value || "·";
    // inline-block: layout animations need a box they can transform
    const base = "inline-block max-w-full align-top rounded-sm";
    const mark = next ? "bg-marker px-0.5 text-marker-ink" : "";
    if (used) {
      return <span key={`${mode}-${i}`} className={`${base} text-ink-3 line-through decoration-1 opacity-60`}>{shown}</span>;
    }
    if (!flies) {
      return <span key={`${mode}-${i}`} className={`${base} ${mark}`}>{shown}</span>;
    }
    return (
      <motion.span key={`${mode}-${i}`} layoutId={`item-${mode}-${i}`} transition={spring} className={`${base} ${mark}`}>
        {shown}
      </motion.span>
    );
  };

  const renderClipboard = () => {
    if (mode === "tab") {
      const rows = text.replace(/\r/g, "").split("\n").filter(r => r.trim()).map(r => r.split("\t"));
      let n = 0;
      return (
        <table className="w-full border-collapse text-[14px]">
          <tbody>
            {rows.map((row, r) => (
              <tr key={r}>
                {row.map((cell, c) => {
                  const i = n++;
                  return (
                    <td key={c} className="border border-line-2 px-2 py-1.5 align-top">
                      {i < MAX_ITEMS ? segment(cell.trim(), i) : cell}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      );
    }
    return (
      <div className="whitespace-pre-wrap break-words px-4 py-3 leading-[1.75]">
        {items.map((item, i) => (
          <Fragment key={i}>
            {i > 0 && JOIN[mode]}
            {segment(item, i)}
          </Fragment>
        ))}
      </div>
    );
  };

  return (
    <LayoutGroup>
      <div id="demo" className="relative mt-14 overflow-hidden rounded-[22px] border border-line bg-card shadow-lift">
        <div className="flex items-center gap-2 border-b border-line px-4 py-3 font-mono text-[12px] text-ink-3 sm:px-5">
          <span className="mr-2 flex gap-1.5" aria-hidden="true">
            <i className="h-2.5 w-2.5 rounded-full bg-line-2" />
            <i className="h-2.5 w-2.5 rounded-full bg-line-2" />
            <i className="h-2.5 w-2.5 rounded-full bg-line-2" />
          </span>
          <span className="truncate">live demo: runs in your browser</span>
          <span className="ml-auto inline-flex items-center gap-1.5 text-green">
            <span className="h-[7px] w-[7px] animate-pulse2 rounded-full bg-green" />
            ready
          </span>
        </div>

        {/* Settings, as in the app */}
        <div className="flex flex-wrap items-center gap-x-5 gap-y-3 border-b border-line bg-paper-2/50 px-3 py-3 sm:px-5">
          <div className="-mx-1 max-w-full overflow-x-auto px-1 pb-0.5">
            <Segmented label="Split by" value={mode} options={MODES} onChange={chooseMode} />
          </div>
          <Segmented
            label="Insert by"
            value={insert}
            options={[{ id: "paste", label: "Paste" }, { id: "type", label: "Type" }]}
            onChange={chooseInsert}
          />
        </div>

        <div className="grid md:grid-cols-[1fr_1.15fr]">
          {/* What you copied */}
          <div className="p-5 sm:p-7">
            <div className="mb-3.5 flex items-center justify-between gap-3 font-mono text-[12px] uppercase tracking-[.08em] text-ink-3">
              <span>You copied</span>
              <span className="flex gap-3 normal-case tracking-normal">
                {custom && !editing && (
                  <button type="button" onClick={useSample} className="text-ink-2 underline underline-offset-[3px] hover:text-ink">Sample</button>
                )}
                <button type="button" onClick={editing ? applyDraft : startEditing} className="text-ink-2 underline underline-offset-[3px] hover:text-ink">
                  {editing ? "Done" : "Use my own text"}
                </button>
              </span>
            </div>

            <div className="min-h-[150px] overflow-hidden rounded-md border border-line bg-tape font-mono text-[14.5px]">
              {editing ? (
                <textarea
                  ref={textareaRef}
                  value={draft}
                  onChange={e => setDraft(e.target.value)}
                  spellCheck={false}
                  aria-label="Text to split"
                  className="min-h-[188px] w-full resize-y bg-transparent px-4 py-3 leading-relaxed text-ink outline-none"
                />
              ) : (
                renderClipboard()
              )}
            </div>

            <button type="button" onClick={pasteNext} aria-label="Paste the next item (Ctrl+Shift+V)" className="group mt-6 flex gap-2">
              {["Ctrl", "Shift", "V"].map(k => (
                <span
                  key={k}
                  className={`grid h-[50px] place-items-center rounded-[10px] border font-mono text-[15px] font-semibold transition-all duration-75 ${
                    k === "V" ? "min-w-[54px]" : "min-w-[76px]"
                  } ${pressed ? "translate-y-1 border-b border-ink bg-marker text-marker-ink" : "border-b-[5px] border-line-2 bg-card group-hover:border-ink-3"}`}
                >
                  {k}
                </span>
              ))}
            </button>
            <p className="mt-3.5 text-[14px] text-ink-2">
              {editing ? (
                <>Paste or type anything, then press <b className="font-semibold">Ctrl+Shift+V</b>. It&apos;s split using the mode above.</>
              ) : (
                <>Press <b className="font-semibold">Ctrl+Shift+V</b> on your keyboard (yes, on this page) or tap the keys.</>
              )}
            </p>
          </div>

          {/* Where it goes */}
          <div className="border-t border-dashed border-line-2 p-5 sm:p-7 md:border-l md:border-t-0">
            <div className="mb-3.5 font-mono text-[12px] uppercase tracking-[.08em] text-ink-3">A form somewhere</div>
            <div className="grid gap-3.5">
              {items.map((value, i) => {
                const filled = i < index;
                const focused = focus === i && !editing;
                const long = value.length > 34;
                return (
                  <div key={`${mode}-${i}`}>
                    <label className="mb-1.5 block text-[13px] text-ink-2">{labels[i] ?? `Field ${i + 1}`}</label>
                    <div
                      className={`flex items-center overflow-hidden rounded-lg border bg-paper px-3.5 text-[16px] transition-[border-color,box-shadow] ${
                        long ? "min-h-[46px] py-2.5" : "h-[46px] whitespace-nowrap"
                      } ${focused ? "border-ink shadow-[0_0_0_3px_rgb(var(--marker)/.7)]" : "border-line-2"}`}
                    >
                      {filled && insert === "paste" && (
                        <motion.span layoutId={`item-${mode}-${i}`} transition={spring} className={long ? "" : "truncate"}>
                          {value || " "}
                        </motion.span>
                      )}
                      {insert === "type" && typed[i] !== undefined && <span className={long ? "" : "truncate"}>{typed[i]}</span>}
                      {focused && <span className="ml-0.5 h-5 w-[1.5px] shrink-0 animate-blink bg-ink" />}
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-4 flex flex-wrap items-center justify-between gap-3 font-mono text-[13px] text-ink-3">
              <span aria-live="polite">{done ? `All ${items.length} pasted` : `Item ${index + 1} of ${items.length} is next`}</span>
              <span className="flex items-center gap-1.5">
                after each item
                <span className="inline-flex overflow-hidden rounded-lg border border-line-2" role="group" aria-label="After each item">
                  {(["tab", "none"] as const).map(v => (
                    <button
                      key={v}
                      type="button"
                      aria-pressed={after === v}
                      onClick={() => setAfter(v)}
                      className={`px-2.5 py-[7px] text-[12px] ${after === v ? "bg-ink text-paper" : "text-ink-2"}`}
                    >
                      {v === "tab" ? "Tab" : "Nothing"}
                    </button>
                  ))}
                </span>
                <span
                  className={`rounded-md border px-2 py-[5px] text-[12px] font-semibold leading-none transition-opacity ${
                    tabFlash ? "border-ink bg-marker text-marker-ink opacity-100" : "border-line-2 opacity-0"
                  }`}
                  style={{ borderBottomWidth: 3 }}
                  aria-hidden="true"
                >
                  Tab
                </span>
              </span>
            </div>

            <AnimatePresence>
              {done && (
                <motion.p initial={{ opacity: 0, y: 6 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0 }} className="mt-4 text-[15px] text-ink-2">
                  That&apos;s the whole idea.{" "}
                  <button type="button" onClick={reset} className="text-ink underline underline-offset-[3px]">Start over</button>{" "}
                  (Ctrl+Shift+R in the app), or try another mode above.
                </motion.p>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </LayoutGroup>
  );
}
