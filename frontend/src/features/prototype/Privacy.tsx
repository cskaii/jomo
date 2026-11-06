"use client";
import { useRef, useState } from "react";
import { request, screening, z } from "@/services/prototype";
import { useAction, Feedback, Panel, Heading, Submit } from "./ui";
import { startEvilDuckGame } from "@/features/privacy-game/EvilDuckGame";
export default function Privacy() {
  const [text, setText] = useState(""),
    [consent, setConsent] = useState(false),
    [result, setResult] = useState<z.infer<typeof screening> | null>(null);
  const action = useAction(),
    generation = useRef(0);
  return (
    <>
      <Heading
        eyebrow="A thoughtful pause before sharing"
        title="Keep personal things personal."
      >
        <p>
          Check text you choose to submit for possible sensitive information.
        </p>
      </Heading>
      <Panel title="You decide what gets checked">
        <p>
          JOMO screens content that you choose to submit to the Privacy
          Guardian. It does not currently monitor messages in other
          applications.
        </p>
        <p>
          This sends your text to JOMO for screening. The screening service
          records the categories it detects, not your original text. This page
          does not save your text or results to browser storage.
        </p>
        <p>
          <small>
            This prototype checks for personal information only. Harmful-content
            screening is not available. A result with no detections is not a
            guarantee of safety.
          </small>
        </p>
      </Panel>
      <Panel title="Spot the trick before the duck does">
        <p>Four quick, fictional challenges about location clues, oversharing, impersonation, and screenshots. A wrong choice shows how a careless share can spoil a practice garden and how to handle it safely.</p>
        <button className="j-button" type="button" onClick={startEvilDuckGame}>Play a privacy challenge</button>
      </Panel>
      <Panel>
        <form
          className="j-form"
          onSubmit={(event) => {
            event.preventDefault();
            const version = ++generation.current;
            setResult(null);
            void action.run(async () => {
              if (!consent)
                throw new Error("Agree to submit this text before screening.");
              const input = z
                .string()
                .min(1)
                .max(10000)
                .refine((value) => value.trim().length > 0, "Enter some text.")
                .parse(text);
              const response = await request(
                screening,
                "/ai/privacy/text",
                "post",
                { text: input, checks: ["pii"], language: "en" },
              );
              if (version === generation.current) setResult(response);
            });
          }}
        >
          <label>
            Text to check
            <textarea
              rows={7}
              required
              maxLength={10000}
              value={text}
              disabled={action.pending}
              onChange={(event) => {
                generation.current += 1;
                setText(event.target.value);
                setResult(null);
              }}
              placeholder="Paste only the text you want to check…"
            />
          </label>
          <small>{text.length.toLocaleString()} / 10,000 characters</small>
          <label className="j-checkbox">
            <input
              type="checkbox"
              checked={consent}
              disabled={action.pending}
              onChange={(event) => setConsent(event.target.checked)}
            />
            I agree to send this text to JOMO for this screening request.
          </label>
          <div className="j-row">
            <Submit pending={action.pending}>
              Check for personal information
            </Submit>
            <button
              className="j-button secondary"
              type="button"
              onClick={() => {
                generation.current += 1;
                setText("");
                setResult(null);
                setConsent(false);
              }}
            >
              Clear text and result
            </button>
          </div>
          <Feedback action={action} />
        </form>
      </Panel>
      {result && (
        <Panel
          title={
            result.has_potential_pii
              ? "Possible personal information found"
              : "No obvious identifiers detected"
          }
        >
          <p role="status">
            Screening status: {result.status}. Automated screening can miss
            sensitive information.
          </p>
          <p>Screening engine: {result.engine === "presidio"
            ? `Microsoft Presidio (${result.ner_enabled ? "language model and pattern detection" : "pattern detection"})`
            : "Personal information check was not requested"}.</p>
          {result.detections.length > 0 && (
            <div className="j-table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Category</th>
                    <th>Character range</th>
                    <th>Detector score</th>
                  </tr>
                </thead>
                <tbody>
                  {result.detections.map((item, index) => (
                    <tr key={`${item.start}-${index}`}>
                      <td>{item.entity_type}</td>
                      <td>
                        {item.start}–{item.end} (end exclusive)
                      </td>
                      <td>{Math.round(item.score * 100)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
          <h3>Redacted draft — review before sharing</h3>
          <p className="j-output">{result.redacted_text}</p>
          <button
            className="j-button secondary"
            disabled={action.pending}
            onClick={() =>
              void action.run(async () => {
                if (!navigator.clipboard)
                  throw new Error(
                    "Clipboard unavailable. Select and copy the draft above.",
                  );
                await navigator.clipboard.writeText(result.redacted_text);
              }, "Redacted draft copied.")
            }
          >
            Copy redacted draft
          </button>
          <ul>
            {result.limitations.map((value, index) => (
              <li key={index}>{value}</li>
            ))}
          </ul>
          <p>
            <small>
              Character positions count Unicode characters. Detector scores are
              not safety probabilities.
            </small>
          </p>
          <Feedback action={action} />
        </Panel>
      )}
    </>
  );
}
