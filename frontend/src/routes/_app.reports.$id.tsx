import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import {
  ArrowLeft,
  FileText,
  Clock,
  Sparkles,
  AlertCircle,
  CheckCircle2,
  Trash2,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  Info,
} from "lucide-react";
import { format } from "date-fns";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { labReportApi, type LabReportValue, type LabReportFlag } from "@/lib/api";

export const Route = createFileRoute("/_app/reports/$id")({
  component: ReportDetailPage,
});

function FlagBadge({ flag }: { flag: LabReportFlag }) {
  switch (flag) {
    case "normal":
      return (
        <Badge
          variant="secondary"
          className="bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-800 font-medium"
        >
          Normal
        </Badge>
      );
    case "high":
      return (
        <Badge
          variant="destructive"
          className="bg-rose-500 text-white font-medium shadow-sm"
        >
          High
        </Badge>
      );
    case "low":
      return (
        <Badge
          variant="secondary"
          className="bg-amber-50 text-amber-800 dark:bg-amber-950/40 dark:text-amber-300 border border-amber-300 dark:border-amber-700 font-medium"
        >
          Low
        </Badge>
      );
    default:
      return (
        <Badge variant="outline" className="text-muted-foreground font-normal">
          Unknown
        </Badge>
      );
  }
}

function ReportDetailPage() {
  const { id } = Route.useParams();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [showRawText, setShowRawText] = useState(false);

  const { data: report, isLoading, error } = useQuery({
    queryKey: ["lab-report", id],
    queryFn: () => labReportApi.get(id),
  });

  const deleteMutation = useMutation({
    mutationFn: (reportId: string) => labReportApi.delete(reportId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-reports"] });
      navigate({ to: "/reports" });
    },
  });

  if (isLoading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-8 w-40" />
        <Skeleton className="h-28 w-full rounded-xl" />
        <Skeleton className="h-44 w-full rounded-xl" />
        <Skeleton className="h-64 w-full rounded-xl" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="space-y-4">
        <Button variant="ghost" size="sm" asChild className="gap-2">
          <Link to="/reports">
            <ArrowLeft className="h-4 w-4" />
            Back to Reports
          </Link>
        </Button>
        <Card className="p-8 text-center border-destructive/20 bg-destructive/5">
          <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
          <h3 className="font-semibold text-lg">Report not found</h3>
          <p className="text-sm text-muted-foreground mt-1">
            {(error as any)?.message || "The requested lab report does not exist or has been deleted."}
          </p>
        </Card>
      </div>
    );
  }

  const formattedDate = (() => {
    try {
      return format(new Date(report.uploaded_at), "MMMM d, yyyy 'at' h:mm a");
    } catch {
      return report.uploaded_at;
    }
  })();

  const values = report.values || [];
  const normalCount = values.filter((v) => v.flag === "normal").length;
  const abnormalCount = values.filter((v) => v.flag === "high" || v.flag === "low").length;

  return (
    <div className="space-y-6 max-w-5xl">
      {/* Navigation Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <Button variant="ghost" size="sm" asChild className="gap-2 -ml-2">
          <Link to="/reports">
            <ArrowLeft className="h-4 w-4" />
            Back to All Reports
          </Link>
        </Button>

        <Button
          variant="outline"
          size="sm"
          className="gap-2 text-destructive hover:bg-destructive/10 hover:text-destructive border-destructive/30"
          onClick={() => {
            if (confirm("Are you sure you want to delete this lab report?")) {
              deleteMutation.mutate(report.id);
            }
          }}
          disabled={deleteMutation.isPending}
        >
          <Trash2 className="h-4 w-4" />
          Delete Report
        </Button>
      </div>

      {/* Report Info Card */}
      <Card className="shadow-sm border-sidebar-border">
        <CardHeader className="pb-4">
          <div className="flex flex-wrap items-start justify-between gap-4">
            <div className="flex items-center gap-3">
              <div className="h-12 w-12 rounded-xl bg-primary/10 flex items-center justify-center text-primary shrink-0">
                <FileText className="h-6 w-6" />
              </div>
              <div>
                <CardTitle className="text-xl font-bold">{report.original_filename}</CardTitle>
                <CardDescription className="flex items-center gap-1 mt-1 text-xs">
                  <Clock className="h-3.5 w-3.5" />
                  Uploaded on {formattedDate}
                </CardDescription>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {report.status === "completed" && (
                <Badge variant="secondary" className="gap-1 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5" />
                  Processed Successfully
                </Badge>
              )}
              {report.status === "processing" && (
                <Badge variant="secondary" className="gap-1 bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border-amber-200">
                  Processing
                </Badge>
              )}
              {report.status === "failed" && (
                <Badge variant="destructive" className="gap-1">
                  <AlertCircle className="h-3.5 w-3.5" />
                  Extraction Failed
                </Badge>
              )}
            </div>
          </div>
        </CardHeader>

        {values.length > 0 && (
          <CardContent className="pt-0">
            <div className="flex flex-wrap gap-4 pt-2 text-xs text-muted-foreground border-t">
              <div>
                Total Extracted Tests: <span className="font-semibold text-foreground">{values.length}</span>
              </div>
              <div>
                Normal Range: <span className="font-semibold text-emerald-600">{normalCount}</span>
              </div>
              <div>
                Out of Range: <span className="font-semibold text-rose-600">{abnormalCount}</span>
              </div>
            </div>
          </CardContent>
        )}
      </Card>

      {/* AI Plain-Language Summary */}
      <Card className="bg-gradient-to-br from-primary/5 via-card to-card border-primary/20 shadow-sm">
        <CardHeader className="pb-3">
          <div className="flex items-center gap-2 text-primary font-semibold text-base">
            <Sparkles className="h-5 w-5" />
            Plain-Language AI Summary
          </div>
          <CardDescription className="text-xs">
            Grounded strictly in the extracted numerical values. Does not speculate beyond provided findings.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="prose dark:prose-invert text-sm max-w-none leading-relaxed whitespace-pre-line text-foreground/90 bg-background/60 p-4 rounded-lg border">
            {report.summary || "No summary available for this report."}
          </div>
        </CardContent>
      </Card>

      {/* Structured Test Results */}
      <Card className="shadow-sm">
        <CardHeader>
          <CardTitle className="text-lg font-bold">Extracted Laboratory Values</CardTitle>
          <CardDescription className="text-xs">
            Numerical results compared with standard diagnostic reference intervals.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {values.length === 0 ? (
            <div className="p-8 text-center bg-muted/20 rounded-xl border border-dashed">
              <AlertTriangle className="h-8 w-8 text-amber-500 mx-auto mb-2" />
              <h4 className="font-semibold text-base">No Structured Data Extracted</h4>
              <p className="text-xs text-muted-foreground max-w-md mx-auto mt-1">
                We couldn't extract structured test data from this report format. This can happen if the report is a low-resolution scan or uses a non-standard layout.
              </p>
            </div>
          ) : (
            <div className="overflow-x-auto rounded-lg border">
              <table className="w-full text-sm text-left">
                <thead className="text-xs text-muted-foreground uppercase bg-muted/50 border-b">
                  <tr>
                    <th scope="col" className="px-4 py-3 font-semibold">Test Name</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Result</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Unit</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Reference Range</th>
                    <th scope="col" className="px-4 py-3 font-semibold">Status Flag</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border">
                  {values.map((v: LabReportValue) => {
                    let rangeDisplay = "—";
                    if (v.reference_low !== null && v.reference_high !== null) {
                      rangeDisplay = `${v.reference_low} - ${v.reference_high}`;
                    } else if (v.reference_high !== null) {
                      rangeDisplay = `< ${v.reference_high}`;
                    } else if (v.reference_low !== null) {
                      rangeDisplay = `> ${v.reference_low}`;
                    }

                    return (
                      <tr key={v.id} className="hover:bg-muted/30 transition-colors">
                        <td className="px-4 py-3 font-medium text-foreground">{v.test_name}</td>
                        <td className="px-4 py-3 font-bold text-foreground">{v.value}</td>
                        <td className="px-4 py-3 text-muted-foreground">{v.unit}</td>
                        <td className="px-4 py-3 text-muted-foreground">{rangeDisplay}</td>
                        <td className="px-4 py-3">
                          <FlagBadge flag={v.flag} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Collapsible Raw Extracted Text */}
      {report.raw_text && (
        <Card className="shadow-sm border-muted">
          <div
            onClick={() => setShowRawText(!showRawText)}
            className="flex items-center justify-between p-4 cursor-pointer select-none hover:bg-muted/30 transition-colors rounded-xl"
          >
            <div className="flex items-center gap-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
              <Info className="h-4 w-4 text-muted-foreground" />
              Raw Extracted Document Text ({report.raw_text.length} characters)
            </div>
            <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
              {showRawText ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
            </Button>
          </div>

          {showRawText && (
            <CardContent className="pt-0">
              <pre className="text-xs bg-muted/40 p-4 rounded-lg overflow-x-auto whitespace-pre-wrap font-mono text-muted-foreground max-h-96">
                {report.raw_text}
              </pre>
            </CardContent>
          )}
        </Card>
      )}
    </div>
  );
}
