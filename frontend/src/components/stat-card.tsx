import type { LucideIcon } from "lucide-react";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";
import { cn } from "@/lib/utils";

type Tint = "teal" | "blue" | "amber" | "rose";

const tintMap: Record<Tint, string> = {
  teal: "bg-accent text-accent-foreground",
  blue: "bg-info/15 text-info",
  amber: "bg-warning/20 text-warning-foreground",
  rose: "bg-destructive/15 text-destructive",
};

export function StatCard({
  label,
  value,
  delta,
  icon: Icon,
  tint = "teal",
  suffix,
}: {
  label: string;
  value: string | number;
  delta?: number | null;
  icon: LucideIcon;
  tint?: Tint;
  suffix?: string;
}) {
  const positive = (delta ?? 0) >= 0;
  return (
    <div className="rounded-2xl bg-card border border-border/60 shadow-sm p-5 flex flex-col gap-2">
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
          {label}
        </span>
        <span className={cn("flex h-9 w-9 items-center justify-center rounded-full", tintMap[tint])}>
          <Icon className="h-4.5 w-4.5" strokeWidth={2} />
        </span>
      </div>
      <div className="flex items-baseline gap-1">
        <span className="text-3xl font-bold tracking-tight">{value}</span>
        {suffix && <span className="text-lg font-semibold text-muted-foreground">{suffix}</span>}
      </div>
      {delta !== undefined && delta !== null && (
        <div
          className={cn(
            "flex items-center gap-1 text-xs font-medium",
            positive ? "text-success" : "text-destructive",
          )}
        >
          {positive ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
          <span>
            {positive ? "+" : ""}
            {delta}% vs last week
          </span>
        </div>
      )}
    </div>
  );
}
