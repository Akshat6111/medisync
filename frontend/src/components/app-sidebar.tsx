import { Link, useRouterState } from "@tanstack/react-router";
import {
  LayoutDashboard,
  User,
  Pill,
  CalendarClock,
  ClipboardList,
  Bell,
  Settings,
  FileHeart,
  FileText,
  CalendarHeart,
  Users,
  HeartPulse,
  Sparkles,
  Hospital as HospitalIcon,
  BadgePercent,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface NavItem {
  to: string;
  label: string;
  icon: React.ComponentType<{ className?: string; strokeWidth?: number }>;
}

interface NavSection {
  title: string;
  items: NavItem[];
}

const navSections: NavSection[] = [
  {
    title: "Overview",
    items: [{ to: "/dashboard", label: "Dashboard", icon: LayoutDashboard }],
  },
  {
    title: "Medications",
    items: [
      { to: "/medications", label: "Medications", icon: Pill },
      { to: "/schedule", label: "Schedule", icon: CalendarClock },
      { to: "/adherence-log", label: "Adherence Log", icon: ClipboardList },
    ],
  },
  {
    title: "Health Tools",
    items: [
      { to: "/reports", label: "Lab Reports", icon: FileText },
      { to: "/cycles", label: "Cycle Tracking", icon: CalendarHeart },
      { to: "/generic-finder", label: "Price Check", icon: BadgePercent },
      { to: "/hospitals", label: "Nearby Hospitals", icon: HospitalIcon },
      { to: "/chat", label: "Health Assistant", icon: Sparkles },
    ],
  },
  {
    title: "Account",
    items: [
      { to: "/profile", label: "My Profile", icon: User },
      { to: "/notifications", label: "Notifications", icon: Bell },
      { to: "/settings", label: "Settings", icon: Settings },
    ],
  },
];

const disabled = [
  { label: "Health Records", icon: FileHeart },
  { label: "Caregivers", icon: Users },
] as const;

export function AppSidebar() {
  const pathname = useRouterState({ select: (s) => s.location.pathname });

  return (
    <aside className="hidden md:flex w-64 shrink-0 flex-col border-r border-sidebar-border bg-sidebar text-sidebar-foreground h-screen sticky top-0">
      <div className="flex items-center gap-3 px-6 py-5 border-b border-sidebar-border shrink-0">
        <img
          src="/favicon.png"
          alt="MediSync"
          className="h-9 w-9 rounded-xl object-contain shadow-xs"
        />
        <div>
          <div className="font-bold tracking-tight">MediSync</div>
          <div className="text-[11px] text-muted-foreground -mt-0.5">Personal health</div>
        </div>
      </div>

      <nav className="px-3 py-4 flex-1 space-y-5 overflow-y-auto">
        {navSections.map((section) => (
          <div key={section.title} className="space-y-1">
            <div className="px-4 pb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
              {section.title}
            </div>
            {section.items.map((item) => {
              const active = pathname === item.to || pathname.startsWith(item.to + "/");
              const Icon = item.icon;
              return (
                <Link
                  key={item.to}
                  to={item.to}
                  className={cn(
                    "flex items-center gap-3 rounded-full px-4 py-2 text-sm font-medium transition-colors",
                    active
                      ? "bg-accent text-accent-foreground font-semibold"
                      : "text-sidebar-foreground/80 hover:bg-sidebar-accent/60 hover:text-sidebar-accent-foreground",
                  )}
                >
                  <Icon className="h-4.5 w-4.5 shrink-0" strokeWidth={active ? 2.25 : 1.75} />
                  <span>{item.label}</span>
                </Link>
              );
            })}
          </div>
        ))}

        <div className="pt-3 border-t border-sidebar-border/70 space-y-1">
          <div className="px-4 pb-1 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
            Coming soon
          </div>
          {disabled.map(({ label, icon: Icon }) => (
            <div
              key={label}
              className="flex items-center gap-3 rounded-full px-4 py-2 text-sm font-medium text-muted-foreground/60 cursor-not-allowed"
              aria-disabled="true"
            >
              <Icon className="h-4.5 w-4.5 shrink-0" strokeWidth={1.75} />
              <span>{label}</span>
              <span className="ml-auto text-[10px] rounded-full bg-muted px-2 py-0.5 font-normal">Soon</span>
            </div>
          ))}
        </div>
      </nav>
    </aside>
  );
}
