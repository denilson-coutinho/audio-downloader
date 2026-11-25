"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { AlertCircle, CheckCircle2, Download, LoaderCircle, Music2 } from "lucide-react";
import { useState } from "react";
import { useForm, useWatch } from "react-hook-form";

import { Alert, AlertDescription } from "@/components/ui/alert";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
  downloadLinks,
  downloadSchema,
  maxDownloadLinks,
  type DownloadFormData,
} from "@/schemas/download.schema";
import { requestDownload } from "@/services/download";

type Feedback = { kind: "success" | "error"; message: string } | null;

export function DownloadForm() {
  const [feedback, setFeedback] = useState<Feedback>(null);
  const {
    register,
    handleSubmit,
    control,
    formState: { errors, isSubmitting },
  } = useForm<DownloadFormData>({
    resolver: zodResolver(downloadSchema),
    defaultValues: { links: "" },
  });
  const links = useWatch({ control, name: "links" });
  const isBatch = downloadLinks(links).length > 1;

  async function onSubmit(values: DownloadFormData) {
    setFeedback(null);
    try {
      const urls = downloadLinks(values.links);
      await requestDownload(urls.length > 1 ? { urls } : { url: urls[0], format: "mp3" });
      setFeedback({ kind: "success", message: "Seu download foi iniciado." });
    } catch (error) {
      setFeedback({
        kind: "error",
        message: error instanceof Error ? error.message : "Ocorreu um erro inesperado.",
      });
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)} noValidate>
      <div className="space-y-2">
        <Label htmlFor="links">Links do YouTube</Label>
        <textarea
          id="links"
          rows={4}
          spellCheck={false}
          className="flex w-full resize-y rounded-md border border-input bg-background px-3 py-2 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50"
          placeholder="https://www.youtube.com/watch?v=..."
          aria-invalid={Boolean(errors.links)}
          aria-describedby={errors.links ? "links-hint links-error" : "links-hint"}
          disabled={isSubmitting}
          {...register("links")}
        />
        <p id="links-hint" className="text-xs text-muted-foreground">
          Cole um link por linha, até {maxDownloadLinks}. Com dois ou mais links, os MP3 vêm em um ZIP.
        </p>
        {errors.links && <p id="links-error" className="text-sm text-destructive">{errors.links.message}</p>}
      </div>

      <div className="flex items-center justify-between rounded-lg border bg-muted/50 px-4 py-3">
        <div className="flex items-center gap-3">
          <span className="rounded-md bg-background p-2 shadow-sm"><Music2 className="h-4 w-4" /></span>
          <div><p className="text-sm font-medium">Áudio</p><p className="text-xs text-muted-foreground">Qualidade 192 kbps</p></div>
        </div>
        <span className="rounded-full bg-primary/10 px-3 py-1 text-xs font-semibold text-primary">MP3</span>
      </div>

      <Button type="submit" size="lg" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? (
          <><LoaderCircle className="mr-2 h-4 w-4 animate-spin" />{isBatch ? "Preparando ZIP..." : "Processando áudio..."}</>
        ) : (
          <><Download className="mr-2 h-4 w-4" />{isBatch ? "Baixar ZIP" : "Baixar MP3"}</>
        )}
      </Button>

      {feedback && (
        <Alert className={feedback.kind === "error" ? "border-destructive/40 text-destructive" : "border-emerald-500/40 text-emerald-700"}>
          <div className="flex items-center gap-2">
            {feedback.kind === "error" ? <AlertCircle className="h-4 w-4" /> : <CheckCircle2 className="h-4 w-4" />}
            <AlertDescription>{feedback.message}</AlertDescription>
          </div>
        </Alert>
      )}
    </form>
  );
}

