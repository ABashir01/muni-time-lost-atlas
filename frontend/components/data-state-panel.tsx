import type { DataNotice } from "@/lib/types";

export function DataStatePanel({
  notice,
  eyebrow = "Live API state",
}: {
  notice: DataNotice;
  eyebrow?: string;
}) {
  return (
    <article className="panel-card state-panel">
      <p className="eyebrow">{eyebrow}</p>
      <h2>{notice.title}</h2>
      <p>{notice.message}</p>
      {notice.detail ? <small>{notice.detail}</small> : null}
    </article>
  );
}
