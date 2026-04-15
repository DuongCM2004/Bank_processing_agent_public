import { NavLink, Outlet } from "react-router-dom";

import { cn } from "@/lib/cn";

const navigation = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/cases", label: "Cases" },
  { to: "/manual-review", label: "Manual Review" },
  { to: "/audit", label: "Audit Trail" },
  { to: "/settings", label: "Settings" },
];

export function AppShell() {
  return (
    <div className="min-h-screen bg-mist text-ink">
      <div className="mx-auto grid min-h-screen max-w-[1600px] grid-cols-1 lg:grid-cols-[280px_minmax(0,1fr)]">
        <aside className="border-b border-line bg-ink px-6 py-8 text-white lg:border-b-0 lg:border-r">
          <div className="flex items-center gap-3">
            <img src="/logo-mark.svg" alt="Ops Agent" className="h-12 w-12 rounded-2xl" />
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.16em] text-white/60">Ops Agent</p>
              <h1 className="text-xl font-semibold">Document Processing</h1>
            </div>
          </div>

          <nav className="mt-10 space-y-2">
            {navigation.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                end={item.end}
                className={({ isActive }) =>
                  cn(
                    "block rounded-xl px-4 py-3 text-sm font-medium transition-colors",
                    isActive ? "bg-white text-ink" : "text-white/72 hover:bg-white/10 hover:text-white",
                  )
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="mt-10 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/72">
            <p className="font-semibold text-white">Ops workflow focus</p>
            <p className="mt-2 leading-6">
              Prioritize queue visibility, evidence review, explicit state transitions, and traceable operator actions.
            </p>
          </div>
        </aside>

        <div className="min-w-0">
          <header className="border-b border-line bg-white px-6 py-5">
            <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
              <div>
                <p className="eyebrow">Operations Dashboard</p>
                <p className="mt-1 text-sm text-slate">
                  Banking-grade review workspace for document intake, validation, decisions, and auditability.
                </p>
              </div>
              <div className="rounded-full bg-mist px-4 py-2 text-xs font-semibold uppercase tracking-wide text-slate">
                MVP frontend scaffold
              </div>
            </div>
          </header>

          <main className="space-y-6 px-6 py-6">
            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
