import { DropZone } from "./DropZone";
import type { FileEntry } from "../types";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface UploadPageProps {
  files: FileEntry[];
  onFiles: (files: File[]) => void;
  onRemove: (id: string) => void;
}

export function UploadPage({ files, onFiles, onRemove }: UploadPageProps) {
  const totalSize = files.reduce((sum, f) => sum + f.size, 0);

  return (
    <div className="flex-1 grid grid-cols-1 lg:grid-cols-[1fr_1fr] gap-6 animate-fade-in">
      {/* Left: Drop Zone */}
      <div className="flex flex-col">
        <DropZone onFiles={onFiles} />
      </div>

      {/* Right: File Queue */}
      <div className="flex flex-col bg-[#141416] rounded-2xl border border-[#27272A] overflow-hidden">
        <div className="px-5 py-4 border-b border-[#1E1E21] flex items-center justify-between">
          <h2 className="font-[family-name:var(--font-display)] text-xs font-bold tracking-widest text-[#71717A] uppercase">
            Queued Files
          </h2>
          {files.length > 0 && (
            <span className="text-xs px-2.5 py-1 rounded-full bg-[#FFD60A]/10 text-[#FFD60A] font-[family-name:var(--font-display)] font-bold">
              {files.length}
            </span>
          )}
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1.5 stagger-children min-h-[200px]">
          {files.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center py-12">
              <div className="w-10 h-10 rounded-xl bg-[#1C1C1F] flex items-center justify-center mb-3">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#3F3F46" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                  <polyline points="13 2 13 9 20 9" />
                </svg>
              </div>
              <p className="text-[#3F3F46] text-sm">No files yet</p>
              <p className="text-[#27272A] text-xs mt-1">Drop or browse to add</p>
            </div>
          ) : (
            files.map((file) => (
              <div
                key={file.id}
                className="
                  group flex items-center gap-3 px-4 py-3 rounded-xl
                  bg-[#1C1C1F]/50 hover:bg-[#1C1C1F]
                  border border-transparent hover:border-[#27272A]
                  transition-all duration-200
                "
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[#F5F5F4] truncate font-medium">
                    {file.originalFilename}
                  </p>
                  <div className="flex items-center gap-2 mt-0.5">
                    <span className="text-[10px] font-[family-name:var(--font-display)] tracking-wider px-1.5 py-0.5 rounded bg-[#27272A] text-[#71717A] uppercase">
                      {file.mime.split("/")[1]}
                    </span>
                    <span className="text-xs text-[#71717A]">
                      {formatSize(file.size)}
                    </span>
                    {file.status === "uploading" && (
                      <span className="text-[10px] text-[#FFD60A] animate-progress-pulse font-[family-name:var(--font-display)]">
                        uploading...
                      </span>
                    )}
                  </div>
                </div>

                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    onRemove(file.id);
                  }}
                  className="
                    opacity-0 group-hover:opacity-100
                    w-7 h-7 rounded-lg flex items-center justify-center
                    text-[#71717A] hover:text-[#F87171] hover:bg-[#F87171]/10
                    transition-all duration-200
                  "
                  title="Remove file"
                >
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </button>
              </div>
            ))
          )}
        </div>

        {files.length > 0 && (
          <div className="px-5 py-3 border-t border-[#1E1E21] flex items-center justify-between">
            <span className="text-xs text-[#71717A]">
              {files.length} {files.length === 1 ? "file" : "files"}
            </span>
            <span className="text-xs font-[family-name:var(--font-display)] text-[#A1A1AA] font-bold">
              {formatSize(totalSize)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
