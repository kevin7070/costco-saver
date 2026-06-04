/**
 * Admin component barrel — import from @/components/admin.
 */

export { DataTable } from "./DataTable";
export type { Column, SortDirection } from "./DataTable";

export { FilterBar } from "./FilterBar";
export { PageHeader } from "./PageHeader";
export type { Breadcrumb } from "./PageHeader";

export { ConfirmDialog } from "./ConfirmDialog";
export type { ConfirmVariant } from "./ConfirmDialog";

export { EmptyState } from "./EmptyState";

export {
  StatusBadge,
  ItemStatusBadge,
  getItemVariant,
} from "./StatusBadge";
export type { BadgeVariant, ItemStatus } from "./StatusBadge";
