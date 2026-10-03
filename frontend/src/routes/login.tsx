import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { HeartPulse, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export const Route = createFileRoute("/login")({
  ssr: false,
  component: LoginPage,
});

function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    try {
      await login(email, password);
      toast.success("Welcome back!");
      navigate({ to: "/dashboard" });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Login failed";
      toast.error(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen grid md:grid-cols-2 bg-hero-mint">
      <div className="hidden md:flex flex-col justify-between p-12">
        <div className="flex items-center gap-3">
          <img
            src="/favicon.png"
            alt="MediSync"
            className="h-10 w-10 rounded-xl object-contain shadow-xs"
          />
          <span className="text-lg font-bold">MediSync</span>
        </div>
        <div className="max-w-md">
          <h1 className="text-4xl font-bold tracking-tight leading-tight">
            Your medications,<br />on track and in sync.
          </h1>
          <p className="mt-4 text-muted-foreground">
            A calm, personal health dashboard to keep your daily routine, doses, and adherence in one place.
          </p>
        </div>
        <div className="text-xs text-muted-foreground">© {new Date().getFullYear()} MediSync</div>
      </div>

      <div className="flex items-center justify-center p-6 md:p-12 bg-background">
        <form onSubmit={onSubmit} className="w-full max-w-sm space-y-5">
          <div>
            <h2 className="text-2xl font-bold">Sign in</h2>
            <p className="text-sm text-muted-foreground mt-1">Welcome back — enter your details.</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" required autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
          <Button type="submit" className="w-full rounded-full" disabled={loading}>
            {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Sign in
          </Button>
          <p className="text-sm text-center text-muted-foreground">
            New to MediSync?{" "}
            <Link to="/register" className="text-primary font-medium hover:underline">
              Create an account
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
