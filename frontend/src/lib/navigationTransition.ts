export const TAB_TRANSITION_MS = 120;
export const WELCOME_TRANSITION_MS = 600;

export type NavigationTransition = { route: string; active: boolean; welcomed: boolean };
export type TransitionEvent = { type: "navigate" | "finish"; route: string };

export function initialTransition(route: string): NavigationTransition {
  return { route, active: true, welcomed: false };
}

export function navigationTransition(state: NavigationTransition, event: TransitionEvent): NavigationTransition {
  if (event.type === "navigate") {
    return event.route === state.route ? state : { ...state, route: event.route, active: true };
  }
  // A rapid second navigation must not be dismissed by the previous route's timer.
  return event.route === state.route ? { ...state, active: false, welcomed: true } : state;
}
