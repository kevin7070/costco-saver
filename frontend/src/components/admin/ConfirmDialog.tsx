"use client";

import { Dialog, DialogPanel, DialogTitle } from "@headlessui/react";
import { Button } from "@/components/ui/catalyst/button";

export type ConfirmVariant = "danger" | "warning" | "info";

interface ConfirmDialogProps {
  open: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
  variant?: ConfirmVariant;
  loading?: boolean;
}

export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title,
  description,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  variant = "info",
  loading = false,
}: ConfirmDialogProps) {
  const confirmColor =
    variant === "danger" ? "red" : variant === "warning" ? "amber" : undefined;
  return (
    <Dialog open={open} onClose={onClose} className="relative z-50">
      <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
      <div className="fixed inset-0 flex items-center justify-center p-4">
        <DialogPanel className="w-full max-w-sm rounded-lg bg-white p-6 dark:bg-zinc-900">
          <DialogTitle className="mb-2 text-lg font-semibold">{title}</DialogTitle>
          {description && (
            <p className="mb-6 text-sm text-zinc-600 dark:text-zinc-400">
              {description}
            </p>
          )}
          <div className="flex justify-end gap-3">
            <Button outline type="button" onClick={onClose} disabled={loading}>
              {cancelLabel}
            </Button>
            <Button
              color={confirmColor}
              type="button"
              onClick={onConfirm}
              disabled={loading}
            >
              {loading ? "…" : confirmLabel}
            </Button>
          </div>
        </DialogPanel>
      </div>
    </Dialog>
  );
}
