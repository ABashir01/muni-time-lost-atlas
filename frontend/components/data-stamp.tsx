import { formatTimestamp } from "@/lib/utils";

export function DataStamp({ value }: { value: string | null | undefined }) {
  if (!value) {
    return <p className="data-stamp">Metric timestamp unavailable.</p>;
  }

  return <p className="data-stamp">Metric updated {formatTimestamp(value)}</p>;
}
