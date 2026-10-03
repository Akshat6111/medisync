import { createFileRoute } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import { toast } from "sonner";
import { Loader2, Pencil, User } from "lucide-react";
import { api, ApiError, type Patient, type PatientCreate } from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";

export const Route = createFileRoute("/_app/profile")({
  component: ProfilePage,
});

const emptyForm: PatientCreate = {
  full_name: "",
  date_of_birth: "",
  gender: "",
  height_cm: null,
  weight_kg: null,
  blood_group: "",
  allergies: "",
  medical_conditions: "",
  wake_up_time: "07:00",
  breakfast_time: "08:00",
  lunch_time: "13:00",
  dinner_time: "20:00",
  sleep_time: "23:00",
};

function ProfilePage() {
  const qc = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState<PatientCreate>(emptyForm);

  const q = useQuery({
    queryKey: ["patient"],
    queryFn: async () => {
      try {
        return await api.get<Patient>("/patients/");
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) return null;
        throw err;
      }
    },
    retry: false,
  });

  useEffect(() => {
    if (q.data) setForm({ ...(q.data as Patient) });
  }, [q.data]);

  const save = useMutation({
    mutationFn: (body: PatientCreate) =>
      q.data ? api.put<Patient>("/patients/", body) : api.post<Patient>("/patients/", body),
    onSuccess: (data) => {
      toast.success("Profile saved");
      qc.setQueryData(["patient"], data);
      setEditing(false);
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to save"),
  });

  if (q.isLoading) {
    return (
      <div className="space-y-4">
        <Skeleton className="h-8 w-64" />
        <Skeleton className="h-64 w-full rounded-2xl" />
      </div>
    );
  }

  const patient = q.data;
  const showForm = editing || !patient;

  return (
    <div>
      <PageHeader
        title="My Profile"
        description="Your personal health info powers reminders and adherence tracking."
        action={
          patient && !editing ? (
            <Button className="rounded-full" onClick={() => setEditing(true)}>
              <Pencil className="h-4 w-4 mr-2" /> Edit profile
            </Button>
          ) : null
        }
      />

      {!patient && !editing && (
        <EmptyState
          icon={User}
          title="Complete your profile"
          description="Add your basic info and daily routine so MediSync can schedule your doses smartly."
          action={<Button className="rounded-full" onClick={() => setEditing(true)}>Create profile</Button>}
        />
      )}

      {showForm && (
        <form
          onSubmit={(e) => { e.preventDefault(); save.mutate(form); }}
          className="space-y-6"
        >
          <Section title="Basic Info">
            <Field label="Full name">
              <Input required value={form.full_name} onChange={(e) => setForm({ ...form, full_name: e.target.value })} />
            </Field>
            <Field label="Date of birth">
              <Input type="date" required value={form.date_of_birth} onChange={(e) => setForm({ ...form, date_of_birth: e.target.value })} />
            </Field>
            <Field label="Gender">
              <Input required value={form.gender} onChange={(e) => setForm({ ...form, gender: e.target.value })} placeholder="Female / Male / Other" />
            </Field>
            <Field label="Blood group">
              <Input value={form.blood_group ?? ""} onChange={(e) => setForm({ ...form, blood_group: e.target.value })} placeholder="A+, O-, …" />
            </Field>
          </Section>

          <Section title="Vitals">
            <Field label="Height (cm)">
              <Input type="number" value={form.height_cm ?? ""} onChange={(e) => setForm({ ...form, height_cm: e.target.value ? Number(e.target.value) : null })} />
            </Field>
            <Field label="Weight (kg)">
              <Input type="number" value={form.weight_kg ?? ""} onChange={(e) => setForm({ ...form, weight_kg: e.target.value ? Number(e.target.value) : null })} />
            </Field>
          </Section>

          <Section title="Medical History">
            <Field label="Allergies" full>
              <Textarea rows={2} value={form.allergies ?? ""} onChange={(e) => setForm({ ...form, allergies: e.target.value })} placeholder="e.g. Penicillin, peanuts" />
            </Field>
            <Field label="Medical conditions" full>
              <Textarea rows={2} value={form.medical_conditions ?? ""} onChange={(e) => setForm({ ...form, medical_conditions: e.target.value })} placeholder="e.g. Hypertension, Type 2 diabetes" />
            </Field>
          </Section>

          <Section title="Daily Routine Times">
            {(["wake_up_time", "breakfast_time", "lunch_time", "dinner_time", "sleep_time"] as const).map((k) => (
              <Field key={k} label={labelForTime(k)}>
                <Input type="time" required value={form[k]} onChange={(e) => setForm({ ...form, [k]: e.target.value })} />
              </Field>
            ))}
          </Section>

          <div className="flex gap-2 justify-end">
            {patient && (
              <Button type="button" variant="ghost" className="rounded-full" onClick={() => { setEditing(false); setForm(patient); }}>
                Cancel
              </Button>
            )}
            <Button type="submit" className="rounded-full" disabled={save.isPending}>
              {save.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Save profile
            </Button>
          </div>
        </form>
      )}

      {patient && !editing && (
        <div className="grid gap-4 md:grid-cols-2">
          <ReadCard title="Basic Info">
            <Info label="Full name" value={patient.full_name} />
            <Info label="Date of birth" value={patient.date_of_birth} />
            <Info label="Gender" value={patient.gender} />
            <Info label="Blood group" value={patient.blood_group ?? "—"} />
          </ReadCard>
          <ReadCard title="Vitals">
            <Info label="Height" value={patient.height_cm ? `${patient.height_cm} cm` : "—"} />
            <Info label="Weight" value={patient.weight_kg ? `${patient.weight_kg} kg` : "—"} />
          </ReadCard>
          <ReadCard title="Medical History" className="md:col-span-2">
            <Info label="Allergies" value={patient.allergies || "None recorded"} />
            <Info label="Medical conditions" value={patient.medical_conditions || "None recorded"} />
          </ReadCard>
          <ReadCard title="Daily Routine" className="md:col-span-2">
            <Info label="Wake up" value={patient.wake_up_time} />
            <Info label="Breakfast" value={patient.breakfast_time} />
            <Info label="Lunch" value={patient.lunch_time} />
            <Info label="Dinner" value={patient.dinner_time} />
            <Info label="Sleep" value={patient.sleep_time} />
          </ReadCard>
        </div>
      )}
    </div>
  );
}

function labelForTime(k: string) {
  return k.replace("_time", "").replace("_", " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <Card className="rounded-2xl">
      <CardHeader><CardTitle className="text-base">{title}</CardTitle></CardHeader>
      <CardContent className="grid gap-4 md:grid-cols-2">{children}</CardContent>
    </Card>
  );
}

function Field({ label, children, full }: { label: string; children: React.ReactNode; full?: boolean }) {
  return (
    <div className={full ? "md:col-span-2 space-y-2" : "space-y-2"}>
      <Label>{label}</Label>
      {children}
    </div>
  );
}

function ReadCard({ title, children, className }: { title: string; children: React.ReactNode; className?: string }) {
  return (
    <Card className={`rounded-2xl ${className ?? ""}`}>
      <CardHeader><CardTitle className="text-base">{title}</CardTitle></CardHeader>
      <CardContent className="grid gap-3 md:grid-cols-2">{children}</CardContent>
    </Card>
  );
}

function Info({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="font-medium">{value}</div>
    </div>
  );
}
