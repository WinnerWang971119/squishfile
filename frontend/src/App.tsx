import { useState, useCallback } from "react";
import { DropZone } from "./components/DropZone";
import { Pipeline } from "./components/Pipeline";
import { SizeControl } from "./components/SizeControl";
import { uploadFile, compressFile, downloadUrl } from "./api/client";
import type { FileEntry } from "./types";

export default function App() {
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [targetKb, setTargetKb] = useState(500);
  const [maxKb, setMaxKb] = useState(10240);

  const handleFiles = useCallback(
    async (newFiles: File[]) => {
      for (const file of newFiles) {
        const tempId = `temp-${Date.now()}-${Math.random().toString(36).slice(2)}`;
        const entry: FileEntry = {
          id: tempId,
          originalFilename: file.name,
          mime: file.type || "application/octet-stream",
          category: "image",
          size: file.size,
          status: "uploading",
          progress: 0,
        };
        setFiles((prev) => [...prev, entry]);

        try {
          const uploaded = await uploadFile(file);
          const realId = uploaded.id;

          setFiles((prev) =>
            prev.map((f) =>
              f.id === tempId
                ? {
                    ...f,
                    id: realId,
                    mime: uploaded.mime,
                    category: uploaded.category as "image" | "pdf",
                    size: uploaded.size,
                    width: uploaded.width,
                    height: uploaded.height,
                    status: "compressing",
                    progress: 10,
                  }
                : f
            )
          );

          const fileSizeKb = Math.ceil(uploaded.size / 1024);
          setMaxKb((prev) => Math.max(prev, fileSizeKb));

          const progressInterval = setInterval(() => {
            setFiles((prev) =>
              prev.map((f) =>
                f.id === realId && f.status === "compressing"
                  ? { ...f, progress: Math.min(f.progress + 15, 90) }
                  : f
              )
            );
          }, 300);

          const result = await compressFile(realId, targetKb);

          clearInterval(progressInterval);

          setFiles((prev) =>
            prev.map((f) =>
              f.id === realId
                ? {
                    ...f,
                    status: "done",
                    progress: 100,
                    compressedSize: result.compressed_size,
                    message: result.message || undefined,
                  }
                : f
            )
          );
        } catch (err: any) {
          setFiles((prev) =>
            prev.map((f) =>
              f.id === tempId || f.status === "uploading" || f.status === "compressing"
                ? { ...f, status: "error", message: err.message }
                : f
            )
          );
        }
      }
    },
    [targetKb]
  );

  const doneFiles = files.filter((f) => f.status === "done");

  const handleDownloadAll = () => {
    doneFiles.forEach((f) => {
      const a = document.createElement("a");
      a.href = downloadUrl(f.id);
      a.download = f.originalFilename;
      a.click();
    });
  };

  return (
    <div className="min-h-screen bg-[#0D0D0D] text-[#FAFAFA] flex flex-col">
      <header className="px-6 py-4 border-b border-[#222]">
        <h1 className="text-xl font-bold">
          <span className="text-[#FFD60A]">Squish</span>File
        </h1>
      </header>

      <main className="flex-1 p-6 flex flex-col gap-6 max-w-6xl mx-auto w-full">
        <div className="grid grid-cols-[280px_1fr] gap-6 flex-1 min-h-[400px]">
          <DropZone onFiles={handleFiles} />
          <Pipeline files={files} />
        </div>

        <div className="bg-[#141414] rounded-xl p-4 border border-[#222]">
          <div className="flex items-center gap-8">
            <div className="flex-1">
              <p className="text-xs text-[#888] mb-2 font-medium">TARGET SIZE</p>
              <SizeControl
                maxSizeKb={maxKb}
                value={targetKb}
                onChange={setTargetKb}
              />
            </div>
            {doneFiles.length > 1 && (
              <button
                onClick={handleDownloadAll}
                className="
                  px-6 py-3 rounded-xl
                  bg-[#FFD60A] text-[#0D0D0D] font-bold
                  hover:bg-[#FFE44D] transition-colors
                  whitespace-nowrap
                "
              >
                Download All ({doneFiles.length})
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
