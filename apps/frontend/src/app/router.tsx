import { Navigate, createBrowserRouter } from "react-router-dom";

import { AppLayout } from "@/layouts/AppLayout";
import { CaseDetailPage } from "@/pages/case-detail/CaseDetailPage";
import { CaseListPage } from "@/pages/cases/CaseListPage";
import { ManualReviewQueuePage } from "@/pages/cases/ManualReviewQueuePage";
import { StateBlock } from "@/components/ui/StateBlock";

export const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to="/cases" replace /> },
      { path: "cases", element: <CaseListPage /> },
      { path: "cases/:caseId", element: <CaseDetailPage /> },
      { path: "manual-review", element: <ManualReviewQueuePage /> },
      {
        path: "*",
        element: (
          <StateBlock
            state="empty"
            title="Page not found"
            message="The requested operations view is not registered in the frontend router."
          />
        ),
      },
    ],
  },
]);
