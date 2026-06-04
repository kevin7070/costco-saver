"use client";

import Link from "next/link";
import { type ReactNode } from "react";

export interface Breadcrumb {
  label: string;
  href?: string;
}

interface PageHeaderProps {
  title: string;
  breadcrumbs?: Breadcrumb[];
  actions?: ReactNode;
}

export function PageHeader({ title, breadcrumbs, actions }: PageHeaderProps) {
  return (
    <header className="mb-6 flex flex-wrap items-start justify-between gap-4">
      <div>
        {breadcrumbs && breadcrumbs.length > 0 && (
          <nav className="mb-1 text-xs text-zinc-500">
            {breadcrumbs.map((crumb, i) => (
              <span key={i}>
                {crumb.href ? (
                  <Link href={crumb.href} className="hover:underline">
                    {crumb.label}
                  </Link>
                ) : (
                  crumb.label
                )}
                {i < breadcrumbs.length - 1 && " / "}
              </span>
            ))}
          </nav>
        )}
        <h1 className="text-2xl font-bold">{title}</h1>
      </div>
      {actions && <div className="flex gap-2">{actions}</div>}
    </header>
  );
}
