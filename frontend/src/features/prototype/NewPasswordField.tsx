"use client";

import { useEffect, useId, useRef, useState } from "react";
import type { PasswordAssessment } from "@/lib/passwordStrength";

export function useNewPasswordAssessment(value: string, email = "", enabled = true) {
  const workerRef = useRef<Worker | null>(null);
  const sequence = useRef(0);
  const [checked, setChecked] = useState<{
    value: string; email: string; result: PasswordAssessment;
  } | null>(null);
  useEffect(() => () => {
    workerRef.current?.terminate();
    workerRef.current = null;
  }, []);
  useEffect(() => {
    if (!enabled || !value) return;
    let active = true;
    let worker: Worker | null = null;
    const id = ++sequence.current;
    const failed = () => {
      if (active) setChecked({ value, email, result: {
        score: 0, label: "Unavailable", accepted: false,
        length: Array.from(value).length,
        hint: "The strength checker could not load. Please refresh and try again.",
      } });
    };
    const receive = (event: MessageEvent<{ id: number; result: PasswordAssessment }>) => {
      if (active && event.data.id === id) setChecked({ value, email, result: event.data.result });
    };
    const timer = window.setTimeout(() => {
      // Dictionaries load on demand in a worker so scoring does not block typing.
      try {
        workerRef.current ??= new Worker(new URL("../../lib/passwordStrength.worker.ts", import.meta.url));
        worker = workerRef.current;
        worker.addEventListener("message", receive);
        worker.addEventListener("error", failed);
        worker.postMessage({ id, password: value, email });
      } catch { failed(); }
    }, 180);
    return () => {
      active = false;
      window.clearTimeout(timer);
      worker?.removeEventListener("message", receive);
      worker?.removeEventListener("error", failed);
    };
  }, [value, email, enabled]);
  return enabled && checked?.value === value && checked.email === email ? checked.result : null;
}

export function NewPasswordField({ value, onChange, assessment, label = "Password" }: {
  value: string;
  onChange: (value: string) => void;
  assessment: PasswordAssessment | null;
  label?: string;
}) {
  const id = useId();
  const [visible, setVisible] = useState(false);
  const status = !value ? "Not entered" : assessment?.label ?? "Checking…";
  return <div className="j-password-field">
    <label htmlFor={id}>{label}</label>
    <div className="j-password-entry">
      <input id={id} name="password" type={visible ? "text" : "password"}
        required maxLength={1024} autoComplete="new-password" spellCheck={false}
        autoCapitalize="none" value={value}
        aria-describedby={`${id}-rules ${id}-hint`}
        onChange={event => onChange(event.target.value)} />
      <button type="button" className="j-password-toggle" aria-controls={id}
        aria-pressed={visible} onClick={() => setVisible(!visible)}>
        {visible ? "Hide" : "Show"}
      </button>
    </div>
    <p id={`${id}-rules`} className="j-password-rules">
      At least 15 characters. Spaces and passphrases are welcome. Aim for Strong or Very strong.
    </p>
    <div className="j-password-strength" data-score={assessment?.score ?? 0}>
      <meter min={0} max={4} low={2} high={3} optimum={4} value={assessment?.score ?? 0}
        aria-label="Estimated password strength" aria-valuetext={status} />
      <span className="j-password-label" role="status" aria-live="polite">{status}</span>
    </div>
    <p id={`${id}-hint`} className="j-password-hint">
      {assessment?.hint ?? (value ? "Checking your password on this device…" : "Try several unrelated words or use your password manager’s generator.")}
    </p>
    <small>Strength is an estimate, not a check against every data breach. Paste and password managers are supported.</small>
  </div>;
}
