"use client";

import { useEffect, useState } from "react";
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
  const [menuOpen, setMenuOpen] = useState(false);

  useEffect(() => {
    setMenuOpen(false);
  }, [pathname]);

  return (
    <header className="homepage-masthead">
      <div className="homepage-masthead-top">
        <Link
          aria-label="Back to the homepage"
          className="homepage-brand"
          href="/"
          title="Back to homepage"
        >
          <div className="homepage-brand-mark">Muni</div>
          <div className="homepage-brand-copy">Muni Lost Time Atlas</div>
        </Link>

        <button
          aria-controls="primary-navigation"
          aria-expanded={menuOpen}
          aria-label={menuOpen ? "Close navigation menu" : "Open navigation menu"}
          className={`homepage-menu-toggle ${menuOpen ? "is-open" : ""}`}
          onClick={() => setMenuOpen((value) => !value)}
          type="button"
        >
          <span />
          <span />
          <span />
        </button>
      </div>
      <nav
        aria-label="Primary"
        className={`homepage-nav${menuOpen ? " is-open" : ""}`}
        id="primary-navigation"
      >
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
