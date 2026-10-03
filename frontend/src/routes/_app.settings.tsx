import { createFileRoute } from "@tanstack/react-router";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { LogOut } from "lucide-react";
import { useNavigate } from "@tanstack/react-router";

export const Route = createFileRoute("/_app/settings")({
  component: SettingsPage,
});

function SettingsPage() {
  const { user, logout } = useAuth();
  const { theme, toggle } = useTheme();
  const navigate = useNavigate();

  const doLogout = () => {
    logout();
    navigate({ to: "/login" });
  };

  return (
    <div>
      <PageHeader title="Settings" description="Manage your MediSync preferences and account." />

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="rounded-2xl">
          <CardHeader><CardTitle className="text-base">Account</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            <div>
              <div className="text-xs text-muted-foreground">Name</div>
              <div className="font-medium">{user?.full_name ?? "—"}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Email</div>
              <div className="font-medium">{user?.email ?? "—"}</div>
            </div>
            <div>
              <div className="text-xs text-muted-foreground">Role</div>
              <div className="font-medium">{user?.role ?? "PATIENT"}</div>
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl">
          <CardHeader><CardTitle className="text-base">Appearance</CardTitle></CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div>
                <Label>Dark mode</Label>
                <p className="text-xs text-muted-foreground">Easier on the eyes at night.</p>
              </div>
              <Switch checked={theme === "dark"} onCheckedChange={toggle} />
            </div>
          </CardContent>
        </Card>

        <Card className="rounded-2xl md:col-span-2">
          <CardHeader><CardTitle className="text-base">Session</CardTitle></CardHeader>
          <CardContent>
            <Button variant="destructive" className="rounded-full" onClick={doLogout}>
              <LogOut className="h-4 w-4 mr-2" /> Sign out
            </Button>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
