import { useState, useCallback } from "react";
import { Stepper } from "./components/Stepper";
import { UploadPage } from "./components/UploadPage";
import { CompressPage } from "./components/CompressPage";
import { DownloadPage } from "./components/DownloadPage";
import { uploadFile, compressFile } from "./api/client";
import type { FileEntry } from "./types";

export default function App() {
  const [currentStep, setCurrentStep] = useState(1);
  const [files, setFiles] = useState<FileEntry[]>([]);
  const [targetKb, setTargetKb] = useState(500);
  const [maxKb, setMaxKb] = useState(10240);

  // Track which steps have been completed for stepper navigation
  const completedSteps: number[] = [];
  if (files.length > 0) completedSteps.push(1);
  if (files.some((f) => f.status === "done" || f.status === "compressing" || f.status === "error"))
    completedSteps.push(2);

  const queuedFiles = files.filter(
    (f) => f.status === "queued" || f.status === "uploading"
  );
  const canGoNext = currentStep === 1 && queuedFiles.length > 0;

  // Upload files to server (queue them, no compression)
  const handleFiles = useCallback(async (newFiles: File[]) => {
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
                  category: uploaded.category as "image" | "pdf" | "video" | "audio",
                  size: uploaded.size,
                  width: uploaded.width,
                  height: uploaded.height,
                  duration: uploaded.duration,
                  status: "queued" as const,
                  progress: 0,
                }
              : f
          )
        );

        const fileSizeKb = Math.ceil(uploaded.size / 1024);
        setMaxKb((prev) => Math.max(prev, fileSizeKb));
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : "Upload failed";
        setFiles((prev) =>
          prev.map((f) =>
            f.id === tempId
              ? { ...f, status: "error" as const, message }
              : f
          )
        );
      }
    }
  }, []);

  // Remove a file from the queue
  const handleRemove = useCallback((id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  }, []);

  // Start compression for all queued files
  const handleCompress = useCallback(async () => {
    setCurrentStep(3);

    // Get all queued files at this moment
    const toCompress = files.filter((f) => f.status === "queued");

    // Mark all as compressing
    setFiles((prev) =>
      prev.map((f) =>
        f.status === "queued"
          ? { ...f, status: "compressing" as const, progress: 10 }
          : f
      )
    );

    // Compress each file sequentially
    for (const file of toCompress) {
      // Start progress animation
      const progressInterval = setInterval(() => {
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id && f.status === "compressing"
              ? { ...f, progress: Math.min(f.progress + 15, 90) }
              : f
          )
        );
      }, 300);

      try {
        const result = await compressFile(file.id, targetKb);

        clearInterval(progressInterval);

        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id
              ? {
                  ...f,
                  status: "done" as const,
                  progress: 100,
                  compressedSize: result.compressed_size,
                  message: result.message || undefined,
                }
              : f
          )
        );
      } catch (err: unknown) {
        clearInterval(progressInterval);
        const message = err instanceof Error ? err.message : "Compression failed";
        setFiles((prev) =>
          prev.map((f) =>
            f.id === file.id
              ? { ...f, status: "error" as const, message }
              : f
          )
        );
      }
    }
  }, [files, targetKb]);

  // Reset everything
  const handleStartOver = useCallback(() => {
    setFiles([]);
    setTargetKb(500);
    setMaxKb(10240);
    setCurrentStep(1);
  }, []);

  // Stepper navigation
  const handleStepClick = (step: number) => {
    if (step <= currentStep || completedSteps.includes(step)) {
      setCurrentStep(step);
    }
  };

  return (
    <div className="grain min-h-screen bg-[#0A0A0B] text-[#F5F5F4] flex flex-col">
      {/* Header */}
      <header className="px-6 py-5 border-b border-[#1E1E21]">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <h1 className="font-[family-name:var(--font-display)] text-lg font-extrabold tracking-tight">
            <span className="text-[#FFD60A]">Squish</span>
            <span className="text-[#F5F5F4]">File</span>
          </h1>
          <Stepper
            currentStep={currentStep}
            completedSteps={completedSteps}
            onStepClick={handleStepClick}
          />
          <div className="w-20" /> {/* Spacer for centering stepper */}
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 p-6 flex flex-col max-w-6xl mx-auto w-full">
        <div className="flex-1 flex flex-col">
          {currentStep === 1 && (
            <UploadPage
              files={files.filter((f) => f.status === "queued" || f.status === "uploading")}
              onFiles={handleFiles}
              onRemove={handleRemove}
            />
          )}

          {currentStep === 2 && (
            <CompressPage
              files={files.filter((f) => f.status === "queued")}
              targetKb={targetKb}
              maxKb={maxKb}
              onTargetChange={setTargetKb}
              hasVideo={files.some((f) => f.category === "video" || f.category === "audio")}
            />
          )}

          {currentStep === 3 && (
            <DownloadPage
              files={files}
              onStartOver={handleStartOver}
            />
          )}
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-6 pt-6 border-t border-[#1E1E21]">
          <div>
            {currentStep > 1 && currentStep < 3 && (
              <button
                onClick={() => setCurrentStep((s) => s - 1)}
                className="
                  flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm
                  text-[#A1A1AA] hover:text-[#F5F5F4]
                  bg-[#141416] border border-[#27272A] hover:border-[#3F3F46]
                  transition-all duration-200
                "
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="19" y1="12" x2="5" y2="12" />
                  <polyline points="12 19 5 12 12 5" />
                </svg>
                Back
              </button>
            )}
          </div>

          <div>
            {currentStep === 1 && (
              <button
                onClick={() => setCurrentStep(2)}
                disabled={!canGoNext}
                className={`
                  flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold
                  font-[family-name:var(--font-display)] tracking-wide
                  transition-all duration-200
                  ${canGoNext
                    ? "bg-[#FFD60A] text-[#0A0A0B] hover:bg-[#FFE44D] active:scale-[0.98] shadow-[0_0_20px_rgba(255,214,10,0.1)]"
                    : "bg-[#1C1C1F] text-[#3F3F46] cursor-not-allowed"
                  }
                `}
              >
                Next
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </button>
            )}

            {currentStep === 2 && (
              <button
                onClick={handleCompress}
                className="
                  flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold
                  font-[family-name:var(--font-display)] tracking-wide
                  bg-[#FFD60A] text-[#0A0A0B] hover:bg-[#FFE44D]
                  active:scale-[0.98] shadow-[0_0_20px_rgba(255,214,10,0.1)]
                  transition-all duration-200
                "
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="4 14 10 14 10 20" />
                  <polyline points="20 10 14 10 14 4" />
                  <line x1="14" y1="10" x2="21" y2="3" />
                  <line x1="3" y1="21" x2="10" y2="14" />
                </svg>
                Compress
              </button>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
