import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Bell } from "lucide-react";
import { api, type Notification } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Card } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

export const Route = createFileRoute("/_app/notifications")({
  component: NotificationsPage,
});

function NotificationsPage() {
  const qc = useQueryClient();
  const q = useQuery({
    queryKey: ["notifications"],
    queryFn: () => api.get<Notification[]>("/notifications/me"),
    retry: false,
  });

  const markRead = useMutation({
    mutationFn: (id: string) => api.patch(`/notifications/${id}/read`),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["notifications"] }),
  });

  return (
    <div>
      <PageHeader title="Notifications" description="Reminders and alerts about your medications." />
      {q.isLoading ? (
        <div className="space-y-3">{Array.from({ length: 4 }).map((_, i) => <Skeleton key={i} className="h-20 rounded-2xl" />)}</div>
      ) : !q.data || q.data.length === 0 ? (
        <EmptyState icon={Bell} title="You're all caught up" description="No notifications right now." />
      ) : (
        <div className="space-y-2">
          {q.data.map((n) => (
            <Card
              key={n.id}
              onClick={() => !n.is_read && markRead.mutate(n.id)}
              className={cn(
                "rounded-2xl p-4 flex gap-4 cursor-pointer transition-colors",
                n.is_read ? "bg-card" : "bg-accent/40 border-primary/30",
              )}
            >
              <div className={cn("h-10 w-10 rounded-full flex items-center justify-center shrink-0", n.is_read ? "bg-muted text-muted-foreground" : "bg-primary text-primary-foreground")}>
                <Bell className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className={cn("font-medium truncate", !n.is_read && "text-foreground")}>{n.title}</h3>
                  {!n.is_read && <span className="h-2 w-2 rounded-full bg-destructive" />}
                </div>
                <p className="text-sm text-muted-foreground mt-0.5">{n.message}</p>
                <div className="text-xs text-muted-foreground mt-1">{new Date(n.created_at).toLocaleString()}</div>
              </div>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
