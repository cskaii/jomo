"use client";
import { useEffect, useReducer } from "react";
import { initialTransition, navigationTransition, TAB_TRANSITION_MS, WELCOME_TRANSITION_MS } from "@/lib/navigationTransition";

export function useNavigationTransition(route: string) {
  const [state, dispatch] = useReducer(navigationTransition, route, initialTransition);
  // Adjust before committing the destination, avoiding a flash of cached content.
  if (state.route !== route) dispatch({ type: "navigate", route });

  useEffect(() => {
    if (!state.active) return;
    const timer = window.setTimeout(() => dispatch({ type: "finish", route: state.route }),
      state.welcomed ? TAB_TRANSITION_MS : WELCOME_TRANSITION_MS);
    return () => window.clearTimeout(timer);
  }, [state.active, state.route, state.welcomed]);

  return state;
}
