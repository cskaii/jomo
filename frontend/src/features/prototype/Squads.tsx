"use client";
import { useCallback, useState } from "react";
import Link from "next/link";
import { ArrowRight, Plus } from "lucide-react";
import { request, group, member, activity, success, z } from "@/services/prototype";
import { useResource, useAction, Feedback, Submit, ResourceState, Heading, Panel } from "./ui";

async function loadGroups() { return request(group.array(), "/groups"); }
export function GroupGardenManagement({ onChanged }: { onChanged: () => void }) {
  const view = useResource(loadGroups);
  const action = useAction();
  const [token, setToken] = useState("");
  if (!view.data) return <ResourceState loading={view.loading} error={view.error} retry={view.refresh} />;
  return <>
    <div className="j-garden-title">
      <Heading level={2} eyebrow="GOOD COMPANY · OPTIONAL" title="Grow a garden together.">
        <p>Your personal garden works on its own. Create or join a group whenever you want company.</p>
      </Heading>
      <Link className="j-button" href="/friends/groups/create"><Plus aria-hidden="true" />Create a group garden</Link>
    </div>
    <div className="j-two">
      <div>{view.data.length ? view.data.map(item => <GroupCard key={item.id} id={item.id} name={item.name} description={item.description} />) : <Panel title="Your own pace, your own space"><p>You do not need a group to enjoy your personal garden. Shared gardens will appear here when you join one.</p></Panel>}</div>
      <Panel title="Have an invitation?">
        <p>Use an invitation code to join their shared garden.</p>
        <form onSubmit={event => {
          event.preventDefault();
          void action.run(async () => {
            const clean = z.string().trim().min(16).max(200).parse(token);
            await request(success, `/group-invites/${encodeURIComponent(clean)}/accept`, "post");
            setToken("");
            view.refresh();
            onChanged();
          }, "Invitation accepted. Your garden list is refreshed.");
        }}>
          <label>Invitation code<input required minLength={16} maxLength={200} autoComplete="off" value={token} onChange={event => setToken(event.target.value)} /></label>
          <Submit pending={action.pending}>Join group garden<ArrowRight aria-hidden="true" /></Submit>
          <Feedback action={action} />
        </form>
      </Panel>
    </div>
  </>;
}

function GroupCard({
  id,
  name,
  description,
}: {
  id: string;
  name: string;
  description?: string | null;
}) {
  const load = useCallback(async () => {
    const [people, activities] = await Promise.all([
      request(member.array(), `/groups/${id}/members`),
      request(activity.array(), `/activities?group_id=${id}`),
    ]);
    return { people, activities };
  }, [id]);
  const view = useResource(load);
  return (
    <Panel className="j-squad-card">
      <div className="j-spread">
        <span className="j-tag">Your group</span>
        <span className="j-mono">
          {view.data ? `${view.data.people.length} members` : "Private group"}
        </span>
      </div>
      <h2>{name}</h2>
      <p>
        <em>{description || "One small plan is all it takes."}</em>
      </p>
      {view.data && (
        <>
          <div className="j-member-chips">
            {view.data.people.map((person) => (
              <span className="j-member-chip" key={person.user_id}>
                <span>
                  {(person.display_name || person.username || "J").slice(0, 1)}
                </span>
                {person.display_name || person.username || "Group member"}
              </span>
            ))}
          </div>
          <p className="j-mono">
            {view.data.activities.length} shared{" "}
            {view.data.activities.length === 1 ? "plan" : "plans"} ·{" "}
            {
              view.data.activities.filter((item) => item.status === "active")
                .length
            }{" "}
            active now
          </p>
        </>
      )}
      {view.error && (
        <p className="j-error" role="alert">
          Member details could not load.{" "}
          <button onClick={view.refresh}>Retry</button>
        </p>
      )}
      <div className="j-row">
        <Link className="j-button" href={`/friends/groups/${id}`}>
          Manage group <ArrowRight aria-hidden="true" />
        </Link>
        <Link className="j-button secondary" href={`/garden?group=${id}`}>
          Shared garden
        </Link>
      </div>
    </Panel>
  );
}

