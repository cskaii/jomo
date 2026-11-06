"use client";
import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import {
  Menu,
  X,
  Users,
  Leaf,
  ArrowLeft,
  ArrowRight,
  LayoutGrid,
  RefreshCw,
} from "lucide-react";
import type { Garden } from "@/types/garden";
import type { GardenDirectory } from "@/services/gardens";
import { gardenHref } from "@/lib/gardenNavigation";
import { Heading } from "./ui";
import { PlanActivityDialog } from "./PlanActivityDialog";

export function GardenNavigation({
  directory,
  current,
  onRefresh,
}: {
  directory: GardenDirectory;
  current?: Garden;
  onRefresh: () => void;
}) {
  const [open, setOpen] = useState(false);
  const personal = directory.gardens.find(
    (item) => item.garden_type === "personal",
  );
  return (
    <>
      {current && (
        <Link className="j-garden-back" href="/garden">
          <ArrowLeft aria-hidden="true" />
          All gardens
        </Link>
      )}
      <div className="j-garden-title j-garden-browser-heading">
        <Heading
          eyebrow={
            current
              ? current.garden_type === "group"
                ? "A SHARED LITTLE WORLD"
                : "YOUR OWN LITTLE WORLD"
              : "GOOD THINGS GROW TOGETHER"
          }
          title={current?.name ?? "Your gardens."}
        >
          <p>
            {current
              ? "A little patch of progress, made by moments away from the screen."
              : "Your own little world, and the ones you share. Choose a garden to step into."}
          </p>
        </Heading>
        <div className="j-garden-heading-actions">
          {current ? (
            <PlanActivityDialog
              key={current.id}
              groupId={current.owner_group_id ?? undefined}
            />
          ) : (
            <button
              className="j-icon-button"
              onClick={onRefresh}
              aria-label="Refresh garden list"
              title="Refresh gardens"
            >
              <RefreshCw aria-hidden="true" />
            </button>
          )}
          <button
            className="j-garden-menu-button"
            onClick={() => setOpen(true)}
            aria-label="Open garden switcher"
            aria-haspopup="dialog"
            aria-expanded={open}
            title="Switch gardens"
          >
            <Menu aria-hidden="true" />
          </button>
        </div>
      </div>
      {!current && (
        <div className="j-garden-directory-toolbar">
          <span className="j-tag">
            <Users aria-hidden="true" />
            Personal & shared gardens
          </span>
          {personal && (
            <Link className="j-button secondary" href={gardenHref(personal.id)}>
              <Leaf aria-hidden="true" />
              My personal garden
              <ArrowRight aria-hidden="true" />
            </Link>
          )}
        </div>
      )}
      <GardenDrawer
        directory={directory}
        currentId={current?.id}
        open={open}
        onClose={() => setOpen(false)}
      />
    </>
  );
}

function GardenDrawer({
  directory,
  currentId,
  open,
  onClose,
}: {
  directory: GardenDirectory;
  currentId?: string;
  open: boolean;
  onClose: () => void;
}) {
  const dialog = useRef<HTMLDialogElement>(null);
  useEffect(() => {
    if (open && !dialog.current?.open) dialog.current?.showModal();
    if (!open && dialog.current?.open) dialog.current?.close();
  }, [open]);
  const groups = directory.gardens.filter(
    (item) => item.garden_type === "group",
  );
  const personal = directory.gardens.filter(
    (item) => item.garden_type === "personal",
  );
  function gardenLink(item: Garden) {
    return (
      <Link
        key={item.id}
        href={gardenHref(item.id)}
        onClick={onClose}
        aria-current={currentId === item.id ? "page" : undefined}
        className="j-garden-drawer-link"
      >
        <span className="j-soft-icon">
          {item.garden_type === "group" ? (
            <Users aria-hidden="true" />
          ) : (
            <Leaf aria-hidden="true" />
          )}
        </span>
        <span>
          <strong>
            {item.garden_type === "group"
              ? (directory.groupNames[item.owner_group_id ?? ""] ?? item.name)
              : item.name}
          </strong>
          <small>
            {item.garden_type === "group" ? "Shared garden" : "Personal garden"}
            {currentId === item.id ? " · You are here" : ""}
          </small>
        </span>
        <ArrowRight aria-hidden="true" />
      </Link>
    );
  }
  return (
    <dialog
      ref={dialog}
      className="j-garden-drawer"
      aria-labelledby="garden-drawer-title"
      onClose={onClose}
      onClick={(event) => {
        if (event.target !== event.currentTarget) return;
        const rect = event.currentTarget.getBoundingClientRect();
        if (
          event.clientX < rect.left ||
          event.clientX > rect.right ||
          event.clientY < rect.top ||
          event.clientY > rect.bottom
        )
          onClose();
      }}
    >
      <div className="j-garden-drawer-header">
        <div>
          <p className="j-eyebrow">A LITTLE CHANGE OF SCENERY</p>
          <h2 id="garden-drawer-title">Your gardens</h2>
        </div>
        <button
          className="j-icon-button"
          aria-label="Close garden switcher"
          onClick={onClose}
        >
          <X aria-hidden="true" />
        </button>
      </div>
      <p className="j-garden-drawer-intro">
        One little patch for every circle you call yours.
      </p>
      <nav aria-label="Garden switcher">
        <Link className="j-garden-drawer-all" href="/garden" onClick={onClose}>
          <LayoutGrid aria-hidden="true" />
          Browse all gardens
        </Link>
        {personal.length > 0 && (
          <section>
            <h3 className="j-eyebrow">JUST YOURS</h3>
            {personal.map(gardenLink)}
          </section>
        )}
        <section>
          <h3 className="j-eyebrow">YOUR GROUPS · {groups.length}</h3>
          {groups.map(gardenLink)}
          {!groups.length && (
            <p className="j-empty">
              No group gardens yet. Your personal garden is ready whenever you are.
            </p>
          )}
        </section>
      </nav>
      <div className="j-garden-drawer-footer">
        <p>There’s always room for something new.</p>
        <Link className="j-button secondary" href="/garden?groups=1#garden-groups" onClick={onClose}>
          Manage group gardens
          <ArrowRight aria-hidden="true" />
        </Link>
      </div>
    </dialog>
  );
}
