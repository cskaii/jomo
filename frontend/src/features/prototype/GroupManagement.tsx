"use client";
import { useCallback, useEffect, useState } from "react";
import { request, member, profile, success, z, dateTime } from "@/services/prototype";
import { Feedback, Panel, useAction, useResource, useVisibleRefresh } from "./ui";

const invitation = z.object({ id: z.string().uuid(), receiver_id: z.string().uuid().nullable(),
  expires_at: z.string(), revoked_at: z.string().nullable(), uses_count: z.number(), max_uses: z.number().nullable() });

export function GroupManagement({ groupId }: { groupId: string }) {
  const load = useCallback(async () => {
    const [me, people] = await Promise.all([request(profile, "/users/me"), request(member.array(), `/groups/${groupId}/members`)]);
    const role = people.find(person => person.user_id === me.id)?.role;
    const invitations = role === "owner" || role === "admin" ? await request(invitation.array(), `/groups/${groupId}/invites`) : [];
    return { me, people, role, invitations };
  }, [groupId]);
  const view = useResource(load); const action = useAction();
  useVisibleRefresh(view.refresh);
  const [receiver, setReceiver] = useState("");
  if (!view.data) return <Panel title="Group management"><p>{view.error || "Loading group permissions…"}</p></Panel>;
  const { people, me, role, invitations } = view.data;
  const mutate = (path: string, method: "post" | "patch" | "delete", data?: unknown) => void action.run(async () => {
    await request(success, path, method, data); view.refresh();
  }, "Group updated.");
  return <Panel title="Group management">
    <p>Your role: {role}. Owners manage membership and ownership. Owners and admins manage invitations.</p>
    {role === "owner" && people.filter(person => person.user_id !== me.id).map(person => <div className="j-panel" key={person.user_id}>
      <strong>{person.display_name || person.username}</strong><p>{person.role}</p><div className="j-row">
        <button disabled={action.pending} onClick={() => mutate(`/groups/${groupId}/members/${person.user_id}`, "patch", { role: person.role === "admin" ? "member" : "admin" })}>{person.role === "admin" ? "Make member" : "Make admin"}</button>
        <button disabled={action.pending} onClick={() => { if (window.confirm("Remove this member? They will lose group access.")) mutate(`/groups/${groupId}/members/${person.user_id}`, "delete"); }}>Remove member</button>
        <button disabled={action.pending} onClick={() => { if (window.confirm("Transfer ownership to this member? You will become an admin.")) mutate(`/groups/${groupId}/transfer-ownership`, "post", { user_id: person.user_id }); }}>Transfer ownership</button>
      </div></div>)}
    {(role === "owner" || role === "admin") && <>
      <form className="j-form" onSubmit={event => { event.preventDefault(); void action.run(async () => {
        await request(z.unknown(), `/groups/${groupId}/invites`, "post", { receiver_id: z.string().uuid().parse(receiver.trim()), max_uses: 1, expires_in_hours: 72 });
        setReceiver(""); view.refresh();
      }, "Private invitation sent to that member's in-app inbox."); }}>
        <label>Invite a member by profile ID<input required value={receiver} onChange={event => setReceiver(event.target.value)} /></label>
        <button type="submit" className="j-button" disabled={action.pending}>Send group invitation</button>
      </form>
      <h3>Invitation history</h3>{invitations.map(item => <div key={item.id} className="j-row"><span>{item.receiver_id ? "Targeted invitation" : "Shared invitation code"} · {item.uses_count}/{item.max_uses ?? "unlimited"} uses · expires {dateTime(item.expires_at)} {item.revoked_at ? "· revoked" : ""}</span>
        {!item.revoked_at && <button disabled={action.pending} onClick={() => mutate(`/groups/${groupId}/invites/${item.id}`, "delete")}>Revoke</button>}</div>)}
    </>}
    <Feedback action={action} />
  </Panel>;
}

const pending = z.object({ id: z.string().uuid(), display_name: z.string(), sender_id: z.string().uuid() });
async function loadRequests() { return request(pending.array(), "/friend-requests"); }
export function FriendRequests() {
  const view = useResource(loadRequests); const action = useAction();
  useVisibleRefresh(view.refresh);
  const refreshRequests = view.refresh;
  useEffect(() => {
    const refresh = () => refreshRequests();
    window.addEventListener("jomo:social-updated", refresh);
    return () => window.removeEventListener("jomo:social-updated", refresh);
  }, [refreshRequests]);
  return <Panel title="Friend requests"><button onClick={view.refresh}>Refresh requests</button>
    {view.error && <p role="alert">{view.error}</p>}
    {!view.data?.length && <p>No pending friend requests.</p>}
    {view.data?.map(item => <div className="j-row" key={item.id}><span>{item.display_name}</span>{["accept", "decline"].map(decision => <button key={decision} disabled={action.pending} onClick={() => void action.run(async () => {
      await request(success, `/friend-requests/${item.id}/${decision}`, "post"); view.refresh(); window.dispatchEvent(new Event("jomo:social-updated"));
    }, `Request ${decision === "accept" ? "accepted" : "declined"}.`)}>{decision === "accept" ? "Accept" : "Decline"}</button>)}</div>)}<Feedback action={action} />
  </Panel>;
}

const pendingInvitation = z.object({ id: z.string().uuid(), group_name: z.string(), expires_at: z.string() });
async function loadInvitations() { return request(pendingInvitation.array(), "/group-invitations"); }
export function GroupInvitations() {
  const view = useResource(loadInvitations); const action = useAction();
  useVisibleRefresh(view.refresh);
  const refreshInvitations = view.refresh;
  useEffect(() => {
    const refresh = () => refreshInvitations();
    window.addEventListener("jomo:social-updated", refresh);
    return () => window.removeEventListener("jomo:social-updated", refresh);
  }, [refreshInvitations]);
  return <Panel title="Group invitations"><button onClick={view.refresh}>Refresh invitations</button>
    {view.error && <p role="alert">{view.error}</p>}
    {!view.data?.length && <p>No pending group invitations.</p>}
    {view.data?.map(item => <div className="j-row" key={item.id}><span>{item.group_name} · expires {dateTime(item.expires_at)}</span><button disabled={action.pending} onClick={() => void action.run(async () => {
      await request(success, `/group-invitations/${item.id}/accept`, "post"); view.refresh(); window.dispatchEvent(new Event("jomo:social-updated"));
    }, "Group invitation accepted. Refresh your groups to open the garden.")}>Accept invitation</button></div>)}<Feedback action={action} />
  </Panel>;
}
