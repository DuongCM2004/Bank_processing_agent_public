import { Link } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { EmptyState } from "@/components/ui/EmptyState";

export function NotFoundPage() {
  return (
    <div className="space-y-4">
      <EmptyState
        title="Page not found"
        message="The requested route is not part of the current operations dashboard scaffold."
      />
      <Link to="/">
        <Button type="button">Return to dashboard</Button>
      </Link>
    </div>
  );
}
