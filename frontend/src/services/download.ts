import type { ApiError, DownloadPayload } from "@/types/download";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function errorMessage(body: ApiError): string {
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) return body.detail[0]?.msg ?? "Não foi possível processar o download.";
  return "Não foi possível processar o download.";
}

function filenameFromHeader(header: string | null, fallback: string): string {
  if (!header) return fallback;
  const utf8Match = header.match(/filename\*=UTF-8''([^;]+)/i);
  if (utf8Match) return decodeURIComponent(utf8Match[1]);
  const match = header.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? fallback;
}

export async function requestDownload(payload: DownloadPayload): Promise<void> {
  const isBatch = "urls" in payload;
  const endpoint = isBatch ? "/api/download/zip" : "/api/download";
  const response = await fetch(`${API_URL}${endpoint}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    let body: ApiError = {};
    try {
      body = (await response.json()) as ApiError;
    } catch {
      // The fallback below is used when an upstream proxy returns a non-JSON error.
    }
    throw new Error(errorMessage(body));
  }

  const blob = await response.blob();
  const objectUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = objectUrl;
  anchor.download = filenameFromHeader(
    response.headers.get("content-disposition"),
    isBatch ? "audios.zip" : "audio.mp3",
  );
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();
  window.setTimeout(() => URL.revokeObjectURL(objectUrl), 0);
}

