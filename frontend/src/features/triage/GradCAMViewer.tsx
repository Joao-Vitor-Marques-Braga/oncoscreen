import React, { useState } from "react";
import { Eye, Layers, MapPin } from "lucide-react";

type ViewMode = "original" | "heatmap" | "overlay";

interface GradCAMViewerProps {
  originalBase64: string;
  heatmapBase64: string;
  quadrant: string;
}

export const GradCAMViewer: React.FC<GradCAMViewerProps> = ({
  originalBase64,
  heatmapBase64,
  quadrant,
}) => {
  const [mode, setMode] = useState<ViewMode>("overlay");
  const [opacity, setOpacity] = useState<number>(55);

  const origSrc = `data:image/jpeg;base64,${originalBase64}`;
  const heatSrc = `data:image/png;base64,${heatmapBase64}`;

  return (
    <div className="space-y-3">
      {/* Mode Switcher */}
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="inline-flex rounded-md border border-[#CBD5E1] dark:border-[#334155] overflow-hidden">
          <button
            type="button"
            onClick={() => setMode("original")}
            className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 border-r border-[#CBD5E1] dark:border-[#334155] ${
              mode === "original"
                ? "bg-[#1E3A8A] text-white"
                : "bg-white dark:bg-[#111827] text-[#475569] dark:text-[#94A3B8]"
            }`}
          >
            <Eye className="w-3.5 h-3.5" />
            Original
          </button>
          <button
            type="button"
            onClick={() => setMode("heatmap")}
            className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 border-r border-[#CBD5E1] dark:border-[#334155] ${
              mode === "heatmap"
                ? "bg-[#1E3A8A] text-white"
                : "bg-white dark:bg-[#111827] text-[#475569] dark:text-[#94A3B8]"
            }`}
          >
            Heatmap Puro
          </button>
          <button
            type="button"
            onClick={() => setMode("overlay")}
            className={`px-3 py-1.5 text-xs font-medium flex items-center gap-1.5 ${
              mode === "overlay"
                ? "bg-[#1E3A8A] text-white"
                : "bg-white dark:bg-[#111827] text-[#475569] dark:text-[#94A3B8]"
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            Sobreposição Interativa
          </button>
        </div>

        <div className="inline-flex items-center gap-1.5 text-xs font-medium text-[#1E3A8A] dark:text-[#93C5FD] bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] px-2.5 py-1 rounded">
          <MapPin className="w-3.5 h-3.5" />
          {quadrant}
        </div>
      </div>

      {/* Image Viewport */}
      <div className="relative w-full aspect-[4/3] bg-[#0F172A] border border-[#CBD5E1] dark:border-[#334155] rounded-md overflow-hidden flex items-center justify-center">
        {mode !== "heatmap" && (
          <img
            src={origSrc}
            alt="Imagem intraoral original"
            className="w-full h-full object-contain"
          />
        )}
        {mode === "heatmap" && (
          <img
            src={heatSrc}
            alt="Mapa de calor Grad-CAM"
            className="w-full h-full object-contain"
          />
        )}
        {mode === "overlay" && (
          <img
            src={heatSrc}
            alt="Sobreposição Grad-CAM"
            style={{ opacity: opacity / 100 }}
            className="absolute inset-0 w-full h-full object-contain pointer-events-none"
          />
        )}
      </div>

      {/* Real-time Opacity Slider */}
      {mode === "overlay" && (
        <div className="flex items-center gap-3 p-2.5 bg-[#F8FAFC] dark:bg-[#1E293B] border border-[#CBD5E1] dark:border-[#334155] rounded-md">
          <label
            htmlFor="gradcam-opacity"
            className="text-xs font-semibold text-[#0F172A] dark:text-[#E2E8F0] whitespace-nowrap"
          >
            Opacidade Grad-CAM: {opacity}%
          </label>
          <input
            id="gradcam-opacity"
            type="range"
            min={0}
            max={100}
            value={opacity}
            onChange={(e) => setOpacity(Number(e.target.value))}
            className="w-full accent-[#1E3A8A]"
          />
        </div>
      )}
    </div>
  );
};

