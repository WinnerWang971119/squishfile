import type { FileEntry } from "../types";
import { downloadUrl } from "../api/client";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface DownloadPageProps {
  files: FileEntry[];
  onStartOver: () => void;
}

export function DownloadPage({ files, onStartOver }: DownloadPageProps) {
  const doneFiles = files.filter((f) => f.status === "done");
  const errorFiles = files.filter((f) => f.status === "error");
  const compressingFiles = files.filter((f) => f.status === "compressing");
  const allDone = compressingFiles.length === 0;

  const totalOriginal = files.reduce((sum, f) => sum + f.size, 0);
  const totalCompressed = doneFiles.reduce(
    (sum, f) => sum + (f.compressedSize ?? f.size),
    0
  );
  const savedBytes = totalOriginal - totalCompressed;
  const savedPercent =
    totalOriginal > 0 ? Math.round((savedBytes / totalOriginal) * 100) : 0;

  const handleDownloadAll = () => {
    if (doneFiles.length === 1) {
      const a = document.createElement("a");
      a.href = downloadUrl(doneFiles[0].id);
      a.download = doneFiles[0].originalFilename;
      a.click();
      return;
    }
    window.location.href = `/api/download-all?ids=${doneFiles.map((f) => f.id).join(",")}`;
  };

  const handleDownloadOne = (file: FileEntry) => {
    const a = document.createElement("a");
    a.href = downloadUrl(file.id);
    a.download = file.originalFilename;
    a.click();
  };

  return (
    <div className="flex-1 grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-6 animate-fade-in">
      {/* Left: Summary */}
      <div className="bg-[#141416] rounded-2xl border border-[#27272A] p-8 flex flex-col justify-between">
        <div>
          <h2 className="font-[family-name:var(--font-display)] text-xs font-bold tracking-widest text-[#71717A] uppercase mb-8">
            {allDone ? "Compression Complete" : "Compressing..."}
          </h2>

          <div className="space-y-6">
            {/* Stats */}
            <div className="grid grid-cols-3 gap-4">
              <div className="bg-[#1C1C1F] rounded-xl p-4 text-center">
                <p className="font-[family-name:var(--font-display)] text-2xl font-extrabold text-[#F5F5F4]">
                  {doneFiles.length}
                  <span className="text-[#3F3F46]">/{files.length}</span>
                </p>
                <p className="text-[10px] font-[family-name:var(--font-display)] tracking-wider text-[#71717A] mt-1">
                  FILES
                </p>
              </div>

              <div className="bg-[#1C1C1F] rounded-xl p-4 text-center">
                <p className="font-[family-name:var(--font-display)] text-2xl font-extrabold text-[#F5F5F4]">
                  {formatSize(totalOriginal)}
                </p>
                <p className="text-[10px] font-[family-name:var(--font-display)] tracking-wider text-[#71717A] mt-1">
                  ORIGINAL
                </p>
              </div>

              <div className="bg-[#1C1C1F] rounded-xl p-4 text-center">
                <p className="font-[family-name:var(--font-display)] text-2xl font-extrabold text-[#34D399]">
                  {allDone ? formatSize(totalCompressed) : "..."}
                </p>
                <p className="text-[10px] font-[family-name:var(--font-display)] tracking-wider text-[#71717A] mt-1">
                  COMPRESSED
                </p>
              </div>
            </div>

            {/* Savings bar */}
            {allDone && savedBytes > 0 && (
              <div className="bg-[#1C1C1F] rounded-xl p-5 animate-scale-in">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-sm text-[#A1A1AA]">Space saved</span>
                  <span className="font-[family-name:var(--font-display)] text-lg font-extrabold text-[#34D399]">
                    {savedPercent}%
                  </span>
                </div>
                <div className="w-full h-2 bg-[#27272A] rounded-full overflow-hidden">
                  <div
                    className="h-full bg-gradient-to-r from-[#34D399] to-[#34D399]/60 rounded-full transition-all duration-1000 ease-out"
                    style={{ width: `${savedPercent}%` }}
                  />
                </div>
                <p className="text-xs text-[#71717A] mt-2 font-[family-name:var(--font-display)]">
                  {formatSize(savedBytes)} freed up
                </p>
              </div>
            )}

            {errorFiles.length > 0 && (
              <div className="bg-[#F87171]/5 border border-[#F87171]/20 rounded-xl p-4">
                <p className="text-sm text-[#F87171] font-medium">
                  {errorFiles.length} {errorFiles.length === 1 ? "file" : "files"} failed
                </p>
              </div>
            )}
          </div>
        </div>

        <div className="flex gap-3 mt-8">
          {doneFiles.length > 0 && (
            <button
              onClick={handleDownloadAll}
              disabled={!allDone}
              className={`
                flex-1 flex items-center justify-center gap-2
                px-6 py-3.5 rounded-xl font-bold text-sm
                font-[family-name:var(--font-display)] tracking-wide
                transition-all duration-200
                ${allDone
                  ? "bg-[#FFD60A] text-[#0A0A0B] hover:bg-[#FFE44D] active:scale-[0.98] shadow-[0_0_20px_rgba(255,214,10,0.15)]"
                  : "bg-[#27272A] text-[#3F3F46] cursor-not-allowed"
                }
              `}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                <polyline points="7 10 12 15 17 10" />
                <line x1="12" y1="15" x2="12" y2="3" />
              </svg>
              {doneFiles.length > 1 ? `Download All (${doneFiles.length})` : "Download"}
            </button>
          )}

          <button
            onClick={onStartOver}
            className="
              px-6 py-3.5 rounded-xl text-sm font-medium
              bg-[#1C1C1F] text-[#A1A1AA] border border-[#27272A]
              hover:text-[#F5F5F4] hover:border-[#3F3F46]
              transition-all duration-200
            "
          >
            Start Over
          </button>
        </div>
      </div>

      {/* Right: Individual Results */}
      <div className="bg-[#141416] rounded-2xl border border-[#27272A] overflow-hidden flex flex-col">
        <div className="px-5 py-4 border-b border-[#1E1E21]">
          <h2 className="font-[family-name:var(--font-display)] text-xs font-bold tracking-widest text-[#71717A] uppercase">
            Results
          </h2>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1.5 stagger-children">
          {files.map((file) => {
            const isDone = file.status === "done";
            const isError = file.status === "error";
            const isCompressing = file.status === "compressing";

            return (
              <div
                key={file.id}
                className={`
                  group px-4 py-3 rounded-xl
                  border-l-2 transition-all duration-200
                  ${isDone
                    ? "bg-[#34D399]/[0.04] border-l-[#34D399]"
                    : isError
                      ? "bg-[#F87171]/[0.04] border-l-[#F87171]"
                      : "bg-[#1C1C1F]/50 border-l-[#FFD60A]"
                  }
                `}
              >
                <div className="flex items-center gap-3">
                  {/* Status icon */}
                  <div className="shrink-0">
                    {isDone && (
                      <div className="w-6 h-6 rounded-full bg-[#34D399]/15 flex items-center justify-center">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#34D399" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                          <polyline points="20 6 9 17 4 12" />
                        </svg>
                      </div>
                    )}
                    {isError && (
                      <div className="w-6 h-6 rounded-full bg-[#F87171]/15 flex items-center justify-center">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#F87171" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
                          <line x1="18" y1="6" x2="6" y2="18" />
                          <line x1="6" y1="6" x2="18" y2="18" />
                        </svg>
                      </div>
                    )}
                    {isCompressing && (
                      <div className="w-6 h-6 rounded-full bg-[#FFD60A]/15 flex items-center justify-center animate-progress-pulse">
                        <div className="w-2.5 h-2.5 rounded-full bg-[#FFD60A]" />
                      </div>
                    )}
                  </div>

                  {/* File info */}
                  <div className="flex-1 min-w-0">
                    <p className="text-sm text-[#F5F5F4] truncate font-medium">
                      {file.originalFilename}
                    </p>
                    <div className="flex items-center gap-1.5 mt-0.5">
                      <span className="text-xs text-[#71717A]">{formatSize(file.size)}</span>
                      {isDone && file.compressedSize != null && (
                        <>
                          <span className="text-[#FFD60A] text-xs">&rarr;</span>
                          <span className="text-xs text-[#34D399] font-medium">
                            {formatSize(file.compressedSize)}
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Download button */}
                  {isDone && (
                    <button
                      onClick={() => handleDownloadOne(file)}
                      className="
                        opacity-0 group-hover:opacity-100
                        p-2 rounded-lg
                        text-[#A1A1AA] hover:text-[#FFD60A] hover:bg-[#FFD60A]/10
                        transition-all duration-200
                      "
                      title="Download"
                    >
                      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="7 10 12 15 17 10" />
                        <line x1="12" y1="15" x2="12" y2="3" />
                      </svg>
                    </button>
                  )}
                </div>

                {/* Progress bar */}
                {isCompressing && (
                  <div className="w-full h-1 bg-[#27272A] rounded-full overflow-hidden mt-2.5">
                    <div
                      className="h-full bg-[#FFD60A] rounded-full transition-all duration-300"
                      style={{ width: `${file.progress}%` }}
                    />
                  </div>
                )}

                {/* Error message */}
                {isError && file.message && (
                  <p className="text-xs text-[#F87171]/80 mt-1.5 pl-9">{file.message}</p>
                )}
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
