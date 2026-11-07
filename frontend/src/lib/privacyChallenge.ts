export const QUIZ_COOLDOWN_MS = 2 * 60 * 60 * 1000;
export const QUIZ_SETTLE_MS = 60 * 1000;

export function quizStorageKey(userId: string) {
  return `jomo:privacy-challenge:last-shown:${userId}`;
}

export function quizDelay(lastShown: number, now: number) {
  if (!Number.isFinite(lastShown) || lastShown <= 0 || lastShown > now) return 0;
  // A clock change must not suppress challenges indefinitely.
  return Math.max(0, lastShown + QUIZ_COOLDOWN_MS - now);
}

export function canAutoChallenge({ visible, active, editing, busy }: {
  visible: boolean; active: boolean; editing: boolean; busy: boolean;
}) {
  return visible && active && !editing && !busy;
}
