type ExplainerIcon = "waiting" | "travel" | "bunching";

export function HomepageTransitSymbol() {
  return (
    <svg
      aria-hidden="true"
      fill="none"
      viewBox="0 0 40 40"
      xmlns="http://www.w3.org/2000/svg"
    >
      <circle cx="20" cy="20" fill="#111111" r="20" />
      <rect fill="#FFFFFF" height="14" rx="3" width="16" x="12" y="8" />
      <rect fill="#FFFFFF" height="3" rx="1.5" width="16" x="12" y="24" />
      <rect fill="#FFFFFF" height="3" rx="1.5" width="4" x="12" y="28" />
      <rect fill="#FFFFFF" height="3" rx="1.5" width="4" x="24" y="28" />
      <rect fill="#111111" height="4" rx="1.2" width="5" x="13.5" y="11" />
      <rect fill="#111111" height="4" rx="1.2" width="5" x="21.5" y="11" />
    </svg>
  );
}

export function HomepageExplainerSymbol({ icon }: { icon: ExplainerIcon }) {
  if (icon === "waiting") {
    return (
      <svg
        aria-hidden="true"
        fill="none"
        viewBox="0 0 160 220"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect width="160" height="220" fill="#ed1c24" />
        <circle cx="80" cy="92" r="40" fill="none" stroke="#ffffff" strokeWidth="10" />
        <circle cx="80" cy="92" r="5" fill="#ffffff" />
        <path d="M80 92V68" stroke="#ffffff" strokeWidth="10" strokeLinecap="round" />
        <path d="M80 92L100 106" stroke="#ffffff" strokeWidth="10" strokeLinecap="round" />
        <path d="M48 152H112" stroke="#ffffff" strokeWidth="8" strokeLinecap="round" />
        <path d="M58 176H102" stroke="#ffffff" strokeWidth="8" strokeLinecap="round" />
      </svg>
    );
  }

  if (icon === "travel") {
    return (
      <svg
        aria-hidden="true"
        fill="none"
        viewBox="0 0 160 220"
        xmlns="http://www.w3.org/2000/svg"
      >
        <rect width="160" height="220" fill="#feedb1" />
        <rect
          x="36"
          y="70"
          width="88"
          height="42"
          rx="11"
          fill="none"
          stroke="#f1af00"
          strokeWidth="8"
        />
        <rect x="48" y="80" width="18" height="11" rx="3" fill="#f1af00" />
        <rect x="71" y="80" width="18" height="11" rx="3" fill="#f1af00" />
        <rect x="94" y="80" width="18" height="11" rx="3" fill="#f1af00" />
        <path d="M46 98H114" stroke="#f1af00" strokeWidth="6" strokeLinecap="round" />
        <circle cx="58" cy="112" r="7" fill="#f1af00" />
        <circle cx="102" cy="112" r="7" fill="#f1af00" />
        <path d="M44 166H108" stroke="#f1af00" strokeWidth="10" strokeLinecap="round" />
        <path d="M108 166L94 152" stroke="#f1af00" strokeWidth="10" strokeLinecap="round" />
        <path d="M108 166L94 180" stroke="#f1af00" strokeWidth="10" strokeLinecap="round" />
      </svg>
    );
  }

  return (
    <svg
      aria-hidden="true"
      fill="none"
      viewBox="0 0 160 220"
      xmlns="http://www.w3.org/2000/svg"
    >
      <rect width="160" height="220" fill="#c7d4f4" />
      <rect
        x="34"
        y="60"
        width="76"
        height="36"
        rx="10"
        fill="none"
        stroke="#2467d6"
        strokeWidth="7"
      />
      <rect x="44" y="69" width="15" height="9" rx="3" fill="#2467d6" />
      <rect x="64" y="69" width="15" height="9" rx="3" fill="#2467d6" />
      <rect x="84" y="69" width="15" height="9" rx="3" fill="#2467d6" />
      <path d="M42 83H102" stroke="#2467d6" strokeWidth="5" strokeLinecap="round" />
      <circle cx="53" cy="96" r="6" fill="#2467d6" />
      <circle cx="91" cy="96" r="6" fill="#2467d6" />
      <rect
        x="42"
        y="96"
        width="76"
        height="36"
        rx="10"
        fill="none"
        stroke="#2467d6"
        strokeWidth="7"
      />
      <rect x="52" y="105" width="15" height="9" rx="3" fill="#2467d6" />
      <rect x="72" y="105" width="15" height="9" rx="3" fill="#2467d6" />
      <rect x="92" y="105" width="15" height="9" rx="3" fill="#2467d6" />
      <path d="M50 119H110" stroke="#2467d6" strokeWidth="5" strokeLinecap="round" />
      <circle cx="61" cy="132" r="6" fill="#2467d6" />
      <circle cx="99" cy="132" r="6" fill="#2467d6" />
      <rect
        x="50"
        y="132"
        width="76"
        height="36"
        rx="10"
        fill="none"
        stroke="#2467d6"
        strokeWidth="7"
      />
      <rect x="60" y="141" width="15" height="9" rx="3" fill="#2467d6" />
      <rect x="80" y="141" width="15" height="9" rx="3" fill="#2467d6" />
      <rect x="100" y="141" width="15" height="9" rx="3" fill="#2467d6" />
      <path d="M58 155H118" stroke="#2467d6" strokeWidth="5" strokeLinecap="round" />
      <circle cx="69" cy="168" r="6" fill="#2467d6" />
      <circle cx="107" cy="168" r="6" fill="#2467d6" />
    </svg>
  );
}
