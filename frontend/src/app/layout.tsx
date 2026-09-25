import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "QuantDesk India | NSE Algorithmic Trading Bot & Paper Simulator",
  description:
    "Production-grade Indian Equity Market Paper Trading & Algorithmic Strategy Research Platform. Zero real-money risk, realistic regulatory cost modeling, and zero look-ahead bias backtesting.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="dark">
      <body className={`${inter.className} bg-slate-950 text-slate-100 antialiased min-h-screen selection:bg-cyan-500 selection:text-slate-950`}>
        {children}
      </body>
    </html>
  );
}
