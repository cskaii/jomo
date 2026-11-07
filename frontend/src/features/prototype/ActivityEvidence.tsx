"use client";
import { useCallback, useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { apiClient } from "@/services/apiClient";
import { request, activity, preferences, proof, checkIn, success, z, dateTime } from "@/services/prototype";
import { useResource, useAction, Feedback, Panel, useVisibleRefresh } from "./ui";

async function optional<T>(load: () => Promise<T>): Promise<T | null> {
  try { return await load(); } catch (error) {
    if (z.object({ status: z.literal(404) }).safeParse(error).success) return null;
    throw error;
  }
}
export function ActivityEvidence({ activityId, item, changed }: {
  activityId: string; item: z.infer<typeof activity>; changed: () => void;
}) {
  const load = useCallback(async () => {
    const [prefs, mine, location, review] = await Promise.all([
      request(preferences, "/users/me/preferences"),
      optional(() => request(proof, `/activities/${activityId}/proofs/me`)),
      optional(() => request(checkIn, `/activities/${activityId}/check-ins/me`)),
      request(proof.array(), `/activities/${activityId}/proofs/review`),
    ]);
    return { prefs, mine, location, review };
  }, [activityId]);
  const view = useResource(load); const action = useAction();
  useVisibleRefresh(view.refresh);
  const [locationConsent, setLocationConsent] = useState(false);
  const [photoConsent, setPhotoConsent] = useState(false);
  const [file, setFile] = useState<File | null>(null);
  const [localPreview, setLocalPreview] = useState("");
  const [preview, setPreview] = useState<{ url: string; id: string } | null>(null);
  const [progress, setProgress] = useState(0);
  useEffect(() => {
    if (!file) return;
    const url = URL.createObjectURL(file); const timer = window.setTimeout(() => setLocalPreview(url), 0);
    return () => { window.clearTimeout(timer); URL.revokeObjectURL(url); };
  }, [file]);
  useEffect(() => {
    if (!preview) return;
    const timer = window.setTimeout(() => setPreview(null), 60_000);
    return () => window.clearTimeout(timer);
  }, [preview]);
  const ended = ["awaiting_proof", "under_review", "completed"].includes(item.status);
  const refresh = () => { view.refresh(); changed(); };
  const showPhoto = (id: string) => void action.run(async () => {
    const result = await request(z.object({ url: z.string().url(), expires_in: z.number() }), `/proofs/${id}/preview`);
    setPreview({ id, url: result.url });
  });
  return <>
    {view.error && <p className="j-error" role="alert">Evidence could not refresh: {view.error} <button onClick={view.refresh}>Retry</button></p>}
    <Panel title="Optional one-time location check-in">
      <p>JOMO records one approximate location to support your activity check-in. Only you can access the coordinates; group members do not see them. The record expires after 24 hours and is removed by scheduled cleanup. No continuous tracking, and no coins are awarded just for sharing a location.</p>
      <p><Link href="/privacy">Read the privacy notice</Link>. You can continue without location and use the activity’s other completion method.</p>
      {!view.data?.prefs.location_enabled && <p>Enable optional check-ins in <Link href="/settings">Settings</Link> first. Turning that setting off removes stored check-ins.</p>}
      <label className="j-checkbox"><input type="checkbox" checked={locationConsent} onChange={event => setLocationConsent(event.target.checked)} />I agree to share one approximate location for this activity.</label>
      <div className="j-row"><button className="j-button secondary" disabled={action.pending || !locationConsent || !view.data?.prefs.location_enabled || item.status !== "active"} onClick={() => void action.run(async () => {
        if (!navigator.geolocation) throw new Error("Location is unavailable. Continue without it or use another completion method.");
        const position = await new Promise<GeolocationPosition>((resolve, reject) => navigator.geolocation.getCurrentPosition(resolve, error => reject(new Error(
          error.code === 1 ? "Location permission was denied. Continue without location, or change this site's browser permission if you want to retry." : error.code === 3 ? "Location timed out. Try again outdoors or continue without it." : "Location is unavailable. Continue without it or try again.")), { enableHighAccuracy: false, timeout: 10000, maximumAge: 0 }));
        if (position.coords.accuracy > 1000) throw new Error("The location reading is too imprecise. Try again or continue without sharing it.");
        await request(checkIn, `/activities/${activityId}/check-ins`, "post", {
          latitude: Math.round(position.coords.latitude * 1000) / 1000,
          longitude: Math.round(position.coords.longitude * 1000) / 1000,
          accuracy_meters: position.coords.accuracy, captured_at: new Date(position.timestamp).toISOString(), consent: true,
        }); setLocationConsent(false); refresh();
      }, "One approximate check-in saved. Location sharing has stopped.")}>Share one check-in</button>
        <button className="j-button secondary" disabled={action.pending || !view.data?.location} onClick={() => void action.run(async () => {
          await request(success, `/activities/${activityId}/check-ins/me`, "delete"); refresh();
        }, "Your stored location check-in was removed.")}>Remove my check-in</button></div>
      {view.data?.location && <p role="status">Check-in recorded {view.data.location.captured_at ? dateTime(view.data.location.captured_at) : "for this activity"}. Expires {view.data.location.expires_at ? dateTime(view.data.location.expires_at) : "after 24 hours"}.</p>}
    </Panel>
    <Panel title="Activity evidence">
      <p>{item.group_id ? "Another eligible group participant reviews your evidence. You cannot approve your own submission." : "Personal completion is self-reported and uses recorded activity time. A photo is optional evidence, not automatic verification."}</p>
      {!ended && <p>End the activity before submitting evidence.</p>}
      <p>Photos are private, re-encoded to remove embedded metadata, and retained for the short period in the privacy notice (7 days by default) before scheduled cleanup. Only you and eligible group reviewers receive temporary preview links. Avoid faces, identity documents and other people’s personal information. <Link href="/privacy">Privacy details</Link>.</p>
      {["none", "photo", "photo_or_group_confirmation"].includes(item.proof_requirement) && <div className="j-form">
        <label>Activity photo (JPEG, PNG or WebP; up to 2 MB, 8 megapixels)<input type="file" accept="image/jpeg,image/png,image/webp" disabled={action.pending || !ended} onChange={event => { setFile(event.target.files?.[0] ?? null); setLocalPreview(""); setPhotoConsent(false); }} /></label>
        {file && localPreview && <Image src={localPreview} alt="Your selected activity photo, not yet uploaded" width={480} height={320} unoptimized className="j-proof-image" />}
        <label className="j-checkbox"><input type="checkbox" checked={photoConsent} onChange={event => setPhotoConsent(event.target.checked)} />I have read the photo notice and agree to upload this photo for activity evidence and authorised review.</label>
        <button className="j-button" disabled={!file || !ended || !photoConsent || action.pending || ["accepted", "pending"].includes(view.data?.mine?.status ?? "")} onClick={() => void action.run(async () => {
          if (!file || !["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size > 2 * 1024 * 1024 || file.size < 1) throw new Error("Choose a JPEG, PNG or WebP photo up to 2 MB.");
          setProgress(0);
          const response = await apiClient.post(`/activities/${activityId}/proofs/photo?consent=true`, file, {
            headers: { "Content-Type": file.type }, timeout: 45000,
            onUploadProgress: event => setProgress(Math.round(event.loaded * 100 / (event.total || file.size))),
          });
          proof.parse(response.data.data); setFile(null); setPhotoConsent(false); setLocalPreview(""); refresh();
        }, "Photo uploaded and evidence recorded.")}>Upload and submit photo</button>
        {action.pending && file && <progress aria-label="Photo upload progress" value={progress} max={100} />}
      </div>}
      {item.group_id && ["group_confirmation", "photo_or_group_confirmation"].includes(item.proof_requirement) && <button className="j-button secondary" disabled={!ended || action.pending || ["pending", "accepted"].includes(view.data?.mine?.status ?? "")} onClick={() => void action.run(async () => {
        await request(proof, `/activities/${activityId}/proofs`, "post", { proof_type: "group_confirmation" }); refresh();
      }, "Group confirmation requested. Eligible participants have been notified.")}>Request group confirmation</button>}
      {view.data?.mine && <div className="j-panel"><strong>Your evidence: {view.data.mine.status}</strong><p>Submitted {dateTime(view.data.mine.submitted_at)}.</p>
        {view.data.mine.proof_type === "photo" && <button disabled={action.pending} onClick={() => showPhoto(view.data!.mine!.id)}>Preview photo</button>}
        <button disabled={action.pending} onClick={() => {
          if (!window.confirm("Remove this evidence? Photo deletion is queued; recorded rewards are not duplicated or refunded.")) return;
          void action.run(async () => { await request(success, `/proofs/${view.data!.mine!.id}`, "delete"); setPreview(null); refresh(); }, "Evidence removed; any private photo is queued for deletion.");
        }}>Remove my evidence</button></div>}
      {!!view.data?.review.length && <h3>Evidence awaiting your review</h3>}
      {view.data?.review.map(entry => <div className="j-panel" key={entry.id}><strong>{entry.proof_type === "photo" ? "Photo evidence" : "Group confirmation request"}</strong><p>Submitted {dateTime(entry.submitted_at)}.</p>
        {entry.proof_type === "photo" && <button disabled={action.pending} onClick={() => showPhoto(entry.id)}>View private photo</button>}
        {["confirm", "reject"].map(decision => <button disabled={action.pending} key={decision} onClick={() => void action.run(async () => {
          await request(success, `/proofs/${entry.id}/confirm`, "post", { decision }); setPreview(null); refresh();
        }, decision === "confirm" ? "Evidence approved. Any eligible reward was awarded once." : "Evidence declined. The participant can resubmit.")}>{decision === "confirm" ? "Approve" : "Decline"}</button>)}</div>)}
      {preview && <div><Image src={preview.url} alt="Private activity evidence" width={480} height={320} unoptimized referrerPolicy="no-referrer" className="j-proof-image" /><p>Preview access expires shortly. Do not share the link.</p><button onClick={() => setPreview(null)}>Close preview</button></div>}
      <Feedback action={action} />
    </Panel>
  </>;
}
