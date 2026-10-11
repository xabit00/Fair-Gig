import { Link } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

export function WorkerDashboard() {
  const { user } = useAuth();
  return (
    <Page title={`Good to see you, ${user.name.split(" ")[0]}`} description="Your income record will take shape here as verified shifts are added.">
      <div className="metric-grid">
        <Metric label="Net income this month" value="PKR 0" note="Connect earnings in Level 2" />
        <Metric label="Verification status" value="No records" note="Screenshots have not been reviewed" />
      </div>
      <section className="action-strip">
        <div><h2>Start with a shift</h2><p>Record gross pay, deductions, hours, and a screenshot reference.</p></div>
        <Link className="primary-button compact" to="/earnings">Log earnings</Link>
      </section>
    </Page>
  );
}

export function EarningsLogger() {
  return <Placeholder title="Earnings logger" description="Shift entry, screenshot references, and CSV import will connect to the earnings service in Level 2." action="Add a shift" />;
}

export function VerifierQueue() {
  return <Placeholder title="Verification queue" description="Submitted proof will appear here for confirmation, discrepancy flags, or an unverifiable decision." action="Refresh queue" />;
}

export function GrievanceBoard({ workerView = false }) {
  return <Placeholder title={workerView ? "My grievances" : "Grievance board"} description={workerView ? "Submit a workplace concern and follow its status without exposing your identity publicly." : "Tag, cluster, escalate, and resolve recurring worker concerns from one queue."} action={workerView ? "Post grievance" : "Review clusters"} />;
}

export function AdvocateAnalytics() {
  return <Placeholder title="Advocate analytics" description="K-anonymous city and platform comparisons will appear here. Groups below five workers stay hidden." action="Load aggregates" />;
}

export function IncomeCertificate() {
  return <Placeholder title="Income certificate" description="Generate a print-ready summary from verified records for banks, landlords, or personal documentation." action="Preview certificate" />;
}

function Page({ title, description, children }) {
  return (
    <div className="page">
      <header className="page-header"><h1>{title}</h1><p>{description}</p></header>
      {children}
    </div>
  );
}

function Placeholder({ title, description, action }) {
  return (
    <Page title={title} description={description}>
      <section className="empty-state">
        <div className="empty-mark" aria-hidden="true">FG</div>
        <h2>Ready for Level 2</h2>
        <p>The route, access control, and service contract are in place.</p>
        <button className="secondary-button" type="button" disabled>{action}</button>
      </section>
    </Page>
  );
}

function Metric({ label, value, note }) {
  return <section className="metric"><span>{label}</span><strong>{value}</strong><p>{note}</p></section>;
}

