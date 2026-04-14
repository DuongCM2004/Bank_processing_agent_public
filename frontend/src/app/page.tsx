import { AccessEntryPanel } from "@/components/access-entry-panel";
import { demoUser } from "@/lib/mock-data";

export default function HomePage() {
  return <main className="shell"><AccessEntryPanel user={demoUser} /></main>;
}
