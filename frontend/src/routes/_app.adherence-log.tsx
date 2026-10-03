import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import { ClipboardList, Trash2 } from "lucide-react";
import { api, ApiError, type LogStatus, type MedicationLog } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/adherence-log")({
  component: LogPage,
});

const statusStyles: Record<LogStatus, string> = {
  taken: "bg-success/15 text-success",
  missed: "bg-destructive/15 text-destructive",
  late: "bg-warning/20 text-warning-foreground",
  skipped: "bg-muted text-muted-foreground",
  pending: "bg-info/15 text-info",
};

function LogPage() {
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["logs"],
    queryFn: () => api.get<MedicationLog[]>("/medication-logs/me"),
    retry: false,
  });

  const update = useMutation({
    mutationFn: ({ id, status }: { id: string; status: LogStatus }) =>
      api.patch<MedicationLog>(`/medication-logs/${id}`, { status }),
    onSuccess: () => {
      toast.success("Log updated");
      qc.invalidateQueries({ queryKey: ["logs"] });
      qc.invalidateQueries({ queryKey: ["adherence"] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to update"),
  });

  const del = useMutation({
    mutationFn: (id: string) => api.del(`/medication-logs/${id}`),
    onSuccess: () => {
      toast.success("Log removed");
      qc.invalidateQueries({ queryKey: ["logs"] });
      qc.invalidateQueries({ queryKey: ["adherence"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to remove"),
  });

  return (
    <div>
      <PageHeader title="Adherence Log" description="A complete history of every dose and its status." />

      {q.isLoading ? (
        <div className="space-y-3">{Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} className="h-16 rounded-2xl" />)}</div>
      ) : !q.data || q.data.length === 0 ? (
        <EmptyState icon={ClipboardList} title="No logs yet" description="Once you start taking scheduled doses, they'll show up here." />
      ) : (
        <Card className="rounded-2xl overflow-hidden">
          <div className="divide-y divide-border">
            {q.data.map((l) => (
              <div key={l.id} className="flex items-center gap-4 p-4">
                <div className="min-w-36 text-sm">
                  <div className="tabular-nums">{new Date(l.scheduled_time).toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })}</div>
                  <div className="text-xs text-muted-foreground font-medium">{l.medication_name ? `${l.medication_name} · Dose #${l.dose_index + 1}` : `Dose #${l.dose_index + 1}`}</div>
                </div>
                <span className={cn("text-xs font-semibold uppercase tracking-wide rounded-full px-2.5 py-1", statusStyles[l.status])}>
                  {l.status}
                </span>
                <div className="flex-1 min-w-0 text-sm text-muted-foreground truncate">{l.notes ?? ""}</div>
                {l.status === "pending" && (
                  <div className="flex gap-1">
                    <Button size="sm" variant="secondary" className="rounded-full" onClick={() => update.mutate({ id: l.id, status: "taken" })}>Taken</Button>
                    <Button size="sm" variant="ghost" className="rounded-full" onClick={() => update.mutate({ id: l.id, status: "skipped" })}>Skip</Button>
                  </div>
                )}
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => del.mutate(l.id)}
                  disabled={del.isPending}
                  className="text-muted-foreground hover:text-destructive"
                  title="Remove log"
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
}
