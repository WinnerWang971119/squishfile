export type FileStatus = "uploading" | "queued" | "compressing" | "done" | "error";

export interface FileEntry {
  id: string;
  originalFilename: string;
  mime: string;
  category: "image" | "pdf";
  size: number;
  width?: number;
  height?: number;
  status: FileStatus;
  progress: number;
  compressedSize?: number;
  message?: string;
  previewUrl?: string;
}

export interface UploadResponse {
  id: string;
  mime: string;
  category: string;
  size: number;
  width?: number;
  height?: number;
  original_filename: string;
}

export interface CompressResponse {
  file_id: string;
  original_size: number;
  compressed_size: number;
  skipped: boolean;
  message?: string;
}
