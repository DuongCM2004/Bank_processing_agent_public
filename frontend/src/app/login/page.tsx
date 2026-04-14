import Link from "next/link";

export default function LoginPage() {
  return (
    <main className="shell">
      <section className="panel hero-panel narrow-panel">
        <p className="eyebrow">Access Control</p>
        <h1>Login / Access Entry</h1>
        <p className="muted">
          Production implementation should hand off to OIDC. This scaffold keeps the route and layout explicit for security integration.
        </p>
        <div className="correction-list">
          <label className="form-field">
            <span className="muted">Employee ID</span>
            <input placeholder="employee_001" />
          </label>
          <label className="form-field">
            <span className="muted">Password</span>
            <input type="password" placeholder="********" />
          </label>
        </div>
        <div className="cta-row">
          <Link href="/review-queue" className="action-link primary">
            Continue
          </Link>
        </div>
      </section>
    </main>
  );
}
