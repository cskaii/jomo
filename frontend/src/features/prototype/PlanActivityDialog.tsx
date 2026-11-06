"use client";
import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Footprints,
  Dumbbell,
  BookOpen,
  ChefHat,
  Wind,
  Palette,
  Trees,
  Users,
  Minus,
  Plus,
  X,
  ArrowRight,
} from "lucide-react";
import { request, activity, localDate, z } from "@/services/prototype";
import { Feedback, useAction } from "./ui";

const categories = [
  ["walk", "Walk", Footprints],
  ["movement", "Movement", Dumbbell],
  ["reading", "Reading", BookOpen],
  ["cooking", "Cooking", ChefHat],
  ["quiet", "Quiet", Wind],
  ["creative", "Creative", Palette],
  ["outdoor", "Outdoors", Trees],
  ["social", "Together", Users],
] as const;

export function PlanActivityDialog({
  groupId,
  label = "Add an activity",
}: {
  groupId?: string;
  label?: string;
}) {
  const dialog = useRef<HTMLDialogElement>(null),
    router = useRouter(),
    action = useAction();
  const [open, setOpen] = useState(false),
    [category, setCategory] = useState("walk"),
    [duration, setDuration] = useState(30),
    [title, setTitle] = useState(""),
    [note, setNote] = useState("");
  useEffect(() => {
    if (open && !dialog.current?.open) {
      dialog.current?.showModal();
      dialog.current
        ?.querySelector<HTMLInputElement>('input[name="activity-title"]')
        ?.focus();
    }
    if (!open && dialog.current?.open) dialog.current?.close();
  }, [open]);
  return (
    <>
      <button className="j-button" onClick={() => setOpen(true)}>
        <Plus aria-hidden="true" />
        {label}
      </button>
      <dialog
        ref={dialog}
        className="j-activity-dialog"
        onClose={() => setOpen(false)}
        aria-labelledby="activity-dialog-title"
      >
        <button
          className="j-dialog-close j-icon-button"
          aria-label="Close activity form"
          onClick={() => setOpen(false)}
        >
          <X aria-hidden="true" />
        </button>
        <h2 id="activity-dialog-title">What will you do offline?</h2>
        <p>Make a little room for something real. Start with one small plan.</p>
        <form
          className="j-form"
          onSubmit={(event) => {
            event.preventDefault();
            void action.run(async () => {
              const input = z
                .object({
                  title: z
                    .string()
                    .trim()
                    .min(1, "Give your activity a title.")
                    .max(120),
                  duration_minutes: z.number().int().min(1).max(480),
                  description: z.string().trim().max(2000),
                })
                .parse({
                  title,
                  duration_minutes: duration,
                  description: note,
                });
              const created = await request(activity, "/activities", "post", {
                ...input,
                category,
                visibility: groupId ? "group" : "personal",
                group_id: groupId ?? null,
                max_participants: groupId ? 10 : 1,
                location_required: false,
                proof_requirement: groupId ? "group_confirmation" : "photo",
              });
              setOpen(false);
              router.push(`/activities/${created.id}`);
            });
          }}
        >
          <fieldset className="j-category-fieldset">
            <legend className="j-sr-only">Activity category</legend>
            <div className="j-category-options">
              {categories.map(([value, text, Icon]) => (
                <button
                  key={value}
                  type="button"
                  className={category === value ? "is-selected" : ""}
                  aria-pressed={category === value}
                  onClick={() => setCategory(value)}
                >
                  <Icon aria-hidden="true" />
                  {text}
                </button>
              ))}
            </div>
          </fieldset>
          <div>
            <span className="j-eyebrow">Minutes</span>
            <div className="j-duration-controls">
              <div className="j-duration-stepper">
                <button
                  type="button"
                  className="j-icon-button"
                  aria-label="Five fewer minutes"
                  disabled={duration <= 1}
                  onClick={() => setDuration(Math.max(1, duration - 5))}
                >
                  <Minus aria-hidden="true" />
                </button>
                <input
                  type="number"
                  min="1"
                  max="480"
                  required
                  aria-label="Activity duration in minutes"
                  value={duration}
                  onChange={(event) => setDuration(Number(event.target.value))}
                />
                <button
                  type="button"
                  className="j-icon-button"
                  aria-label="Five more minutes"
                  disabled={duration >= 480}
                  onClick={() => setDuration(Math.min(480, duration + 5))}
                >
                  <Plus aria-hidden="true" />
                </button>
              </div>
              <div className="j-duration-presets">
                {[15, 30, 45, 60].map((value) => (
                  <button
                    key={value}
                    type="button"
                    aria-pressed={duration === value}
                    onClick={() => setDuration(value)}
                  >
                    {value}
                  </button>
                ))}
              </div>
            </div>
          </div>
          <div className="j-dialog-fields">
            <label>
              What is the plan?
              <input
                name="activity-title"
                required
                maxLength={120}
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="A wander with no destination"
              />
            </label>
            <label>
              Day
              <input type="date" readOnly value={localDate()} />
            </label>
          </div>
          <label>
            A note for your garden <small>(optional)</small>
            <textarea
              rows={3}
              maxLength={2000}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              placeholder="Leave a little intention…"
            />
          </label>
          <p className="j-form-note">
            This creates a plan for today. Start your activity to record
            participation. Points follow the existing verification process.
          </p>
          <button
            className="j-button"
            type="submit"
            disabled={action.pending}
            aria-busy={action.pending}
          >
            {action.pending ? "Creating your plan…" : "Create activity"}
            <ArrowRight aria-hidden="true" />
          </button>
          <Feedback action={action} />
        </form>
      </dialog>
    </>
  );
}
