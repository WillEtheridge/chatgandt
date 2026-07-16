import type { Metadata } from "next";
import localFont from "next/font/local";
import "./globals.css";

const neueMontrealMono = localFont({
  src: "./fonts/PPNeueMontrealMono-Book.woff2",
  weight: "400",
  style: "normal",
  display: "swap",
  fallback: ["Courier New", "monospace"],
});

export const metadata: Metadata = {
  title: "ChatG&T",
  description: "Useful answers, mixed differently.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body className={`${neueMontrealMono.className} bg-concrete text-steel antialiased`}>
        {children}
      </body>
    </html>
  );
}
