import { createFileRoute, Link } from "@tanstack/react-router";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useState, useRef, type ChangeEvent } from "react";
import { toast } from "sonner";
import {
  Loader2,
  Pencil,
  Pill,
  Plus,
  Trash2,
  ScanLine,
  Clock,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Info,
  Sparkles,
  Check,
  BadgePercent,
} from "lucide-react";
import {
  api,
  ApiError,
  prescriptionApi,
  type Medication,
  type MedicationCreate,
  type ParsedMedicationCandidate,
  type PrescriptionParseResponse,
} from "@/lib/api";
import { PageHeader } from "@/components/page-header";
import { EmptyState } from "@/components/empty-state";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

export const Route = createFileRoute("/_app/medications")({
  component: MedicationsPage,
});

const empty: MedicationCreate = {
  name: "",
  dosage_amount: 1,
  dosage_unit: "mg",
  frequency_per_day: 1,
  duration_days: 7,
  route: "oral",
  with_food: false,
  empty_stomach: false,
  bedtime_only: false,
  start_date: new Date().toISOString().slice(0, 10),
  notes: "",
  scheduled_time: undefined,
};

function getDefaultTimes(frequency: number): string[] {
  if (frequency <= 1) return ["08:00"];
  if (frequency === 2) return ["08:00", "20:00"];
  if (frequency === 3) return ["08:00", "14:00", "20:00"];
  if (frequency === 4) return ["08:00", "12:00", "16:00", "20:00"];
  const times: string[] = [];
  const interval = Math.floor(14 / (frequency - 1 || 1));
  for (let i = 0; i < frequency; i++) {
    const h = 8 + i * interval;
    times.push(`${String(Math.min(22, h)).padStart(2, "0")}:00`);
  }
  return times;
}

function MedicationsPage() {
  const qc = useQueryClient();
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<MedicationCreate>(empty);
  const [scheduleMode, setScheduleMode] = useState<"solver" | "manual">("manual");

  const [editingMed, setEditingMed] = useState<Medication | null>(null);
  const [editForm, setEditForm] = useState<MedicationCreate>(empty);
  const [editScheduleMode, setEditScheduleMode] = useState<"solver" | "manual">("manual");

  // RxParse State
  const [scanOpen, setScanOpen] = useState(false);
  const [scanFile, setScanFile] = useState<File | null>(null);
  const [isScanning, setIsScanning] = useState(false);
  const [parsedCandidates, setParsedCandidates] = useState<ParsedMedicationCandidate[]>([]);
  const [scanRawText, setScanRawText] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const startEdit = (m: Medication) => {
    setEditingMed(m);
    const hasManual = Array.isArray(m.scheduled_time) && m.scheduled_time.length > 0;
    setEditScheduleMode(hasManual ? "manual" : "solver");
    setEditForm({
      name: m.name,
      dosage_amount: m.dosage_amount,
      dosage_unit: m.dosage_unit,
      frequency_per_day: m.frequency_per_day,
      duration_days: m.duration_days,
      route: m.route,
      with_food: m.with_food,
      empty_stomach: m.empty_stomach,
      bedtime_only: m.bedtime_only,
      start_date: m.start_date,
      notes: m.notes ?? "",
      scheduled_time: hasManual ? m.scheduled_time : undefined,
    });
  };

  const update = useMutation({
    mutationFn: ({ id, body }: { id: string; body: MedicationCreate }) =>
      api.put<Medication>(`/medications/${id}`, body),
    onSuccess: () => {
      toast.success("Medication updated");
      qc.invalidateQueries({ queryKey: ["medications"] });
      qc.invalidateQueries({ queryKey: ["schedule"] });
      qc.invalidateQueries({ queryKey: ["logs"] });
      setEditingMed(null);
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to update"),
  });

  const q = useQuery({
    queryKey: ["medications"],
    queryFn: () => api.get<Medication[]>("/medications/"),
    retry: false,
  });

  const add = useMutation({
    mutationFn: (body: MedicationCreate) => api.post<Medication>("/medications/", body),
    onSuccess: () => {
      toast.success("Medication added");
      qc.invalidateQueries({ queryKey: ["medications"] });
      qc.invalidateQueries({ queryKey: ["schedule"] });
      qc.invalidateQueries({ queryKey: ["logs"] });
      setOpen(false);
      setForm(empty);
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to add"),
  });

  const del = useMutation({
    mutationFn: (id: string) => api.del(`/medications/${id}`),
    onSuccess: () => {
      toast.success("Medication removed");
      qc.invalidateQueries({ queryKey: ["medications"] });
      qc.invalidateQueries({ queryKey: ["schedule"] });
      qc.invalidateQueries({ queryKey: ["logs"] });
      qc.invalidateQueries({ queryKey: ["adherence"] });
      qc.invalidateQueries({ queryKey: ["notifications"] });
      qc.invalidateQueries({ queryKey: ["dashboard"] });
    },
    onError: (err) => toast.error(err instanceof ApiError ? err.message : "Failed to remove"),
  });

  // Handle RxParse File Selection & Parsing
  const handleFileChange = async (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setScanFile(file);
    setIsScanning(true);
    try {
      const res: PrescriptionParseResponse = await prescriptionApi.parse(file);
      setScanRawText(res.raw_text);
      setParsedCandidates(res.candidates);
      if (res.candidates.length === 0) {
        toast.info("No medications clearly recognized in prescription. You can add manually.");
      } else {
        toast.success(`Recognized ${res.candidates.length} medication candidate(s)`);
      }
    } catch (err: any) {
      toast.error(err?.message || "Failed to parse prescription file");
    } finally {
      setIsScanning(false);
    }
  };

  // Add individual parsed candidate
  const handleAddCandidate = async (cand: ParsedMedicationCandidate, index: number) => {
    const medPayload: MedicationCreate = {
      name: cand.matched_drug_name,
      dosage_amount: cand.dosage_amount,
      dosage_unit: cand.dosage_unit,
      frequency_per_day: cand.frequency_per_day,
      duration_days: cand.duration_days,
      route: cand.route,
      with_food: cand.with_food,
      empty_stomach: cand.empty_stomach,
      bedtime_only: cand.bedtime_only,
      start_date: new Date().toISOString().slice(0, 10),
      notes: cand.notes,
      scheduled_time: cand.suggested_times,
    };

    try {
      await add.mutateAsync(medPayload);
      setParsedCandidates((prev) => prev.filter((_, i) => i !== index));
    } catch (err) {
      // Handled by onError in add mutation
    }
  };

  // Add all reviewed candidates
  const handleAddAllCandidates = async () => {
    if (parsedCandidates.length === 0) return;
    let addedCount = 0;
    for (const cand of parsedCandidates) {
      const medPayload: MedicationCreate = {
        name: cand.matched_drug_name,
        dosage_amount: cand.dosage_amount,
        dosage_unit: cand.dosage_unit,
        frequency_per_day: cand.frequency_per_day,
        duration_days: cand.duration_days,
        route: cand.route,
        with_food: cand.with_food,
        empty_stomach: cand.empty_stomach,
        bedtime_only: cand.bedtime_only,
        start_date: new Date().toISOString().slice(0, 10),
        notes: cand.notes,
        scheduled_time: cand.suggested_times,
      };
      try {
        await api.post<Medication>("/medications/", medPayload);
        addedCount++;
      } catch (err) {
        console.error("Failed to add candidate:", cand.matched_drug_name, err);
      }
    }

    toast.success(`Successfully added ${addedCount} medication(s)`);
    qc.invalidateQueries({ queryKey: ["medications"] });
    qc.invalidateQueries({ queryKey: ["schedule"] });
    qc.invalidateQueries({ queryKey: ["logs"] });
    setScanOpen(false);
    setParsedCandidates([]);
    setScanFile(null);
  };

  return (
    <div>
      <PageHeader
        title="Medications"
        description="Everything you take, on a single clean list."
        action={
          <div className="flex items-center gap-2">
            {/* 1. RxParse Button */}
            <Button
              variant="outline"
              className="rounded-full gap-2 border-primary/30 hover:bg-primary/10"
              onClick={() => {
                setScanOpen(true);
                setParsedCandidates([]);
                setScanFile(null);
              }}
            >
              <ScanLine className="h-4 w-4 text-primary" />
              <span>Scan Prescription</span>
            </Button>

            {/* 2. Add Medication Dialog */}
            <Dialog open={open} onOpenChange={setOpen}>
              <DialogTrigger asChild>
                <Button className="rounded-full">
                  <Plus className="h-4 w-4 mr-1.5" /> Add medication
                </Button>
              </DialogTrigger>
              <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
                <DialogHeader>
                  <DialogTitle>Add a medication</DialogTitle>
                </DialogHeader>
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    add.mutate(form);
                  }}
                  className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2"
                >
                  <F label="Name" full>
                    <Input
                      required
                      value={form.name}
                      onChange={(e) => setForm({ ...form, name: e.target.value })}
                      placeholder="e.g. Metformin"
                    />
                  </F>
                  <F label="Dosage amount">
                    <Input
                      type="number"
                      min={1}
                      required
                      value={form.dosage_amount}
                      onChange={(e) =>
                        setForm({ ...form, dosage_amount: Number(e.target.value) })
                      }
                    />
                  </F>
                  <F label="Dosage unit">
                    <Input
                      required
                      value={form.dosage_unit}
                      onChange={(e) => setForm({ ...form, dosage_unit: e.target.value })}
                      placeholder="mg, ml, tablet"
                    />
                  </F>
                  <F label="Frequency per day">
                    <Input
                      type="number"
                      min={1}
                      max={6}
                      required
                      value={form.frequency_per_day}
                      onChange={(e) => {
                        const freq = Math.max(1, Number(e.target.value));
                        setForm({
                          ...form,
                          frequency_per_day: freq,
                          scheduled_time:
                            scheduleMode === "manual" ? getDefaultTimes(freq) : undefined,
                        });
                      }}
                    />
                  </F>
                  <F label="Duration (days)">
                    <Input
                      type="number"
                      min={1}
                      required
                      value={form.duration_days}
                      onChange={(e) =>
                        setForm({ ...form, duration_days: Number(e.target.value) })
                      }
                    />
                  </F>
                  <F label="Route">
                    <Input
                      required
                      value={form.route}
                      onChange={(e) => setForm({ ...form, route: e.target.value })}
                      placeholder="oral, topical…"
                    />
                  </F>
                  <F label="Start date">
                    <Input
                      type="date"
                      required
                      value={form.start_date}
                      onChange={(e) => setForm({ ...form, start_date: e.target.value })}
                    />
                  </F>

                  <div className="md:col-span-2 flex flex-wrap gap-4 pt-1">
                    <CheckField
                      checked={form.with_food}
                      onChange={(v) => setForm({ ...form, with_food: v })}
                      label="Take with food"
                    />
                    <CheckField
                      checked={form.empty_stomach}
                      onChange={(v) => setForm({ ...form, empty_stomach: v })}
                      label="Empty stomach"
                    />
                    <CheckField
                      checked={form.bedtime_only}
                      onChange={(v) => setForm({ ...form, bedtime_only: v })}
                      label="Bedtime only"
                    />
                  </div>

                  {/* PART 1: Manual Dose Scheduling Options */}
                  <div className="md:col-span-2 space-y-2 border-t pt-3 mt-1">
                    <div className="flex items-center justify-between">
                      <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                        Dose Timing Method
                      </Label>
                      <span className="text-[11px] text-muted-foreground">
                        {scheduleMode === "manual" ? "Exact chosen times" : "Solver calculates gaps"}
                      </span>
                    </div>
                    <div className="flex gap-2">
                      <Button
                        type="button"
                        size="sm"
                        variant={scheduleMode === "manual" ? "default" : "outline"}
                        onClick={() => {
                          setScheduleMode("manual");
                          setForm({
                            ...form,
                            scheduled_time: form.scheduled_time?.length
                              ? form.scheduled_time
                              : getDefaultTimes(form.frequency_per_day),
                          });
                        }}
                        className="rounded-lg text-xs"
                      >
                        <Clock className="h-3.5 w-3.5 mr-1" />
                        Manual Specific Times
                      </Button>
                      <Button
                        type="button"
                        size="sm"
                        variant={scheduleMode === "solver" ? "default" : "outline"}
                        onClick={() => {
                          setScheduleMode("solver");
                          setForm({ ...form, scheduled_time: undefined });
                        }}
                        className="rounded-lg text-xs"
                      >
                        <Sparkles className="h-3.5 w-3.5 mr-1" />
                        Automatic (CSP Solver)
                      </Button>
                    </div>

                    {scheduleMode === "manual" && (
                      <div className="p-3 bg-muted/40 rounded-xl border space-y-2 mt-2">
                        <div className="text-xs font-medium text-foreground">
                          Set time for each of the {form.frequency_per_day} daily dose{form.frequency_per_day > 1 ? "s" : ""}:
                        </div>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                          {Array.from({ length: form.frequency_per_day }).map((_, idx) => (
                            <div key={idx} className="space-y-1">
                              <span className="text-[11px] text-muted-foreground font-medium">
                                Dose #{idx + 1}
                              </span>
                              <Input
                                type="time"
                                required
                                value={form.scheduled_time?.[idx] || "08:00"}
                                onChange={(e) => {
                                  const updated = [
                                    ...(form.scheduled_time ||
                                      getDefaultTimes(form.frequency_per_day)),
                                  ];
                                  updated[idx] = e.target.value;
                                  setForm({ ...form, scheduled_time: updated });
                                }}
                                className="text-xs h-8 bg-background"
                              />
                            </div>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>

                  <F label="Notes" full>
                    <Textarea
                      rows={2}
                      value={form.notes ?? ""}
                      onChange={(e) => setForm({ ...form, notes: e.target.value })}
                      placeholder="Special instructions or precautions…"
                    />
                  </F>
                  <DialogFooter className="md:col-span-2 pt-2">
                    <Button type="button" variant="ghost" onClick={() => setOpen(false)}>
                      Cancel
                    </Button>
                    <Button type="submit" className="rounded-full" disabled={add.isPending}>
                      {add.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Save
                    </Button>
                  </DialogFooter>
                </form>
              </DialogContent>
            </Dialog>
          </div>
        }
      />

      {/* 3. Prescription Digitizer (RxParse) Modal */}
      <Dialog open={scanOpen} onOpenChange={setScanOpen}>
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <div className="flex items-center gap-2">
              <div className="h-9 w-9 rounded-xl bg-primary/10 text-primary flex items-center justify-center">
                <ScanLine className="h-5 w-5" />
              </div>
              <div>
                <DialogTitle>RxParse: Digitize Prescription</DialogTitle>
                <p className="text-xs text-muted-foreground mt-0.5">
                  Upload a prescription photo or scanned PDF to automatically parse medication names, doses, and shorthand timings.
                </p>
              </div>
            </div>
          </DialogHeader>

          {/* Upload Dropzone */}
          <div className="space-y-4 pt-2">
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-border hover:border-primary/60 rounded-2xl p-6 text-center cursor-pointer transition-all bg-muted/20 hover:bg-muted/40"
            >
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.pdf"
                className="hidden"
                onChange={handleFileChange}
              />
              <div className="mx-auto w-12 h-12 rounded-full bg-primary/10 text-primary flex items-center justify-center mb-2">
                {isScanning ? (
                  <Loader2 className="h-6 w-6 animate-spin" />
                ) : (
                  <UploadCloud className="h-6 w-6" />
                )}
              </div>
              <div className="font-semibold text-sm">
                {isScanning
                  ? "Scanning & parsing clinical shorthand..."
                  : scanFile
                  ? scanFile.name
                  : "Click to upload prescription image or PDF"}
              </div>
              <p className="text-xs text-muted-foreground mt-1">
                Supports PNG, JPG, JPEG, and PDF documents
              </p>
            </div>

            {/* Parsed Candidates Review Screen */}
            {parsedCandidates.length > 0 && (
              <div className="space-y-4">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-semibold flex items-center gap-2">
                    <span>Parsed Candidates ({parsedCandidates.length})</span>
                    <Badge variant="secondary" className="text-xs">
                      Ready for review
                    </Badge>
                  </div>
                  <Button
                    size="sm"
                    onClick={handleAddAllCandidates}
                    className="rounded-xl text-xs gap-1.5"
                  >
                    <CheckCircle2 className="h-3.5 w-3.5" />
                    Add All Reviewed
                  </Button>
                </div>

                <div className="space-y-3">
                  {parsedCandidates.map((cand, idx) => {
                    const isHighConfidence = cand.match_confidence >= 80;
                    return (
                      <Card
                        key={idx}
                        className="rounded-2xl border p-4 space-y-3 bg-card/70 shadow-sm"
                      >
                        {/* Header & Confidence Badge */}
                        <div className="flex items-start justify-between gap-2">
                          <div className="space-y-1">
                            <div className="flex items-center gap-2 flex-wrap">
                              <span className="font-bold text-sm text-foreground">
                                {cand.matched_drug_name}
                              </span>
                              <Badge
                                variant="outline"
                                className={`text-[10px] font-bold ${
                                  isHighConfidence
                                    ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30"
                                    : "bg-amber-500/15 text-amber-600 dark:text-amber-400 border-amber-500/30"
                                }`}
                              >
                                {isHighConfidence
                                  ? `${cand.match_confidence}% Match`
                                  : `Needs Review (${cand.match_confidence}%)`}
                              </Badge>

                              {cand.needs_review.times && (
                                <Badge
                                  variant="outline"
                                  className="text-[10px] bg-amber-500/10 text-amber-600 border-amber-500/30"
                                >
                                  Verify Bedtime
                                </Badge>
                              )}

                              <Link
                                to="/generic-finder"
                                search={{ q: cand.matched_drug_name }}
                                target="_blank"
                                className="inline-flex items-center gap-1 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 hover:underline"
                              >
                                <BadgePercent className="h-3 w-3" />
                                <span>Find Generics</span>
                              </Link>
                            </div>
                            <div className="text-[11px] text-muted-foreground italic">
                              Raw text: "{cand.raw_text_snippet}"
                            </div>
                          </div>

                          <Button
                            size="sm"
                            variant="secondary"
                            onClick={() => handleAddCandidate(cand, idx)}
                            className="rounded-lg text-xs h-8 shrink-0"
                          >
                            <Plus className="h-3 w-3 mr-1" /> Add
                          </Button>
                        </div>

                        {/* Editable Candidate Fields */}
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 pt-1 text-xs">
                          {/* Drug Name Edit */}
                          <div className="space-y-1">
                            <Label className="text-[11px] text-muted-foreground flex items-center gap-1">
                              Drug Name
                              {cand.needs_review.drug_name && (
                                <span className="text-amber-600">*</span>
                              )}
                            </Label>
                            <Input
                              value={cand.matched_drug_name}
                              onChange={(e) => {
                                const val = e.target.value;
                                setParsedCandidates((prev) =>
                                  prev.map((c, i) =>
                                    i === idx ? { ...c, matched_drug_name: val } : c
                                  )
                                );
                              }}
                              className={`h-8 text-xs ${
                                cand.needs_review.drug_name
                                  ? "border-amber-500 bg-amber-500/5"
                                  : ""
                              }`}
                            />
                          </div>

                          {/* Dosage Amount & Unit */}
                          <div className="space-y-1">
                            <Label className="text-[11px] text-muted-foreground flex items-center gap-1">
                              Dosage
                              {cand.needs_review.dosage && (
                                <span className="text-amber-600">*</span>
                              )}
                            </Label>
                            <div className="flex gap-1">
                              <Input
                                type="number"
                                min={1}
                                value={cand.dosage_amount}
                                onChange={(e) => {
                                  const val = Number(e.target.value);
                                  setParsedCandidates((prev) =>
                                    prev.map((c, i) =>
                                      i === idx ? { ...c, dosage_amount: val } : c
                                    )
                                  );
                                }}
                                className={`h-8 text-xs w-16 ${
                                  cand.needs_review.dosage
                                    ? "border-amber-500 bg-amber-500/5"
                                    : ""
                                }`}
                              />
                              <Input
                                value={cand.dosage_unit}
                                onChange={(e) => {
                                  const val = e.target.value;
                                  setParsedCandidates((prev) =>
                                    prev.map((c, i) =>
                                      i === idx ? { ...c, dosage_unit: val } : c
                                    )
                                  );
                                }}
                                className="h-8 text-xs"
                              />
                            </div>
                          </div>

                          {/* Frequency */}
                          <div className="space-y-1">
                            <Label className="text-[11px] text-muted-foreground flex items-center gap-1">
                              Daily Doses
                              {cand.needs_review.frequency && (
                                <span className="text-amber-600">*</span>
                              )}
                            </Label>
                            <Input
                              type="number"
                              min={1}
                              max={6}
                              value={cand.frequency_per_day}
                              onChange={(e) => {
                                const val = Math.max(1, Number(e.target.value));
                                setParsedCandidates((prev) =>
                                  prev.map((c, i) =>
                                    i === idx
                                      ? {
                                          ...c,
                                          frequency_per_day: val,
                                          suggested_times: getDefaultTimes(val),
                                        }
                                      : c
                                  )
                                );
                              }}
                              className="h-8 text-xs"
                            />
                          </div>

                          {/* Duration */}
                          <div className="space-y-1">
                            <Label className="text-[11px] text-muted-foreground">
                              Duration (days)
                            </Label>
                            <Input
                              type="number"
                              min={1}
                              value={cand.duration_days}
                              onChange={(e) => {
                                const val = Number(e.target.value);
                                setParsedCandidates((prev) =>
                                  prev.map((c, i) =>
                                    i === idx ? { ...c, duration_days: val } : c
                                  )
                                );
                              }}
                              className="h-8 text-xs"
                            />
                          </div>
                        </div>

                        {/* Scheduled Times per dose */}
                        <div className="p-2.5 rounded-xl bg-muted/40 border space-y-1.5">
                          <div className="text-[11px] font-semibold text-muted-foreground flex items-center gap-1.5">
                            <Clock className="h-3 w-3 text-primary" />
                            <span>Scheduled Times (from shorthand):</span>
                            {cand.needs_review.times && (
                              <span className="text-amber-600 font-normal">
                                (Please verify timing)
                              </span>
                            )}
                          </div>
                          <div className="flex flex-wrap gap-2">
                            {cand.suggested_times.map((t, timeIdx) => (
                              <div key={timeIdx} className="flex items-center gap-1">
                                <span className="text-[10px] text-muted-foreground">
                                  #{timeIdx + 1}
                                </span>
                                <Input
                                  type="time"
                                  value={t}
                                  onChange={(e) => {
                                    const val = e.target.value;
                                    setParsedCandidates((prev) =>
                                      prev.map((c, i) => {
                                        if (i !== idx) return c;
                                        const updatedTimes = [...c.suggested_times];
                                        updatedTimes[timeIdx] = val;
                                        return { ...c, suggested_times: updatedTimes };
                                      })
                                    );
                                  }}
                                  className="h-7 w-24 text-xs bg-background"
                                />
                              </div>
                            ))}
                          </div>
                        </div>

                        {/* Food / Bedtime toggles */}
                        <div className="flex items-center gap-4 text-xs text-muted-foreground pt-1">
                          <label className="flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={cand.with_food}
                              onChange={(e) => {
                                const chk = e.target.checked;
                                setParsedCandidates((prev) =>
                                  prev.map((c, i) =>
                                    i === idx ? { ...c, with_food: chk } : c
                                  )
                                );
                              }}
                              className="rounded border-border"
                            />
                            <span>Take with food</span>
                          </label>

                          <label className="flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={cand.empty_stomach}
                              onChange={(e) => {
                                const chk = e.target.checked;
                                setParsedCandidates((prev) =>
                                  prev.map((c, i) =>
                                    i === idx ? { ...c, empty_stomach: chk } : c
                                  )
                                );
                              }}
                              className="rounded border-border"
                            />
                            <span>Empty stomach</span>
                          </label>

                          <label className="flex items-center gap-1.5 cursor-pointer">
                            <input
                              type="checkbox"
                              checked={cand.bedtime_only}
                              onChange={(e) => {
                                const chk = e.target.checked;
                                setParsedCandidates((prev) =>
                                  prev.map((c, i) =>
                                    i === idx ? { ...c, bedtime_only: chk } : c
                                  )
                                );
                              }}
                              className="rounded border-border"
                            />
                            <span>Bedtime only</span>
                          </label>
                        </div>
                      </Card>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => {
                setScanOpen(false);
                setParsedCandidates([]);
              }}
            >
              Close
            </Button>
            {parsedCandidates.length > 0 && (
              <Button
                type="button"
                onClick={handleAddAllCandidates}
                className="rounded-full gap-1.5"
              >
                <CheckCircle2 className="h-4 w-4" />
                Add All ({parsedCandidates.length}) to Medications
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 4. Medications List */}
      {q.isLoading ? (
        <div className="grid gap-3">
          {Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-24 rounded-2xl" />
          ))}
        </div>
      ) : !q.data || q.data.length === 0 ? (
        <EmptyState
          icon={Pill}
          title="No medications yet"
          description="Add your first medication to start tracking doses and adherence."
          action={
            <Button className="rounded-full" onClick={() => setOpen(true)}>
              <Plus className="h-4 w-4 mr-1.5" /> Add medication
            </Button>
          }
        />
      ) : (
        <div className="grid gap-3">
          {q.data.map((m) => (
            <Card key={m.id} className="rounded-2xl p-5 flex items-start gap-4">
              <div className="h-11 w-11 rounded-full bg-accent text-accent-foreground flex items-center justify-center shrink-0">
                <Pill className="h-5 w-5" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 flex-wrap">
                  <h3 className="font-semibold truncate">{m.name}</h3>
                  <span className="text-sm text-muted-foreground">
                    {m.dosage_amount} {m.dosage_unit} · {m.frequency_per_day}× / day · {m.route}
                  </span>
                </div>

                <div className="mt-1.5 flex flex-wrap gap-1.5">
                  {m.with_food && <Badge variant="secondary">With food</Badge>}
                  {m.empty_stomach && <Badge variant="secondary">Empty stomach</Badge>}
                  {m.bedtime_only && <Badge variant="secondary">Bedtime only</Badge>}
                </div>

                {/* Scheduled Times Badge (if manual) */}
                {Array.isArray(m.scheduled_time) && m.scheduled_time.length > 0 && (
                  <div className="mt-2 flex items-center gap-1.5 flex-wrap">
                    <Clock className="h-3.5 w-3.5 text-primary shrink-0" />
                    <span className="text-xs font-medium text-muted-foreground mr-1">
                      Scheduled:
                    </span>
                    {m.scheduled_time.map((t, idx) => (
                      <span
                        key={idx}
                        className="text-xs font-semibold px-2 py-0.5 rounded-md bg-primary/10 text-primary border border-primary/20"
                      >
                        {t}
                      </span>
                    ))}
                  </div>
                )}

                <div className="text-xs text-muted-foreground mt-2">
                  {m.start_date} → {m.end_date}
                </div>
                {m.notes && <p className="text-sm text-muted-foreground mt-2">{m.notes}</p>}

                <div className="mt-3 pt-2.5 border-t border-border/40 flex items-center justify-between">
                  <Link
                    to="/generic-finder"
                    search={{ q: m.name }}
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:underline transition-colors"
                  >
                    <BadgePercent className="h-3.5 w-3.5" />
                    <span>Compare Pharmacy Prices & Generics</span>
                  </Link>
                </div>
              </div>

              <div className="flex items-center gap-1">
                <Button
                  variant="ghost"
                  size="icon"
                  className="text-muted-foreground hover:text-foreground"
                  onClick={() => startEdit(m)}
                  title="Edit medication"
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="text-muted-foreground hover:text-destructive"
                      disabled={del.isPending}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Remove {m.name}?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will remove the medication and its associated logs. This action cannot be undone.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={() => del.mutate(m.id)}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      >
                        Remove
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            </Card>
          ))}
        </div>
      )}

      {/* 5. Edit Medication Dialog */}
      <Dialog
        open={!!editingMed}
        onOpenChange={(o) => {
          if (!o) setEditingMed(null);
        }}
      >
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit medication</DialogTitle>
          </DialogHeader>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (editingMed) update.mutate({ id: editingMed.id, body: editForm });
            }}
            className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2"
          >
            <F label="Name" full>
              <Input
                required
                value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
              />
            </F>
            <F label="Dosage amount">
              <Input
                type="number"
                min={1}
                required
                value={editForm.dosage_amount}
                onChange={(e) =>
                  setEditForm({ ...editForm, dosage_amount: Number(e.target.value) })
                }
              />
            </F>
            <F label="Dosage unit">
              <Input
                required
                value={editForm.dosage_unit}
                onChange={(e) => setEditForm({ ...editForm, dosage_unit: e.target.value })}
              />
            </F>
            <F label="Frequency per day">
              <Input
                type="number"
                min={1}
                max={6}
                required
                value={editForm.frequency_per_day}
                onChange={(e) => {
                  const freq = Math.max(1, Number(e.target.value));
                  setEditForm({
                    ...editForm,
                    frequency_per_day: freq,
                    scheduled_time:
                      editScheduleMode === "manual" ? getDefaultTimes(freq) : undefined,
                  });
                }}
              />
            </F>
            <F label="Duration (days)">
              <Input
                type="number"
                min={1}
                required
                value={editForm.duration_days}
                onChange={(e) =>
                  setEditForm({ ...editForm, duration_days: Number(e.target.value) })
                }
              />
            </F>
            <F label="Route">
              <Input
                required
                value={editForm.route}
                onChange={(e) => setEditForm({ ...editForm, route: e.target.value })}
              />
            </F>
            <F label="Start date">
              <Input
                type="date"
                required
                value={editForm.start_date}
                onChange={(e) => setEditForm({ ...editForm, start_date: e.target.value })}
              />
            </F>
            <div className="md:col-span-2 flex flex-wrap gap-4 pt-1">
              <CheckField
                checked={editForm.with_food}
                onChange={(v) => setEditForm({ ...editForm, with_food: v })}
                label="Take with food"
              />
              <CheckField
                checked={editForm.empty_stomach}
                onChange={(v) => setEditForm({ ...editForm, empty_stomach: v })}
                label="Empty stomach"
              />
              <CheckField
                checked={editForm.bedtime_only}
                onChange={(v) => setEditForm({ ...editForm, bedtime_only: v })}
                label="Bedtime only"
              />
            </div>

            {/* Manual Dose Timing for Edit Dialog */}
            <div className="md:col-span-2 space-y-2 border-t pt-3">
              <div className="flex items-center justify-between">
                <Label className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                  Dose Timing Method
                </Label>
              </div>
              <div className="flex gap-2">
                <Button
                  type="button"
                  size="sm"
                  variant={editScheduleMode === "manual" ? "default" : "outline"}
                  onClick={() => {
                    setEditScheduleMode("manual");
                    setEditForm({
                      ...editForm,
                      scheduled_time: editForm.scheduled_time?.length
                        ? editForm.scheduled_time
                        : getDefaultTimes(editForm.frequency_per_day),
                    });
                  }}
                  className="rounded-lg text-xs"
                >
                  <Clock className="h-3.5 w-3.5 mr-1" />
                  Manual Specific Times
                </Button>
                <Button
                  type="button"
                  size="sm"
                  variant={editScheduleMode === "solver" ? "default" : "outline"}
                  onClick={() => {
                    setEditScheduleMode("solver");
                    setEditForm({ ...editForm, scheduled_time: undefined });
                  }}
                  className="rounded-lg text-xs"
                >
                  <Sparkles className="h-3.5 w-3.5 mr-1" />
                  Automatic (CSP Solver)
                </Button>
              </div>

              {editScheduleMode === "manual" && (
                <div className="p-3 bg-muted/40 rounded-xl border space-y-2 mt-2">
                  <div className="text-xs font-medium text-foreground">
                    Set times for {editForm.frequency_per_day} dose{editForm.frequency_per_day > 1 ? "s" : ""}:
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
                    {Array.from({ length: editForm.frequency_per_day }).map((_, idx) => (
                      <div key={idx} className="space-y-1">
                        <span className="text-[11px] text-muted-foreground font-medium">
                          Dose #{idx + 1}
                        </span>
                        <Input
                          type="time"
                          required
                          value={editForm.scheduled_time?.[idx] || "08:00"}
                          onChange={(e) => {
                            const updated = [
                              ...(editForm.scheduled_time ||
                                getDefaultTimes(editForm.frequency_per_day)),
                            ];
                            updated[idx] = e.target.value;
                            setEditForm({ ...editForm, scheduled_time: updated });
                          }}
                          className="text-xs h-8 bg-background"
                        />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            <F label="Notes" full>
              <Textarea
                rows={2}
                value={editForm.notes ?? ""}
                onChange={(e) => setEditForm({ ...editForm, notes: e.target.value })}
              />
            </F>
            <DialogFooter className="md:col-span-2 pt-2">
              <Button type="button" variant="ghost" onClick={() => setEditingMed(null)}>
                Cancel
              </Button>
              <Button type="submit" className="rounded-full" disabled={update.isPending}>
                {update.isPending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />} Save changes
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function F({
  label,
  children,
  full,
}: {
  label: string;
  children: React.ReactNode;
  full?: boolean;
}) {
  return (
    <div className={`space-y-1.5 ${full ? "md:col-span-2" : ""}`}>
      <Label className="text-xs font-medium">{label}</Label>
      {children}
    </div>
  );
}

function CheckField({
  checked,
  onChange,
  label,
}: {
  checked: boolean;
  onChange: (v: boolean) => void;
  label: string;
}) {
  return (
    <label className="flex items-center gap-2 cursor-pointer text-sm">
      <Checkbox checked={checked} onCheckedChange={(c) => onChange(Boolean(c))} />
      <span>{label}</span>
    </label>
  );
}
