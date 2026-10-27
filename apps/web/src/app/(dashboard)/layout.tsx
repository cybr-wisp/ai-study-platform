import type { ReactNode } from "react";
import AppBar from "../../components/layout/AppBar";

export default function DashboardLayout({ children }: { children: ReactNode }) {
  return (
    <>
      <AppBar />
      {children}
    </>
  );
}
