"use client";

import { type ReactNode } from "react";

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export function EmptyState({ title, description, action }: EmptyStateProps) {
  return (
    <div className="rounded-lg border border-dashed border-zinc-300 p-12 text-center dark:border-zinc-700">
      <h3 className="mb-2 font-semibold">{title}</h3>
      {description && (
        <p className="mb-4 text-sm text-zinc-600 dark:text-zinc-400">
          {description}
        </p>
      )}
      {action}
    </div>
  );
}
