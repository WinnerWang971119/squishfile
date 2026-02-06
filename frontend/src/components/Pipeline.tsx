import type { FileEntry } from "../types";
import { FileCard } from "./FileCard";

interface PipelineProps {
  files: FileEntry[];
}

export function Pipeline({ files }: PipelineProps) {
  const queued = files.filter(
    (f) => f.status === "uploading" || f.status === "queued"
  );
  const compressing = files.filter((f) => f.status === "compressing");
  const done = files.filter((f) => f.status === "done" || f.status === "error");

  return (
    <div className="grid grid-cols-3 gap-4 h-full">
      <Column title="QUEUED" count={queued.length} accent="text-[#FFD60A]">
        {queued.map((f) => (
          <FileCard key={f.id} file={f} />
        ))}
      </Column>

      <Column title="COMPRESSING" count={compressing.length} accent="text-[#FFD60A]">
        {compressing.map((f) => (
          <FileCard key={f.id} file={f} />
        ))}
      </Column>

      <Column title="DONE" count={done.length} accent="text-[#22C55E]">
        {done.map((f) => (
          <FileCard key={f.id} file={f} />
        ))}
      </Column>
    </div>
  );
}

function Column({
  title,
  count,
  accent,
  children,
}: {
  title: string;
  count: number;
  accent: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col">
      <div className="flex items-center gap-2 mb-3 px-1">
        <h2 className={`text-xs font-bold tracking-wider ${accent}`}>
          {title}
        </h2>
        {count > 0 && (
          <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[#252525] text-[#888]">
            {count}
          </span>
        )}
      </div>
      <div className="flex-1 space-y-2 overflow-y-auto pr-1">{children}</div>
    </div>
  );
}
