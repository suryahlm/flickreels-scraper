import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import Header from "@/components/Header";
import AuthProvider from "@/components/AuthProvider";

const plusJakarta = Plus_Jakarta_Sans({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700", "800"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "AsianDrama Admin Console — Luxury Management Suite",
  description: "Executive Portal for AsianDrama Streaming Infrastructure",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="id" className={`dark ${plusJakarta.className}`}>
      <body className="bg-[#07090E] text-slate-100 min-h-screen antialiased selection:bg-amber-500/30 selection:text-amber-200">
        <AuthProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex-1 flex flex-col min-w-0 bg-[#07090E]">
              <Header />
              <main className="flex-1 px-8 pb-12 min-w-0">
                {children}
              </main>
            </div>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
