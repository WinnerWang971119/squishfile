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

export function SizeControl({ maxSizeKb, value, onChange }: SizeControlProps) {
  const [customInput, setCustomInput] = useState("");

  const handlePreset = (preset: (typeof PRESETS)[number]) => {
    const kb = preset.kb ?? Math.round(maxSizeKb * (preset as any).factor);
    onChange(Math.max(10, Math.min(kb, maxSizeKb)));
  };

  const handleCustom = () => {
    const num = parseInt(customInput, 10);
    if (!isNaN(num) && num > 0) {
      onChange(Math.max(10, Math.min(num, maxSizeKb)));
    }
  };

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-3">
        <span className="text-xs text-[#888] w-12">10 KB</span>
        <input
          type="range"
          min={10}
          max={maxSizeKb}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="flex-1 accent-[#FFD60A] h-2 cursor-pointer"
        />
        <span className="text-xs text-[#888] w-16 text-right">
          {maxSizeKb >= 1024
            ? `${(maxSizeKb / 1024).toFixed(1)} MB`
            : `${maxSizeKb} KB`}
        </span>
      </div>

      <div className="text-center">
        <span className="text-[#FFD60A] font-bold text-lg">
          {value >= 1024
            ? `${(value / 1024).toFixed(1)} MB`
            : `${value} KB`}
        </span>
      </div>

      <div className="flex flex-wrap gap-2 justify-center">
        {PRESETS.map((preset) => (
          <button
            key={preset.label}
            onClick={() => handlePreset(preset)}
            className="
              px-3 py-1 text-xs rounded-full
              bg-[#252525] text-[#FAFAFA] border border-[#333]
              hover:border-[#FFD60A] hover:text-[#FFD60A]
              transition-colors
            "
          >
            {preset.label}
          </button>
        ))}
      </div>

      <div className="flex gap-2 justify-center">
        <input
          type="number"
          placeholder="Custom KB"
          value={customInput}
          onChange={(e) => setCustomInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleCustom()}
          className="
            w-28 px-3 py-1.5 text-xs rounded-lg
            bg-[#1A1A1A] text-[#FAFAFA] border border-[#333]
            focus:border-[#FFD60A] focus:outline-none
            placeholder:text-[#555]
          "
        />
        <button
          onClick={handleCustom}
          className="
            px-3 py-1.5 text-xs rounded-lg
            bg-[#FFD60A] text-[#0D0D0D] font-medium
            hover:bg-[#FFE44D] transition-colors
          "
        >
          Set
        </button>
      </div>
    </div>
  );
}
