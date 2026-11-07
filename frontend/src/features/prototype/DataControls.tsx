"use client";
import Link from "next/link";
import { request, success, z } from "@/services/prototype";
import { Panel, useAction, Feedback } from "./ui";

export function DataControls() {
  const action = useAction();
  return <Panel title="Your personal data">
    <p>Download your account records, remove stored proof photos, or clear screening history. <Link href="/privacy">Read the privacy notice and find the privacy contact.</Link></p>
    <div className="j-row"><button className="j-button secondary" disabled={action.pending} onClick={() => void action.run(async () => {
      const data = await request(z.record(z.string(), z.unknown()), "/users/me/export");
      const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], { type: "application/json" }));
      const link = document.createElement("a"); link.href = url; link.download = "jomo-my-data.json"; link.click();
      window.setTimeout(() => URL.revokeObjectURL(url), 1000);
    }, "Your account-data download is ready.")}>Download my data</button>
      <button className="j-button secondary" disabled={action.pending} onClick={() => {
        if (!window.confirm("Remove access to all your saved proof photos and queue their deletion? Activity records and earned rewards remain.")) return;
        void action.run(async () => { await request(success, "/users/me/proof-images", "delete"); }, "Photo access removed; private file deletion is queued.");
      }}>Remove my proof photos</button>
      <button className="j-button secondary" disabled={action.pending} onClick={() => {
        if (!window.confirm("Clear your screening-event history?")) return;
        void action.run(async () => { await request(success, "/users/me/screening-history", "delete"); }, "Screening history cleared.");
      }}>Clear screening history</button>
    </div><Feedback action={action} />
  </Panel>;
}
