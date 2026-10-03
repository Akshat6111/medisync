import { createFileRoute } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  CalendarHeart,
  ChevronLeft,
  ChevronRight,
  Plus,
  Trash2,
  AlertCircle,
  Info,
  Clock,
  Sparkles,
  Calendar as CalendarIcon,
  Check,
} from "lucide-react";
import {
  format,
  addMonths,
  subMonths,
  startOfMonth,
  endOfMonth,
  startOfWeek,
  endOfWeek,
  isSameMonth,
  isSameDay,
  addDays,
  parseISO,
  isWithinInterval,
} from "date-fns";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cycleApi, type CycleLog, type CyclePrediction } from "@/lib/api";

export const Route = createFileRoute("/_app/cycles")({
  component: CyclesPage,
});

function CyclesPage() {
  const queryClient = useQueryClient();
  const [currentMonth, setCurrentMonth] = useState<Date>(new Date());
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedDate, setSelectedDate] = useState<string>(format(new Date(), "yyyy-MM-dd"));
  const [endDate, setEndDate] = useState<string>("");
  const [actionError, setActionError] = useState<string | null>(null);

  // Queries
  const { data: logs = [], isLoading: logsLoading } = useQuery({
    queryKey: ["cycle-logs"],
    queryFn: () => cycleApi.list(),
  });

  const { data: prediction } = useQuery({
    queryKey: ["cycle-prediction"],
    queryFn: () => cycleApi.prediction(),
  });

  // Mutations
  const createMutation = useMutation({
    mutationFn: (body: { start_date: string; end_date?: string | null }) =>
      cycleApi.create(body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cycle-logs"] });
      queryClient.invalidateQueries({ queryKey: ["cycle-prediction"] });
      setDialogOpen(false);
      setEndDate("");
      setActionError(null);
    },
    onError: (err: any) => {
      setActionError(err?.message || "Failed to save cycle log.");
    },
  });

  const updateMutation = useMutation({
    mutationFn: ({ id, body }: { id: string; body: { start_date?: string; end_date?: string | null } }) =>
      cycleApi.update(id, body),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cycle-logs"] });
      queryClient.invalidateQueries({ queryKey: ["cycle-prediction"] });
      setActionError(null);
    },
    onError: (err: any) => {
      setActionError(err?.message || "Failed to update cycle log.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => cycleApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["cycle-logs"] });
      queryClient.invalidateQueries({ queryKey: ["cycle-prediction"] });
    },
  });

  // Check whether a date is a logged period day
  const isPeriodDay = (dateToCheck: Date) => {
    return logs.some((log) => {
      const start = parseISO(log.start_date);
      const end = log.end_date ? parseISO(log.end_date) : start;
      return (
        isSameDay(dateToCheck, start) ||
        isSameDay(dateToCheck, end) ||
        (dateToCheck >= start && dateToCheck <= end)
      );
    });
  };

  // Find the specific log for a date if any
  const getLogForDate = (dateToCheck: Date) => {
    return logs.find((log) => {
      const start = parseISO(log.start_date);
      const end = log.end_date ? parseISO(log.end_date) : start;
      return (
        isSameDay(dateToCheck, start) ||
        isSameDay(dateToCheck, end) ||
        (dateToCheck >= start && dateToCheck <= end)
      );
    });
  };

  // Check whether a date is in the predicted window
  const isPredictedDay = (dateToCheck: Date) => {
    if (!prediction?.predicted_window_start || !prediction?.predicted_window_end) return false;
    const pStart = parseISO(prediction.predicted_window_start);
    const pEnd = parseISO(prediction.predicted_window_end);
    return dateToCheck >= pStart && dateToCheck <= pEnd;
  };

  // Calendar Day Click Handler
  const handleDayClick = (day: Date) => {
    const formatted = format(day, "yyyy-MM-dd");
    const existingLog = getLogForDate(day);

    if (existingLog) {
      // If day is already part of a log, open dialog pre-populated to allow editing or removing
      setSelectedDate(existingLog.start_date);
      setEndDate(existingLog.end_date || "");
      setDialogOpen(true);
      return;
    }

    // Check if there is an ongoing period without an end date that occurred before this day
    const ongoingLog = logs.find((l) => !l.end_date);
    if (ongoingLog) {
      const ongoingStart = parseISO(ongoingLog.start_date);
      if (day >= ongoingStart) {
        // Set this day as the end date of the ongoing period
        updateMutation.mutate({
          id: ongoingLog.id,
          body: { end_date: formatted },
        });
        return;
      }
    }

    // Otherwise, start a new cycle log for this day
    setSelectedDate(formatted);
    setEndDate("");
    setDialogOpen(true);
  };

  // Calendar generation
  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(monthStart);
  const startDate = startOfWeek(monthStart);
  const endDateGrid = endOfWeek(monthEnd);

  const days: Date[] = [];
  let day = startDate;
  while (day <= endDateGrid) {
    days.push(day);
    day = addDays(day, 1);
  }

  const today = new Date();

  return (
    <div className="space-y-6 max-w-5xl">
      <PageHeader
        title="CycleSync"
        description="Personalized menstrual cycle tracking with adaptive variance predictions based on your personal cycle history."
        action={
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 shadow-sm rounded-full">
                <Plus className="h-4 w-4" />
                Log Period
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Log Menstrual Period</DialogTitle>
                <DialogDescription>
                  Enter the start and optional end date of your period bleeding.
                </DialogDescription>
              </DialogHeader>
              <form
                onSubmit={(e) => {
                  e.preventDefault();
                  createMutation.mutate({
                    start_date: selectedDate,
                    end_date: endDate ? endDate : null,
                  });
                }}
                className="space-y-4 pt-2"
              >
                <div className="space-y-2">
                  <Label htmlFor="start_date">Period Start Date</Label>
                  <Input
                    id="start_date"
                    type="date"
                    required
                    value={selectedDate}
                    onChange={(e) => setSelectedDate(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="end_date">Period End Date (Optional)</Label>
                  <Input
                    id="end_date"
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    placeholder="Leave blank if currently ongoing"
                  />
                  <p className="text-xs text-muted-foreground">
                    Leave blank if your period is currently ongoing.
                  </p>
                </div>

                {actionError && (
                  <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 p-3 rounded-lg">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{actionError}</span>
                  </div>
                )}

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    type="button"
                    variant="outline"
                    className="rounded-full"
                    onClick={() => setDialogOpen(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    type="submit"
                    className="rounded-full"
                    disabled={createMutation.isPending}
                  >
                    {createMutation.isPending ? "Saving..." : "Save Log"}
                  </Button>
                </div>
              </form>
            </DialogContent>
          </Dialog>
        }
      />

      {/* Calendar Card */}
      <Card className="rounded-2xl shadow-sm border-sidebar-border overflow-hidden">
        <CardHeader className="flex flex-row items-center justify-between pb-4 border-b border-border/40">
          <div>
            <CardTitle className="text-xl font-bold tracking-tight">
              {format(currentMonth, "MMMM yyyy")}
            </CardTitle>
            <CardDescription className="text-xs mt-0.5">
              Click any date to log or extend period days
            </CardDescription>
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              className="rounded-full text-xs h-8 px-3"
              onClick={() => setCurrentMonth(new Date())}
            >
              Today
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full"
              onClick={() => setCurrentMonth(subMonths(currentMonth, 1))}
            >
              <ChevronLeft className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 rounded-full"
              onClick={() => setCurrentMonth(addMonths(currentMonth, 1))}
            >
              <ChevronRight className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>

        <CardContent className="p-4 md:p-6">
          {/* Day of Week Headers */}
          <div className="grid grid-cols-7 gap-1 md:gap-2 mb-2 text-center text-xs font-semibold text-muted-foreground uppercase tracking-wider">
            {["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"].map((dayName) => (
              <div key={dayName} className="py-2">
                {dayName}
              </div>
            ))}
          </div>

          {/* Day Cells Grid */}
          <div className="grid grid-cols-7 gap-1 md:gap-2">
            {days.map((d, index) => {
              const inCurrentMonth = isSameMonth(d, currentMonth);
              const isToday = isSameDay(d, today);
              const isPeriod = isPeriodDay(d);
              const isPredicted = isPredictedDay(d);

              return (
                <button
                  key={index}
                  type="button"
                  onClick={() => handleDayClick(d)}
                  className={`relative min-h-[52px] md:min-h-[64px] p-2 rounded-xl text-left flex flex-col justify-between transition-all duration-300 select-none group focus:outline-none focus:ring-2 focus:ring-primary/40 ${
                    !inCurrentMonth ? "opacity-35 text-muted-foreground" : "text-foreground"
                  } ${
                    isPeriod
                      ? "bg-[#fb7185] text-white shadow-sm font-semibold hover:bg-[#f43f5e]"
                      : isPredicted
                      ? "border-2 border-dotted border-primary bg-primary/5 hover:bg-primary/10"
                      : "border border-border/50 hover:border-primary/40 hover:bg-accent/40 bg-card"
                  } ${
                    isToday && !isPeriod
                      ? "ring-2 ring-primary ring-offset-2 dark:ring-offset-background"
                      : ""
                  }`}
                >
                  <div className="flex items-center justify-between w-full">
                    <span
                      className={`text-sm md:text-base font-semibold ${
                        isPeriod
                          ? "text-white"
                          : isToday
                          ? "text-primary font-bold"
                          : ""
                      }`}
                    >
                      {format(d, "d")}
                    </span>

                    {isPeriod && (
                      <span className="h-1.5 w-1.5 rounded-full bg-white opacity-80" />
                    )}
                  </div>

                  {/* Status Indicator inside cell */}
                  <div className="text-[10px] truncate leading-tight">
                    {isPeriod ? (
                      <span className="text-white/90 font-medium">Period</span>
                    ) : isPredicted ? (
                      <span className="text-primary font-medium">Expected</span>
                    ) : isToday ? (
                      <span className="text-primary font-medium">Today</span>
                    ) : null}
                  </div>
                </button>
              );
            })}
          </div>

          {/* Legend */}
          <div className="flex flex-wrap items-center gap-6 mt-6 pt-4 border-t text-xs text-muted-foreground">
            <div className="flex items-center gap-2">
              <span className="h-3.5 w-3.5 rounded-md bg-[#fb7185]" />
              <span>Logged Period</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3.5 w-3.5 rounded-md border-2 border-dotted border-primary bg-primary/5" />
              <span>Predicted Period Window</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-3.5 w-3.5 rounded-md ring-2 ring-primary ring-offset-1" />
              <span>Today</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Cycle Statistics Card — Matching Profile 'Vitals' Card Style */}
      <Card className="rounded-2xl shadow-sm border-sidebar-border">
        <CardHeader className="pb-3">
          <CardTitle className="text-base font-bold">Cycle Statistics & Insights</CardTitle>
          <CardDescription className="text-xs">
            Calculated from your logged historical cycle lengths.
          </CardDescription>
        </CardHeader>
        <CardContent className="grid gap-4 md:grid-cols-3 pt-2">
          {/* Metric 1 */}
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Current Cycle Day</div>
            <div className="text-xl font-bold tracking-tight">
              {prediction?.current_cycle_day ? `Day ${prediction.current_cycle_day}` : "—"}
            </div>
          </div>

          {/* Metric 2 */}
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Average Cycle Length</div>
            <div className="text-xl font-bold tracking-tight">
              {prediction?.average_cycle_length ? (
                <>
                  {prediction.average_cycle_length} <span className="text-sm font-normal text-muted-foreground">days</span>
                  {prediction.std_deviation !== null && prediction.std_deviation > 0 && (
                    <span className="text-xs text-muted-foreground font-normal ml-1">
                      (±{prediction.std_deviation}d)
                    </span>
                  )}
                </>
              ) : (
                <span className="text-sm font-normal text-muted-foreground">
                  Log at least 2 cycles to compute
                </span>
              )}
            </div>
          </div>

          {/* Metric 3 */}
          <div className="space-y-1">
            <div className="text-xs text-muted-foreground">Predicted Next Period</div>
            <div className="text-xl font-bold tracking-tight">
              {prediction?.predicted_window_start && prediction?.predicted_window_end ? (
                (() => {
                  try {
                    const startFmt = format(parseISO(prediction.predicted_window_start), "MMM d");
                    const endFmt = format(parseISO(prediction.predicted_window_end), "MMM d, yyyy");
                    return `${startFmt} – ${endFmt}`;
                  } catch {
                    return prediction.predicted_next_start;
                  }
                })()
              ) : (
                <span className="text-sm font-normal text-muted-foreground">
                  Log a few cycles to see predictions
                </span>
              )}
            </div>
          </div>
        </CardContent>

        {/* Calm Anomaly Inline Notice */}
        {prediction?.anomaly_flag && (
          <div className="mx-6 mb-6 p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 text-amber-900 dark:text-amber-200 text-xs flex items-start gap-3">
            <Info className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0 mt-0.5" />
            <div className="space-y-0.5">
              <div className="font-semibold text-amber-800 dark:text-amber-300">
                Cycle Pattern Observation
              </div>
              <p className="leading-relaxed">
                {prediction.anomaly_reason ||
                  "Your latest cycle length varied from your personal historical average."}{" "}
                Cycles naturally vary with changes in sleep, stress, travel, or physical activity.
              </p>
            </div>
          </div>
        )}
      </Card>

      {/* Logged Cycles History */}
      <Card className="rounded-2xl shadow-sm border-sidebar-border">
        <CardHeader className="pb-3 flex flex-row items-center justify-between">
          <div>
            <CardTitle className="text-base font-bold">Logged Periods ({logs.length})</CardTitle>
            <CardDescription className="text-xs">
              Past cycle start and end dates recorded for your profile.
            </CardDescription>
          </div>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <div className="py-8 text-center text-sm text-muted-foreground">
              No cycles logged yet. Tap any date on the calendar above to log your first period.
            </div>
          ) : (
            <div className="divide-y divide-border">
              {logs.map((log) => {
                const startFmt = format(parseISO(log.start_date), "MMM d, yyyy");
                const endFmt = log.end_date
                  ? format(parseISO(log.end_date), "MMM d, yyyy")
                  : "Ongoing";
                const durationDays = log.end_date
                  ? (parseISO(log.end_date).getTime() - parseISO(log.start_date).getTime()) /
                      (1000 * 3600 * 24) +
                    1
                  : null;

                return (
                  <div
                    key={log.id}
                    className="py-3 flex items-center justify-between hover:bg-muted/20 px-2 rounded-lg transition-colors"
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-8 w-8 rounded-full bg-[#fb7185]/15 flex items-center justify-center text-[#fb7185] shrink-0">
                        <CalendarIcon className="h-4 w-4" />
                      </div>
                      <div>
                        <div className="text-sm font-semibold">
                          {startFmt} → {endFmt}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          {durationDays
                            ? `${durationDays} ${durationDays === 1 ? "day" : "days"} bleeding`
                            : "Ongoing period"}
                        </div>
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-8 w-8 text-muted-foreground hover:text-destructive"
                      onClick={() => {
                        if (confirm("Delete this logged period?")) {
                          deleteMutation.mutate(log.id);
                        }
                      }}
                      disabled={deleteMutation.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                );
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
