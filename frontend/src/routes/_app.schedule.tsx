import { createFileRoute } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import { AlertTriangle, CalendarClock, Pill } from "lucide-react";
import { api, type ScheduleResponse } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

export const Route = createFileRoute("/_app/schedule")({
  component: SchedulePage,
});

function SchedulePage() {
  const q = useQuery({
    queryKey: ["schedule"],
    queryFn: () => api.get<ScheduleResponse>("/schedule/me"),
    retry: false,
  });

  return (
    <div>
      <PageHeader title="Today's Schedule" description="A chronological view of every dose you should take today." />

      {q.data?.conflict && (
        <div className="mb-6 rounded-2xl border border-warning/50 bg-warning/10 p-5">
          <div className="flex items-start gap-3">
            <div className="h-10 w-10 rounded-full bg-warning/30 flex items-center justify-center">
              <AlertTriangle className="h-5 w-5 text-warning-foreground" />
            </div>
            <div>
              <div className="font-semibold">Medication conflict detected</div>
              <p className="text-sm mt-0.5">{q.data.conflict.reason}</p>
              {q.data.conflict.detail && <p className="text-sm text-muted-foreground mt-1">{q.data.conflict.detail}</p>}
              {q.data.conflict.required_gap_hours > 0 && (
                <p className="text-xs text-muted-foreground mt-2">
                  Recommended gap: <span className="font-medium">{q.data.conflict.required_gap_hours}h</span>
                </p>
              )}
            </div>
          </div>
        </div>
      )}

      {q.isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-2xl" />)}
        </div>
      ) : !q.data || !q.data.schedule || q.data.schedule.length === 0 ? (
        q.data?.conflict ? (
          <EmptyState
            icon={AlertTriangle}
            title="Scheduling conflict detected"
            description="Your daily schedule could not be created because of the medication conflict shown above."
          />
        ) : (
          <EmptyState
            icon={CalendarClock}
            title="No doses scheduled today"
            description="Add medications to see your daily schedule here."
          />
        )
      ) : (
        <Card className="rounded-2xl p-2 md:p-4">
          <ol className="relative">
            {q.data.schedule.map((s, i) => {
              const t = formatTime(s.scheduled_time);
              return (
                <li key={`${s.medication_id}-${s.dose_index}-${i}`} className="flex items-center gap-4 py-3 md:py-4 px-2 md:px-3 border-b border-border last:border-b-0">
                  <div className="w-16 text-sm font-semibold tabular-nums text-muted-foreground">{t}</div>
                  <div className="h-10 w-10 rounded-full bg-accent text-accent-foreground flex items-center justify-center shrink-0">
                    <Pill className="h-5 w-5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="font-medium truncate">{s.medication_name}</div>
                    <div className="text-xs text-muted-foreground">Dose #{s.dose_index + 1}</div>
                  </div>
                </li>
              );
            })}
          </ol>
        </Card>
      )}
    </div>
  );
}

function formatTime(iso: string) {
  if (/^\d{2}:\d{2}/.test(iso)) return iso.slice(0, 5);
  try {
    const d = new Date(iso);
    if (!isNaN(d.getTime())) return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  } catch {}
  return iso;
}
