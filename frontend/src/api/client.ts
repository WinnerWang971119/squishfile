import type { UploadResponse, CompressResponse } from "../types";

const BASE = "/api";

export async function uploadFile(file: File): Promise<UploadResponse> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${BASE}/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error((await res.json()).detail || "Upload failed");
  return res.json();
}

export async function compressFile(
  fileId: string,
  targetSizeKb: number
): Promise<CompressResponse> {
  const res = await fetch(`${BASE}/compress`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ file_id: fileId, target_size_kb: targetSizeKb }),
  });
  if (!res.ok) throw new Error((await res.json()).detail || "Compression failed");
  return res.json();
}

export function downloadUrl(fileId: string): string {
  return `${BASE}/download/${fileId}`;
}
