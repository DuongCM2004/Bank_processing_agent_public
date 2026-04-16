import { NavLink, Outlet } from "react-router-dom";

import { useCurrentUser } from "@/app/providers";

const navItems = [
  { to: "/cases", label: "Cases" },
  { to: "/manual-review", label: "Manual Review" },
];

export function AppLayout() {
  const user = useCurrentUser();

  return (
    <div className="min-h-screen bg-surface text-ink">
      <header className="border-b border-line bg-panel">
        <div className="mx-auto flex max-w-7xl flex-col gap-4 px-4 py-4 sm:flex-row sm:items-center sm:justify-between lg:px-8">
          <div>
            <p className="text-xs font-bold uppercase tracking-wider text-teal">Banking Ops Agent</p>
            <p className="text-lg font-semibold">Document Processing</p>
          </div>
          <nav aria-label="Primary navigation" className="flex flex-wrap gap-2">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  `rounded-md px-3 py-2 text-sm font-semibold ${
                    isActive ? "bg-tealSoft text-teal" : "text-muted hover:bg-surface hover:text-ink"
                  }`
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>
          <div className="rounded-md border border-line px-3 py-2 text-sm">
            <span className="font-semibold">{user.displayName}</span>
            <span className="ml-2 text-muted">{user.role}</span>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-7xl px-4 py-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  );
}
