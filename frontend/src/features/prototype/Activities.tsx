"use client";
import { ActivityEvidence } from "./ActivityEvidence";
import { useCallback, useState } from "react";
import Link from "next/link";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  request,
  activity,
  participant,
  member,
  group,
  profile,
  session,
  success,
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
  useVisibleRefresh,
} from "./ui";
async function loadActivities() {
  const items = await request(activity.array(), "/activities");
  return { items };
}
export default function Activities({ embedded = false }: { embedded?: boolean }) {
  const view = useResource(loadActivities),
    [filter, setFilter] = useState("all");
  useVisibleRefresh(view.refresh, 60000);
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
    [description, setDescription] = useState(params.get("description") ?? "");
  const [category, setCategory] = useState(params.get("category") ?? "outdoor"),
    [duration, setDuration] = useState(params.get("minutes") ?? "30");
  const [evidence, setEvidence] = useState("");
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
                proof_requirement: evidence || (groupId ? "photo_or_group_confirmation" : "none"),
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
              onChange={(event) => { setGroupId(event.target.value); setEvidence(""); }}
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
          <label>Completion evidence<select value={evidence} onChange={event => setEvidence(event.target.value)}>
            <option value="">{groupId ? "Photo or group confirmation" : "Self-reported activity time"}</option>
            <option value="photo">Photo evidence</option>
            {groupId && <option value="group_confirmation">Group confirmation without a photo</option>}
          </select></label>
          <p>
            <small>
              {groupId
                ? "Group confirmation is requested after your activity."
                : "Personal completion is self-reported and based on recorded activity time."}{" "}
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
    const members = item.group_id ? await request(member.array(), `/groups/${item.group_id}/members`) : [];
    const manager = item.created_by === me.id || members.some(person => person.user_id === me.id && person.status === "active" && ["owner", "admin"].includes(person.role));
    return { item, people, me, manager };
  }, [activityId]);
  const view = useResource(load);
  useVisibleRefresh(view.refresh);
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
    try {
      if (path.endsWith("/join")) await request(participant, path, "post", body);
      else if (path.endsWith("/leave"))
        await request(success, path, "post", body);
      else await request(activity, path, "post", body);
    } finally {
      // A lost response does not establish whether the server committed the action.
      view.refresh();
    }
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
            joined && (item.group_id || item.created_by === me.id) && (
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
          {active && joined && view.data.manager && (
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
        <ActivityEvidence
          activityId={activityId}
          item={item}
          changed={view.refresh}
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
            Personal activity time is self-reported. Group evidence is reviewed by another eligible participant.
            Rewards use server-recorded elapsed time, eligibility limits and one transaction per completion.
            A photo or location alone does not prove completion.
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
