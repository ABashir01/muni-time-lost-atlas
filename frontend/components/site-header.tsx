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
    <header className="homepage-masthead">
      <Link
        aria-label="Back to the homepage"
        className="homepage-brand"
        href="/"
        title="Back to homepage"
      >
        <div className="homepage-brand-mark">Muni</div>
        <div className="homepage-brand-copy">Muni Lost Time Atlas</div>
      </Link>
      <nav aria-label="Primary" className="homepage-nav">
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
