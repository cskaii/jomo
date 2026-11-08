"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import Activities from "./Activities";
import {
  Award, BookOpen, Check, ChevronRight, Clock, Compass, Heart,
  Leaf, Search, Sparkles, Star, Trophy, Users, X,
} from "lucide-react";
import {
  activitiesOverview, progressMission, quest, questCompletion, questInstance,
  request, success, z,
} from "@/services/prototype";
import { Feedback, ResourceState, useAction, useResource, useVisibleRefresh } from "./ui";

const categories = [
  ["all", "All quests", Compass],
  ["movement_outdoors", "Outdoors", Leaf],
  ["social_connections", "Social", Users],
  ["creativity_hobbies", "Creativity", Sparkles],
  ["mindfulness_growth", "Mindfulness", Star],
  ["learning_skills", "Learning", BookOpen],
  ["digital_wellbeing", "Digital balance", Clock],
  ["community_kindness", "Kindness", Heart],
] as const;

function loadOverview() {
  return request(activitiesOverview, "/progression/activities");
}

export default function Quests() {
  const view = useResource(loadOverview, "activities-overview");
  useVisibleRefresh(view.refresh, 60000);
  const refreshAt = view.data?.discovery.refresh_at;
  useEffect(() => {
    if (!refreshAt) return;
    const remaining = Date.parse(refreshAt) - Date.now();
    if (remaining <= 0) return;
    const timer = window.setTimeout(view.refresh, Math.min(remaining + 500, 2147483647));
    return () => window.clearTimeout(timer);
  }, [refreshAt, view.refresh]);
  const action = useAction();
  const [category, setCategory] = useState("all");
  const [difficulty, setDifficulty] = useState("all");
  const [search, setSearch] = useState("");
  const [savedOnly, setSavedOnly] = useState(false);
  const [selected, setSelected] = useState<z.infer<typeof quest> | null>(null);
  const [completing, setCompleting] = useState<z.infer<typeof quest> | null>(null);
  const [reflection, setReflection] = useState("");
  const [reward, setReward] = useState<z.infer<typeof questCompletion> | null>(null);

  const filtered = useMemo(() => (view.data?.quests ?? []).filter((item) =>
    (!savedOnly || item.is_favorite) &&
    (category === "all" || item.category === category) &&
    (difficulty === "all" || item.difficulty === difficulty) &&
    (!search || `${item.title} ${item.description}`.toLowerCase().includes(search.toLowerCase())),
  ), [view.data?.quests, category, difficulty, search, savedOnly]);

  if (!view.data) return <ResourceState loading={view.loading} error={view.error} retry={view.refresh} />;
  const { progress } = view.data;
  const xpPercent = Math.min(100, Math.round(progress.xp_current / progress.xp_to_next_level * 100));

  const refresh = () => { view.refresh(); setSelected(null); };
  const start = (item: z.infer<typeof quest>) => void action.run(async () => {
    await request(questInstance, `/quests/${item.code}/start`, "post");
    refresh();
  }, `${item.title} started. Put your phone aside and enjoy the moment.`);

  const cards = (items: z.infer<typeof quest>[]) => <div className="j-quest-grid">{items.map((item) => <QuestCard key={item.id} item={item} pending={action.pending} onOpen={() => setSelected(item)} onStart={() => start(item)} onComplete={() => setCompleting(item)} onFavorite={() => void action.run(async () => {
    await request(success, `/quests/${item.code}/favorite`, "post"); view.refresh();
  })} />)}</div>;

  return (
    <div className="j-quest-page">
      <header className="j-quest-hero">
        <div>
          <p className="j-eyebrow">GO MAKE A MEMORY</p>
          <h1>Your activities</h1>
          <p>Small actions. Bigger adventures. Choose one, then go offline.</p>
          <Link href="/activities/create" className="j-button">Create an activity</Link>
        </div>
        <section className="j-progression-card" aria-label={`Level ${progress.level} progression`}>
          <div><span>Level {progress.level}</span><strong>{progress.xp_current} / {progress.xp_to_next_level} XP</strong></div>
          <div className="j-xp-track"><i style={{ width: `${xpPercent}%` }} /></div>
          <footer><span><Leaf /> {progress.garden_points} garden points</span><span><Award /> {progress.achievements_unlocked} achievements</span><span><Sparkles /> {progress.current_streak} day rhythm</span></footer>
        </section>
      </header>
      {view.error && <p role="alert">Updates could not load. Your previous choices are shown. <button onClick={view.refresh}>Retry</button></p>}
      {!!view.data.quests.filter(item => item.active_instance_id).length && <section className="j-explore-quests"><div className="j-section-heading"><div><p className="j-eyebrow">KEEP GOING</p><h2>In progress</h2></div><span>Your started activities stay here after midnight</span></div>{cards(view.data.quests.filter(item => item.active_instance_id))}</section>}

      <section className="j-mission-section">
        <div className="j-section-heading"><div><p className="j-eyebrow">TODAY</p><h2>Daily missions</h2></div><span>Resets at midnight ({view.data.discovery.timezone}) · no penalty if missed</span></div>
        <div className="j-mission-grid">{view.data.daily.map((item) => <MissionCard key={item.id} item={item} action={action} onExplore={() => { setCategory(item.categories[0] ?? "all"); setDifficulty("all"); setSearch(""); setSavedOnly(false); }} onClaim={() => void action.run(async () => {
          await request(progressMission, `/missions/${item.id}/claim`, "post"); view.refresh();
        }, "Mission XP claimed.")} />)}</div>
        {!view.data.daily.length && <p>No daily missions have been added yet.</p>}
      </section>

      <section className="j-mission-section">
        <div className="j-section-heading"><div><p className="j-eyebrow">THIS WEEK</p><h2>Weekly challenges</h2></div><span>Three calm goals, refreshed each Monday</span></div>
        <div className="j-mission-grid">{view.data.weekly.map((item) => <MissionCard key={item.id} item={item} action={action} onExplore={() => { setCategory(item.categories[0] ?? "all"); setDifficulty("all"); setSearch(""); setSavedOnly(false); }} onClaim={() => void action.run(async () => {
          await request(progressMission, `/missions/${item.id}/claim`, "post"); view.refresh();
        }, "Weekly challenge XP claimed.")} />)}</div>
        {!view.data.weekly.length && <p>No weekly challenges have been added yet.</p>}
      </section>

      <section className="j-explore-quests">
        <div className="j-section-heading"><div><p className="j-eyebrow">PICK YOUR ADVENTURE</p><h2>Today’s quests</h2></div><span>Fresh choices each day</span></div>
        {cards(view.data.discovery.quests)}
        {!view.data.discovery.quests.length && <p>No daily quests available yet. You can create your own activity.</p>}
      </section>
      <section className="j-explore-quests">
        <div className="j-section-heading"><div><p className="j-eyebrow">SOMETHING DIFFERENT</p><h2>Suggested activities</h2></div><span>Complete these to earn XP and advance missions too</span></div>
        {cards(view.data.discovery.suggestions)}
        {!view.data.discovery.suggestions.length && <p>No suggestions available yet.</p>}
        <p><small>Daily picks rotate through the catalogue before repeating. The full library is always available below.</small></p>
      </section>
      <section className="j-explore-quests" id="quest-library">
        <div className="j-section-heading"><div><p className="j-eyebrow">QUEST LIBRARY</p><h2>Explore something offline</h2></div><span>{filtered.length} available</span></div>
        <div className="j-quest-toolbar">
          <label><Search /><input value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search quests" /></label>
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)} aria-label="Difficulty"><option value="all">All difficulties</option><option value="easy">Easy</option><option value="medium">Medium</option><option value="hard">Hard</option></select>
          <label><input type="checkbox" checked={savedOnly} onChange={event => setSavedOnly(event.target.checked)} /> Favourites only</label>
        </div>
        <div className="j-category-tabs">{categories.map(([id, label, Icon]) => <button key={id} className={category === id ? "is-active" : ""} onClick={() => setCategory(id)}><Icon />{label}</button>)}</div>
        {cards(filtered)}
        {!filtered.length && <p>No quests match this view. You can create your own activity above.</p>}
      </section>

      <section className="j-achievement-strip">
        <div className="j-section-heading"><div><p className="j-eyebrow">MILESTONES</p><h2>Your achievements</h2></div><span>{progress.achievements_unlocked} unlocked</span></div>
        <div>{view.data.achievements.map((item) => <article key={item.code} className={item.unlocked ? "is-unlocked" : ""}><Trophy /><strong>{item.name}</strong><span>{item.current_progress}/{item.target_value}</span><div><i style={{ width: `${Math.min(100, item.current_progress / item.target_value * 100)}%` }} /></div></article>)}</div>
      </section>

      <Feedback action={action} />
      <Activities embedded />

      {selected && <div className="j-quest-modal" role="presentation" onMouseDown={(e) => e.target === e.currentTarget && setSelected(null)}><section role="dialog" aria-modal="true" aria-labelledby="quest-title"><button className="j-modal-close" onClick={() => setSelected(null)}><X /></button><p className="j-eyebrow">{selected.category_label} · {selected.difficulty}</p><h2 id="quest-title">{selected.title}</h2><p>{selected.description}</p><div className="j-quest-instructions"><strong>Your quest</strong><p>{selected.instructions}</p></div><div className="j-quest-rewards"><span><Clock /> {selected.estimated_duration_minutes} min</span><span><Sparkles /> +{selected.xp_reward} XP</span><span><Leaf /> Garden points follow verified eligible minutes</span></div>{selected.active_instance_id ? <button className="j-button" onClick={() => { setCompleting(selected); setSelected(null); }}>Check in</button> : <button className="j-button" disabled={action.pending || selected.completed_today} onClick={() => start(selected)}>{selected.completed_today ? "Completed today" : "Start activity"}</button>}<p><Link href={`/activities/create?title=${encodeURIComponent(selected.title)}&category=${encodeURIComponent(selected.category)}&minutes=${selected.estimated_duration_minutes}&description=${encodeURIComponent(selected.instructions)}`}>Customise as your own activity</Link></p><small>Self-reported unless the activity says otherwise. No location or photo is required.</small></section></div>}

      {completing?.active_instance_id && <div className="j-quest-modal" role="presentation"><form onSubmit={(e) => { e.preventDefault(); void action.run(async () => {
        const result = await request(questCompletion, `/quest-instances/${completing.active_instance_id}/complete`, "post", { reflection: reflection || null });
        setReward(result); setCompleting(null); setReflection(""); view.refresh();
      }, "Quest completed."); }}><button type="button" className="j-modal-close" onClick={() => setCompleting(null)}><X /></button><p className="j-eyebrow">WELCOME BACK</p><h2>How did it go?</h2><p>{completing.reflection_prompt}</p><textarea value={reflection} onChange={(e) => setReflection(e.target.value)} maxLength={1000} placeholder="Optional reflection" /><button className="j-button" disabled={action.pending}>Complete quest</button><button type="button" className="j-button secondary" onClick={() => void action.run(async () => {
        await request(success, `/quest-instances/${completing.active_instance_id}/abandon`, "post"); setCompleting(null); view.refresh();
      }, "Quest left without penalty.")}>Abandon without penalty</button></form></div>}

      {reward && <div className="j-reward-pop" role="dialog" aria-modal="true"><section><Sparkles /><p className="j-eyebrow">QUEST COMPLETE</p><h2>Meaningful time, rewarded.</h2><div><strong>+{reward.xp_awarded} XP</strong><strong>+{reward.garden_points_awarded} garden points</strong></div>{reward.unlocked_achievements.length > 0 && <p>Unlocked: {reward.unlocked_achievements.join(", ")}</p>}<button className="j-button" onClick={() => setReward(null)}>Continue</button></section></div>}
    </div>
  );
}

function MissionCard({ item, action, onClaim, onExplore }: { item: z.infer<typeof progressMission>; action: ReturnType<typeof useAction>; onClaim: () => void; onExplore: () => void }) {
  const done = item.current_progress >= item.target_value;
  return <article className={`j-mission-card${done ? " is-complete" : ""}`}><div><Trophy /><span>{item.code}</span></div><h3>{item.title}</h3><p>{item.description}</p><div className="j-mission-progress"><i style={{ width: `${Math.min(100, item.current_progress / item.target_value * 100)}%` }} /></div><footer><span>{item.current_progress}/{item.target_value}</span><strong>+{item.reward_xp} XP</strong></footer>{!done && <a href="#quest-library" onClick={onExplore}>Find an activity</a>}{done && !item.reward_claimed && <button onClick={onClaim} disabled={action.pending}>Claim reward</button>}{item.reward_claimed && <span className="j-claimed"><Check /> Claimed</span>}</article>;
}

function QuestCard({ item, pending, onOpen, onStart, onComplete, onFavorite }: { item: z.infer<typeof quest>; pending: boolean; onOpen: () => void; onStart: () => void; onComplete: () => void; onFavorite: () => void }) {
  return <article className={`j-quest-card difficulty-${item.difficulty}`}><button className={`j-favorite${item.is_favorite ? " is-saved" : ""}`} onClick={onFavorite} aria-label={item.is_favorite ? "Remove favorite" : "Save favorite"}><Heart /></button><div className="j-quest-card-top"><span>{item.category_label}</span><b>{item.difficulty}</b></div><h3>{item.title}</h3><p>{item.description}</p><div className="j-quest-meta"><span><Clock />{item.estimated_duration_minutes} min</span><span><Sparkles />{item.xp_reward} XP</span></div><footer>{item.active_instance_id ? <button disabled={pending} onClick={onComplete}>Check in</button> : <button disabled={pending || item.completed_today} onClick={onStart}>{item.completed_today ? "Completed today" : item.completion_count ? "Do again" : "Start activity"}</button>}<button onClick={onOpen} aria-label={`Details for ${item.title}`}><ChevronRight /></button></footer></article>;
}
