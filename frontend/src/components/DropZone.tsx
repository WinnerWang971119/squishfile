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
        flex flex-col items-center justify-center
        h-full min-h-[200px] rounded-xl border-2 border-dashed
        cursor-pointer transition-all duration-200
        ${
          isDragging
            ? "border-[#FFD60A] bg-[#FFD60A]/10"
            : "border-[#333] hover:border-[#FFD60A]/50 hover:bg-[#1A1A1A]"
        }
      `}
    >
      <div className="text-4xl mb-3">+</div>
      <p className="text-[#FAFAFA] font-medium">Drop files here</p>
      <p className="text-[#888] text-sm mt-1">or click to browse</p>
      <p className="text-[#555] text-xs mt-3">Images & PDFs up to 100MB</p>
    </div>
  );
}
