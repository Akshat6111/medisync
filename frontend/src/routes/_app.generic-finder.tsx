import { createFileRoute, Link } from "@tanstack/react-router";
import { useState, useEffect } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";
import {
  Search,
  Sparkles,
  ExternalLink,
  Loader2,
  TrendingDown,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Coins,
  Pill,
  Clock,
  Building2,
  Database,
  Flame,
  Copy,
  Check,
  Calculator,
  ArrowRight,
  Info,
  Layers,
  HeartHandshake,
  BadgeCheck,
  Plus,
  RefreshCw,
  SlidersHorizontal,
} from "lucide-react";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";
import {
  api,
  genericFinderApi,
  type GenericFinderResponse,
  type PharmacyPriceItem,
  type CabinetSavingsResponse,
  type CabinetSavingsItem,
  type MedicationCreate,
} from "@/lib/api";

type GenericFinderSearch = {
  q?: string;
};

export const Route = createFileRoute("/_app/generic-finder")({
  validateSearch: (search: Record<string, unknown>): GenericFinderSearch => {
    return {
      q: typeof search.q === "string" ? search.q : undefined,
    };
  },
  component: GenericFinderPage,
});

const POPULAR_CATEGORIES = [
  {
    category: "Pain & Fever",
    icon: Flame,
    medicines: ["Dolo 650", "Combiflam", "Meftal Forte", "Zerodol-P", "Calpol 650"],
  },
  {
    category: "Antibiotics",
    icon: ShieldCheck,
    medicines: ["Augmentin 625 Duo", "Azithral 500", "Zifi 200", "Ciplox 500", "Ceftum 500"],
  },
  {
    category: "Acidity & Digestion",
    icon: Layers,
    medicines: ["Pan 40", "Pan-D", "Omez 20", "Razo 20", "Emeset 4"],
  },
  {
    category: "Allergy & Cough",
    icon: Pill,
    medicines: ["Montair LC", "Allegra 120", "Levocet 5", "Ascoril LS Syrup", "Cetzine 10"],
  },
  {
    category: "Diabetes",
    icon: Coins,
    medicines: ["Glycomet 500", "Galvus 50", "Januvia 100", "Jardiance 10", "Forxiga 10"],
  },
  {
    category: "Blood Pressure & Heart",
    icon: HeartHandshake,
    medicines: ["Telma 40", "Amlong 5", "Atorva 10", "Ecosprin 75", "Betaloc 50"],
  },
  {
    category: "Thyroid & Vitamins",
    icon: Sparkles,
    medicines: ["Thyronorm 50", "Shelcal 500", "Becosules", "Evion 400", "Limcee 500"],
  },
];

function GenericFinderPage() {
  const searchParams = Route.useSearch();
  const initialQuery =
    searchParams.q?.trim() ||
    (typeof window !== "undefined"
      ? new URLSearchParams(window.location.search).get("q")?.trim()
      : "") ||
    "Dolo 650";

  const [searchInput, setSearchInput] = useState(initialQuery);
  const [activeQuery, setActiveQuery] = useState(initialQuery);
  const [filterSource, setFilterSource] = useState<string>("ALL");
  const [selectedCategoryIndex, setSelectedCategoryIndex] = useState(0);

  // Sync when search parameter in URL changes
  useEffect(() => {
    if (searchParams.q && searchParams.q.trim() !== activeQuery) {
      setSearchInput(searchParams.q.trim());
      setActiveQuery(searchParams.q.trim());
    }
  }, [searchParams.q]);

  // Interactive Calculator State
  const [dosesPerDay, setDosesPerDay] = useState(1);
  const [durationDays, setDurationDays] = useState(30);

  // Cabinet Analysis Dialog State
  const [cabinetDialogOpen, setCabinetDialogOpen] = useState(false);

  // Add Medication Dialog State
  const [addMedDialogOpen, setAddMedDialogOpen] = useState(false);
  const [selectedSubstituteToAdd, setSelectedSubstituteToAdd] = useState<{
    brand_name: string;
    generic_name: string;
  } | null>(null);

  const [addMedForm, setAddMedForm] = useState<MedicationCreate>({
    name: "",
    dosage_amount: 1,
    dosage_unit: "tablet",
    frequency_per_day: 1,
    duration_days: 30,
    route: "oral",
    with_food: true,
    empty_stomach: false,
    bedtime_only: false,
    start_date: new Date().toISOString().slice(0, 10),
    notes: "Switched to generic equivalent formulation via GenericFinder.",
  });

  const [copiedDoctorNote, setCopiedDoctorNote] = useState(false);

  const qc = useQueryClient();

  // Query 1: Active Medicine Price Comparison
  const { data, isLoading, isFetching, refetch } = useQuery<GenericFinderResponse>({
    queryKey: ["generic-finder-search", activeQuery],
    queryFn: () => genericFinderApi.search(activeQuery),
    enabled: Boolean(activeQuery && activeQuery.trim().length >= 2),
    staleTime: 1000 * 60 * 5,
  });

  // Query 2: Patient's Cabinet Savings
  const cabinetQuery = useQuery<CabinetSavingsResponse>({
    queryKey: ["cabinet-savings"],
    queryFn: () => genericFinderApi.cabinetSavings(),
    enabled: cabinetDialogOpen,
    staleTime: 1000 * 60 * 2,
  });

  // Mutation: Add Generic to Medications Cabinet
  const addMedMutation = useMutation({
    mutationFn: (medData: MedicationCreate) => api.post("/medications/", medData),
    onSuccess: () => {
      toast.success("Medication added to your MediSync cabinet!");
      qc.invalidateQueries({ queryKey: ["medications"] });
      qc.invalidateQueries({ queryKey: ["cabinet-savings"] });
      setAddMedDialogOpen(false);
    },
    onError: (err: any) => {
      toast.error(err?.message || "Failed to add medication.");
    },
  });

  const handleSearchSubmit = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const trimmed = searchInput.trim();
    if (trimmed.length >= 2) {
      setActiveQuery(trimmed);
    }
  };

  const handleChipClick = (medName: string) => {
    setSearchInput(medName);
    setActiveQuery(medName);
  };

  const handleOpenAddMedModal = (brandName: string, genericName: string) => {
    setSelectedSubstituteToAdd({ brand_name: brandName, generic_name: genericName });
    setAddMedForm({
      name: brandName,
      dosage_amount: 1,
      dosage_unit: "tablet",
      frequency_per_day: dosesPerDay,
      duration_days: durationDays,
      route: "oral",
      with_food: true,
      empty_stomach: false,
      bedtime_only: false,
      start_date: new Date().toISOString().slice(0, 10),
      notes: `Generic equivalent of ${data?.query_matched_to || "prescribed brand"} (${genericName}).`,
    });
    setAddMedDialogOpen(true);
  };

  const results = data?.results ?? [];
  const filteredResults =
    filterSource === "ALL"
      ? results
      : results.filter((r) => r.pharmacy_source.toLowerCase() === filterSource.toLowerCase());

  const availableSources = Array.from(new Set(results.map((r) => r.pharmacy_source)));

  // Dynamic Savings Calculator Math
  const totalTabletsNeeded = Math.round(dosesPerDay * durationDays);
  const baselineBrandPricePerTab = (data?.most_expensive_price || 35.0) / 10.0;
  const cheapestPricePerTab = (data?.cheapest_option?.price || 12.0) / 10.0;
  const pmbjpPricePerTab = (data?.pmbjp_reference?.typical_price || 9.5) / 10.0;

  const totalBrandCost = Math.round(totalTabletsNeeded * baselineBrandPricePerTab);
  const totalCheapestCost = Math.round(totalTabletsNeeded * cheapestPricePerTab);
  const totalPmbjpCost = Math.round(totalTabletsNeeded * pmbjpPricePerTab);

  const marketSavingsInr = Math.max(0, totalBrandCost - totalCheapestCost);
  const pmbjpSavingsInr = Math.max(0, totalBrandCost - totalPmbjpCost);
  const annualProjectedMarketSavings = Math.round((marketSavingsInr / durationDays) * 365);

  const handleCopyDoctorNote = () => {
    const note = `Hi Doctor,\n\nI am currently prescribed ${data?.query_matched_to || activeQuery}. I noticed that identical bioequivalent generic formulations sharing active salt ${data?.generic_name || "the same molecule"} are widely available (e.g. ${data?.cheapest_option?.brand_name || "generic equivalent"}).\n\nCould we discuss if switching to this generic alternative is suitable for my treatment? It would save approximately ₹${annualProjectedMarketSavings}/year.\n\nThank you!`;
    navigator.clipboard.writeText(note);
    setCopiedDoctorNote(true);
    toast.success("Doctor discussion note copied to clipboard!");
    setTimeout(() => setCopiedDoctorNote(false), 3000);
  };

  const handleOpenJanAushadhi = (medicineName: string, targetUrl?: string) => {
    const cleanName = medicineName.replace(/\(.*?\)/g, "").trim();
    if (navigator?.clipboard?.writeText) {
      navigator.clipboard.writeText(cleanName);
      toast.success(`Copied "${cleanName}"! Paste it into Jan Aushadhi search.`);
    }
    const dest = targetUrl || "https://janaushadhi.gov.in/product-portfolio/product-mrp-list";
    window.open(dest, "_blank", "noopener,noreferrer");
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto pb-16">
      {/* 1. Header with Cabinet Savings Action */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <PageHeader
          title="GenericFinder: Price & Substitute Engine"
          description="Resolve any medicine brand to its active chemical salt, benchmark Indian pharmacy prices, and uncover huge savings with bioequivalent generics."
        />
        <Button
          onClick={() => setCabinetDialogOpen(true)}
          className="rounded-xl px-5 h-11 shrink-0 font-semibold gap-2 bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-700 hover:to-teal-700 text-white shadow-sm transition-all hover:scale-[1.02]"
        >
          <Coins className="h-4 w-4" />
          <span>Analyze My Cabinet Savings</span>
        </Button>
      </div>

      {/* 2. Search Box & Therapeutic Category Carousel */}
      <Card className="rounded-2xl border bg-card shadow-sm p-4 sm:p-6 space-y-4">
        <form onSubmit={handleSearchSubmit} className="space-y-3">
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <div className="relative flex-1">
              <Search className="pointer-events-none absolute left-3.5 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
              <Input
                type="text"
                value={searchInput}
                onChange={(e) => setSearchInput(e.target.value)}
                placeholder="Search brand or salt (e.g. Dolo 650, Augmentin, Pan 40, Montair LC, Paracetamol)..."
                className="pl-11 pr-4 h-12 rounded-xl text-base bg-muted/30 focus-visible:ring-primary shadow-xs"
              />
            </div>
            <Button
              type="submit"
              disabled={isLoading || isFetching || searchInput.trim().length < 2}
              className="h-12 px-6 rounded-xl font-semibold gap-2 shrink-0 bg-primary hover:bg-primary/90 text-primary-foreground shadow-sm"
            >
              {isLoading || isFetching ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />
                  <span>Searching...</span>
                </>
              ) : (
                <>
                  <Sparkles className="h-4 w-4" />
                  <span>Compare Prices</span>
                </>
              )}
            </Button>
          </div>
        </form>

        {/* Therapeutic Categories Tabs */}
        <div className="pt-2 border-t border-border/40 space-y-3">
          <div className="flex items-center justify-between text-xs font-medium text-muted-foreground">
            <span className="flex items-center gap-1.5 font-semibold text-foreground">
              <Flame className="h-3.5 w-3.5 text-amber-500" />
              Browse by Therapeutic Category:
            </span>
            <span className="text-[11px]">Click any medicine to compare</span>
          </div>

          {/* Category Pill Tabs */}
          <div className="flex items-center gap-1.5 overflow-x-auto pb-1 scrollbar-none">
            {POPULAR_CATEGORIES.map((cat, idx) => {
              const Icon = cat.icon;
              const isSelected = selectedCategoryIndex === idx;
              return (
                <button
                  key={cat.category}
                  type="button"
                  onClick={() => setSelectedCategoryIndex(idx)}
                  className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all ${
                    isSelected
                      ? "bg-primary text-primary-foreground shadow-xs"
                      : "bg-muted/60 hover:bg-muted text-muted-foreground hover:text-foreground border border-border/40"
                  }`}
                >
                  <Icon className="h-3.5 w-3.5" />
                  <span>{cat.category}</span>
                </button>
              );
            })}
          </div>

          {/* Medicines for Selected Category */}
          <div className="flex flex-wrap items-center gap-2 pt-1">
            {POPULAR_CATEGORIES[selectedCategoryIndex].medicines.map((med) => (
              <button
                key={med}
                type="button"
                onClick={() => handleChipClick(med)}
                className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-medium transition-all ${
                  activeQuery.toLowerCase() === med.toLowerCase()
                    ? "bg-primary text-primary-foreground font-semibold shadow-xs scale-105"
                    : "bg-background hover:bg-muted text-foreground border border-border/60 hover:border-primary/50 shadow-2xs"
                }`}
              >
                <Pill className="h-3 w-3 text-primary" />
                <span>{med}</span>
              </button>
            ))}
          </div>
        </div>
      </Card>

      {/* 3. Loading State Skeleton */}
      {(isLoading || isFetching) && (
        <Card className="rounded-2xl border p-8 shadow-sm text-center space-y-4">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 text-primary mx-auto animate-pulse">
            <Loader2 className="h-6 w-6 animate-spin" />
          </div>
          <div className="space-y-1">
            <h3 className="text-base font-semibold text-foreground">
              Analyzing Salt Composition & Benchmarking Pharmacy Prices...
            </h3>
            <p className="text-sm text-muted-foreground max-w-md mx-auto">
              Scanning 24h rates and comparing public Indian pharmacy listings from PharmEasy, 1mg, and PMBJP for{" "}
              <strong className="text-foreground">"{activeQuery}"</strong>.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 pt-4 max-w-3xl mx-auto">
            <Skeleton className="h-28 rounded-2xl" />
            <Skeleton className="h-28 rounded-2xl" />
            <Skeleton className="h-28 rounded-2xl" />
          </div>
        </Card>
      )}

      {/* 4. Not Found in Catalog State */}
      {!isLoading && !isFetching && data && !data.is_salt_dictionary_match && (
        <Card className="rounded-2xl border-amber-500/30 bg-amber-500/5 p-6 shadow-sm">
          <div className="flex items-start gap-4">
            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-amber-500/10 text-amber-600">
              <AlertCircle className="h-6 w-6" />
            </div>
            <div className="space-y-2">
              <h3 className="text-base font-semibold text-foreground">
                Medicine Not Resolved in Reference Catalog
              </h3>
              <p className="text-sm text-muted-foreground leading-relaxed">
                We could not resolve <span className="font-semibold text-foreground">"{data.query_matched_to}"</span> to an active salt formulation in our curated Indian medicine directory.
              </p>
              <div className="text-xs text-muted-foreground pt-1">
                Tip: Try searching by common brand names like <strong>Dolo 650</strong>, <strong>Pan 40</strong>, <strong>Augmentin</strong>, <strong>Montair LC</strong>, or active ingredients like <strong>Paracetamol</strong> or <strong>Metformin</strong>.
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* 5. Main Results View */}
      {!isLoading && !isFetching && data && data.is_salt_dictionary_match && (
        <div className="space-y-6">
          {/* Active Salt & Clinical Summary Card */}
          <Card className="rounded-2xl border bg-card p-5 sm:p-6 shadow-sm">
            <div className="flex flex-col md:flex-row md:items-start justify-between gap-4">
              <div className="space-y-2 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <Badge variant="outline" className="rounded-md font-semibold text-xs bg-primary/10 text-primary border-primary/20">
                    {data.category}
                  </Badge>
                  <Badge variant="secondary" className="rounded-md font-semibold text-xs capitalize bg-muted text-foreground border border-border/60">
                    Form: {data.dosage_form}
                  </Badge>
                  <span className="text-xs text-muted-foreground">
                    Query Matched To: <strong className="text-foreground">{data.query_matched_to}</strong>
                  </span>
                </div>

                <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-2.5">
                  <Pill className="h-6 w-6 text-primary shrink-0" />
                  <span>Active Salt: {data.generic_name}</span>
                </h2>

                {/* Exact Active Salts Composition */}
                {data.active_ingredients && data.active_ingredients.length > 0 && (
                  <div className="flex flex-wrap items-center gap-1.5 pt-0.5 text-xs">
                    <span className="text-muted-foreground font-semibold">Exact Active Salts:</span>
                    {data.active_ingredients.map((salt) => (
                      <span
                        key={salt}
                        className="px-2.5 py-0.5 rounded-md bg-emerald-500/10 text-emerald-700 dark:text-emerald-400 border border-emerald-500/25 font-bold text-[11px]"
                      >
                        {salt}
                      </span>
                    ))}
                  </div>
                )}

                {data.description && (
                  <p className="text-sm text-muted-foreground leading-relaxed pt-1">
                    {data.description}
                  </p>
                )}

                {/* Clinical Guidance and Strengths */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                  {data.how_to_use && (
                    <div className="p-3 rounded-xl bg-muted/40 border border-border/40 space-y-1">
                      <div className="font-semibold text-foreground flex items-center gap-1.5">
                        <Info className="h-3.5 w-3.5 text-primary" />
                        <span>How To Take / Usage:</span>
                      </div>
                      <p className="text-muted-foreground leading-snug">{data.how_to_use}</p>
                    </div>
                  )}

                  {data.common_strengths && data.common_strengths.length > 0 && (
                    <div className="p-3 rounded-xl bg-muted/40 border border-border/40 space-y-1">
                      <div className="font-semibold text-foreground flex items-center gap-1.5">
                        <BadgeCheck className="h-3.5 w-3.5 text-emerald-600" />
                        <span>Standard Available Strengths:</span>
                      </div>
                      <div className="flex flex-wrap gap-1 pt-0.5">
                        {data.common_strengths.map((s) => (
                          <span key={s} className="px-2 py-0.5 rounded-md bg-background border border-border/60 font-medium text-foreground text-[11px]">
                            {s}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {/* Common Side Effects */}
                {data.side_effects && data.side_effects.length > 0 && (
                  <div className="flex items-center gap-1.5 pt-1 text-xs text-muted-foreground flex-wrap">
                    <span className="font-semibold text-foreground">Common mild side effects:</span>
                    {data.side_effects.map((se) => (
                      <span key={se} className="px-2 py-0.5 rounded-md bg-amber-500/10 text-amber-700 dark:text-amber-400 border border-amber-500/20 text-[11px]">
                        {se}
                      </span>
                    ))}
                  </div>
                )}
              </div>

              {/* Cache status & summary badge */}
              <div className="flex flex-col items-start md:items-end gap-1.5 shrink-0 text-xs">
                <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-muted text-muted-foreground font-medium border border-border/40">
                  <Database className="h-3.5 w-3.5 text-primary" />
                  <span>24h Rate-Limit Cache Active</span>
                </div>
                <div className="text-[11px] text-muted-foreground">
                  {results.length} same-form prices compared
                </div>
              </div>
            </div>

            {/* Interchangeable Peer Brands Pills (Strictly Same Dosage Form) */}
            {data.all_generic_substitutes.length > 0 && (
              <div className="mt-4 pt-4 border-t border-border/50">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-1 mb-2">
                  <div className="text-xs font-bold text-foreground uppercase tracking-wider flex items-center gap-1.5">
                    <ShieldCheck className="h-4 w-4 text-emerald-600" />
                    <span>Exact Substitutes ({data.dosage_form.toUpperCase()} ONLY):</span>
                  </div>
                  <span className="text-[11px] text-emerald-600 dark:text-emerald-400 font-medium">
                    100% Identical Active Salt Composition & Dosage Form
                  </span>
                </div>
                <div className="flex flex-wrap gap-1.5">
                  {data.all_generic_substitutes.map((brand) => (
                    <button
                      key={brand}
                      type="button"
                      onClick={() => handleChipClick(brand)}
                      className="px-2.5 py-1 rounded-lg text-xs font-semibold bg-muted/60 hover:bg-muted text-foreground transition-all border border-border/40 hover:border-primary/40 flex items-center gap-1"
                    >
                      <span>{brand}</span>
                      <span className="text-[10px] text-muted-foreground font-normal capitalize">({data.dosage_form})</span>
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Alternative Dosage Forms (Explicitly Separated and Warned) */}
            {data.other_form_substitutes && Object.keys(data.other_form_substitutes).length > 0 && (
              <div className="mt-4 pt-4 border-t border-amber-500/20 bg-amber-500/5 -mx-5 sm:-mx-6 -mb-5 sm:-mb-6 p-4 sm:p-5 rounded-b-2xl space-y-2">
                <div className="flex items-center gap-2 text-xs font-bold text-amber-800 dark:text-amber-300">
                  <AlertCircle className="h-4 w-4 shrink-0 text-amber-600" />
                  <span>Other Dosage Forms Available (NOT Directly Interchangeable):</span>
                </div>
                <p className="text-[11px] text-muted-foreground leading-snug">
                  These brands share the identical active chemical salt but are manufactured in different physical forms (e.g. pediatric syrups vs adult tablets) with differing absorption and dosage volumes. Do not switch forms without physician consultation.
                </p>
                {Object.entries(data.other_form_substitutes).map(([altForm, altBrands]) => (
                  <div key={altForm} className="flex flex-wrap items-center gap-1.5 pt-1">
                    <span className="px-2 py-0.5 rounded-md bg-amber-500/20 text-amber-900 dark:text-amber-200 text-[11px] font-bold uppercase tracking-wider">
                      {altForm}s:
                    </span>
                    {altBrands.map((altB) => (
                      <button
                        key={altB}
                        type="button"
                        onClick={() => handleChipClick(altB)}
                        className="px-2.5 py-1 rounded-lg text-xs font-medium bg-card hover:bg-muted text-foreground transition-all border border-amber-500/30 hover:border-amber-500/60"
                      >
                        {altB}
                      </button>
                    ))}
                  </div>
                ))}
              </div>
            )}
          </Card>

          {/* Savings Highlight Hero Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 1. Cheapest Online Pharmacy Option */}
            {data.cheapest_option && (
              <Card className="rounded-2xl border-2 border-emerald-500/30 bg-gradient-to-br from-emerald-500/10 via-card to-card p-5 sm:p-6 shadow-sm flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs font-bold">
                      <TrendingDown className="h-3.5 w-3.5" />
                      Best Online Pharmacy Deal
                    </span>
                    <Badge variant="outline" className="text-xs border-emerald-500/30">
                      on {data.cheapest_option.pharmacy_source}
                    </Badge>
                  </div>

                  <div>
                    <h3 className="text-lg font-bold text-foreground line-clamp-1">
                      {data.cheapest_option.brand_name}
                    </h3>
                    <div className="flex items-baseline gap-3 mt-1">
                      <span className="text-3xl font-extrabold text-emerald-600 dark:text-emerald-400">
                        ₹{data.cheapest_option.price}
                      </span>
                      {data.most_expensive_price && data.most_expensive_price > data.cheapest_option.price && (
                        <span className="text-sm text-muted-foreground line-through">
                          ₹{data.most_expensive_price} max
                        </span>
                      )}
                      {data.estimated_savings_percent > 0 && (
                        <span className="text-xs font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/15 px-2 py-0.5 rounded-md">
                          Save {data.estimated_savings_percent}%
                        </span>
                      )}
                    </div>
                  </div>
                </div>

                <div className="pt-4 border-t border-emerald-500/20 flex items-center justify-between gap-2 mt-4">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleOpenAddMedModal(data.cheapest_option!.brand_name, data.generic_name)}
                    className="rounded-xl text-xs gap-1.5 font-semibold border-emerald-500/30 hover:bg-emerald-500/10"
                  >
                    <Plus className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Switch to This Option</span>
                  </Button>

                  {data.cheapest_option.url && (
                    <Button
                      size="sm"
                      asChild
                      className="rounded-xl text-xs gap-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold"
                    >
                      <a href={data.cheapest_option.url} target="_blank" rel="noopener noreferrer">
                        <span>View Deal</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </Button>
                  )}
                </div>
              </Card>
            )}

            {/* 2. Pradhan Mantri Jan Aushadhi (PMBJP) Kendra Benchmark */}
            {data.pmbjp_reference && (
              <Card className="rounded-2xl border-2 border-primary/30 bg-gradient-to-br from-primary/10 via-card to-card p-5 sm:p-6 shadow-sm flex flex-col justify-between">
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-primary/20 text-primary text-xs font-bold">
                      <ShieldCheck className="h-3.5 w-3.5" />
                      Govt. Jan Aushadhi (PMBJP) Generic
                    </span>
                    <Badge variant="outline" className="text-xs border-primary/30 text-primary">
                      Save {data.pmbjp_reference.savings_percent}%
                    </Badge>
                  </div>

                  <div>
                    <h3 className="text-lg font-bold text-foreground line-clamp-1">
                      {data.pmbjp_reference.generic_name}
                    </h3>
                    <div className="flex items-baseline gap-3 mt-1">
                      <span className="text-3xl font-extrabold text-primary">
                        ₹{data.pmbjp_reference.typical_price}
                      </span>
                      <span className="text-sm text-muted-foreground line-through">
                        ₹{data.pmbjp_reference.market_avg_price} market avg
                      </span>
                    </div>
                  </div>

                  <p className="text-xs text-muted-foreground leading-snug">
                    Pure generic medicine manufactured in WHO-GMP certified facilities under Ministry of Chemicals & Fertilizers, Government of India.
                  </p>
                </div>

                <div className="pt-4 border-t border-primary/20 flex flex-wrap items-center justify-between gap-2 mt-4">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => handleOpenAddMedModal(data.pmbjp_reference!.generic_name, data.generic_name)}
                    className="rounded-xl text-xs gap-1.5 font-semibold"
                  >
                    <Plus className="h-3.5 w-3.5" />
                    <span>Add to Cabinet</span>
                  </Button>

                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() => handleOpenJanAushadhi(data.generic_name, data.pmbjp_reference?.product_url)}
                      className="rounded-xl text-xs gap-1 font-semibold border-primary/40 hover:bg-primary/10 text-primary"
                      title="Open Jan Aushadhi Product & MRP Catalog"
                    >
                      <span>View Govt MRP</span>
                      <ExternalLink className="h-3 w-3" />
                    </Button>

                    <Button
                      size="sm"
                      asChild
                      variant="secondary"
                      className="rounded-xl text-xs gap-1 font-semibold"
                    >
                      <a
                        href={data.pmbjp_reference.kendra_url || "https://janaushadhi.gov.in/locate-kendra"}
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        <span>Find Kendra</span>
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </Button>
                  </div>
                </div>
              </Card>
            )}
          </div>

          {/* 6. Interactive Prescription Savings Calculator */}
          <Card className="rounded-2xl border bg-card p-5 sm:p-6 shadow-sm space-y-5">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-border/50 pb-3">
              <div className="space-y-0.5">
                <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                  <Calculator className="h-5 w-5 text-primary" />
                  <span>Prescription Savings Calculator: {data.query_matched_to}</span>
                </h3>
                <p className="text-xs text-muted-foreground">
                  Simulate your recurring prescription costs and annual cash savings by switching to generics.
                </p>
              </div>

              <div className="flex items-center gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  onClick={handleCopyDoctorNote}
                  className="rounded-xl text-xs gap-1.5 font-medium shrink-0"
                >
                  {copiedDoctorNote ? (
                    <>
                      <Check className="h-3.5 w-3.5 text-emerald-600" />
                      <span>Copied!</span>
                    </>
                  ) : (
                    <>
                      <Copy className="h-3.5 w-3.5" />
                      <span>Copy Doctor Note</span>
                    </>
                  )}
                </Button>
              </div>
            </div>

            {/* Slider & Duration Controls */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              {/* Daily Dose Control */}
              <div className="space-y-2 bg-muted/30 p-4 rounded-xl border border-border/40">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-foreground">Daily Dosage Frequency:</span>
                  <Badge variant="secondary" className="font-bold">
                    {dosesPerDay} {dosesPerDay === 1 ? "dose" : "doses"} / day
                  </Badge>
                </div>
                <div className="flex items-center gap-2 pt-1">
                  {[1, 2, 3, 4].map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setDosesPerDay(d)}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                        dosesPerDay === d
                          ? "bg-primary text-primary-foreground shadow-xs"
                          : "bg-background hover:bg-muted text-muted-foreground border border-border/60"
                      }`}
                    >
                      {d}x / day
                    </button>
                  ))}
                </div>
              </div>

              {/* Duration Horizon Control */}
              <div className="space-y-2 bg-muted/30 p-4 rounded-xl border border-border/40">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-foreground">Treatment Horizon:</span>
                  <Badge variant="secondary" className="font-bold">
                    {durationDays === 365 ? "1 Year (365d)" : `${durationDays} Days`}
                  </Badge>
                </div>
                <div className="flex items-center gap-2 pt-1">
                  {[
                    { label: "1 Month (30d)", val: 30 },
                    { label: "3 Months (90d)", val: 90 },
                    { label: "1 Year (365d)", val: 365 },
                  ].map((dur) => (
                    <button
                      key={dur.val}
                      type="button"
                      onClick={() => setDurationDays(dur.val)}
                      className={`flex-1 py-1.5 rounded-lg text-xs font-semibold transition-all ${
                        durationDays === dur.val
                          ? "bg-primary text-primary-foreground shadow-xs"
                          : "bg-background hover:bg-muted text-muted-foreground border border-border/60"
                      }`}
                    >
                      {dur.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Visual Calculated Metrics */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-1">
              <div className="p-4 rounded-xl bg-muted/40 border border-border/50 space-y-1">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
                  Branded Spend ({totalTabletsNeeded} doses)
                </div>
                <div className="text-2xl font-bold text-foreground">
                  ₹{totalBrandCost}
                </div>
                <div className="text-[11px] text-muted-foreground">
                  ₹{baselineBrandPricePerTab.toFixed(1)} / tablet
                </div>
              </div>

              <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/25 space-y-1">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
                  Online Generic Spend
                </div>
                <div className="text-2xl font-bold text-emerald-600 dark:text-emerald-400">
                  ₹{totalCheapestCost}
                </div>
                <div className="text-[11px] text-emerald-700/80 dark:text-emerald-400/80 font-medium">
                  Saves ₹{marketSavingsInr} ({Math.round(((totalBrandCost - totalCheapestCost) / (totalBrandCost || 1)) * 100)}%)
                </div>
              </div>

              <div className="p-4 rounded-xl bg-primary/10 border border-primary/25 space-y-1">
                <div className="text-[11px] font-semibold uppercase tracking-wider text-primary">
                  Annual Projected Savings
                </div>
                <div className="text-2xl sm:text-3xl font-black text-primary">
                  ₹{annualProjectedMarketSavings}
                </div>
                <div className="text-[11px] text-muted-foreground">
                  Over 12 months of therapy
                </div>
              </div>
            </div>
          </Card>

          {/* 7. Side-by-Side Brand vs. Generic Comparison Matrix */}
          <Card className="rounded-2xl border bg-card p-5 sm:p-6 shadow-sm space-y-4">
            <div className="space-y-1">
              <h3 className="text-base font-bold text-foreground flex items-center gap-2">
                <ShieldCheck className="h-5 w-5 text-emerald-600" />
                <span>Brand vs. Generic: Bioequivalence Comparison</span>
              </h3>
              <p className="text-xs text-muted-foreground">
                Both formulations share identical active pharmacological salts and therapeutic bioequivalence standards approved by the CDSCO / DCGI.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-xs text-left">
                <thead>
                  <tr className="border-b border-border/60 text-muted-foreground font-semibold">
                    <th className="py-2.5 pr-4">Evaluation Criteria</th>
                    <th className="py-2.5 px-4 text-foreground">Branded Formulation ({data.query_matched_to})</th>
                    <th className="py-2.5 px-4 text-emerald-600 dark:text-emerald-400 font-bold">
                      Generic Equivalent ({data.generic_name})
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40 text-foreground">
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-muted-foreground">Active Chemical Ingredient</td>
                    <td className="py-2.5 px-4 font-semibold">{data.generic_name}</td>
                    <td className="py-2.5 px-4 font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                      <span>100% Identical Chemical Salt</span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-muted-foreground">Therapeutic Bioequivalence</td>
                    <td className="py-2.5 px-4">Standard Clinical Profile</td>
                    <td className="py-2.5 px-4 text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                      <span>Equivalent Bioavailability & Potency</span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-muted-foreground">Manufacturing Standard</td>
                    <td className="py-2.5 px-4">WHO-GMP Compliant</td>
                    <td className="py-2.5 px-4 text-emerald-600 dark:text-emerald-400 font-semibold flex items-center gap-1.5">
                      <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600 shrink-0" />
                      <span>WHO-GMP & CDSCO Regulated</span>
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-muted-foreground">Estimated Strip Price</td>
                    <td className="py-2.5 px-4 font-bold text-foreground">₹{data.most_expensive_price || 35}</td>
                    <td className="py-2.5 px-4 font-black text-emerald-600 dark:text-emerald-400 text-sm">
                      ₹{data.cheapest_option?.price || 12}
                    </td>
                  </tr>
                  <tr>
                    <td className="py-2.5 pr-4 font-medium text-muted-foreground">Typical Patient Savings</td>
                    <td className="py-2.5 px-4 text-muted-foreground">Baseline Price</td>
                    <td className="py-2.5 px-4 font-extrabold text-emerald-600 dark:text-emerald-400">
                      Up to {data.estimated_savings_percent}% Cheaper
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </Card>

          {/* 8. Price Comparison Results Grid */}
          <div className="space-y-4 pt-2">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div>
                <h3 className="text-lg font-bold tracking-tight text-foreground flex items-center gap-2">
                  <Building2 className="h-5 w-5 text-primary" />
                  <span>All Pharmacy Price Comparison Results ({filteredResults.length})</span>
                </h3>
                <p className="text-xs text-muted-foreground">
                  Sorted from lowest to highest price across Indian online pharmacies and generic stores.
                </p>
              </div>

              {/* Source Filter */}
              {availableSources.length > 1 && (
                <div className="flex items-center gap-1 bg-muted/60 p-1 rounded-xl border border-border/50 text-xs">
                  <button
                    type="button"
                    onClick={() => setFilterSource("ALL")}
                    className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                      filterSource === "ALL"
                        ? "bg-background text-foreground shadow-xs font-semibold"
                        : "text-muted-foreground hover:text-foreground"
                    }`}
                  >
                    All Sources
                  </button>
                  {availableSources.map((source) => (
                    <button
                      key={source}
                      type="button"
                      onClick={() => setFilterSource(source)}
                      className={`px-3 py-1 rounded-lg font-medium transition-colors ${
                        filterSource.toLowerCase() === source.toLowerCase()
                          ? "bg-background text-foreground shadow-xs font-semibold"
                          : "text-muted-foreground hover:text-foreground"
                      }`}
                    >
                      {source}
                    </button>
                  ))}
                </div>
              )}
            </div>

            {/* Results Cards */}
            {filteredResults.length === 0 ? (
              <Card className="rounded-2xl border p-8 text-center text-muted-foreground">
                No matching price options found for the selected filter.
              </Card>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                {filteredResults.map((item, idx) => {
                  const isSearched = Boolean(item.is_searched_medicine);
                  const isBestSubstitute =
                    !isSearched &&
                    (idx === 1 || (idx === 0 && !filteredResults.some((r) => r.is_searched_medicine)));
                  const searchedItem = filteredResults.find((r) => r.is_searched_medicine);

                  return (
                    <Card
                      key={`${item.brand_name}-${item.pharmacy_source}-${idx}`}
                      className={`rounded-2xl border transition-all hover:shadow-md ${
                        isSearched
                          ? "border-primary/50 bg-gradient-to-br from-primary/10 via-card to-card shadow-sm ring-1 ring-primary/30"
                          : isBestSubstitute
                          ? "border-emerald-500/40 bg-emerald-500/5 shadow-sm ring-1 ring-emerald-500/20"
                          : "bg-card hover:border-border/80"
                      }`}
                    >
                      <CardContent className="p-4 sm:p-5 flex flex-col justify-between h-full space-y-4">
                        <div className="space-y-2">
                          <div className="flex items-center justify-between gap-2">
                            {isSearched ? (
                              <Badge
                                variant="default"
                                className="bg-primary text-primary-foreground font-bold text-[11px] gap-1 shadow-xs"
                              >
                                <Pill className="h-3 w-3" />
                                <span>Your Search (Position #1)</span>
                              </Badge>
                            ) : (
                              <Badge
                                variant={isBestSubstitute ? "default" : "secondary"}
                                className={
                                  isBestSubstitute
                                    ? "bg-emerald-600 text-white font-semibold text-[11px]"
                                    : "text-[11px]"
                                }
                              >
                                {isBestSubstitute ? "Lowest Price Substitute" : `Substitute #${idx}`}
                              </Badge>
                            )}

                            <div className="flex items-center gap-1.5 text-[11px]">
                              {item.dosage_form && (
                                <Badge variant="outline" className="text-[10px] capitalize bg-muted border-border/60">
                                  {item.dosage_form}
                                </Badge>
                              )}
                              {item.is_generic && (
                                <Badge variant="outline" className="text-[10px] bg-primary/10 text-primary border-primary/20">
                                  Pure Generic
                                </Badge>
                              )}
                              {item.is_fallback ? (
                                <span className="inline-flex items-center gap-1 text-amber-600 dark:text-amber-400 font-medium bg-amber-500/10 px-2 py-0.5 rounded-md border border-amber-500/20">
                                  <ShieldCheck className="h-3 w-3 text-amber-600 dark:text-amber-400" />
                                  Benchmark
                                </span>
                              ) : item.is_cached ? (
                                <span className="inline-flex items-center gap-1 text-muted-foreground font-medium">
                                  <Database className="h-3 w-3 text-primary/70" />
                                  24h Cached
                                </span>
                              ) : (
                                <span className="inline-flex items-center gap-1 text-emerald-600 font-medium">
                                  <CheckCircle2 className="h-3 w-3" />
                                  Live Scraped
                                </span>
                              )}
                            </div>
                          </div>

                          <div>
                            <h4 className="font-semibold text-foreground text-base leading-snug line-clamp-2">
                              {item.brand_name}
                            </h4>
                            <div className="text-xs text-muted-foreground mt-0.5">
                              Source Pharmacy: <span className="font-medium text-foreground">{item.pharmacy_source}</span>
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center justify-between pt-3 border-t border-border/40">
                          <div>
                            <div className="text-[10px] text-muted-foreground uppercase font-semibold">
                              {isSearched ? "Searched Brand Price (₹)" : "Substitute Price (₹)"}
                            </div>
                            <div className="flex items-baseline gap-2">
                              <span className="text-2xl font-bold text-foreground">
                                ₹{item.price}
                              </span>
                              {!isSearched && searchedItem && searchedItem.price > item.price && (
                                <span className="text-[11px] font-bold text-emerald-600 dark:text-emerald-400 bg-emerald-500/15 px-1.5 py-0.5 rounded">
                                  Save {Math.round(((searchedItem.price - item.price) / searchedItem.price) * 100)}%
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="flex items-center gap-1.5">
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleOpenAddMedModal(item.brand_name, data.generic_name)}
                              className="rounded-xl text-xs gap-1 h-9 font-medium"
                              title="Add to MediSync Medications"
                            >
                              <Plus className="h-3.5 w-3.5" />
                              <span>Add</span>
                            </Button>

                            {item.url ? (
                              <Button
                                variant="outline"
                                size="sm"
                                asChild
                                className="rounded-xl text-xs gap-1.5 h-9 font-medium"
                              >
                                <a
                                  href={item.url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  onClick={(e) => {
                                    if (
                                      item.pharmacy_source?.toLowerCase().includes("jan aushadhi") ||
                                      item.pharmacy_source?.toLowerCase().includes("pmbjp")
                                    ) {
                                      e.preventDefault();
                                      handleOpenJanAushadhi(data.generic_name, item.url);
                                    }
                                  }}
                                >
                                  <span>View</span>
                                  <ExternalLink className="h-3.5 w-3.5" />
                                </a>
                              </Button>
                            ) : (
                              <span className="text-xs text-muted-foreground">Listing unavailable</span>
                            )}
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  );
                })}
              </div>
            )}

            {/* Other Dosage Forms Price Results Section (Clearly Separated) */}
            {data.other_form_results && data.other_form_results.length > 0 && (
              <div className="mt-8 pt-6 border-t-2 border-dashed border-border/80 space-y-4">
                <div className="space-y-1">
                  <h4 className="text-base font-bold text-foreground flex items-center gap-2 text-amber-700 dark:text-amber-400">
                    <AlertCircle className="h-5 w-5 shrink-0" />
                    <span>Prices for Alternative Dosage Forms ({data.other_form_results.length})</span>
                  </h4>
                  <p className="text-xs text-muted-foreground">
                    Formulations in other forms (e.g. pediatric syrups vs adult tablets) sharing the same chemical salts. Separated here because they have different dosing instructions and are not directly interchangeable.
                  </p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-3.5">
                  {data.other_form_results.map((item, idx) => (
                    <Card
                      key={`other-${item.brand_name}-${item.pharmacy_source}-${idx}`}
                      className="rounded-2xl border border-amber-500/25 bg-amber-500/5 hover:border-amber-500/50 transition-all"
                    >
                      <CardContent className="p-4 sm:p-5 flex flex-col justify-between h-full space-y-3">
                        <div className="space-y-1.5">
                          <div className="flex items-center justify-between gap-2">
                            <Badge variant="outline" className="text-[11px] bg-amber-500/20 text-amber-800 dark:text-amber-200 border-amber-500/30 uppercase font-bold">
                              Form: {item.dosage_form || "Other"}
                            </Badge>
                            <span className="text-[11px] text-muted-foreground">
                              Pharmacy: <strong className="text-foreground">{item.pharmacy_source}</strong>
                            </span>
                          </div>

                          <h5 className="font-semibold text-foreground text-sm leading-snug">
                            {item.brand_name}
                          </h5>
                        </div>

                        <div className="flex items-center justify-between pt-2 border-t border-amber-500/20">
                          <div className="text-xl font-bold text-foreground">
                            ₹{item.price}
                          </div>

                          {item.url && (
                            <Button
                              variant="outline"
                              size="sm"
                              asChild
                              className="rounded-xl text-xs gap-1.5 h-8 font-medium border-amber-500/30 hover:bg-amber-500/10"
                            >
                              <a
                                href={item.url}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => {
                                  if (
                                    item.pharmacy_source?.toLowerCase().includes("jan aushadhi") ||
                                    item.pharmacy_source?.toLowerCase().includes("pmbjp")
                                  ) {
                                    e.preventDefault();
                                    handleOpenJanAushadhi(data.generic_name, item.url);
                                  }
                                }}
                              >
                                <span>View Deal</span>
                                <ExternalLink className="h-3 w-3" />
                              </a>
                            </Button>
                          )}
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sources Transparency & Status */}
          <Card className="rounded-2xl border bg-muted/20 p-4 text-xs text-muted-foreground space-y-2">
            <div className="flex flex-wrap items-center justify-between gap-2 font-medium">
              <div className="flex items-center gap-1.5 text-foreground">
                <Building2 className="h-4 w-4 text-primary" />
                <span>Pharmacy Scraping Coverage & Status:</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {data.sources_checked.map((src) => (
                  <Badge key={src} variant="outline" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/20 text-[11px] gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    {src}
                  </Badge>
                ))}
                {data.sources_failed.map((src) => (
                  <Badge key={src} variant="outline" className="bg-destructive/10 text-destructive border-destructive/20 text-[11px] gap-1">
                    <AlertCircle className="h-3 w-3" />
                    {src}
                  </Badge>
                ))}
              </div>
            </div>
          </Card>

          {/* Medical Disclaimer */}
          <div className="rounded-2xl border border-muted-foreground/15 bg-muted/10 p-4 flex items-start gap-3 text-xs text-muted-foreground">
            <Info className="h-4 w-4 text-muted-foreground shrink-0 mt-0.5" />
            <p className="leading-relaxed">
              <strong>Medical Disclaimer:</strong> Prices shown are collected from public listings on Indian online pharmacies (PharmEasy, 1mg, Apollo) and Pradhan Mantri Bhartiya Janaushadhi Pariyojana benchmarks. Prices may vary based on pack size or state taxes. Always consult your doctor or pharmacist before switching between branded medications and generic equivalents.
            </p>
          </div>
        </div>
      )}

      {/* ------------------------------------------------------------- */}
      {/* DIALOG 1: Patient Cabinet Prescription Savings Analysis       */}
      {/* ------------------------------------------------------------- */}
      <Dialog open={cabinetDialogOpen} onOpenChange={setCabinetDialogOpen}>
        <DialogContent className="max-w-2xl max-h-[85vh] overflow-y-auto rounded-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2 text-xl">
              <Coins className="h-5 w-5 text-emerald-600" />
              <span>Your Prescription Cabinet Savings</span>
            </DialogTitle>
            <DialogDescription>
              We analyzed your current active medications to uncover how much you can save each month and year by substituting brand medicines with equivalent generics.
            </DialogDescription>
          </DialogHeader>

          {cabinetQuery.isLoading ? (
            <div className="py-12 text-center space-y-3">
              <Loader2 className="h-8 w-8 animate-spin text-primary mx-auto" />
              <p className="text-sm text-muted-foreground">Analyzing your prescribed medications...</p>
            </div>
          ) : !cabinetQuery.data || cabinetQuery.data.items.length === 0 ? (
            <div className="py-8 text-center space-y-3">
              <div className="h-12 w-12 rounded-full bg-muted flex items-center justify-center mx-auto text-muted-foreground">
                <Pill className="h-6 w-6" />
              </div>
              <h4 className="font-semibold text-foreground">No Substitutable Medications Found</h4>
              <p className="text-xs text-muted-foreground max-w-sm mx-auto">
                You either have no active medications in your list, or your prescribed medicines are already generics or not in our catalog.
              </p>
              <Button asChild size="sm" className="rounded-xl">
                <Link to="/medications">View My Medications</Link>
              </Button>
            </div>
          ) : (
            <div className="space-y-4 pt-2">
              {/* Grand Total Hero Card */}
              <div className="p-4 rounded-xl bg-gradient-to-r from-emerald-500/15 via-teal-500/10 to-transparent border border-emerald-500/30 flex items-center justify-between">
                <div>
                  <div className="text-xs font-semibold text-muted-foreground uppercase">
                    Total Potential Savings
                  </div>
                  <div className="text-2xl font-black text-emerald-600 dark:text-emerald-400">
                    ₹{cabinetQuery.data.total_monthly_savings_inr} / month
                  </div>
                  <div className="text-xs font-medium text-emerald-700 dark:text-emerald-400">
                    ₹{cabinetQuery.data.total_annual_savings_inr} projected per year
                  </div>
                </div>
                <Badge className="bg-emerald-600 text-white font-bold text-xs px-3 py-1">
                  {cabinetQuery.data.medications_with_substitutes} Medicines Substitutable
                </Badge>
              </div>

              {/* Items Breakdown List */}
              <div className="space-y-2.5">
                {cabinetQuery.data.items.map((item, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl border border-border/60 bg-card space-y-2 hover:border-emerald-500/30 transition-colors"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <div className="font-bold text-sm text-foreground flex items-center gap-2">
                          <span>{item.medication_name}</span>
                          <Badge variant="outline" className="text-[10px] bg-primary/10 text-primary border-primary/20">
                            {item.generic_name}
                          </Badge>
                        </div>
                        <div className="text-xs text-muted-foreground mt-0.5">
                          Recommended Generic: <strong className="text-foreground">{item.recommended_generic_name}</strong>
                        </div>
                      </div>

                      <Badge className="bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 text-xs font-bold shrink-0">
                        Save {item.savings_percent}%
                      </Badge>
                    </div>

                    <div className="flex items-center justify-between pt-2 border-t border-border/40 text-xs">
                      <div className="flex items-center gap-4">
                        <div>
                          <span className="text-muted-foreground">Current monthly: </span>
                          <span className="font-semibold line-through text-muted-foreground">₹{item.current_estimated_price}</span>
                        </div>
                        <div>
                          <span className="text-muted-foreground">Generic monthly: </span>
                          <span className="font-bold text-emerald-600 dark:text-emerald-400">₹{item.cheapest_substitute_price}</span>
                        </div>
                      </div>

                      <div className="font-bold text-foreground">
                        Save ₹{item.monthly_savings_inr}/mo
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <DialogFooter className="pt-2">
            <Button variant="ghost" onClick={() => setCabinetDialogOpen(false)} className="rounded-xl">
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* ------------------------------------------------------------- */}
      {/* DIALOG 2: Add Generic Substitute to MediSync Cabinet           */}
      {/* ------------------------------------------------------------- */}
      <Dialog open={addMedDialogOpen} onOpenChange={setAddMedDialogOpen}>
        <DialogContent className="max-w-md rounded-2xl">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Pill className="h-5 w-5 text-primary" />
              <span>Add Generic to Your Medications</span>
            </DialogTitle>
            <DialogDescription>
              Add {selectedSubstituteToAdd?.brand_name} ({selectedSubstituteToAdd?.generic_name}) to your MediSync cabinet to start tracking doses and schedule.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-3.5 py-2 text-xs">
            <div className="space-y-1">
              <Label className="text-xs font-semibold">Medication Name</Label>
              <Input
                value={addMedForm.name}
                onChange={(e) => setAddMedForm({ ...addMedForm, name: e.target.value })}
                className="rounded-xl h-10 text-xs"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs font-semibold">Dosage (Amount)</Label>
                <Input
                  type="number"
                  min="0.25"
                  step="0.25"
                  value={addMedForm.dosage_amount}
                  onChange={(e) => setAddMedForm({ ...addMedForm, dosage_amount: parseFloat(e.target.value) || 1 })}
                  className="rounded-xl h-10 text-xs"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-semibold">Unit</Label>
                <Input
                  value={addMedForm.dosage_unit}
                  onChange={(e) => setAddMedForm({ ...addMedForm, dosage_unit: e.target.value })}
                  className="rounded-xl h-10 text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1">
                <Label className="text-xs font-semibold">Doses Per Day</Label>
                <Input
                  type="number"
                  min="1"
                  max="6"
                  value={addMedForm.frequency_per_day}
                  onChange={(e) => setAddMedForm({ ...addMedForm, frequency_per_day: parseInt(e.target.value) || 1 })}
                  className="rounded-xl h-10 text-xs"
                />
              </div>

              <div className="space-y-1">
                <Label className="text-xs font-semibold">Duration (Days)</Label>
                <Input
                  type="number"
                  min="1"
                  max="365"
                  value={addMedForm.duration_days}
                  onChange={(e) => setAddMedForm({ ...addMedForm, duration_days: parseInt(e.target.value) || 30 })}
                  className="rounded-xl h-10 text-xs"
                />
              </div>
            </div>

            <div className="space-y-1">
              <Label className="text-xs font-semibold">Notes</Label>
              <Input
                value={addMedForm.notes || ""}
                onChange={(e) => setAddMedForm({ ...addMedForm, notes: e.target.value })}
                className="rounded-xl h-10 text-xs"
              />
            </div>
          </div>

          <DialogFooter className="pt-2">
            <Button
              type="button"
              variant="ghost"
              onClick={() => setAddMedDialogOpen(false)}
              className="rounded-xl text-xs"
            >
              Cancel
            </Button>
            <Button
              type="button"
              disabled={addMedMutation.isPending || !addMedForm.name.trim()}
              onClick={() => addMedMutation.mutate(addMedForm)}
              className="rounded-xl text-xs gap-1.5 font-semibold"
            >
              {addMedMutation.isPending ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  <span>Adding...</span>
                </>
              ) : (
                <>
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  <span>Add to My Medications</span>
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
