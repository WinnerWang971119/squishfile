import { useCallback, useState } from "react";

interface DropZoneProps {
  onFiles: (files: File[]) => void;
}

export function DropZone({ onFiles }: DropZoneProps) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrag = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDragIn = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragOut = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) onFiles(files);
    },
    [onFiles]
  );

  const handleClick = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.multiple = true;
    input.accept = "image/*,.pdf";
    input.onchange = (e) => {
      const files = Array.from((e.target as HTMLInputElement).files || []);
      if (files.length > 0) onFiles(files);
    };
    input.click();
  };

  return (
    <div
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      onClick={handleClick}
      className={`
        relative flex flex-col items-center justify-center
        h-full min-h-[280px] rounded-2xl border-2 border-dashed
        cursor-pointer transition-all duration-300 ease-out
        overflow-hidden
        ${isDragging
          ? "border-[#FFD60A] bg-[#FFD60A]/[0.06] scale-[1.01] shadow-[0_0_40px_rgba(255,214,10,0.06)]"
          : "border-[#27272A] hover:border-[#FFD60A]/40 hover:bg-[#141416]"
        }
      `}
    >
      <div className={`
        absolute inset-0 transition-opacity duration-300
        ${isDragging ? "opacity-100" : "opacity-0"}
      `}>
        <div className="absolute inset-0 animate-shimmer" />
      </div>

      <div className="relative z-10 flex flex-col items-center gap-4">
        <div className={`
          w-16 h-16 rounded-2xl flex items-center justify-center
          transition-all duration-300
          ${isDragging
            ? "bg-[#FFD60A]/15 text-[#FFD60A] scale-110"
            : "bg-[#1C1C1F] text-[#71717A]"
          }
        `}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
            <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
            <polyline points="17 8 12 3 7 8" />
            <line x1="12" y1="3" x2="12" y2="15" />
          </svg>
        </div>

        <div className="text-center">
          <p className="font-[family-name:var(--font-display)] text-sm font-bold text-[#F5F5F4] tracking-wide">
            {isDragging ? "Release to upload" : "Drop files here"}
          </p>
          <p className="text-[#71717A] text-sm mt-1.5">or click to browse</p>
        </div>

        <div className="flex gap-2 mt-1">
          {["JPEG", "PNG", "WebP", "GIF", "PDF"].map((fmt) => (
            <span
              key={fmt}
              className="px-2 py-0.5 text-[10px] font-[family-name:var(--font-display)] tracking-wider rounded bg-[#1C1C1F] text-[#52525B]"
            >
              {fmt}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
