import Link from "next/link";
import type { ReactNode } from "react";

import { getPrimaryNav } from "@/lib/navigation";
import type { CurrentUser } from "@/lib/types";

export function AppShell({ user, children }: { user: CurrentUser; children: ReactNode }) {
  const navItems = getPrimaryNav(user);

  return (
    <main className="app-shell">
      <aside className="sidebar panel">
        <div>
          <p className="eyebrow">Ops Agent</p>
          <h1>Review Workspace</h1>
          <p className="muted">Banking-safe document processing console for operations and compliance teams.</p>
        </div>
        <nav className="nav-list">
          {navItems.map((item) => (
            <Link key={item.href} href={item.href} className="nav-link">
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="user-card">
          <div className="muted">Signed in as</div>
          <strong>{user.display_name}</strong>
          <div className="pill-row">
            <span className="pill">{user.role}</span>
          </div>
        </div>
      </aside>
      <section className="content-shell">{children}</section>
    </main>
  );
}
