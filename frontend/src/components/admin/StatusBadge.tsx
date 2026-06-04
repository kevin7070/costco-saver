"use client";

import { clsx } from "clsx";

export type BadgeVariant =
  | "success"
  | "warning"
  | "error"
  | "info"
  | "purple"
  | "muted";

const variantClasses: Record<BadgeVariant, string> = {
  success: "bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400",
  warning: "bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400",
  error: "bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400",
  info: "bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400",
  purple: "bg-purple-100 text-purple-700 dark:bg-purple-900/30 dark:text-purple-400",
  muted: "bg-zinc-100 text-zinc-700 dark:bg-zinc-800 dark:text-zinc-400",
};

interface StatusBadgeProps {
  variant: BadgeVariant;
  children: React.ReactNode;
  className?: string;
}

export function StatusBadge({ variant, children, className }: StatusBadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
        variantClasses[variant],
        className,
      )}
    >
      {children}
    </span>
  );
}

// Domain-specific badge example for items.
// Each project should add its own domain badges here and
// call StatusBadge internally — do not use the generic
// StatusBadge directly in pages.

export type ItemStatus = "active" | "archived";

export function getItemVariant(status: ItemStatus): BadgeVariant {
  switch (status) {
    case "active":
      return "success";
    case "archived":
      return "muted";
    default:
      return "muted";
  }
}

export function ItemStatusBadge({ status }: { status: ItemStatus }) {
  return <StatusBadge variant={getItemVariant(status)}>{status}</StatusBadge>;
}
