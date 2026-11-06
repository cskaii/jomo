"use client";
import { useCallback, useState } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  request,
  activity,
  participant,
  group,
  profile,
  activityMission,
  session,
  success,
  proof,
  checkIn,
  upload,
  z,
  dateTime,
} from "@/services/prototype";
import {
  useResource,
  useAction,
  Feedback,
  ResourceState,
  Panel,
  Heading,
  Empty,
  Submit,
} from "./ui";
async function loadActivities() {
  const items = await request(activity.array(), "/activities");
  const ideas = await request(
    activityMission.array(),
    "/ai/missions/recommend",
    "post",
    {},
  ).catch(() => null);
  return { items, ideas };
}
export default function Activities({ embedded = false }: { embedded?: boolean }) {
  const view = useResource(loadActivities),
    [filter, setFilter] = useState("all");
  if (!view.data)
    return (
      <ResourceState
        loading={view.loading}
        error={view.error}
        retry={view.refresh}
      />
    );
  const items = view.data.items.filter(
    (item) => filter === "all" || item.status === filter,
  );
  return (
    <>
      <Heading level={embedded ? 2 : 1} eyebrow="Go make a memory" title={embedded ? "Activities for your garden." : "Less feed. More feeling."}>
        <p>Choose something that makes today a little more yours.</p>
      </Heading>
      <div className="j-spread">
        <label>
          Show{" "}
          <select
            className="j-select"
            value={filter}
            onChange={(event) => setFilter(event.target.value)}
          >
            <option value="all">All activities</option>
            {["published", "active", "awaiting_proof", "completed"].map(
              (value) => (
                <option key={value} value={value}>
                  {value.replaceAll("_", " ")}
                </option>
              ),
            )}
          </select>
        </label>
        <Link className="j-button" href="/activities/create">
          + Create activity
        </Link>
      </div>
      <div className="j-grid">
        {items.map((item) => (
          <Panel key={item.id}>
            <span className="j-tag">
              {item.category} · {item.status.replaceAll("_", " ")}
            </span>
            {embedded ? <h3>{item.title}</h3> : <h2>{item.title}</h2>}
            <p>{item.description}</p>
            <p>
              <small>
                {item.duration_minutes} minutes · {item.visibility} · capacity{" "}
                {item.max_participants}
              </small>
            </p>
            <Link href={`/activities/${item.id}`}>See activity →</Link>
          </Panel>
        ))}
      </div>
      {!items.length && (
        <Empty>No activities in this view. Start with one small plan.</Empty>
      )}
      <Panel title="A few ideas to get you going">
        {view.data.ideas === null ? (
          <p>Ideas are unavailable. You can still create your own activity.</p>
        ) : view.data.ideas.length ? (
          <div className="j-grid">
            {view.data.ideas.map((idea) => (
              <div key={idea.id}>
                <h3>{idea.title}</h3>
                <p>{idea.description}</p>
                <small>{idea.duration_minutes} minutes · curated idea</small>
                <p>
                  <Link
                    href={`/activities/create?title=${encodeURIComponent(idea.title)}&category=${encodeURIComponent(idea.category)}&minutes=${idea.duration_minutes}`}
                  >
                    Make this your plan →
                  </Link>
                </p>
              </div>
            ))}
          </div>
        ) : (
          <Empty>No catalogue suggestions available.</Empty>
        )}
      </Panel>
    </>
  );
}
const creation = z.object({
  title: z.string().trim().min(1).max(120),
  description: z.string().trim().max(2000),
  category: z.string().trim().min(1).max(40),
  duration_minutes: z.coerce.number().int().min(1).max(480),
  max_participants: z.coerce.number().int().min(1).max(100),
  group_id: z.string(),
});
async function loadGroups() {
  return request(group.array(), "/groups");
}
export function CreateActivity() {
  const params = useSearchParams(),
    router = useRouter(),
    action = useAction(),
    groups = useResource(loadGroups);
  const [title, setTitle] = useState(params.get("title") ?? ""),
    [description, setDescription] = useState("");
  const [category, setCategory] = useState(params.get("category") ?? "outdoor"),
    [duration, setDuration] = useState(params.get("minutes") ?? "30");
  const [capacity, setCapacity] = useState("10"),
    [groupId, setGroupId] = useState(params.get("group") ?? "");
  return (
    <>
      <Heading eyebrow="One small plan" title="Make time for something good." />
      <Panel title="Your activity">
        <form
          className="j-form"
          onSubmit={(event) => {
            event.preventDefault();
            void action.run(async () => {
              const input = creation.parse({
                title,
                description,
                category,
                duration_minutes: duration,
                max_participants: capacity,
                group_id: groupId,
              });
              if (groupId && !groups.data?.some((item) => item.id === groupId))
                throw new Error("Choose a circle you belong to.");
              const created = await request(activity, "/activities", "post", {
                ...input,
                group_id: groupId || null,
                visibility: groupId ? "group" : "personal",
                location_required: false,
                proof_requirement: groupId ? "group_confirmation" : "none",
              });
              router.push(`/activities/${created.id}`);
            });
          }}
        >
          <label>
            Activity title
            <input
              required
              maxLength={120}
              value={title}
              onChange={(event) => setTitle(event.target.value)}
            />
          </label>
          <label>
            What will you do?
            <textarea
              maxLength={2000}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
          <label>
            Category
            <input
              required
              maxLength={40}
              list="activity-categories"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
            />
            <datalist id="activity-categories">
              {["outdoor", "social", "creative", "wellness"].map((value) => (
                <option key={value} value={value} />
              ))}
            </datalist>
          </label>
          <label>
            Minutes
            <input
              required
              type="number"
              min="1"
              max="480"
              value={duration}
              onChange={(event) => setDuration(event.target.value)}
            />
          </label>
          <label>
            Participant limit
            <input
              required
              type="number"
              min="1"
              max="100"
              value={capacity}
              onChange={(event) => setCapacity(event.target.value)}
            />
          </label>
          <label>
            Who is this for?
            <select
              value={groupId}
              onChange={(event) => setGroupId(event.target.value)}
            >
              <option value="">Just me</option>
              {groups.data?.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </label>
          {groups.error && (
            <p role="alert">
              Circles could not load. Personal activities are still available.{" "}
              <button type="button" onClick={groups.refresh}>
                Retry circles
              </button>
            </p>
          )}
          <p>
            <small>
              {groupId
                ? "Group confirmation is requested after your activity."
                : "Personal photo verification needs real storage before rewards can be demonstrated."}{" "}
              Location is optional.
            </small>
          </p>
          <Submit pending={action.pending}>Create activity</Submit>
          <Feedback action={action} />
          <Link href="/activities">Back to activities</Link>
        </form>
      </Panel>
    </>
  );
}
export function ActivityDetails() {
  const { activityId } = useParams<{ activityId: string }>(),
    router = useRouter(),
    action = useAction();
  const load = useCallback(async () => {
    const [item, people, me] = await Promise.all([
      request(activity, `/activities/${activityId}`),
      request(participant.array(), `/activities/${activityId}/participants`),
      request(profile, "/users/me"),
    ]);
    return { item, people, me };
  }, [activityId]);
  const view = useResource(load);
  if (!view.data)
    return (
      <ResourceState
        loading={view.loading}
        error={view.error}
        retry={view.refresh}
      />
    );
  const { item, people, me } = view.data,
    mine = people.find((person) => person.user_id === me.id);
  const joined = mine && mine.status !== "left",
    active = item.status === "active";
  async function mutate(path: string, body?: unknown) {
    if (path.endsWith("/join")) await request(participant, path, "post", body);
    else if (path.endsWith("/leave"))
      await request(success, path, "post", body);
    else await request(activity, path, "post", body);
    view.refresh();
  }
  return (
    <>
      <Link href="/activities">← Activities</Link>
      <Heading eyebrow={item.category} title={item.title}>
        <p>{item.description}</p>
      </Heading>
      <Panel>
        <div className="j-spread">
          <span className="j-tag">{item.status.replaceAll("_", " ")}</span>
          <span>
            {item.duration_minutes} min ·{" "}
            {people.filter((person) => person.status !== "left").length}/
            {item.max_participants} people
          </span>
        </div>
        {item.started_at && <p>Started {dateTime(item.started_at)}</p>}
        <div className="j-row">
          {!joined && ["published", "active"].includes(item.status) && (
            <button
              className="j-button"
              disabled={action.pending}
              onClick={() =>
                void action.run(
                  () => mutate(`/activities/${activityId}/join`),
                  "Joined activity.",
                )
              }
            >
              Join activity
            </button>
          )}
          {item.status === "published" &&
            (item.group_id || item.created_by === me.id) && (
              <button
                className="j-button"
                disabled={action.pending}
                onClick={() =>
                  void action.run(
                    () =>
                      mutate(`/activities/${activityId}/start`, {
                        client_started_at: new Date().toISOString(),
                      }),
                    "Activity started. You can now open a voluntary focus timer.",
                  )
                }
              >
                Start activity
              </button>
            )}
          {active && joined && (
            <button
              className="j-button"
              disabled={action.pending}
              onClick={() =>
                void action.run(async () => {
                  const focus = await request(
                    session,
                    `/activities/${activityId}/focus-sessions`,
                    "post",
                  );
                  router.push(`/focus/${focus.id}`);
                })
              }
            >
              Open focus session
            </button>
          )}
          {active && joined && (
            <button
              className="j-button secondary"
              disabled={action.pending}
              onClick={() =>
                void action.run(
                  () => mutate(`/activities/${activityId}/end`),
                  "Activity ended. Submit any required evidence below.",
                )
              }
            >
              End activity for participants
            </button>
          )}
          {joined && ["published", "active"].includes(item.status) && (
            <button
              className="j-button secondary"
              disabled={action.pending}
              onClick={() =>
                void action.run(
                  () => mutate(`/activities/${activityId}/leave`),
                  "You left this activity.",
                )
              }
            >
              Leave activity
            </button>
          )}
        </div>
        <Feedback action={action} />
        <p>
          <small>
            Start your activity, then open a voluntary focus timer when you are
            ready. Ending this activity affects all participants.
          </small>
        </p>
      </Panel>
      <Panel title="Participation">
        <div className="j-table-wrap">
          <table>
            <thead>
              <tr>
                <th>Participant</th>
                <th>Status</th>
                <th>Eligible minutes</th>
                <th>Awarded points</th>
              </tr>
            </thead>
            <tbody>
              {people.map((person, index) => (
                <tr key={person.id}>
                  <td>
                    {person.user_id === me.id
                      ? "You"
                      : `Participant ${index + 1}`}
                  </td>
                  <td>{person.status}</td>
                  <td>{person.eligible_minutes}</td>
                  <td>{person.points_awarded}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <p>
          <small>
            Points appear here after your participation has been verified.
          </small>
        </p>
      </Panel>
      {joined && (
        <Evidence
          activityId={activityId}
          item={item}
          enabled={["awaiting_proof", "under_review", "completed"].includes(
            item.status,
          )}
        />
      )}
      <Panel title="Completion status">
        <p>
          {mine?.points_awarded
            ? `The server reports ${mine.points_awarded} points for your participation.`
            : "No reward is reported for your participation yet."}
        </p>
        <p>
          <small>
            Completion verification is still being connected for this prototype.
            Submitted evidence does not guarantee a reward. Check your garden
            history for confirmed points.
          </small>
        </p>
        <button className="j-button secondary" onClick={view.refresh}>
          Refresh status
        </button>
        <Link href="/garden"> Open garden history →</Link>
      </Panel>
    </>
  );
}
function Evidence({
  activityId,
  item,
  enabled,
}: {
  activityId: string;
  item: z.infer<typeof activity>;
  enabled: boolean;
}) {
  const action = useAction(),
    [consent, setConsent] = useState(false),
    [file, setFile] = useState<File | null>(null);
  const [submitted, setSubmitted] = useState<z.infer<typeof proof> | null>(
      null,
    ),
    [peerProof, setPeerProof] = useState("");
  const [checkedIn, setCheckedIn] = useState(false);
  return (
    <>
      <Panel title="Optional location check-in">
        <p>
          One approximate check-in for this activity. No continuous tracking.
          Stored evidence can be removed below.
        </p>
        <label className="j-checkbox">
          <input
            type="checkbox"
            checked={consent}
            onChange={(event) => setConsent(event.target.checked)}
          />{" "}
          I agree to send an approximate activity check-in to JOMO.
        </label>
        <div className="j-row">
          <button
            className="j-button secondary"
            disabled={!consent || action.pending || item.status !== "active"}
            onClick={() =>
              void action.run(async () => {
                if (!navigator.geolocation)
                  throw new Error(
                    "Location is unavailable. You can continue without sharing it.",
                  );
                const position = await new Promise<GeolocationPosition>(
                  (resolve, reject) =>
                    navigator.geolocation.getCurrentPosition(
                      resolve,
                      () =>
                        reject(
                          new Error(
                            "Location was denied or unavailable. You can continue without it.",
                          ),
                        ),
                      {
                        enableHighAccuracy: false,
                        timeout: 10000,
                        maximumAge: 0,
                      },
                    ),
                );
                const result = await request(
                  checkIn,
                  `/activities/${activityId}/check-ins`,
                  "post",
                  {
                    latitude:
                      Math.round(position.coords.latitude * 1000) / 1000,
                    longitude:
                      Math.round(position.coords.longitude * 1000) / 1000,
                    accuracy_meters: position.coords.accuracy,
                    captured_at: new Date(position.timestamp).toISOString(),
                    consent: true,
                  },
                );
                if (!result.accepted)
                  throw new Error("The server did not accept this check-in.");
                setCheckedIn(true);
              }, "Approximate check-in saved. No ongoing location sharing is active.")
            }
          >
            Share one check-in
          </button>
          <button
            className="j-button secondary"
            disabled={action.pending}
            onClick={() =>
              void action.run(async () => {
                await request(
                  success,
                  `/activities/${activityId}/check-ins/me`,
                  "delete",
                );
                setCheckedIn(false);
                setConsent(false);
              }, "Stored check-in removed.")
            }
          >
            Remove my stored check-in
          </button>
        </div>
        {checkedIn && <p>Check-in saved for this visit.</p>}
        <Feedback action={action} />
      </Panel>
      <Panel title="Activity evidence">
        <p>
          Prefer a photo of the activity or object. A selfie is not required.
          Group confirmation is an alternative where permitted.
        </p>
        {!enabled && <p>End the activity before submitting evidence.</p>}
        <div className="j-form">
          <label>
            Optional activity photo · JPEG/PNG/WebP, up to 10 MB
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp"
              disabled={action.pending || !enabled}
              onChange={(event) => setFile(event.target.files?.[0] ?? null)}
            />
          </label>
          <p>
            <small>
              Photo would be sent to JOMO storage for review. Private storage
              access, metadata removal, viewers and retention must be finalized
              before using real personal photos.
            </small>
          </p>
          <button
            className="j-button secondary"
            disabled={
              !file ||
              !enabled ||
              action.pending ||
              !["photo", "photo_or_group_confirmation"].includes(
                item.proof_requirement,
              )
            }
            onClick={() =>
              void action.run(async () => {
                if (
                  !file ||
                  !["image/jpeg", "image/png", "image/webp"].includes(
                    file.type,
                  ) ||
                  file.size < 1 ||
                  file.size > 10 * 1024 * 1024
                )
                  throw new Error(
                    "Choose a JPEG, PNG or WebP image up to 10 MB.",
                  );
                const signed = await request(
                  upload,
                  `/activities/${activityId}/proofs/upload-url`,
                  "post",
                  {
                    file_name: file.name,
                    mime_type: file.type,
                    file_size_bytes: file.size,
                  },
                );
                if (!/^https:\/\//.test(signed.upload_url))
                  throw new Error(
                    "Photo uploads are not connected yet. Your photo was not submitted.",
                  );
                const sent = await fetch(signed.upload_url, {
                  method: "PUT",
                  headers: { "Content-Type": file.type },
                  body: file,
                  credentials: "omit",
                });
                if (!sent.ok)
                  throw new Error("Upload failed. No proof was registered.");
                setSubmitted(
                  await request(
                    proof,
                    `/activities/${activityId}/proofs`,
                    "post",
                    { proof_type: "photo", storage_key: signed.storage_key },
                  ),
                );
              })
            }
          >
            Upload and submit photo
          </button>
          {item.group_id &&
            ["group_confirmation", "photo_or_group_confirmation"].includes(
              item.proof_requirement,
            ) && (
              <button
                className="j-button"
                disabled={!enabled || action.pending}
                onClick={() =>
                  void action.run(async () => {
                    setSubmitted(
                      await request(
                        proof,
                        `/activities/${activityId}/proofs`,
                        "post",
                        { proof_type: "group_confirmation" },
                      ),
                    );
                  })
                }
              >
                Request group confirmation
              </button>
            )}
          <button
            className="j-button secondary"
            disabled={action.pending}
            onClick={() =>
              void action.run(async () => {
                setSubmitted(
                  await request(proof, `/activities/${activityId}/proofs/me`),
                );
              })
            }
          >
            Load my latest proof
          </button>
        </div>
        {submitted && (
          <div className="j-notice">
            <p>
              Proof status: {submitted.status}. This is not a separate reward
              confirmation.
            </p>
            <p className="j-output">Proof reference: {submitted.id}</p>
            <small>
              Share this reference with a circle peer if confirmation is
              pending.
            </small>
            <button
              className="j-button secondary"
              disabled={action.pending}
              onClick={() =>
                void action.run(async () => {
                  await request(success, `/proofs/${submitted.id}`, "delete");
                  setSubmitted(null);
                }, "Proof record removed. Previously awarded rewards are subject to server audit rules.")
              }
            >
              Delete proof record
            </button>
          </div>
        )}
        {item.group_id && (
          <form
            className="j-form"
            onSubmit={(event) => {
              event.preventDefault();
              void action.run(async () => {
                const reference = z.string().uuid().parse(peerProof.trim());
                await request(success, `/proofs/${reference}/confirm`, "post", {
                  decision: "confirm",
                  comment: "Confirmed by circle peer",
                });
              }, "Confirmation submitted. Refresh participation and garden history for server results.");
            }}
          >
            <label>
              A peer’s proof reference
              <input
                required
                value={peerProof}
                onChange={(event) => setPeerProof(event.target.value)}
              />
            </label>
            <p>
              <small>
                Confirm only an activity you participated in with this peer.
                Peer verification is available for local demonstration only.
              </small>
            </p>
            <Submit pending={action.pending}>Confirm peer participation</Submit>
          </form>
        )}
        <Feedback action={action} />
      </Panel>
    </>
  );
}
