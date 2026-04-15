import { createBrowserRouter } from "react-router-dom";

import { AppShell } from "@/components/layout/AppShell";
import { AuditTrailPage } from "@/pages/audit/AuditTrailPage";
import { CaseDetailPage } from "@/pages/cases/CaseDetailPage";
import { CaseListPage } from "@/pages/cases/CaseListPage";
import { DashboardPage } from "@/pages/dashboard/DashboardPage";
import { NotFoundPage } from "@/pages/not-found/NotFoundPage";
import { ManualReviewQueuePage } from "@/pages/review/ManualReviewQueuePage";
import { SettingsPage } from "@/pages/settings/SettingsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppShell />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "cases", element: <CaseListPage /> },
      { path: "cases/:caseId", element: <CaseDetailPage /> },
      { path: "manual-review", element: <ManualReviewQueuePage /> },
      { path: "audit", element: <AuditTrailPage /> },
      { path: "settings", element: <SettingsPage /> },
      { path: "*", element: <NotFoundPage /> },
    ],
  },
]);
