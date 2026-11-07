"use client";
import { useCallback } from "react";
import { request, ledger, member, z, dateTime } from "@/services/prototype";
import { useResource, useVisibleRefresh } from "./ui";

export function GardenHistory({ gardenId, groupId }: { gardenId: string; groupId?: string | null }) {
  const load = useCallback(async () => {
    const [entries, members] = await Promise.all([request(ledger.array(), `/gardens/${gardenId}/ledger`),
      groupId ? request(member.array(), `/groups/${groupId}/members`) : Promise.resolve([] as z.infer<typeof member>[])]);
    return { entries, members };
  }, [gardenId, groupId]);
  const view = useResource(load);
  useVisibleRefresh(view.refresh);
  return <details className="j-garden-history"><summary>Coin history</summary><section aria-label="Garden coin history"><h2>{groupId ? "Shared coin history" : "Your coin history"}</h2>
    <p>Purchases use this garden’s balance. Moving an existing item is free. Updates are checked every 15 seconds while this tab is visible.</p>
    <button onClick={view.refresh}>Refresh history</button>
    {view.error && <p role="alert">History could not refresh. {view.error}</p>}
    {!view.data?.entries.length && <p>No transactions yet.</p>}
    <ul>{view.data?.entries.map(entry => <li key={entry.id}><strong>{entry.amount > 0 ? "+" : ""}{entry.amount} coins</strong> · {entry.reason}
      <small>{dateTime(entry.created_at)} · {entry.user_id == null ? "Former member" : groupId ? view.data?.members.find(person => person.user_id === entry.user_id)?.display_name || "Group member" : "You"}</small></li>)}</ul>
  </section></details>;
}
