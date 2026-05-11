"use client";

import { usePathname } from "next/navigation";
import { SiteFooter } from "@/components/site-footer";
import { SiteHeader } from "@/components/site-header";

export function AppChrome({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const isHome = pathname === "/";

  return (
    <div className={`site-frame${isHome ? " homepage-active-frame" : ""}`}>
      {isHome ? null : <SiteHeader />}
      <main>{children}</main>
      {isHome ? null : <SiteFooter />}
    </div>
  );
}
