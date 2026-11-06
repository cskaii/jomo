import { request, profile, activity, participant } from "./prototype";
import { participationRecords } from "@/lib/offline";

export async function loadOfflineOverview() {
  const [me, activities] = await Promise.all([
    request(profile, "/users/me"),
    request(activity.array(), "/activities"),
  ]);
  const participants = await Promise.all(
    activities.map((item) =>
      request(participant.array(), `/activities/${item.id}/participants`),
    ),
  );
  return { me, records: participationRecords(activities, participants, me.id) };
}
