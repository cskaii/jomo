"use client";
import { useEffect } from "react";
import Link from "next/link";
import { Bell } from "lucide-react";
import { request, success, z, dateTime } from "@/services/prototype";
import { useAction, useResource, Feedback } from "./ui";

const notice = z.object({ id: z.string().uuid(), type: z.string(), title: z.string(), body: z.string(),
  read_at: z.string().nullable(), created_at: z.string(),
  payload: z.object({ href: z.string().optional(), request_id: z.string().uuid().optional(), invite_id: z.string().uuid().optional(), handled: z.boolean().optional() }).nullable() });
async function load() { return request(notice.array(), "/notifications"); }

export function NotificationBell() {
  const view = useResource(load, "notifications");
  const action = useAction();
  const refreshNotifications = view.refresh;
  useEffect(() => {
    const refresh = () => { if (document.visibilityState === "visible") refreshNotifications(); };
    const timer = window.setInterval(refresh, 20_000);
    window.addEventListener("focus", refresh);
    document.addEventListener("visibilitychange", refresh);
    return () => { window.clearInterval(timer); window.removeEventListener("focus", refresh); document.removeEventListener("visibilitychange", refresh); };
  }, [refreshNotifications]);
  const unread = view.data?.filter(item => !item.read_at).length ?? 0;
  const perform = (path: string, message: string) => void action.run(async () => {
    await request(success, path, "post"); view.refresh();
    window.dispatchEvent(new Event("jomo:social-updated"));
  }, message);
  return <details className="j-notifications">
    <summary aria-label={`Notifications, ${unread} unread in recent history`}><Bell aria-hidden="true" />{unread > 0 && <span>{unread >= 50 ? "50+" : unread}</span>}</summary>
    <section className="j-notification-panel" aria-label="Notifications">
      <h2>Notifications</h2><small>In-app updates while JOMO is open. Latest 50 notices, retained for 30 days.</small>
      <button onClick={() => perform("/notifications/read-all", "Marked all as read.")} disabled={action.pending}>Mark all as read</button>
      {view.error && <p role="alert">Notifications could not refresh. <button onClick={view.refresh}>Retry</button></p>}
      {!view.data?.length && <p>{view.loading ? "Loading notifications…" : "You are all caught up."}</p>}
      {view.data?.map(item => <article key={item.id} className={item.read_at ? undefined : "j-unread"}>
        <strong>{item.title}</strong><p>{item.body}</p><small>{dateTime(item.created_at)}</small>
        <div className="j-row">
          {item.payload?.href && /^\/(friends|activities|garden)(?:[/?#]|$)/.test(item.payload.href) && !item.payload.href.includes("\\") && <Link href={item.payload.href}>Open</Link>}
          {!item.read_at && <button disabled={action.pending} onClick={() => perform(`/notifications/${item.id}/read`, "Marked as read.")}>Mark read</button>}
          {item.type === "friend_request" && !item.payload?.handled && item.payload?.request_id && <><button disabled={action.pending} onClick={() => perform(`/friend-requests/${item.payload?.request_id}/accept`, "Friend request accepted.")}>Accept friend</button><button disabled={action.pending} onClick={() => perform(`/friend-requests/${item.payload?.request_id}/decline`, "Friend request declined.")}>Decline</button></>}
          {item.type === "group_invite" && !item.payload?.handled && item.payload?.invite_id && <button disabled={action.pending} onClick={() => perform(`/group-invitations/${item.payload?.invite_id}/accept`, "Group invitation accepted.")}>Join group</button>}
        </div>
      </article>)}
      <Feedback action={action} />
    </section>
  </details>;
}
