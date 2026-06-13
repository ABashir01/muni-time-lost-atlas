import type { Metadata } from "next";
import Script from "next/script";
import {
  Anton,
  Archivo_Narrow,
  Bebas_Neue,
  Fjalla_One,
  League_Gothic,
  Oswald,
  Public_Sans,
  Roboto_Condensed,
} from "next/font/google";
import { AppChrome } from "@/components/app-chrome";
import { MaintenanceModeScreen } from "@/components/maintenance-mode-screen";
import { getMaintenanceState } from "@/lib/maintenance";
import "./globals.css";
import "maplibre-gl/dist/maplibre-gl.css";

export const dynamic = "force-dynamic";

const oswald = Oswald({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-oswald",
});

const anton = Anton({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-anton",
});

const leagueGothic = League_Gothic({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-league-gothic",
});

const robotoCondensed = Roboto_Condensed({
  subsets: ["latin"],
  weight: ["400", "500", "700"],
  variable: "--font-roboto-condensed",
});

const bebasNeue = Bebas_Neue({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-bebas-neue",
});

const archivoNarrow = Archivo_Narrow({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-archivo-narrow",
});

const fjallaOne = Fjalla_One({
  subsets: ["latin"],
  weight: ["400"],
  variable: "--font-fjalla-one",
});

const body = Public_Sans({
  subsets: ["latin"],
  variable: "--font-body",
});

export const metadata: Metadata = {
  title: "Muni Lost Time Atlas",
  description: "Where Muni riders lose the most time.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const maintenanceState = getMaintenanceState();

  return (
    <html lang="en">
      <body
        className={`${oswald.variable} ${anton.variable} ${leagueGothic.variable} ${robotoCondensed.variable} ${bebasNeue.variable} ${archivoNarrow.variable} ${fjallaOne.variable} ${body.variable}`}
      >
        {maintenanceState.enabled ? (
          <MaintenanceModeScreen />
        ) : (
          <AppChrome>{children}</AppChrome>
        )}
        <Script
          data-cf-beacon='{"token":"5753986c203d4701a73f24304e6c83e9"}'
          defer
          src="https://static.cloudflareinsights.com/beacon.min.js"
          strategy="afterInteractive"
        />
      </body>
    </html>
  );
}
