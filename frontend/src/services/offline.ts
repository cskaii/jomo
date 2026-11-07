import { request, profile, activity, participant, preferences } from "./prototype";
import { participationRecords } from "@/lib/offline";

export async function loadOfflineOverview() {
  const [me, activities, prefs] = await Promise.all([
    request(profile, "/users/me"),
    request(activity.array(), "/activities"),
    request(preferences, "/users/me/preferences"),
  ]);
  const participants = await Promise.all(
    activities.map((item) =>
      request(participant.array(), `/activities/${item.id}/participants`),
    ),
  );
  return { me, timezone: prefs.timezone, records: participationRecords(activities, participants, me.id, prefs.timezone) };
}
