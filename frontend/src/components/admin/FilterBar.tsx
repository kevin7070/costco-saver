"use client";

import { type ReactNode } from "react";

import { Button } from "@/components/ui/catalyst/button";
import { Input } from "@/components/ui/catalyst/input";

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
      <Input
        type="search"
        value={search}
        onChange={(e) => onSearchChange(e.target.value)}
        placeholder={searchPlaceholder}
        className="max-w-sm"
      />
      {children}
      {hasActiveFilters && onClear && (
        <Button plain type="button" onClick={onClear}>
          Clear all
        </Button>
      )}
    </div>
  );
}
