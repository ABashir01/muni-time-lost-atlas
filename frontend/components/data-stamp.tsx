import { formatTimestamp } from "@/lib/utils";

export function DataStamp({ value }: { value: string }) {
  return <p className="data-stamp">Metric updated {formatTimestamp(value)}</p>;
}
