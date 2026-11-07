"use client";
import { GroupManagement, FriendRequests, GroupInvitations } from "./GroupManagement";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { Users, ArrowRight, UserPlus, Leaf, Sprout } from "lucide-react";
import { PlanActivityDialog } from "./PlanActivityDialog";
import { SharedGardenPreview } from "./SharedGardenPreview";
import { useParams, useRouter } from "next/navigation";
import {
  request,
  profile,
  group,
  friend,
  member,
  activity,
  invite,
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
} from "./ui";
async function loadSocial() {
  const [groups, friends] = await Promise.all([
    request(group.array(), "/groups"),
    request(friend.array(), "/friends"),
  ]);
  return { groups, friends };
}
export default function Friends() {
  const view = useResource(loadSocial),
    action = useAction(),
    friendAction = useAction();
  const refreshSocial = view.refresh;
  useEffect(() => {
    window.addEventListener("jomo:social-updated", refreshSocial);
    return () => window.removeEventListener("jomo:social-updated", refreshSocial);
  }, [refreshSocial]);
  const [token, setToken] = useState(""),
    [friendId, setFriendId] = useState("");
  if (!view.data)
    return (
      <ResourceState
        loading={view.loading}
        error={view.error}
        retry={view.refresh}
      />
    );
  return (
    <>
      <div className="j-garden-title">
        <Heading eyebrow="BETTER WITH A LITTLE COMPANY" title="Your circle.">
          <p>
            Gardens grow better within sight of each other. Make a plan, share a
            little time, and grow together.
          </p>
        </Heading>
        <span className="j-tag">{view.data.friends.length} friends</span>
      </div>
      <p className="j-section-note">
        A little more connection, a little less scrolling. Your real friends and
        private groups live here.
      </p>
      <FriendRequests />
      <GroupInvitations />
      <div className="j-two">
        <div>
          {view.data.friends.length ? (
            <div className="j-friend-grid">
              {view.data.friends.map((person) => (
                <Panel className="j-friend-card" key={person.id}>
                  <div className="j-person-heading">
                    <span className="j-person-avatar">
                      {person.display_name.slice(0, 1)}
                    </span>
                    <div>
                      <h3>{person.display_name}</h3>
                      <small className="j-mono">@{person.username}</small>
                    </div>
                  </div>
                  <p>Good company for your next offline moment.</p>
                  <div className="j-row">
                    <Link className="j-button" href="/garden?groups=1#garden-groups">
                      Plan together
                    </Link>
                    <Link className="j-button secondary" href="/garden?groups=1#garden-groups">
                      Invite to a group <ArrowRight aria-hidden="true" />
                    </Link>
                  </div>
                </Panel>
              ))}
            </div>
          ) : (
            <Panel className="j-social-empty">
              <Users aria-hidden="true" />
              <h2>There’s room for your people.</h2>
              <p>
                Start with a friend, a private group,
                <br />
                and one small plan away from the screen.
              </p>
              <Link className="j-button" href="/friends/groups/create">
                Create a group <ArrowRight aria-hidden="true" />
              </Link>
            </Panel>
          )}
          <br />
          <Panel title="Your shared spaces">
            {view.data.groups.length ? (
              view.data.groups.map((item) => (
                <Link
                  className="j-moment"
                  key={item.id}
                  href={`/friends/groups/${item.id}`}
                >
                  <span className="j-soft-icon">
                    <Sprout aria-hidden="true" />
                  </span>
                  <div>
                    <strong>{item.name}</strong>
                    <small>Open your private group</small>
                  </div>
                </Link>
              ))
            ) : (
              <Empty>Your first group is waiting to be planted.</Empty>
            )}
          </Panel>
        </div>
        <div>
          <Panel title="Add a friend">
            <p>
              Use their JOMO profile ID to send a request. Email search is not
              connected yet.
            </p>
            <form
              className="j-form"
              onSubmit={(event) => {
                event.preventDefault();
                void friendAction.run(async () => {
                  const receiver_id = z
                    .string()
                    .uuid("Enter a valid JOMO profile ID.")
                    .parse(friendId.trim());
                  await request(success, "/friend-requests", "post", {
                    receiver_id,
                  });
                  setFriendId("");
                }, "Friend request sent.");
              }}
            >
              <label>
                Friend’s profile ID
                <input
                  required
                  value={friendId}
                  onChange={(event) => setFriendId(event.target.value)}
                  placeholder="Their JOMO profile ID"
                />
              </label>
              <Submit pending={friendAction.pending}>
                <UserPlus aria-hidden="true" /> Send request
              </Submit>
              <Feedback action={friendAction} />
            </form>
          </Panel>
          <div id="join-group">
            <Panel title="Have a group invitation?">
              <p>Bring your code. We’ll make a little room.</p>
              <form
                className="j-form"
                onSubmit={(event) => {
                  event.preventDefault();
                  void action.run(async () => {
                    const clean = z
                      .string()
                      .trim()
                      .min(16)
                      .max(200)
                      .parse(token);
                    await request(
                      success,
                      "/group-invites/accept",
                      "post", { token: clean },
                    );
                    setToken("");
                    view.refresh();
                  }, "Invitation accepted. Your groups have been refreshed.");
                }}
              >
                <label>
                  Invitation code
                  <input
                    required
                    autoComplete="off"
                    maxLength={200}
                    value={token}
                    onChange={(event) => setToken(event.target.value)}
                  />
                </label>
                <div className="j-row">
                  <Submit pending={action.pending}>
                    Join group <ArrowRight aria-hidden="true" />
                  </Submit>
                  <button
                    type="button"
                    className="j-button secondary"
                    onClick={() => setToken("")}
                  >
                    Clear code
                  </button>
                </div>
                <Feedback action={action} />
              </form>
            </Panel>
          </div>
          <Panel title="A thought for today">
            <Leaf aria-hidden="true" />
            <p>
              Whatever you do today, leave a little space for the people beside
              you.
            </p>
          </Panel>
        </div>
      </div>
    </>
  );
}
const groupForm = z.object({
  name: z.string().trim().min(1).max(80),
  description: z.string().trim().max(2000),
});
export function CreateGroup() {
  const router = useRouter(),
    action = useAction(),
    [name, setName] = useState(""),
    [description, setDescription] = useState("");
  return (
    <>
      <Heading
        eyebrow="Make a little group"
        title="Good things start together."
      />
      <Panel title="Create your group">
        <form
          className="j-form"
          onSubmit={(event) => {
            event.preventDefault();
            void action.run(async () => {
              const input = groupForm.parse({ name, description });
              const created = await request(group, "/groups", "post", {
                ...input,
                visibility: "invite_only",
              });
              router.push(`/garden?group=${created.id}`);
            });
          }}
        >
          <label>
            Group name
            <input
              required
              maxLength={80}
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>
          <label>
            A little about your circle
            <textarea
              maxLength={2000}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
          </label>
          <p>Your circle comes with its own private shared garden.</p>
          <Submit pending={action.pending}>Create group</Submit>
          <Feedback action={action} />
          <Link href="/garden?groups=1#garden-groups">Back to gardens</Link>
        </form>
      </Panel>
    </>
  );
}
export function GroupDetails() {
  const { groupId } = useParams<{ groupId: string }>(),
    router = useRouter();
  const load = useCallback(async () => {
    const [details, members, activities, me] = await Promise.all([
      request(group, `/groups/${groupId}`),
      request(member.array(), `/groups/${groupId}/members`),
      request(
        activity.array(),
        `/activities?group_id=${encodeURIComponent(groupId)}`,
      ),
      request(profile, "/users/me"),
    ]);
    return { details, members, activities, me };
  }, [groupId]);
  const view = useResource(load),
    action = useAction(),
    [code, setCode] = useState(""),
    [expires, setExpires] = useState("");
  if (!view.data)
    return (
      <ResourceState
        loading={view.loading}
        error={view.error}
        retry={view.refresh}
      />
    );
  return (
    <>
      <Link className="j-mono" href="/garden?groups=1#garden-groups">
        ← Your groups
      </Link>
      <br />
      <br />
      <div className="j-garden-title">
        <Heading eyebrow="YOUR SQUAD" title={view.data.details.name}>
          <p>
            {view.data.details.description ||
              "A little circle of people, growing something good together."}
          </p>
        </Heading>
        <PlanActivityDialog groupId={groupId} label="Plan something together" />
      </div>
      <div className="j-two">
        <SharedGardenPreview groupId={groupId} />
        <div>
          <Panel title="Who is growing">
            <div className="j-moment-list">
              {view.data.members.map((person) => (
                <div className="j-moment" key={person.user_id}>
                  <span className="j-person-avatar">
                    {(person.display_name || person.username || "J").slice(
                      0,
                      1,
                    )}
                  </span>
                  <div>
                    <strong>
                      {person.display_name || person.username || "Group member"}
                    </strong>
                    <small>
                      {person.role === "owner" ? "Founder" : person.role}
                    </small>
                  </div>
                </div>
              ))}
            </div>
          </Panel>
          <Panel title="In your group">
            {view.data.activities.length ? (
              view.data.activities.map((item) => (
                <Link
                  className="j-moment"
                  key={item.id}
                  href={`/activities/${item.id}`}
                >
                  <span className="j-soft-icon">
                    <Leaf aria-hidden="true" />
                  </span>
                  <div>
                    <strong>{item.title}</strong>
                    <small>
                      {item.category} · {item.duration_minutes} min planned
                    </small>
                    <span className="j-tag">
                      {item.status.replaceAll("_", " ")}
                    </span>
                  </div>
                </Link>
              ))
            ) : (
              <Empty>
                No shared plans yet. Start with one unhurried moment.
              </Empty>
            )}
          </Panel>
        </div>
      </div>
      <div className="j-two">
        <Panel title="A little room for someone new">
          <p>
            Invite a friend into {view.data.details.name}. Codes last 72 hours,
            with up to 10 uses. Share only with people you want in your group.
          </p>
          <button
            className="j-button"
            disabled={action.pending || !view.data.members.some(person => person.user_id === view.data?.me.id && ["owner", "admin"].includes(person.role))}
            onClick={() =>
              void action.run(async () => {
                const response = await request(
                  invite,
                  `/groups/${groupId}/invites`,
                  "post",
                  { expires_in_hours: 72, max_uses: 10 },
                );
                if (!response.invite_token)
                  throw new Error("No invite code returned. Try again.");
                setCode(response.invite_token);
                setExpires(response.expires_at);
              })
            }
          >
            Generate invitation <UserPlus aria-hidden="true" />
          </button>
          {code && (
            <>
              <p className="j-output">{code}</p>
              <p>
                <small>Expires {dateTime(expires)}</small>
              </p>
              <button
                className="j-button secondary"
                disabled={action.pending}
                onClick={() =>
                  void action.run(async () => {
                    if (!navigator.clipboard)
                      throw new Error(
                        "Clipboard unavailable. Select and copy the code above.",
                      );
                    await navigator.clipboard.writeText(code);
                  }, "Invitation copied.")
                }
              >
                Copy invitation
              </button>
            </>
          )}
          <Feedback action={action} />
        </Panel>
        <Panel title="Something worth keeping">
          <p>
            Your shared garden belongs to this group. Your personal garden
            always stays yours.
          </p>
          <Link href="/garden?view=personal" className="j-button secondary">
            Visit your own garden <ArrowRight aria-hidden="true" />
          </Link>
        </Panel>
      </div>
      <GroupManagement groupId={groupId} />
      <details className="j-panel">
        <summary>Leave this group</summary>
        <p>
          You lose access to its shared garden. Your personal garden stays
          yours.
        </p>
        <button
          className="j-button danger"
          disabled={action.pending}
          onClick={() =>
            void action.run(async () => {
              await request(success, `/groups/${groupId}/leave`, "post");
              router.push("/garden?groups=1#garden-groups");
            })
          }
        >
          Leave group
        </button>
        <Feedback action={action} />
      </details>
    </>
  );
}
