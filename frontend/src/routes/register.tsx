import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { HeartPulse, Loader2 } from "lucide-react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useAuth } from "@/lib/auth";
import { ApiError } from "@/lib/api";

export const Route = createFileRoute("/register")({
  ssr: false,
  component: RegisterPage,
});

function RegisterPage() {
  const { register, login } = useAuth();
  const navigate = useNavigate();
  const [full_name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (password.length < 8) {
      toast.error("Password must be at least 8 characters");
      return;
    }
    setLoading(true);
    try {
      await register({ full_name, email, password });
      await login(email, password);
      toast.success("Account created — welcome!");
      navigate({ to: "/dashboard" });
    } catch (err) {
      const msg = err instanceof ApiError ? err.message : "Registration failed";
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
            Build a routine<br />your health can rely on.
          </h1>
          <p className="mt-4 text-muted-foreground">
            Log medications, get smart reminders, and see your adherence trends at a glance.
          </p>
        </div>
        <div className="text-xs text-muted-foreground">© {new Date().getFullYear()} MediSync</div>
      </div>

      <div className="flex items-center justify-center p-6 md:p-12 bg-background">
        <form onSubmit={onSubmit} className="w-full max-w-sm space-y-5">
          <div>
            <h2 className="text-2xl font-bold">Create your account</h2>
            <p className="text-sm text-muted-foreground mt-1">Start syncing your medications in seconds.</p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="full_name">Full name</Label>
            <Input id="full_name" required value={full_name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">Email</Label>
            <Input id="email" type="email" required autoComplete="email" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password">Password</Label>
            <Input id="password" type="password" required autoComplete="new-password" minLength={8} value={password} onChange={(e) => setPassword(e.target.value)} />
            <p className="text-xs text-muted-foreground">At least 8 characters.</p>
          </div>
          <Button type="submit" className="w-full rounded-full" disabled={loading}>
            {loading && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Create account
          </Button>
          <p className="text-sm text-center text-muted-foreground">
            Already have an account?{" "}
            <Link to="/login" className="text-primary font-medium hover:underline">
              Sign in
            </Link>
          </p>
        </form>
      </div>
    </div>
  );
}
