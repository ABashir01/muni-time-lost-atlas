const tabs = [
  { label: "Now", match: ["now"] },
  { label: "Today", match: ["today", "all day", "all_day"] },
  { label: "This week", match: ["this week", "week"] },
  { label: "This month", match: ["this month", "month"] },
];

export function TimeWindowStrip({ currentWindow }: { currentWindow: string }) {
  const normalizedCurrent = currentWindow.toLowerCase();

  return (
    <div className="window-strip" aria-label="Published time windows">
      {tabs.map((tab) => {
        const current = tab.match.includes(normalizedCurrent);
        return (
          <span
            className={`window-tab ${current ? "current" : "inactive"}`}
            key={tab.label}
          >
            <span>{tab.label}</span>
            {current ? <i aria-hidden="true" className="window-tab-dot" /> : null}
          </span>
        );
      })}
    </div>
  );
}
