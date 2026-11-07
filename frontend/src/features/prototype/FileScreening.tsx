"use client";

import Image from "next/image";
import { useRef, useState } from "react";
import { apiClient } from "@/services/apiClient";
import { z } from "@/services/prototype";
import { Feedback, Panel, Submit, useAction } from "./ui";
import { LoadingScene } from "@/components/common/LoadingScene";

const common = {
  status: z.literal("completed"),
  ner_enabled: z.boolean(),
  flagged_fields: z.number().int().nonnegative(),
  detected_categories: z.string().array(),
  limitations: z.string().array().min(1),
};
const resultSchema = z.discriminatedUnion("format", [
  z.object({ ...common, format: z.literal("image"), engine: z.literal("presidio-image-redactor"),
    media_type: z.literal("image/png"), filename: z.literal("redacted.png"),
    content_base64: z.string().min(1).max(3400000).regex(/^[A-Za-z0-9+/]*={0,2}$/) }),
  z.object({ ...common, format: z.literal("csv"), engine: z.literal("presidio-structured"),
    media_type: z.literal("text/csv;charset=utf-8"), filename: z.literal("redacted.csv"), content: z.string() }),
  z.object({ ...common, format: z.literal("json"), engine: z.literal("presidio-structured"),
    media_type: z.literal("application/json"), filename: z.literal("redacted.json"), content: z.string() }),
]);
type ScanResult = z.infer<typeof resultSchema>;

function download(result: ScanResult) {
  const content = result.format === "image"
    ? Uint8Array.from(atob(result.content_base64), character => character.charCodeAt(0))
    : result.content;
  const url = URL.createObjectURL(new Blob([content], { type: result.media_type }));
  const link = document.createElement("a");
  link.href = url;
  link.download = result.filename;
  link.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1000);
}

export default function FileScreening({ kind }: { kind: "image" | "structured" }) {
  const [file, setFile] = useState<File | null>(null);
  const [consent, setConsent] = useState(false);
  const [result, setResult] = useState<ScanResult | null>(null);
  const input = useRef<HTMLInputElement>(null);
  const generation = useRef(0);
  const controller = useRef<AbortController | null>(null);
  const action = useAction();
  const image = kind === "image";

  function clear() {
    generation.current += 1;
    controller.current?.abort();
    setFile(null);
    setResult(null);
    setConsent(false);
    if (input.current) input.current.value = "";
  }

  return <Panel title={image ? "Redact personal information in an image" : "Screen a CSV or JSON file"}>
    <p>{image
      ? "Upload a PNG or JPEG. Presidio uses OCR to find possible personal information in visible text and covers the detected regions."
      : "Upload UTF-8 CSV or JSON. Presidio Structured replaces detected JSON values or entire sensitive CSV columns."}</p>
    <p><small>{image
      ? "Maximum 2 MiB and 4 million pixels. This checks text, not faces."
      : "Maximum 256 KiB. CSV supports 1–200 data rows and 50 columns. Headers and JSON keys are preserved and are not screened."}</small></p>
    <p>Files are processed for this request and are not retained in Supabase. Image OCR may use temporary processing files. Review every result before sharing.</p>
    <form className="j-form" onSubmit={event => {
      event.preventDefault();
      const version = ++generation.current;
      setResult(null);
      void action.run(async () => {
        if (!file || !consent) throw new Error("Choose a file and agree to submit it for screening.");
        const limit = image ? 2 * 1024 * 1024 : 256 * 1024;
        if (!file.size || file.size > limit) throw new Error(image ? "Choose an image up to 2 MiB." : "Choose a CSV or JSON file up to 256 KiB.");
        const extension = file.name.split(".").pop()?.toLowerCase();
        let endpoint: string, mediaType: string;
        if (image) {
          if (!["png", "jpg", "jpeg"].includes(extension || "")) throw new Error("Choose a PNG or JPEG image.");
          endpoint = "/ai/privacy/image";
          mediaType = extension === "png" ? "image/png" : "image/jpeg";
        } else {
          if (extension !== "csv" && extension !== "json") throw new Error("Choose a .csv or .json file.");
          endpoint = `/ai/privacy/structured?format=${extension}`;
          mediaType = extension === "csv" ? "text/csv" : "application/json";
        }
        controller.current = new AbortController();
        try {
          const response = await apiClient.post(endpoint, await file.arrayBuffer(), {
            headers: { "Content-Type": mediaType, "X-Screening-Consent": "true" },
            timeout: 90000, signal: controller.current.signal,
          });
          const parsed = z.object({ data: resultSchema, request_id: z.string() }).parse(response.data);
          if ((parsed.data.format === "image") !== image) throw new Error("The server returned the wrong file type.");
          if (version === generation.current) setResult(parsed.data);
        } catch (error) {
          if (version === generation.current) throw error;
        }
      });
    }}>
      <label>{image ? "Image to redact" : "Data file to screen"}
        <input ref={input} type="file" required disabled={action.pending}
          accept={image ? ".png,.jpg,.jpeg,image/png,image/jpeg" : ".csv,.json,text/csv,application/json"}
          onChange={event => { generation.current += 1; setFile(event.target.files?.[0] ?? null); setResult(null); setConsent(false); }} />
      </label>
      <label className="j-checkbox"><input type="checkbox" required checked={consent} disabled={action.pending}
        onChange={event => setConsent(event.target.checked)} />I agree to send this file to JOMO for this screening request.</label>
      <div className="j-row"><Submit pending={action.pending}>{image ? "Redact image" : "Screen data file"}</Submit>
        <button className="j-button secondary" type="button" onClick={clear}>Clear file and result</button></div>
      {action.pending && <LoadingScene variant="inline" section="Privacy Guardian"
        title={image ? "Looking a little closer." : "A thoughtful check, field by field."}
        description={image ? "Reading visible text and checking for personal details…" : "Checking your data file for personal information…"} />}
      <Feedback action={action} />
    </form>
    {result && <section aria-label="File screening result" aria-live="polite">
      <h3>{result.flagged_fields ? "Potential personal information detected" : "No obvious identifiers detected"}</h3>
      <p>Engine: Microsoft {result.format === "image" ? "Presidio Image Redactor" : "Presidio Structured"}.
        {" "}{result.flagged_fields} {result.format === "image" ? "redacted regions" : result.format === "csv" ? "flagged columns" : "flagged values"}.
        {!result.ner_enabled && " The language model is unavailable; Presidio used pattern detection."}</p>
      {result.detected_categories.length > 0 && <p>Categories: {result.detected_categories.join(", ")}</p>}
      {result.format === "image"
        ? <Image src={`data:image/png;base64,${result.content_base64}`} alt="Redacted image: review before sharing" width={960} height={640}
            unoptimized style={{ width: "100%", height: "auto", maxHeight: 600, objectFit: "contain" }} />
        : <pre className="j-output" style={{ maxHeight: 400, overflow: "auto", whiteSpace: "pre-wrap" }}>{result.content}</pre>}
      <p><button type="button" className="j-button" onClick={() => download(result)}>Download redacted {result.format === "image" ? "image" : "file"}</button></p>
      <ul>{result.limitations.map(limitation => <li key={limitation}>{limitation}</li>)}</ul>
    </section>}
  </Panel>;
}
