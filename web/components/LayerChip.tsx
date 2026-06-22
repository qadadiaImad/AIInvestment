import { layerColor, layerLabel } from "@/lib/format";

export default function LayerChip({ layer }: { layer?: string | null }) {
  const color = layerColor(layer);
  return (
    <span
      className="inline-block px-1.5 py-px text-[9.5px] font-semibold uppercase tracking-wider rounded-sm align-middle"
      style={{
        color,
        border: `1px solid ${color}`,
        backgroundColor: `${color}1a`,
      }}
    >
      {layerLabel(layer)}
    </span>
  );
}
