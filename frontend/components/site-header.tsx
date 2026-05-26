"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const navigation = [
  { href: "/map", label: "Explore the map" },
  { href: "/rankings", label: "Rankings" },
  { href: "/compare", label: "Compare" },
  { href: "/methodology", label: "Data & Methods" },
];

export function SiteHeader() {
  const pathname = usePathname();

  return (
    <header className="site-header">
      <Link aria-label="Back to the homepage" className="brand-lockup" href="/" title="Back to homepage">
        <div className="brand-mark">Muni</div>
        <div className="brand-copy">
          <strong>Muni Lost Time Atlas</strong>
          <span>Where riders lose the most time</span>
        </div>
      </Link>
      <nav className="site-nav" aria-label="Primary">
        {navigation.map((item) => (
          <Link
            className={pathname === item.href ? "is-active" : undefined}
            href={item.href}
            key={item.href}
          >
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
