import { DownloadForm } from "@/components/download-form";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Headphones } from "lucide-react";

export default function Home() {
  return (
    <main className="relative flex min-h-screen items-center justify-center overflow-hidden px-4 py-12">
      <div className="absolute inset-0 -z-10 bg-[radial-gradient(circle_at_top_left,hsl(var(--primary)/0.14),transparent_34%),radial-gradient(circle_at_bottom_right,hsl(var(--primary)/0.08),transparent_32%)]" />
      <div className="w-full max-w-xl">
        <div className="mb-8 text-center">
          <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary text-primary-foreground shadow-lg shadow-primary/20">
            <Headphones className="h-7 w-7" />
          </div>
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">YouTube Downloader</h1>
          <p className="mx-auto mt-3 max-w-md text-muted-foreground">Converta o áudio de um vídeo autorizado para MP3 de forma simples e rápida.</p>
        </div>
        <Card className="border-white/60 bg-card/90 shadow-2xl shadow-slate-900/10 backdrop-blur">
          <CardHeader><p className="text-lg font-semibold">Baixar áudio</p></CardHeader>
          <CardContent><DownloadForm /></CardContent>
        </Card>
        <p className="mt-5 text-center text-xs text-muted-foreground">Baixe somente conteúdos que você tem autorização para utilizar.</p>
      </div>
    </main>
  );
}

