"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import { z } from "zod";
import { Heading, Panel } from "./ui";

const notice = z.object({ organisation: z.string(), contact_email: z.string(), photo_retention_days: z.number() });
export default function PrivacyNotice() {
  const [details, setDetails] = useState<z.infer<typeof notice> | null>(null);
  useEffect(() => {
    const controller = new AbortController();
    void fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL || "/api/v1"}/privacy-notice`, { cache: "no-store", signal: controller.signal })
      .then(response => { if (!response.ok) throw new Error(); return response.json(); })
      .then(data => setDetails(notice.parse(data))).catch(() => {});
    return () => controller.abort();
  }, []);
  return <div className="j-privacy-notice">
    <Link href="/insights">Back to JOMO</Link><Heading eyebrow="Your data, your choices" title="Privacy notice" />
    <Panel title="Who operates JOMO"><p>{details?.organisation || "The JOMO operator"} operates JOMO. Notice version: 7 November 2026.</p>
      {details?.contact_email && /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(details.contact_email)
        ? <p>For privacy questions, withdrawal, access or correction requests, contact <a href={`mailto:${details.contact_email}`}>{details.contact_email}</a>.</p>
        : <p>A public privacy contact has not been configured. Contact the project organiser who invited you; JOMO is not ready for unrestricted public launch.</p>}
    </Panel>
    <Panel title="What we collect and why">
      <ul><li>Email and authentication details to create and secure your account. Supabase manages password hashing.</li>
        <li>Display name, preferences, screen-time entries and activity records to provide Insights, activities, friends, rewards and gardens.</li>
        <li>Group membership and shared activity evidence to support collaboration. Group members can see shared garden history and eligible participants can review submitted evidence.</li>
        <li>A one-time approximate location only if you enable the setting and expressly share it for an active activity. No route tracking or background location collection.</li>
        <li>Optional activity photos only when you submit them with consent. Avoid faces, documents, addresses, or other people’s personal data unless you have an appropriate basis to share them.</li>
        <li>Guardian submissions to detect and redact possible identifiers. Screening is requested by you, can miss information, and does not certify content as safe. Submitted content is processed for the request; the screening history stores event metadata rather than raw submitted content.</li></ul>
      <p>The website does not automatically monitor other applications or infer offline time from screen-time totals.</p>
    </Panel>
    <Panel title="Choices, viewers and security"><p>Location and photo sharing are optional. Choose an activity with a suitable alternative when you do not want to share evidence. Do not submit unnecessary or third-party personal information. Location never automatically grants rewards.</p>
      <p>Coordinates are restricted to your account; other members receive no coordinates. Photos are stored privately, re-encoded to remove embedded metadata, and previewed by the uploader or eligible group reviewers through short-lived links. A photo cannot prove that an activity happened.</p>
      <p>Use Settings to withdraw location sharing (which removes saved check-ins), request photo removal, clear screening history, download your account data, or delete your account. You can correct manual screen-time records in Insights. Withdrawal may prevent a particular evidence-based completion method; personal self-reported and group-confirmation activities remain available.</p>
    </Panel>
    <Panel title="Retention and deletion"><p>Check-in coordinates expire after 24 hours. Photos expire after {details?.photo_retention_days ?? 7} days. Notification and screening-event metadata is retained for 30 days. Physical cleanup runs on a daily schedule and can occur after access expires; storage deletion retries on subsequent runs when a provider is unavailable. A failed schedule or deletion backlog can delay removal further. Expired photos cannot be previewed through JOMO.</p>
      <p>Account deletion removes live account and personal records. Other members retain their shared garden, purchases and activity history; former-member ledger attribution is removed. Photo deletion is queued durably. Existing signed photo links can remain usable briefly until they expire or the object is removed. Hosted backups follow the operator’s/provider’s retention arrangements rather than disappearing instantly.</p>
      <p>Security and consent records are retained while reasonably needed to operate and protect the account and demonstrate handling of requests. Contact the privacy operator about retained records, access/disclosure history, correction or complaints.</p>
      <p>Minimal photo-storage and preview-access events are retained for up to 366 days to support security and access/disclosure-history requests. They do not contain the photo, coordinates, or signed link.</p>
    </Panel>
    <Panel title="Service providers and overseas processing"><p>JOMO uses Supabase for authentication, database and private file storage, and Vercel for the website and backend. Their selected hosting regions and support arrangements may involve processing outside Singapore.</p>
      <p>The operator must verify the selected regions, vendor agreements, safeguards for overseas transfers, privacy contact, incident-response process and backup retention before public launch. This notice does not by itself establish Singapore PDPA compliance.</p>
    </Panel>
  </div>;
}
