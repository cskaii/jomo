"use client";
import { DataControls } from "./DataControls";
import { useState } from "react";
import { clearSession } from "@/services/authSession";
import {
  request,
  profile,
  preferences,
  z,
  message,
} from "@/services/prototype";
import {
  useResource,
  useAction,
  Feedback,
  ResourceState,
  Panel,
  Heading,
  Submit,
} from "./ui";
async function load() {
  const me = await request(profile, "/users/me");
  return { me, prefs: await request(preferences, "/users/me/preferences") };
}
const form = z.object({
  name: z.string().trim().min(1).max(80),
  goal: z.coerce.number().int().min(1).max(1440),
  timezone: z.string().min(1).max(64),
  location: z.boolean(),
  screening: z.boolean(),
  notifications: z.boolean(),
});
export default function Settings() {
  const view = useResource(load);
  if (!view.data)
    return (
      <ResourceState
        loading={view.loading}
        error={view.error}
        retry={view.refresh}
      />
    );
  return <SettingsForm initial={view.data} />;
}
function SettingsForm({
  initial,
}: {
  initial: Awaited<ReturnType<typeof load>>;
}) {
  const action = useAction(),
    [name, setName] = useState(initial.me.display_name),
    [goal, setGoal] = useState(
      String(initial.prefs.daily_screen_goal_minutes ?? 120),
    );
  const [timezone, setTimezone] = useState(initial.prefs.timezone),
    [location, setLocation] = useState(initial.prefs.location_enabled);
  const [screening, setScreening] = useState(initial.prefs.screening_enabled),
    [notifications, setNotifications] = useState(
      initial.prefs.notifications_enabled,
    );
  return (
    <>
      <Heading
        eyebrow="Your space, your choices"
        title="Make yourself at home."
      />
      <Panel title="Profile and privacy">
        <form
          className="j-form"
          onSubmit={(event) => {
            event.preventDefault();
            void action.run(async () => {
              const input = form.parse({
                name,
                goal,
                timezone,
                location,
                screening,
                notifications,
              });
              try {
                new Intl.DateTimeFormat("en", {
                  timeZone: input.timezone,
                }).format();
              } catch {
                throw new Error(
                  "Enter a valid time zone, such as Asia/Singapore.",
                );
              }
              await request(profile, "/users/me", "patch", {
                display_name: input.name,
              });
                window.dispatchEvent(new Event("jomo:profile-updated"));
              try {
                await request(preferences, "/users/me/preferences", "patch", {
                  daily_screen_goal_minutes: input.goal,
                  timezone: input.timezone,
                  location_enabled: input.location,
                  screening_enabled: input.screening,
                  notifications_enabled: input.notifications,
                });
              } catch (error: unknown) {
                throw new Error(
                  `Your name was saved, but preferences were not confirmed: ${message(error)}`,
                  { cause: error },
                );
              }
            }, "Profile and preferences saved. Your intention will appear on Insights.");
          }}
        >
          <label>
            Display name
            <input
              required
              maxLength={80}
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
          </label>
          <p>Username: @{initial.me.username}</p>
          <label>
            Your JOMO profile ID
            <input readOnly value={initial.me.id} />
          </label>
          <small>
            Share this profile ID with someone you want to add as a friend.
          </small>
          <label>
            Daily screen-time intention (minutes)
            <input
              required
              type="number"
              min="1"
              max="1440"
              value={goal}
              onChange={(event) => setGoal(event.target.value)}
            />
          </label>
          <label>
            Time zone
            <input
              required
              maxLength={64}
              value={timezone}
              onChange={(event) => setTimezone(event.target.value)}
            />
          </label>
          <label className="j-checkbox">
            <input
              type="checkbox"
              checked={location}
              onChange={(event) => setLocation(event.target.checked)}
            />{" "}
            Enable optional activity check-ins
          </label>
          <small>
            Turning this off removes saved location check-ins and prevents new ones. Browser permission is requested separately.
            Every check-in still requires your action and consent.
          </small>
          <label className="j-checkbox">
            <input
              type="checkbox"
              checked={screening}
              onChange={(event) => setScreening(event.target.checked)}
            />{" "}
            Save my preference for in-app screening
          </label>
          <small>
            This does not activate automatic screening in other apps. Guardian
            submissions remain explicit.
          </small>
          <label className="j-checkbox">
            <input
              type="checkbox"
              checked={notifications}
              onChange={(event) => setNotifications(event.target.checked)}
            />{" "}
            Receive gentle in-app reminders
          </label>
          <small>
            This saves your reminder preference. Device push notifications are
            not connected yet.
          </small>
          <Submit pending={action.pending}>Save preferences</Submit>
          <Feedback action={action} />
        </form>
      </Panel>
      <DataControls />
      <DeleteAccount />
    </>
  );
}

function DeleteAccount() {
  const action = useAction();
  const [expanded, setExpanded] = useState(false);
  const [password, setPassword] = useState("");
  const [confirmation, setConfirmation] = useState("");
  return (
    <Panel title="Delete account">
      <p>
        Permanently delete your login, profile, personal garden, coins, and activity
        history. This cannot be undone.
      </p>
      <p>
        Your shared gardens, plants, pets, and group coins stay with the remaining
        members. Ownership transfers to another active member when needed. Groups
        with no active members left are deleted.
      </p>
      {!expanded ? (
        <button className="j-button danger" type="button" onClick={() => setExpanded(true)}>
          Delete my account
        </button>
      ) : (
        <form className="j-form" onSubmit={(event) => {
          event.preventDefault();
          if (confirmation !== "DELETE" || action.pending) return;
          void action.run(async () => {
            try {
              await request(z.object({ success: z.literal(true) }), "/users/me", "delete", {
                password, confirmation,
              }, { timeout: 45000 });
              clearSession();
              window.location.replace("/login?account_deleted=1");
            } finally {
              setPassword("");
            }
          });
        }}>
          <label>
            Current password
            <input type="password" autoComplete="current-password" required
              maxLength={1024} value={password} disabled={action.pending}
              onChange={(event) => setPassword(event.target.value)} />
          </label>
          <label>
            Type DELETE to confirm
            <input required pattern="DELETE" autoComplete="off" spellCheck={false}
              value={confirmation} disabled={action.pending}
              onChange={(event) => setConfirmation(event.target.value)} />
          </label>
          <button className="j-button danger" type="submit" aria-busy={action.pending}
            disabled={action.pending || confirmation !== "DELETE" || !password}>
            {action.pending ? "Deleting account…" : "Permanently delete my account"}
          </button>
          <button className="j-button secondary" type="button" disabled={action.pending}
            onClick={() => { setExpanded(false); setPassword(""); setConfirmation(""); }}>
            Keep my account
          </button>
          <Feedback action={action} />
        </form>
      )}
    </Panel>
  );
}
