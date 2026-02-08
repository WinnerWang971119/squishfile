import { useState } from "react";

interface SizeControlProps {
  maxSizeKb: number;
  value: number;
  onChange: (kb: number) => void;
}

const PRESETS = [
  { label: "50%", factor: 0.5 },
  { label: "25%", factor: 0.25 },
  { label: "1 MB", kb: 1024 },
  { label: "500 KB", kb: 500 },
  { label: "200 KB", kb: 200 },
];

function formatKb(kb: number): string {
  return kb >= 1024 ? `${(kb / 1024).toFixed(1)} MB` : `${kb} KB`;
}

export function SizeControl({ maxSizeKb, value, onChange }: SizeControlProps) {
  const [customInput, setCustomInput] = useState("");

  const handlePreset = (preset: (typeof PRESETS)[number]) => {
    const kb = preset.kb ?? Math.round(maxSizeKb * (preset as { factor: number }).factor);
    onChange(Math.max(10, Math.min(kb, maxSizeKb)));
  };

  const handleCustom = () => {
    const num = parseInt(customInput, 10);
    if (!isNaN(num) && num > 0) {
      onChange(Math.max(10, Math.min(num, maxSizeKb)));
      setCustomInput("");
    }
  };

  return (
    <div className="space-y-6">
      {/* Current value display */}
      <div className="text-center">
        <span className="font-[family-name:var(--font-display)] text-4xl font-extrabold text-[#FFD60A] tracking-tight">
          {formatKb(value)}
        </span>
        <p className="text-[#71717A] text-xs mt-1.5 font-[family-name:var(--font-display)] tracking-wide">
          TARGET SIZE
        </p>
      </div>

      {/* Slider */}
      <div className="px-1">
        <input
          type="range"
          min={10}
          max={maxSizeKb}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full cursor-pointer"
        />
        <div className="flex justify-between mt-1.5">
          <span className="text-[10px] font-[family-name:var(--font-display)] text-[#3F3F46]">10 KB</span>
          <span className="text-[10px] font-[family-name:var(--font-display)] text-[#3F3F46]">{formatKb(maxSizeKb)}</span>
        </div>
      </div>

      {/* Presets */}
      <div className="flex flex-wrap gap-2 justify-center">
        {PRESETS.map((preset) => {
          const presetKb = preset.kb ?? Math.round(maxSizeKb * (preset as { factor: number }).factor);
          const isActive = Math.abs(value - presetKb) < 5;
          return (
            <button
              key={preset.label}
              onClick={() => handlePreset(preset)}
              className={`
                px-4 py-2 text-xs rounded-xl
                font-[family-name:var(--font-display)] font-bold tracking-wide
                border transition-all duration-200
                ${isActive
                  ? "bg-[#FFD60A]/15 text-[#FFD60A] border-[#FFD60A]/30"
                  : "bg-[#1C1C1F] text-[#A1A1AA] border-[#27272A] hover:border-[#FFD60A]/30 hover:text-[#F5F5F4]"
                }
              `}
            >
              {preset.label}
            </button>
          );
        })}
      </div>

      {/* Custom input */}
      <div className="flex gap-2 justify-center">
        <input
          type="number"
          placeholder="Custom KB"
          value={customInput}
          onChange={(e) => setCustomInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCustom()}
          className="
            w-32 px-4 py-2.5 text-sm rounded-xl
            bg-[#1C1C1F] text-[#F5F5F4] border border-[#27272A]
            focus:border-[#FFD60A]/50 focus:outline-none focus:shadow-[0_0_0_3px_rgba(255,214,10,0.08)]
            placeholder:text-[#3F3F46]
            font-[family-name:var(--font-display)]
            transition-all duration-200
          "
        />
        <button
          onClick={handleCustom}
          className="
            px-4 py-2.5 text-sm rounded-xl
            bg-[#FFD60A] text-[#0A0A0B] font-bold
            hover:bg-[#FFE44D] active:scale-95
            transition-all duration-200
            font-[family-name:var(--font-display)]
          "
        >
          Set
        </button>
      </div>
    </div>
  );
}
