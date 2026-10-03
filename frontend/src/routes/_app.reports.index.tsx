import { createFileRoute, Link } from "@tanstack/react-router";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState, useRef, type ChangeEvent, type DragEvent } from "react";
import {
  FileText,
  UploadCloud,
  Loader2,
  Trash2,
  CheckCircle2,
  AlertCircle,
  Clock,
  ArrowRight,
  Sparkles,
  FileCheck,
} from "lucide-react";
import { format } from "date-fns";
import { PageHeader } from "@/components/page-header";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { labReportApi, type LabReportListItem } from "@/lib/api";

export const Route = createFileRoute("/_app/reports/")({
  component: ReportsPage,
});

function ReportsPage() {
  const queryClient = useQueryClient();
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const { data: reports, isLoading, error } = useQuery({
    queryKey: ["lab-reports"],
    queryFn: () => labReportApi.list(),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => labReportApi.upload(file),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-reports"] });
      setSelectedFile(null);
      setUploadError(null);
      setDialogOpen(false);
    },
    onError: (err: any) => {
      setUploadError(err?.message || "Failed to upload and analyze report.");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => labReportApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["lab-reports"] });
    },
  });

  const handleFileSelect = (file: File) => {
    const validExtensions = [".pdf", ".png", ".jpg", ".jpeg"];
    const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase();
    if (!validExtensions.includes(ext)) {
      setUploadError("Please upload a PDF or image file (.png, .jpg, .jpeg).");
      return;
    }
    setSelectedFile(file);
    setUploadError(null);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const handleUploadSubmit = () => {
    if (!selectedFile) return;
    uploadMutation.mutate(selectedFile);
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="ReportBrief"
        description="AI-powered medical lab report analyzer. Upload lab test results to automatically extract metrics and plain-language clinical summaries."
        action={
          <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
            <DialogTrigger asChild>
              <Button className="gap-2 shadow-sm">
                <UploadCloud className="h-4 w-4" />
                Upload Report
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-md">
              <DialogHeader>
                <DialogTitle>Upload Lab Report</DialogTitle>
                <DialogDescription>
                  Upload your pathology or diagnostic test results (PDF, PNG, JPG).
                </DialogDescription>
              </DialogHeader>

              <div className="space-y-4 pt-2">
                <div
                  onDrop={handleDrop}
                  onDragOver={handleDragOver}
                  onDragLeave={handleDragLeave}
                  onClick={() => fileInputRef.current?.click()}
                  className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-colors flex flex-col items-center justify-center gap-3 ${
                    isDragging
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/50 hover:bg-muted/30"
                  }`}
                >
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,.png,.jpg,.jpeg"
                    className="hidden"
                    onChange={(e: ChangeEvent<HTMLInputElement>) => {
                      if (e.target.files && e.target.files.length > 0) {
                        handleFileSelect(e.target.files[0]);
                      }
                    }}
                  />
                  <div className="h-12 w-12 rounded-full bg-primary/10 flex items-center justify-center text-primary">
                    <UploadCloud className="h-6 w-6" />
                  </div>
                  <div>
                    <p className="text-sm font-medium">
                      {selectedFile ? selectedFile.name : "Click to browse or drag & drop"}
                    </p>
                    <p className="text-xs text-muted-foreground mt-1">
                      PDF, PNG, or JPG (max 20MB)
                    </p>
                  </div>
                  {selectedFile && (
                    <Badge variant="secondary" className="gap-1 text-xs">
                      <FileCheck className="h-3.5 w-3.5 text-emerald-600" />
                      {(selectedFile.size / 1024).toFixed(0)} KB ready
                    </Badge>
                  )}
                </div>

                {uploadError && (
                  <div className="flex items-center gap-2 text-sm text-destructive bg-destructive/10 p-3 rounded-lg">
                    <AlertCircle className="h-4 w-4 shrink-0" />
                    <span>{uploadError}</span>
                  </div>
                )}

                <div className="flex justify-end gap-2 pt-2">
                  <Button
                    variant="outline"
                    onClick={() => {
                      setSelectedFile(null);
                      setUploadError(null);
                      setDialogOpen(false);
                    }}
                    disabled={uploadMutation.isPending}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleUploadSubmit}
                    disabled={!selectedFile || uploadMutation.isPending}
                    className="gap-2"
                  >
                    {uploadMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 animate-spin" />
                        Analyzing with AI...
                      </>
                    ) : (
                      <>
                        <Sparkles className="h-4 w-4" />
                        Extract & Analyze
                      </>
                    )}
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        }
      />

      {/* Report List Section */}
      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3].map((i) => (
            <Card key={i} className="p-6 space-y-4">
              <Skeleton className="h-5 w-2/3" />
              <Skeleton className="h-4 w-1/3" />
              <Skeleton className="h-16 w-full" />
              <div className="flex justify-between pt-2">
                <Skeleton className="h-9 w-24" />
                <Skeleton className="h-9 w-9 rounded-md" />
              </div>
            </Card>
          ))}
        </div>
      ) : error ? (
        <Card className="p-8 text-center border-destructive/20 bg-destructive/5">
          <AlertCircle className="h-8 w-8 text-destructive mx-auto mb-2" />
          <h3 className="font-semibold text-lg">Unable to load reports</h3>
          <p className="text-sm text-muted-foreground mt-1">
            {(error as any)?.message || "Check your connection and try again."}
          </p>
        </Card>
      ) : !reports || reports.length === 0 ? (
        <Card className="p-12 text-center border-dashed">
          <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center text-primary mx-auto mb-4">
            <FileText className="h-8 w-8" />
          </div>
          <h3 className="font-semibold text-xl">No Lab Reports Yet</h3>
          <p className="text-sm text-muted-foreground max-w-md mx-auto mt-2 mb-6">
            Upload your first blood test, metabolic panel, or lab report to extract structured metrics and receive an AI-powered summary.
          </p>
          <Button onClick={() => setDialogOpen(true)} className="gap-2">
            <UploadCloud className="h-4 w-4" />
            Upload Your First Report
          </Button>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {reports.map((report: LabReportListItem) => {
            const formattedDate = (() => {
              try {
                return format(new Date(report.uploaded_at), "MMM d, yyyy • h:mm a");
              } catch {
                return report.uploaded_at;
              }
            })();

            return (
              <Card key={report.id} className="flex flex-col hover:border-primary/40 transition-colors shadow-sm">
                <CardHeader className="pb-3">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex items-center gap-2">
                      <div className="h-9 w-9 rounded-lg bg-primary/10 flex items-center justify-center text-primary shrink-0">
                        <FileText className="h-5 w-5" />
                      </div>
                      <div className="truncate">
                        <CardTitle className="text-base font-semibold truncate" title={report.original_filename}>
                          {report.original_filename}
                        </CardTitle>
                        <CardDescription className="text-xs flex items-center gap-1 mt-0.5">
                          <Clock className="h-3 w-3" />
                          {formattedDate}
                        </CardDescription>
                      </div>
                    </div>
                  </div>
                </CardHeader>

                <CardContent className="flex-1 space-y-3 pb-3">
                  <div className="flex items-center gap-2">
                    {report.status === "completed" && (
                      <Badge variant="secondary" className="gap-1 bg-emerald-50 text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-400 border-emerald-200">
                        <CheckCircle2 className="h-3 w-3" />
                        Completed
                      </Badge>
                    )}
                    {report.status === "processing" && (
                      <Badge variant="secondary" className="gap-1 bg-amber-50 text-amber-700 dark:bg-amber-950/40 dark:text-amber-400 border-amber-200">
                        <Loader2 className="h-3 w-3 animate-spin" />
                        Processing
                      </Badge>
                    )}
                    {report.status === "failed" && (
                      <Badge variant="destructive" className="gap-1">
                        <AlertCircle className="h-3 w-3" />
                        Failed
                      </Badge>
                    )}

                    <Badge variant="outline" className="text-xs font-normal">
                      {report.values_count} {report.values_count === 1 ? "test" : "tests"}
                    </Badge>
                  </div>

                  <p className="text-xs text-muted-foreground line-clamp-3 leading-relaxed">
                    {report.summary || "No summary preview available."}
                  </p>
                </CardContent>

                <CardFooter className="pt-2 border-t flex justify-between gap-2">
                  <Button variant="ghost" size="sm" asChild className="gap-1 text-primary hover:text-primary">
                    <Link to="/reports/$id" params={{ id: report.id }}>
                      View Analysis
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Link>
                  </Button>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-8 w-8 text-muted-foreground hover:text-destructive"
                    onClick={() => {
                      if (confirm("Are you sure you want to delete this lab report?")) {
                        deleteMutation.mutate(report.id);
                      }
                    }}
                    disabled={deleteMutation.isPending}
                    title="Delete report"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
