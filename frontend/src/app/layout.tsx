import "./globals.css";
import type { ReactNode } from "react";

export const metadata = {
  title: "Ops Agent Review Console",
  description: "Operations-focused banking document review console",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
