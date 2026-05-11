import type { Metadata } from "next";
import { Oswald, Public_Sans } from "next/font/google";
import { AppChrome } from "@/components/app-chrome";
import "./globals.css";

const display = Oswald({
  subsets: ["latin"],
  weight: ["400", "500", "600", "700"],
  variable: "--font-display",
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
  return (
    <html lang="en">
      <body className={`${display.variable} ${body.variable}`}>
        <AppChrome>{children}</AppChrome>
      </body>
    </html>
  );
}
