import { z } from "zod";

const allowedHosts = new Set([
  "youtube.com",
  "www.youtube.com",
  "m.youtube.com",
  "music.youtube.com",
  "youtu.be",
]);

export const maxDownloadLinks = 10;

export function downloadLinks(value: string): string[] {
  return value.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
}

const youtubeUrl = z.url().refine((value) => {
  if (!URL.canParse(value)) return false;
  const url = new URL(value);
  return (
    ["http:", "https:"].includes(url.protocol) &&
    allowedHosts.has(url.hostname) &&
    !url.username &&
    !url.password &&
    ["", "80", "443"].includes(url.port)
  );
});

export const downloadSchema = z.object({
  links: z.string().superRefine((value, context) => {
    const links = downloadLinks(value);
    if (links.length === 0) {
      context.addIssue({ code: "custom", message: "Informe pelo menos um link." });
    } else if (links.length > maxDownloadLinks) {
      context.addIssue({ code: "custom", message: `Informe no máximo ${maxDownloadLinks} links.` });
    } else {
      const invalidIndex = links.findIndex((link) => !youtubeUrl.safeParse(link).success);
      if (invalidIndex !== -1) {
        context.addIssue({
          code: "custom",
          message: `O link ${invalidIndex + 1} precisa ser uma URL válida do YouTube.`,
        });
      }
    }
  }),
});

export type DownloadFormData = z.infer<typeof downloadSchema>;

