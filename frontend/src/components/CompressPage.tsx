import { SizeControl } from "./SizeControl";
import type { FileEntry } from "../types";

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

interface CompressPageProps {
  files: FileEntry[];
  targetKb: number;
  maxKb: number;
  onTargetChange: (kb: number) => void;
  hasVideo?: boolean;
}

export function CompressPage({ files, targetKb, maxKb, onTargetChange, hasVideo }: CompressPageProps) {
  const targetBytes = targetKb * 1024;

  return (
    <div className="flex-1 grid grid-cols-1 lg:grid-cols-[3fr_2fr] gap-6 animate-fade-in">
      {/* Left: Size Control (larger) */}
      <div className="bg-[#141416] rounded-2xl border border-[#27272A] p-8 flex flex-col justify-center">
        <SizeControl
          maxSizeKb={maxKb}
          value={targetKb}
          onChange={onTargetChange}
          hasVideo={hasVideo}
        />
      </div>

      {/* Right: File List (compact) */}
      <div className="bg-[#141416] rounded-2xl border border-[#27272A] overflow-hidden flex flex-col">
        <div className="px-5 py-4 border-b border-[#1E1E21] flex items-center justify-between">
          <h2 className="font-[family-name:var(--font-display)] text-xs font-bold tracking-widest text-[#71717A] uppercase">
            Files
          </h2>
          <span className="text-xs px-2.5 py-1 rounded-full bg-[#FFD60A]/10 text-[#FFD60A] font-[family-name:var(--font-display)] font-bold">
            {files.length}
          </span>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-1 stagger-children">
          {files.map((file) => {
            const underTarget = file.size <= targetBytes;
            return (
              <div
                key={file.id}
                className="
                  flex items-center gap-3 px-4 py-3 rounded-xl
                  bg-[#1C1C1F]/50 border border-transparent
                  transition-colors duration-200
                "
              >
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-[#F5F5F4] truncate font-medium">
                    {file.originalFilename}
                  </p>
                  <span className="text-xs text-[#71717A]">
                    {formatSize(file.size)}
                  </span>
                </div>

                <div className="text-right shrink-0">
                  {underTarget ? (
                    <span className="text-[10px] font-[family-name:var(--font-display)] text-[#34D399] tracking-wide">
                      UNDER TARGET
                    </span>
                  ) : (
                    <span className="text-xs font-[family-name:var(--font-display)] text-[#A1A1AA]">
                      &rarr; {formatSize(targetBytes)}
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <div className="px-5 py-3 border-t border-[#1E1E21]">
          <div className="flex items-center justify-between text-xs text-[#71717A]">
            <span>Total original</span>
            <span className="font-[family-name:var(--font-display)] font-bold text-[#A1A1AA]">
              {formatSize(files.reduce((sum, f) => sum + f.size, 0))}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
