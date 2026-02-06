import type { FileEntry } from "../types";
import { downloadUrl } from "../api/client";

interface FileCardProps {
  file: FileEntry;
}

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function FileCard({ file }: FileCardProps) {
  const isCompressing = file.status === "compressing";
  const isDone = file.status === "done";
  const isError = file.status === "error";

  return (
    <div
      className={`
        bg-[#1A1A1A] rounded-lg p-3 border-l-3
        transition-all duration-300 ease-in-out
        ${isDone ? "border-l-[#22C55E]" : isError ? "border-l-[#EF4444]" : "border-l-[#FFD60A]"}
      `}
    >
      <div className="flex items-center justify-between mb-2">
        <span className="text-[#FAFAFA] text-sm font-medium truncate max-w-[140px]">
          {file.originalFilename}
        </span>
        <span className="text-[10px] px-1.5 py-0.5 rounded bg-[#333] text-[#888] uppercase">
          {file.mime.split("/")[1]}
        </span>
      </div>

      <div className="text-xs text-[#888] mb-2">
        {formatSize(file.size)}
        {file.compressedSize != null && (
          <>
            <span className="text-[#FFD60A] mx-1">&rarr;</span>
            <span className="text-[#FAFAFA]">{formatSize(file.compressedSize)}</span>
          </>
        )}
      </div>

      {isCompressing && (
        <div className="w-full h-1.5 bg-[#333] rounded-full overflow-hidden">
          <div
            className="h-full bg-[#FFD60A] rounded-full transition-all duration-300"
            style={{ width: `${file.progress}%` }}
          />
        </div>
      )}

      {isDone && (
        <a
          href={downloadUrl(file.id)}
          className="
            inline-block mt-1 text-xs px-3 py-1 rounded
            bg-[#FFD60A] text-[#0D0D0D] font-medium
            hover:bg-[#FFE44D] transition-colors
          "
        >
          Download
        </a>
      )}

      {isError && (
        <p className="text-xs text-[#EF4444] mt-1">{file.message}</p>
      )}
    </div>
  );
}
