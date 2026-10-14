import type { ReactNode } from "react";

export const metadata = { title: "Profe Marisol" };

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, background: "#f7f7f5" }}>
        {children}
      </body>
    </html>
  );
}
