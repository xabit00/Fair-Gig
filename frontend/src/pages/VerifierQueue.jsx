import { useEffect, useState } from "react";
import { CheckCircle, FileText, Flag, XCircle } from "@phosphor-icons/react";
import { useAuth } from "../auth/AuthContext";
import { Button, Card, EmptyState, Skeleton, StatusBadge, useToast } from "../components/ui";
import { isDemoMode, verificationQueue } from "../mocks/data";
import { DemoNotice, EndpointUnavailable, Page, formatDate, formatPKR, titleCase } from "./shared";

export default function VerifierQueue({ view = "all" }) {
  const { api } = useAuth();
  const { notify } = useToast();
  const demo = isDemoMode();
  const [records, setRecords] = useState(demo ? verificationQueue : []);
  const [selectedId, setSelectedId] = useState(demo ? verificationQueue[0].id : null);
  const [note, setNote] = useState("");
  const [loading, setLoading] = useState(!demo);
  const [error, setError] = useState("");
  const filtered = records.filter((item) => view === "pending" ? item.verification_status === "pending" : view === "history" ? item.verification_status !== "pending" : true);
  const selected = records.find((item) => item.id === selectedId) || filtered[0];

  async function load() {
    if (demo) return;
    setLoading(true);
    setError("");
    try {
      const query = view === "pending" ? "?verification_status=pending" : "";
      const response = await api.get("earnings", `/shifts/verification-queue${query}`);
      const nextRecords = response.shifts || [];
      setRecords(nextRecords);
      setSelectedId((current) => current && nextRecords.some((item) => item.id === current) ? current : nextRecords[0]?.id || null);
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, [demo, view]);

  async function decide(status) {
    if (!selected) return;
    if (demo) {
      setRecords((items) => items.map((item) => item.id === selected.id ? { ...item, verification_status: status, verifier_note: note } : item));
      notify(`Sample record marked ${titleCase(status).toLowerCase()} locally.`, "success");
      setNote("");
      return;
    }
    try {
      const updated = await api.patch("earnings", `/shifts/${selected.id}/verification`, { verification_status: status, note: note || null });
      setRecords((items) => items.map((item) => item.id === selected.id ? { ...item, ...updated } : item));
      notify(updated.note_persisted === false && note ? "Decision saved. Notes are not persisted by the current database schema." : "Verification decision saved.", updated.note_persisted === false && note ? "info" : "success");
      setNote("");
    } catch (decisionError) {
      notify(decisionError.message, "error");
    }
  }

  const titles = { all: "Verification queue", pending: "Pending reviews", history: "Review history" };
  return (
    <Page eyebrow="Evidence review" title={titles[view]} description="Compare submitted earnings with their evidence and record a clear decision.">
      {demo && <DemoNotice />}
      {!demo && loading ? <Skeleton height="22rem" /> : !demo && error ? <EndpointUnavailable title="Could not load verification queue" message={error} retry={load} /> : (
        <div className="review-layout">
          <Card className="review-list" padded={false}>
            <div className="review-list__head"><strong>{filtered.length} records</strong><span>{titleCase(view)}</span></div>
            {filtered.length ? filtered.map((record) => (
              <button className={`review-row${selected?.id === record.id ? " review-row--active" : ""}`} type="button" key={record.id} onClick={() => setSelectedId(record.id)}>
                <span><strong>{record.worker_name}</strong><small>{record.platform} · {formatDate(record.date)}</small></span>
                <span><strong>{formatPKR(record.net_received)}</strong><StatusBadge status={record.verification_status} /></span>
              </button>
            )) : <EmptyState title="No records in this view" message="Try another verification filter." />}
          </Card>
          {selected && <Card className="review-detail">
            <div className="section-head"><div><h2>{selected.worker_name}</h2><p>Submitted {formatDate(selected.submitted_at)}</p></div><StatusBadge status={selected.verification_status} /></div>
            <div className="comparison-grid">
              <div className="evidence-panel"><FileText size={34} /><strong>Evidence preview</strong><span>{selected.screenshot_url}</span><small>The development sample does not load or represent a real worker screenshot.</small></div>
              <div className="claim-panel"><strong>Submitted claim</strong><span>Gross: {formatPKR(selected.gross_earned)}</span><span>Deductions: {formatPKR(selected.deductions)}</span><span>Net: {formatPKR(selected.net_received)}</span><small>Compare these values with the evidence before deciding.</small></div>
            </div>
            <dl className="detail-grid"><div><dt>Gross</dt><dd>{formatPKR(selected.gross_earned)}</dd></div><div><dt>Deductions</dt><dd>{formatPKR(selected.deductions)}</dd></div><div><dt>Net received</dt><dd>{formatPKR(selected.net_received)}</dd></div><div><dt>Hours</dt><dd>{selected.hours_worked}</dd></div></dl>
            <label className="ui-field"><span className="ui-field__label">Review note</span><textarea value={note} onChange={(event) => setNote(event.target.value)} placeholder="Add a concise reason for the decision." /></label>
            <div className="decision-grid"><Button type="button" onClick={() => decide("confirmed")}><CheckCircle size={18} />Confirm</Button><Button type="button" variant="secondary" onClick={() => decide("discrepancy_flagged")}><Flag size={18} />Flag discrepancy</Button><Button type="button" variant="ghost" onClick={() => decide("unverifiable")}><XCircle size={18} />Unverifiable</Button></div>
          </Card>}
        </div>
      )}
    </Page>
  );
}
