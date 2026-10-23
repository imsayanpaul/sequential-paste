"use client";

import { AnimatePresence, LayoutGroup, motion } from "framer-motion";
import { useCallback, useEffect, useRef, useState } from "react";

const DEFAULT_ITEMS = ["Priya Sharma", "Bengaluru", "98450 12345", "priya@example.com"];
const DEFAULT_LABELS = ["Name", "City", "Phone", "Email"];
const MAX_ITEMS = 8;
const spring = { type: "spring" as const, stiffness: 420, damping: 34 };

export function Demo() {
  const [items, setItems] = useState(DEFAULT_ITEMS);
  const [labels, setLabels] = useState<string[]>(DEFAULT_LABELS);
  const [index, setIndex] = useState(0);
  const [focus, setFocus] = useState(0);
  const [after, setAfter] = useState<"tab" | "none">("tab");
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");
  const [pressed, setPressed] = useState(false);
  const [tabFlash, setTabFlash] = useState(false);
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const afterRef = useRef(after);
  afterRef.current = after;

  const done = index >= items.length;

  const flash = (set: (v: boolean) => void, ms: number) => {
    set(true);
    setTimeout(() => set(false), ms);
  };

  // A ref, so fast repeated presses each advance by one
  const indexRef = useRef(0);

  const pasteNext = useCallback(() => {
    flash(setPressed, 140);
    const i = indexRef.current;
    if (i >= items.length) return;
    const next = i + 1;
    indexRef.current = next;
    setIndex(next);
    if (afterRef.current === "tab") {
      flash(setTabFlash, 320);
      setFocus(next);
    } else {
      // "Do nothing": the caret stays put until you'd click the next field
      setFocus(-1);
      setTimeout(() => setFocus(f => (f === -1 ? next : f)), 500);
    }
  }, [items.length]);

  const reset = useCallback(() => {
    indexRef.current = 0;
    setIndex(0);
    setFocus(0);
  }, []);

  const applyDraft = useCallback(() => {
    const parsed = draft.split("\n").map(s => s.trim()).filter(Boolean).slice(0, MAX_ITEMS);
    setEditing(false);
    if (parsed.length) {
      setItems(parsed);
      setLabels(parsed.join("\n") === DEFAULT_ITEMS.join("\n") ? DEFAULT_LABELS : []);
    }
    reset();
  }, [draft, reset]);

  const startEditing = () => {
    setDraft(items.join("\n"));
    setEditing(true);
    setTimeout(() => textareaRef.current?.select(), 0);
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
      } else if (k === "r" && index > 0) {
        e.preventDefault();
        reset();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [editing, index, pasteNext, applyDraft, reset]);

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

        <div className="grid md:grid-cols-[1fr_1.15fr]">
          {/* Clipboard tape */}
          <div className="p-5 sm:p-7">
            <div className="mb-3.5 flex items-center justify-between font-mono text-[12px] uppercase tracking-[.08em] text-ink-3">
              <span>Your clipboard</span>
              <button
                type="button"
                onClick={editing ? applyDraft : startEditing}
                className="normal-case tracking-normal text-ink-2 underline underline-offset-[3px] hover:text-ink"
              >
                {editing ? "Done" : "Use my own list"}
              </button>
            </div>

            <div className="rounded-md border border-line bg-tape py-1.5 font-mono text-[15px]">
              {editing ? (
                <textarea
                  ref={textareaRef}
                  value={draft}
                  onChange={e => setDraft(e.target.value)}
                  spellCheck={false}
                  aria-label="Your list, one item per line"
                  className="min-h-[188px] w-full resize-y bg-transparent px-4 py-2 leading-relaxed text-ink outline-none"
                />
              ) : (
                <ol>
                  {items.map((t, i) => {
                    const used = i < index;
                    const next = i === index;
                    return (
                      <li
                        key={`${i}-${t}`}
                        className="grid grid-cols-[34px_1fr] items-center border-b border-dashed border-line px-4 py-2.5 last:border-b-0"
                      >
                        <span className="text-[12px] text-ink-3">{String(i + 1).padStart(2, "0")}</span>
                        <span className="relative min-w-0">
                          {/* Ghost left behind once an item has been pasted */}
                          <span className={`block truncate ${used ? "text-ink-3 line-through decoration-1 opacity-50" : "invisible"}`}>
                            {t}
                          </span>
                          {!used && (
                            <span className="absolute inset-0 flex items-center">
                              <motion.span
                                layoutId={`item-${i}`}
                                transition={spring}
                                className={`max-w-full truncate rounded-sm ${next ? "-mx-1 bg-marker px-1 py-0.5 text-marker-ink" : ""}`}
                              >
                                {t}
                              </motion.span>
                            </span>
                          )}
                        </span>
                      </li>
                    );
                  })}
                </ol>
              )}
            </div>

            <button
              type="button"
              onClick={pasteNext}
              aria-label="Paste the next item (Ctrl+Shift+V)"
              className="group mt-6 flex gap-2"
            >
              {["Ctrl", "Shift", "V"].map(k => (
                <span
                  key={k}
                  className={`grid h-[50px] place-items-center rounded-[10px] border font-mono text-[15px] font-semibold transition-all duration-75 ${
                    k === "V" ? "min-w-[54px]" : "min-w-[76px]"
                  } ${
                    pressed
                      ? "translate-y-1 border-ink border-b bg-marker text-marker-ink"
                      : "border-line-2 border-b-[5px] bg-card group-hover:border-ink-3"
                  }`}
                >
                  {k}
                </span>
              ))}
            </button>
            <p className="mt-3.5 text-[14px] text-ink-2">
              {editing ? (
                <>Paste or type a list, one item per line (up to 8). Then press <b className="font-semibold">Ctrl+Shift+V</b>.</>
              ) : (
                <>Press <b className="font-semibold">Ctrl+Shift+V</b> on your keyboard (yes, on this page) or tap the keys.</>
              )}
            </p>
          </div>

          {/* Form */}
          <div className="border-t border-dashed border-line-2 p-5 sm:p-7 md:border-l md:border-t-0">
            <div className="mb-3.5 font-mono text-[12px] uppercase tracking-[.08em] text-ink-3">A form somewhere</div>
            <div className="grid gap-3.5">
              {items.map((t, i) => {
                const filled = i < index;
                const focused = focus === i && !editing;
                return (
                  <div key={`${i}-${t}`}>
                    <label className="mb-1.5 block text-[13px] text-ink-2">{labels[i] ?? `Field ${i + 1}`}</label>
                    <div
                      className={`flex h-[46px] items-center overflow-hidden whitespace-nowrap rounded-lg border bg-paper px-3.5 text-[16px] transition-[border-color,box-shadow] ${
                        focused ? "border-ink shadow-[0_0_0_3px_rgb(var(--marker)/.7)]" : "border-line-2"
                      }`}
                    >
                      {filled && (
                        <motion.span layoutId={`item-${i}`} transition={spring} className="truncate">
                          {t}
                        </motion.span>
                      )}
                      {focused && <span className="ml-0.5 h-5 w-[1.5px] animate-blink bg-ink" />}
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
                <motion.p
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  className="mt-4 text-[15px] text-ink-2"
                >
                  That&apos;s the whole idea.{" "}
                  <button type="button" onClick={reset} className="text-ink underline underline-offset-[3px]">
                    Start over
                  </button>{" "}
                  (Ctrl+Shift+R in the app)
                </motion.p>
              )}
            </AnimatePresence>
          </div>
        </div>
      </div>
    </LayoutGroup>
  );
}
