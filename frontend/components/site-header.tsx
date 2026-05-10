import Link from "next/link";

const navigation = [
  { href: "/map", label: "Explore the map" },
  { href: "/", label: "Rankings" },
  { href: "/compare?ids=14,49", label: "Compare" },
  { href: "/methodology", label: "Data and methods" },
];

export function SiteHeader() {
  return (
    <header className="site-header">
      <Link className="brand-lockup" href="/">
        <div className="brand-mark">Muni</div>
        <div className="brand-copy">
          <strong>Muni Lost Time Atlas</strong>
          <span>Where riders lose the most time</span>
        </div>
      </Link>
      <nav className="site-nav" aria-label="Primary">
        {navigation.map((item) => (
          <Link href={item.href} key={item.href}>
            {item.label}
          </Link>
        ))}
      </nav>
    </header>
  );
}
