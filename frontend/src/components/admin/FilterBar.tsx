"use client";

import { type ReactNode } from "react";

interface FilterBarProps {
  search: string;
  onSearchChange: (value: string) => void;
  searchPlaceholder?: string;
  children?: ReactNode;
  onClear?: () => void;
  hasActiveFilters?: boolean;
}

export function FilterBar({
  search,
  onSearchChange,
  searchPlaceholder = "Search…",
  children,
  onClear,
  hasActiveFilters = false,
}: FilterBarProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-3">
      <input
        type="search"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder={searchPlaceholder}
        className="w-full max-w-sm rounded-md border border-zinc-300 px-3 py-2 text-sm dark:border-zinc-700 dark:bg-zinc-900"
      />
      {children}
      {hasActiveFilters && onClear && (
        <button
          type="button"
          onClick={onClear}
          className="text-sm text-zinc-600 hover:text-zinc-900 dark:text-zinc-400 dark:hover:text-white"
        >
          Clear all
        </button>
      )}
    </div>
  );
}
