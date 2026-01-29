import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import Sidebar from "@/components/Sidebar";
import AuthProvider from "@/components/AuthProvider";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "AsianDrama Admin",
  description: "Admin Portal for AsianDrama Streaming App",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${inter.className} bg-gray-950 text-white`}>
        <AuthProvider>
          <div className="flex min-h-screen">
            <Sidebar />
            <main className="flex-1 p-8">
              {children}
            </main>
          </div>
        </AuthProvider>
      </body>
    </html>
  );
}
