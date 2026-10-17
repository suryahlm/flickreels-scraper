import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import AuthProvider from "@/components/AuthProvider";
import AdminShell from "@/components/AdminShell";

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "FreeDrama Admin Console — Luxury Management Suite",
  description: "Executive Portal for FreeDrama Streaming Infrastructure",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id" className={`dark ${plusJakarta.className}`}>
      <body className="bg-[#07090E] text-slate-100 h-screen overflow-hidden antialiased selection:bg-amber-500/30 selection:text-amber-200">
        <AuthProvider>
          <AdminShell>{children}</AdminShell>
        </AuthProvider>
      </body>
    </html>
  );
}
