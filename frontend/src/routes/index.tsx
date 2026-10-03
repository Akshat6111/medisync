import { createFileRoute, redirect } from "@tanstack/react-router";

export const Route = createFileRoute("/")({
  ssr: false,
  beforeLoad: () => {
    const token = typeof window !== "undefined" ? window.localStorage.getItem("medisync_token") : null;
    throw redirect({ to: token ? "/dashboard" : "/login" });
  },
});
