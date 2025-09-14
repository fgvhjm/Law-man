import { veryLongText } from "@/assets/samples/texts/text";
import { SummaryPanelProps } from "@/types";

export default function SummaryPanel({ summary }: SummaryPanelProps) {
  return (
    <div className="border rounded-lg p-4">
      <h2 className="text-lg font-semibold mb-2">Summary</h2>
      <p className="text-sm text-slate-600 overflow-y-auto h-60">
        {summary}
      </p>
    </div>
  );
}
