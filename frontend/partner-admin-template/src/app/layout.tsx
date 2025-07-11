import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { TronWalletProvider } from "@/contexts/TronWalletContext";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Partner Admin Template",
  description: "TronLink 통합 파트너 관리자 대시보드",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ko">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <TronWalletProvider>
          {children}
        </TronWalletProvider>
      </body>
    </html>
  );
}
