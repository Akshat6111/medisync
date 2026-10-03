import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery } from "@tanstack/react-query";
import {
  Activity,
  Bell,
  CalendarClock,
  Loader2,
  Pill,
  Coins,
  ArrowRight,
  UserCheck,
  PlusCircle,
  AlertCircle,
  Plus,
  ScanLine,
  Sparkles,
} from "lucide-react";
import {
  api,
  type AdherenceStats,
  type Medication,
  type Notification,
  type Patient,
  type ScheduleResponse,
} from "@/lib/api";
import { StatCard } from "@/components/stat-card";
import { useAuth } from "@/lib/auth";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Button } from "@/components/ui/button";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { format, parseISO } from "date-fns";

export const Route = createFileRoute("/_app/dashboard")({
  component: DashboardPage,
});

function greeting() {
  const h = new Date().getHours();
  if (h < 12) return "Good morning";
  if (h < 18) return "Good afternoon";
  return "Good evening";
}

function DashboardPage() {
  const { user } = useAuth();

  const patient = useQuery({
    queryKey: ["patient"],
    queryFn: async () => {
      try {
        return await api.get<Patient>("/patients/");
      } catch (err: any) {
        if (err?.status === 404) return null;
        return null;
      }
    },
    retry: false,
  });

  const meds = useQuery({
    queryKey: ["medications"],
    queryFn: async () => {
      try {
        return await api.get<Medication[]>("/medications/");
      } catch (err: any) {
        if (err?.status === 404) return [];
        return [];
      }
    },
    retry: false,
  });

  const adherence = useQuery({
    queryKey: ["adherence"],
    queryFn: async () => {
      try {
        return await api.get<AdherenceStats>("/analytics/adherence");
      } catch (err: any) {
        return {
          total_doses: 0,
          eligible_doses: 0,
          taken: 0,
          missed: 0,
          late: 0,
          skipped: 0,
          pending: 0,
          adherence_rate: 0,
        };
      }
    },
    retry: false,
  });

  const schedule = useQuery({
    queryKey: ["schedule"],
    queryFn: async () => {
      try {
        return await api.get<ScheduleResponse>("/schedule/me");
      } catch (err: any) {
        return { success: true, schedule: [], conflict: null };
      }
    },
    retry: false,
  });

  const notif = useQuery({
    queryKey: ["notifications"],
    queryFn: async () => {
      try {
        return await api.get<Notification[]>("/notifications/me");
      } catch (err: any) {
        return [];
      }
    },
    retry: false,
  });

  const medCount = meds.data?.length ?? 0;
  const rate = adherence.data ? Math.round(adherence.data.adherence_rate) : 0;
  const dosesToday = schedule.data?.schedule?.length ?? 0;
  const unread = (notif.data ?? []).filter((n) => !n.is_read).length;

  const chartData = adherence.data
    ? [
        { name: "Taken", value: adherence.data.taken, fill: "var(--success)" },
        { name: "Missed", value: adherence.data.missed, fill: "var(--destructive)" },
        { name: "Late", value: adherence.data.late, fill: "var(--warning)" },
        { name: "Skipped", value: adherence.data.skipped, fill: "var(--muted-foreground)" },
      ]
    : [];

  const donut = [
    { name: "Adherence", value: rate, fill: "var(--primary)" },
    { name: "Rest", value: Math.max(0, 100 - rate), fill: "var(--muted)" },
  ];

  const upcoming = (schedule.data?.schedule ?? []).slice(0, 4);
  const hasLoggedDoses = (adherence.data?.total_doses ?? 0) > 0;
  const hasMedications = (meds.data ?? []).length > 0;

  // Loading skeleton while initial data resolves
  if (meds.isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-28 w-full rounded-2xl" />
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-24 rounded-2xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <Skeleton className="h-72 lg:col-span-2 rounded-2xl" />
          <Skeleton className="h-72 rounded-2xl" />
        </div>
      </div>
    );
  }

  // State 1: Zero medications -> Empty-state Onboarding Prompt
  if (!hasMedications) {
    return (
      <div>
        <div className="rounded-2xl bg-hero-mint p-6 md:p-8 mb-6 border border-border/60">
          <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
            {greeting()}, {user?.full_name?.split(" ")[0] ?? "there"}
          </h1>
          <p className="text-muted-foreground mt-1">Here's what's happening with your health today.</p>
        </div>

        {/* Prominent Onboarding Card / Banner */}
        <div className="mb-8 rounded-2xl border border-primary/25 bg-gradient-to-br from-primary/15 via-card to-card p-6 md:p-8 shadow-sm">
          <div className="max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-primary/20 text-primary text-xs font-semibold mb-3">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Get Started</span>
            </div>
            <h2 className="text-2xl md:text-3xl font-bold tracking-tight text-foreground">
              Let's get you set up
            </h2>
            <p className="text-muted-foreground mt-2 text-sm md:text-base leading-relaxed">
              Add your first medication to start tracking your schedule and adherence.
            </p>
            <div className="flex flex-wrap items-center gap-3.5 mt-6">
              <Button asChild size="default" className="rounded-xl gap-2 font-semibold shadow-xs px-5">
                <Link to="/medications">
                  <Plus className="h-4 w-4" />
                  <span>Add Medication Manually</span>
                </Link>
              </Button>
              <Button asChild size="default" variant="outline" className="rounded-xl gap-2 font-semibold border-primary/30 hover:bg-primary/5 px-5">
                <Link to="/medications">
                  <ScanLine className="h-4 w-4 text-primary" />
                  <span>Scan a Prescription</span>
                </Link>
              </Button>
            </div>
          </div>
        </div>

        {/* Visually De-emphasized Stat Cards below banner */}
        <div className="space-y-3 opacity-60 grayscale-[25%] pointer-events-none select-none">
          <div className="text-xs font-semibold uppercase tracking-wider text-muted-foreground px-1">
            Health Metrics (Pending first medication)
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4">
            <StatCard label="Medications tracked" value="0" icon={Pill} tint="teal" />
            <StatCard label="Adherence rate" value="—" icon={Activity} tint="blue" />
            <StatCard label="Doses today" value="0" icon={CalendarClock} tint="amber" />
            <StatCard label="Unread alerts" value={unread} icon={Bell} tint="rose" />
          </div>
        </div>
      </div>
    );
  }

  // State 2: Normal Dashboard (Stats + Charts) once user has >= 1 medication
  return (
    <div>
      <div className="rounded-2xl bg-hero-mint p-6 md:p-8 mb-6 border border-border/60">
        <h1 className="text-2xl md:text-3xl font-bold tracking-tight">
          {greeting()}, {user?.full_name?.split(" ")[0] ?? "there"}
        </h1>
        <p className="text-muted-foreground mt-1">Here's what's happening with your health today.</p>
      </div>

      {/* Profile Onboarding Callout if patient record is missing */}
      {!patient.isLoading && patient.data === null && (
        <div className="mb-6 rounded-2xl border border-primary/30 bg-primary/5 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="h-10 w-10 rounded-xl bg-primary/20 text-primary flex items-center justify-center shrink-0">
              <UserCheck className="h-5 w-5" />
            </div>
            <div>
              <div className="font-semibold text-foreground text-sm">Complete your health profile</div>
              <p className="text-xs text-muted-foreground mt-0.5 max-w-xl">
                Set your routine wake-up, meal, and sleep times so our engine can generate tailored medication schedules and check for potential drug interactions.
              </p>
            </div>
          </div>
          <Button asChild size="sm" className="rounded-xl shrink-0 font-semibold shadow-xs">
            <Link to="/profile">
              <span>Set Up Routine</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </Button>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-6">
        <StatCard label="Medications tracked" value={medCount} icon={Pill} tint="teal" />
        <StatCard label="Adherence rate" value={`${rate}%`} icon={Activity} tint="blue" />
        <StatCard label="Doses today" value={dosesToday} icon={CalendarClock} tint="amber" />
        <StatCard label="Unread alerts" value={unread} icon={Bell} tint="rose" />
      </div>

      {schedule.data?.conflict && (
        <div className="mb-6 rounded-2xl border border-warning/40 bg-warning/10 p-5">
          <div className="flex items-start gap-3">
            <div className="h-9 w-9 rounded-full bg-warning/30 flex items-center justify-center text-warning-foreground shrink-0">
              <AlertCircle className="h-5 w-5" />
            </div>
            <div>
              <div className="font-semibold">Possible medication conflict</div>
              <p className="text-sm text-muted-foreground mt-0.5">{schedule.data.conflict.reason}</p>
              {schedule.data.conflict.detail && (
                <p className="text-sm mt-1">{schedule.data.conflict.detail}</p>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Generic Price Finder Banner */}
      <div className="mb-6 rounded-2xl bg-gradient-to-r from-emerald-500/15 via-teal-500/10 to-card border border-emerald-500/25 p-5 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div className="flex items-start gap-3.5">
          <div className="h-10 w-10 rounded-xl bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 flex items-center justify-center shrink-0">
            <Coins className="h-5 w-5" />
          </div>
          <div>
            <div className="font-bold text-foreground text-sm flex items-center gap-2">
              <span>Prescription Price & Generic Substitute Engine</span>
              <span className="text-[10px] bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 font-bold px-2 py-0.5 rounded-full">
                Save up to 80%
              </span>
            </div>
            <p className="text-xs text-muted-foreground mt-0.5">
              Compare pharmacy prices across PharmEasy, 1mg, and PMBJP Jan Aushadhi Kendras for all your medications.
            </p>
          </div>
        </div>
        <Button asChild size="sm" className="rounded-xl shrink-0 gap-1.5 font-semibold bg-emerald-600 hover:bg-emerald-700 text-white shadow-xs">
          <Link to="/generic-finder">
            <span>Check Generic Prices</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </Link>
        </Button>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2 rounded-2xl">
          <CardHeader>
            <CardTitle>Adherence breakdown</CardTitle>
          </CardHeader>
          <CardContent>
            {adherence.isLoading ? (
              <Skeleton className="h-64 w-full rounded-xl" />
            ) : !hasLoggedDoses ? (
              <div className="h-64 flex flex-col items-center justify-center text-center p-6 border border-dashed border-border/80 rounded-xl bg-muted/20">
                <Activity className="h-9 w-9 text-muted-foreground/40 mb-2" />
                <div className="font-medium text-sm text-foreground">No adherence records yet</div>
                <p className="text-xs text-muted-foreground mt-1 max-w-sm">
                  As you log your daily medication doses as taken, missed, or late, your full visual breakdown will appear here.
                </p>
              </div>
            ) : (
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" opacity={0.3} />
                    <XAxis dataKey="name" fontSize={12} />
                    <YAxis fontSize={12} allowDecimals={false} />
                    <Tooltip />
                    <Bar dataKey="value" radius={[8, 8, 0, 0]}>
                      {chartData.map((d, i) => <Cell key={i} fill={d.fill} />)}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardHeader>
            <CardTitle>Adherence rate</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-col items-center">
            {adherence.isLoading ? (
              <Skeleton className="h-48 w-48 rounded-full" />
            ) : !hasLoggedDoses ? (
              <div className="flex flex-col items-center justify-center py-6 text-center">
                <div className="h-32 w-32 rounded-full border-4 border-dashed border-muted flex flex-col items-center justify-center">
                  <span className="text-2xl font-bold text-muted-foreground">—</span>
                  <span className="text-[10px] text-muted-foreground uppercase tracking-wider">no doses yet</span>
                </div>
                <p className="text-xs text-muted-foreground mt-4 max-w-xs">
                  Adherence is calculated automatically based on your scheduled vs. confirmed doses.
                </p>
              </div>
            ) : (
              <>
                <div className="relative h-48 w-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={donut} innerRadius={62} outerRadius={82} startAngle={90} endAngle={-270} dataKey="value" stroke="none">
                        {donut.map((d, i) => <Cell key={i} fill={d.fill} />)}
                      </Pie>
                    </PieChart>
                  </ResponsiveContainer>
                  <div className="absolute inset-0 flex flex-col items-center justify-center">
                    <span className="text-4xl font-bold">{rate}%</span>
                    <span className="text-xs text-muted-foreground">on time</span>
                  </div>
                </div>
                {adherence.data && (
                  <div className="grid grid-cols-2 gap-x-6 gap-y-1 mt-4 text-sm w-full">
                    <div className="flex justify-between"><span className="text-muted-foreground">Taken</span><span className="font-medium">{adherence.data.taken}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Missed</span><span className="font-medium">{adherence.data.missed}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Late</span><span className="font-medium">{adherence.data.late}</span></div>
                    <div className="flex justify-between"><span className="text-muted-foreground">Skipped</span><span className="font-medium">{adherence.data.skipped}</span></div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>

        <Card className="lg:col-span-3 rounded-2xl">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Upcoming doses</CardTitle>
            {upcoming.length > 0 && (
              <Button asChild variant="ghost" size="sm" className="gap-1 text-xs font-semibold">
                <Link to="/schedule">View Full Schedule</Link>
              </Button>
            )}
          </CardHeader>
          <CardContent>
            {schedule.isLoading ? (
              <div className="flex items-center gap-2 text-muted-foreground py-4">
                <Loader2 className="h-4 w-4 animate-spin" /> Loading schedule…
              </div>
            ) : upcoming.length === 0 ? (
              <div className="py-8 text-center flex flex-col items-center">
                <CalendarClock className="h-8 w-8 text-muted-foreground/40 mb-2" />
                <p className="text-sm font-medium">No upcoming doses scheduled</p>
                <p className="text-xs text-muted-foreground mt-1 max-w-sm">
                  Add your prescription medications to automatically generate your optimized daily dosing timeline.
                </p>
                <Button asChild size="sm" className="mt-4 rounded-xl gap-1.5 font-semibold">
                  <Link to="/medications">
                    <PlusCircle className="h-4 w-4" />
                    <span>Add Medication</span>
                  </Link>
                </Button>
              </div>
            ) : (
              <ul className="divide-y divide-border">
                {upcoming.map((s, i) => (
                  <li key={`${s.medication_id}-${s.dose_index}-${i}`} className="flex items-center gap-4 py-3">
                    <div className="h-10 w-10 rounded-full bg-accent text-accent-foreground flex items-center justify-center shrink-0">
                      <Pill className="h-5 w-5" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium truncate">{s.medication_name}</div>
                      <div className="text-xs text-muted-foreground">Dose #{s.dose_index + 1}</div>
                    </div>
                    <div className="text-sm font-semibold tabular-nums text-foreground bg-muted/60 px-2.5 py-1 rounded-lg">
                      {formatTime(s.scheduled_time)}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

function formatTime(iso: string) {
  try {
    if (/^\d{2}:\d{2}$/.test(iso)) {
      const [hStr, mStr] = iso.split(":");
      const h = parseInt(hStr, 10);
      const m = parseInt(mStr, 10);
      const period = h >= 12 ? "PM" : "AM";
      const h12 = h % 12 || 12;
      return `${h12}:${m.toString().padStart(2, "0")} ${period}`;
    }
    return format(parseISO(iso), "p");
  } catch {
    return iso;
  }
}

