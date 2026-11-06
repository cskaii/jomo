"use client";
import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  request,
  session,
  activity,
  participant,
  utc,
} from "@/services/prototype";
import {
  useResource,
  useAction,
  Feedback,
  ResourceState,
  Panel,
  Heading,
} from "./ui";
export default function Focus() {
  const { sessionId } = useParams<{ sessionId: string }>(),
    [now, setNow] = useState<number | null>(null),
    action = useAction();
  const load = useCallback(async () => {
    const focus = await request(session, `/focus-sessions/${sessionId}`);
    const [item, people] = await Promise.all([
      request(activity, `/activities/${focus.activity_id}`),
      request(
        participant.array(),
        `/activities/${focus.activity_id}/participants`,
      ),
    ]);
    return { focus, item, people };
  }, [sessionId]);
  const view = useResource(load);
  useEffect(() => {
    const handle = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(handle);
  }, []);
  if (!view.data)
    return (
      <ResourceState
        loading={view.loading}
        error={view.error}
        retry={view.refresh}
      />
    );
  const { focus, item, people } = view.data;
  const start = Date.parse(utc(focus.started_at)),
    end = focus.ended_at ? Date.parse(utc(focus.ended_at)) : now;
  const elapsed =
    end === null || !Number.isFinite(start) || !Number.isFinite(end)
      ? null
      : Math.max(0, Math.floor((end - start) / 1000));
  return (
    <>
      <Heading eyebrow="Be here, for a while" title={item.title}>
        <p>A voluntary pause for the things that matter.</p>
      </Heading>
      <Panel>
        <div className="j-clock">
          <strong role="timer" aria-label="Elapsed focus time">
            {elapsed === null
              ? "—"
              : `${String(Math.floor(elapsed / 60)).padStart(2, "0")}:${String(elapsed % 60).padStart(2, "0")}`}
          </strong>
          <span>{focus.status}</span>
        </div>
        <p>
          Your timer continues across refreshes and time spent away from this
          tab. Participation and rewards are verified separately.
        </p>
        <p>
          Focus sessions do not block native apps or lock your device. You can
          end your own session at any time.
        </p>
        <p>
          {people.filter((person) => person.status === "active").length} active
          activity participants. This does not imply their focus timers are
          running.
        </p>
        {focus.status === "active" && (
          <button
            className="j-button"
            disabled={action.pending}
            onClick={() =>
              void action.run(async () => {
                await request(
                  session,
                  `/focus-sessions/${sessionId}/end`,
                  "post",
                );
                view.refresh();
              }, "Your focus session ended. Activity completion is a separate step.")
            }
          >
            End my focus session
          </button>
        )}
        <Feedback action={action} />
        <Link href={`/activities/${focus.activity_id}`}>
          Return to activity →
        </Link>
        <p>
          <small>
            You can end this session whenever you need a break. Ending your
            timer does not end the group activity.
          </small>
        </p>
      </Panel>
    </>
  );
}
