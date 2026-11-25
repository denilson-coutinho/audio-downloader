export type DownloadPayload = { url: string; format: "mp3" } | { urls: string[] };

export interface ApiError {
  detail?: string | Array<{ msg?: string }>;
}

