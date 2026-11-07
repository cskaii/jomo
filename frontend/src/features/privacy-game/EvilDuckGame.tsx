"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { ShieldCheck, X } from "lucide-react";
import { canAutoChallenge, quizDelay, quizStorageKey, QUIZ_SETTLE_MS } from "@/lib/privacyChallenge";

type Round = {
  name: string;
  scene: string;
  preview: { heading: string; lines: string[] };
  prompt: string;
  choices: { text: string; safe: boolean; clue?: string }[];
  lesson: string;
};

const rounds: Round[] = [
  {
    name: "Location leak",
    scene: "A social post · after school",
    preview: { heading: "Mina's post · just now", lines: ["📷 A smiling selfie beside the blue school gate", "Background: Westbrook School crest · Pine St bus stop", "📍 Location tag: Westbrook · sharing publicly"] },
    prompt: "The photo looks cute. What should you check before posting it?",
    choices: [
      { text: "Post it now — the school sign is just in the background.", safe: false, clue: "The school crest and the bus-stop name can identify where you are." },
      { text: "Crop the school sign and location clues, then ask before posting.", safe: true },
      { text: "Add a live location tag so friends can find the photo.", safe: false, clue: "A live location tag can tell strangers where you are right now." },
    ],
    lesson: "Before sharing a photo, check signs, uniforms, landmarks, reflections, and location tags. Share only with people you trust, and avoid posting your live location.",
  },
  {
    name: "Over-sharing",
    scene: "A new social profile · preview",
    preview: { heading: "@sunny_skater · public profile", lines: ["Name: Jamie Lee · age 13", "School: Westbrook Middle · Grade 8", "Call me: 555-0148 · Home: 14 Pine Street", "Usually home alone after 4 pm 🏠"] },
    prompt: "The profile asks for a bio. Which version protects the person best?",
    choices: [
      { text: "Include a phone number so classmates can message anytime.", safe: false, clue: "A public phone number can invite unwanted calls and messages." },
      { text: "List the school, home street, and when the family is away.", safe: false, clue: "School, address, and routine together can expose where someone lives and when they are alone." },
      { text: "Use a nickname and leave contact, school, address, and schedule private.", safe: true },
    ],
    lesson: "Keep phone numbers, home addresses, school details, identity documents, and personal schedules off public profiles. You can leave a profile field blank.",
  },
  {
    name: "AI impersonation",
    scene: "A direct message · new account",
    preview: { heading: "Messages · 'Riley (new account)'", lines: ["Riley: hey, new phone! Need your login code fast", "Riley: it's urgent, don't call, just send it here", "Riley: also send a photo of your ID to verify"] },
    prompt: "A familiar-looking account says it is your friend. What is the safest next step?",
    choices: [
      { text: "Send the one-time sign-in code to prove it is really me.", safe: false, clue: "A sign-in code can give someone access to your account. Real support and friends should not ask for it." },
      { text: "Pause, verify through a different trusted channel, and report the account if unsure.", safe: true },
      { text: "Send a photo of an ID because the account says there is an emergency.", safe: false, clue: "Urgency and requests for ID or codes are warning signs. A convincing voice, face, or profile can be faked with AI." },
    ],
    lesson: "Slow down when a message creates urgency or asks for money, codes, passwords, or ID. Verify using a separate contact method you already trust, and report suspicious accounts.",
  },
  {
    name: "Screenshot trap",
    scene: "A screenshot · ready to share",
    preview: { heading: "Screenshot · ready to forward", lines: ["Notifications: mail for alex@example.test", "Private chat: 'I'm home alone until 6'", "Account screen: alex_s · recovery phone •••• 0148"] },
    prompt: "Before forwarding this screenshot, what is the best move?",
    choices: [
      { text: "Forward it — the private chat is small and hard to read.", safe: false, clue: "Zooming in can reveal private messages, email addresses, account names, or notification previews." },
      { text: "Check the whole image, remove private details, and get permission before sharing.", safe: true },
      { text: "Keep the notification banner; it helps show the screenshot is real.", safe: false, clue: "Notification banners can reveal private messages, names, and account details." },
    ],
    lesson: "Inspect the whole screenshot, including status bars, notifications, chat previews, and account screens. Crop or cover sensitive details, and get permission before sharing someone else's conversation.",
  },
];

function duckRound() {
  return rounds[Math.floor(Math.random() * rounds.length)];
}

export function EvilDuckGame({ userId }: { userId: string }) {
  const [open, setOpen] = useState(false);
  const [round, setRound] = useState<Round>(rounds[0]);
  const [result, setResult] = useState<"safe" | "tricked" | null>(null);
  const [damage, setDamage] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const dialog = useRef<HTMLElement>(null);
  const lastShown = useRef(0);
  const lastActivity = useRef(0);
  const settledAt = useRef(0);
  const storageKey = quizStorageKey(userId);

  const remember = useCallback(() => {
    lastShown.current = Date.now();
    try { localStorage.setItem(storageKey, String(lastShown.current)); } catch { /* Use the in-memory cooldown if storage is blocked. */ }
  }, [storageKey]);

  const startRound = useCallback(() => {
    remember();
    setRound(duckRound());
    setSelected(null);
    setResult(null);
    setOpen(true);
  }, [remember]);

  const close = useCallback(() => {
    remember();
    setOpen(false);
    setResult(null);
    setSelected(null);
  }, [remember]);

  useEffect(() => {
    const launch = () => startRound();
    window.addEventListener("jomo:evil-duck", launch);
    return () => window.removeEventListener("jomo:evil-duck", launch);
  }, [startRound]);

  useEffect(() => {
    if (open) return;
    if (!settledAt.current) settledAt.current = Date.now() + QUIZ_SETTLE_MS;
    lastActivity.current = Date.now();
    const active = () => { lastActivity.current = Date.now(); };
    const schedule = () => {
      if (timer.current) clearTimeout(timer.current);
      const now = Date.now();
      try { lastShown.current = Number(localStorage.getItem(storageKey)) || lastShown.current; } catch { /* Keep the in-memory value. */ }
      const wait = Math.max(quizDelay(lastShown.current, now), settledAt.current - now, 0);
      timer.current = setTimeout(attempt, Math.max(wait, 1000));
    };
    const attempt = () => {
      const now = Date.now();
      try { lastShown.current = Number(localStorage.getItem(storageKey)) || lastShown.current; } catch { /* Keep the in-memory value. */ }
      if (quizDelay(lastShown.current, now) > 0) { schedule(); return; }
      const focused = document.activeElement;
      const ready = canAutoChallenge({
        visible: document.visibilityState === "visible" && document.hasFocus(),
        active: now - lastActivity.current < 90_000,
        editing: focused instanceof HTMLElement && !!focused.closest("input, textarea, select, [contenteditable='true']"),
        busy: !!document.querySelector("[aria-modal='true'], [aria-busy='true'], .j-loading-placeholder")
          || /^\/(focus|activities)(\/|$)/.test(window.location.pathname),
      });
      if (ready) startRound();
      else timer.current = setTimeout(attempt, 15_000);
    };
    const changed = (event: StorageEvent) => { if (event.key === storageKey) schedule(); };
    window.addEventListener("pointerdown", active);
    window.addEventListener("pointermove", active, { passive: true });
    window.addEventListener("keydown", active);
    window.addEventListener("focus", active);
    window.addEventListener("storage", changed);
    schedule();
    return () => {
      if (timer.current) clearTimeout(timer.current);
      window.removeEventListener("pointerdown", active);
      window.removeEventListener("pointermove", active);
      window.removeEventListener("keydown", active);
      window.removeEventListener("focus", active);
      window.removeEventListener("storage", changed);
    };
  }, [open, startRound, storageKey]);

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    const priorOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    dialog.current?.focus();
    const escape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        close();
        return;
      }
      if (event.key === "Tab" && dialog.current) {
        const focusable = dialog.current.querySelectorAll<HTMLElement>("button:not(:disabled), a[href], [tabindex]:not([tabindex='-1'])");
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (event.shiftKey && (document.activeElement === first || document.activeElement === dialog.current)) {
          event.preventDefault();
          last?.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
          event.preventDefault();
          first?.focus();
        }
      }
    };
    window.addEventListener("keydown", escape);
    return () => {
      document.body.style.overflow = priorOverflow;
      window.removeEventListener("keydown", escape);
      previous?.focus();
    };
  }, [open, close]);

  function choose(index: number) {
    if (result) return;
    setSelected(index);
    if (round.choices[index].safe) setResult("safe");
    else {
      setDamage((value) => Math.min(value + 1, 3));
      setResult("tricked");
    }
  }

  return (
    <>
      {open && (
        <div className="j-duck-backdrop" role="presentation">
          <section ref={dialog} tabIndex={-1} className="j-duck-game" role="dialog" aria-modal="true" aria-labelledby="duck-title">
            <button className="j-duck-close" onClick={close} aria-label="Close challenge"><X aria-hidden="true" /></button>
            <div className="j-duck-content">
              <div className={`j-duck-garden j-duck-damage-${damage}`} aria-label={`Practice garden, ${damage} damage marks`}>
                <span className="j-duck-sun" />
                <span className="j-duck-hill" />
                <span className="j-duck-flower j-duck-flower-one">✿</span>
                <span className="j-duck-flower j-duck-flower-two">✿</span>
                <span className="j-duck-flower j-duck-flower-three">✿</span>
                {damage > 0 && <span className="j-duck-weed">♣</span>}
                {damage > 1 && <span className="j-duck-weed j-duck-weed-two">♣</span>}
                {damage > 2 && <span className="j-duck-puddle">〰</span>}
                <span className="j-duck-mascot" role="img" aria-label="The mischievous Evil Duck" />
                <span className="j-duck-garden-caption">{damage ? "The duck's mischief is showing" : "Your little practice garden"}</span>
              </div>
              <div className="j-duck-quiz">
                <p className="j-duck-eyebrow">EVIL DUCK · {round.name.toUpperCase()}</p>
                <h2 id="duck-title">{result === "tricked" ? "Quack! A clue slipped through." : result === "safe" ? "Nice catch. The garden is safe." : "A little privacy pop quiz."}</h2>
                {!result ? <>
                  <p className="j-duck-scene">{round.scene}</p>
                  <div className={`j-duck-evidence j-duck-evidence-${round.name.toLowerCase().replaceAll(" ", "-")}`}>
                    <strong>{round.preview.heading}</strong>
                    {round.preview.lines.map((line) => <span key={line}>{line}</span>)}
                    <small>FICTIONAL PRACTICE EXAMPLE</small>
                  </div>
                  <p>{round.prompt}</p>
                  <div className="j-duck-choices" role="group" aria-label="Choose the safest response">
                    {round.choices.map((choice, index) => <button key={choice.text} className="j-duck-choice" onClick={() => choose(index)}>{choice.text}</button>)}
                  </div>
                  <button className="j-duck-dismiss" onClick={close}>Maybe later</button>
                </> : <div className={`j-duck-feedback ${result}`} role="status">
                  <p>{result === "tricked" ? round.choices[selected ?? 0].clue : "You spotted the safer choice. The duck didn't get to spoil this patch."}</p>
                  <p>{round.lesson}</p>
                  <div className="j-duck-next-row">
                    <span>{damage} {damage === 1 ? "mischief mark" : "mischief marks"} · practice garden only</span>
                    <button className="j-button" onClick={startRound}>Next challenge</button>
                  </div>
                  <button className="j-duck-dismiss" onClick={close}>Close</button>
                </div>}
                <p className="j-duck-privacy-note"><ShieldCheck aria-hidden="true" /> All profiles and messages are fictional. No personal information is requested or shared.</p>
              </div>
            </div>
          </section>
        </div>
      )}
      <span className="j-duck-screenreader" aria-live="polite">{open ? "Evil Duck privacy challenge opened" : ""}</span>
    </>
  );
}

export function startEvilDuckGame() {
  window.dispatchEvent(new Event("jomo:evil-duck"));
}
