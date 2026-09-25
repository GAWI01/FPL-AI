import type { ReactNode } from "react";


export function DataState({
  title,
  children,
  tone = "neutral",
  loading = false,
}: {
  title: string;
  children?: ReactNode;
  tone?: "neutral" | "warning" | "error";
  loading?: boolean;
}) {
  return (
    <section className={`data-state data-state-${tone}`} role={tone === "error" ? "alert" : "status"} aria-busy={loading || undefined}>
      <strong>{title}</strong>
      {children ? <div>{children}</div> : null}
      {loading ? <div className="data-state-skeleton" aria-hidden="true"><i /><i /><i /></div> : null}
    </section>
  );
}
