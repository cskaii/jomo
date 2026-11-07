export function loadingCopy(pathname: string) {
  if (pathname.startsWith("/privacy-guardian")) return {
    section: "Privacy Guardian", title: "A little care before you share.", description: "Preparing your privacy toolkit…",
  };
  if (pathname.startsWith("/settings") || pathname.startsWith("/preferences")) return {
    section: "Your preferences", title: "A space that feels like you.", description: "Getting your preferences ready…",
  };
  if (pathname.startsWith("/friends/groups") || pathname.startsWith("/squads")) return {
    section: "Your shared space", title: "Good things grow together.", description: "Gathering your group’s little moments…",
  };
  if (pathname.startsWith("/friends")) return {
    section: "Your circle", title: "A little closer to your people.", description: "Bringing your circle together…",
  };
  if (pathname.startsWith("/garden")) return {
    section: "Your garden", title: "Your sanctuary is taking root.", description: "Preparing your little garden…",
  };
  if (pathname.startsWith("/insights")) return {
    section: "Your insights", title: "Every little moment matters.", description: "Gathering your daily moments…",
  };
  if (pathname.startsWith("/focus")) return {
    section: "Your quiet moment", title: "A little room to be present.", description: "Preparing your focus session…",
  };
  if (pathname.startsWith("/activities")) return {
    section: "Offline moments", title: "Make room for something good.", description: "Gathering your offline activities…",
  };
  return { section: "JOMO", title: "Your space is taking root.", description: "Preparing your little space…" };
}

export function welcomeTitle(registration: boolean, displayName?: string | null, username?: string | null) {
  if (registration) return "Welcome to your little space.";
  const name = displayName?.trim() || username?.trim();
  if (!name) return "Welcome back.";
  return `Welcome back, ${name}.`;
}
