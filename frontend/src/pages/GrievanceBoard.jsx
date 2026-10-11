import { useEffect, useMemo, useState } from "react";
import { MagnifyingGlass, Warning } from "@phosphor-icons/react";
import { useAuth } from "../auth/AuthContext";
import { Button, Card, EmptyState, Skeleton, StatusBadge, useToast } from "../components/ui";
import { isDemoMode, sampleGrievances } from "../mocks/data";
import { DemoNotice, EndpointUnavailable, Page, formatDate, grievanceCategories, platformOptions, titleCase } from "./shared";

export default function GrievanceBoard({ workerView = false }) {
  const { api } = useAuth();
  const { notify } = useToast();
  const demo = isDemoMode();
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [contractSample, setContractSample] = useState(false);
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [form, setForm] = useState({ platform: "Foodpanda", category: "commission_change", description: "" });
  const [submitting, setSubmitting] = useState(false);

  async function load() {
    setLoading(true);
    setError("");
    if (demo) { setItems(sampleGrievances); setLoading(false); return; }
    try {
      const response = await api.get("grievance", "/grievances");
      setItems(response.grievances || []);
      setContractSample(Boolean(response.stub));
    } catch (loadError) {
      setError(loadError.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => { load(); }, []);

  const filtered = useMemo(() => items.filter((item) => {
    const text = `${item.platform} ${item.category} ${item.description}`.toLowerCase();
    return text.includes(query.toLowerCase()) && (status === "all" || item.status === status);
  }), [items, query, status]);

  async function submit(event) {
    event.preventDefault();
    if (form.description.trim().length < 20) return notify("Please describe the concern in at least 20 characters.", "error");
    setSubmitting(true);
    try {
      if (demo) {
        setItems((current) => [{ id: crypto.randomUUID(), ...form, status: "submitted", cluster_id: null, tags: [], created_at: new Date().toISOString() }, ...current]);
        notify("Sample grievance added locally.", "success");
        setForm((current) => ({ ...current, description: "" }));
      } else {
        const response = await api.post("grievance", "/grievances", form);
        if (response?.stub) notify("The backend validated this grievance but did not persist it because the endpoint is still a Level 1 stub.", "info");
        else { notify("Grievance submitted.", "success"); await load(); }
      }
    } catch (submitError) {
      notify(submitError.message, "error");
    } finally {
      setSubmitting(false);
    }
  }

  async function updateWorkflow(item, changes, message) {
    const updated = {
      ...item,
      status: changes.status || item.status,
      cluster_id: changes.cluster_id === undefined ? item.cluster_id : changes.cluster_id,
      tags: changes.tags || item.tags || [],
    };
    try {
      if (demo) {
        setItems((current) => current.map((record) => record.id === item.id ? updated : record));
        notify(`${message} This sample change is local only.`, "success");
        return;
      }
      const response = await api.patch("grievance", `/grievances/${item.id}/workflow`, { status: updated.status, cluster_id: updated.cluster_id, tags: updated.tags });
      notify(response?.stub ? "The workflow endpoint is a Level 1 stub, so this change was not persisted." : "Workflow updated.", response?.stub ? "info" : "success");
      if (!response?.stub) await load();
    } catch (workflowError) {
      notify(workflowError.message, "error");
    }
  }

  return (
    <Page eyebrow={workerView ? "Worker support" : "Advocacy workflow"} title={workerView ? "My grievances" : "Grievance board"} description={workerView ? "Document a workplace concern and follow its status." : "Find recurring concerns, review clusters, and move cases through escalation."}>
      {demo && <DemoNotice />}
      {contractSample && <div className="data-note data-note--warning"><Warning size={18} /><span>The grievance service returned a Level 1 contract sample. It is not a persisted worker record.</span></div>}

      {workerView && <Card className="grievance-form-card">
        <div className="section-head"><div><h2>Submit a concern</h2><p>Use factual details. Your identity remains protected by role access.</p></div></div>
        <form className="form-grid" onSubmit={submit}>
          <label className="ui-field"><span className="ui-field__label">Platform</span><select value={form.platform} onChange={(event) => setForm({ ...form, platform: event.target.value })}>{platformOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
          <label className="ui-field"><span className="ui-field__label">Category</span><select value={form.category} onChange={(event) => setForm({ ...form, category: event.target.value })}>{grievanceCategories.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label className="ui-field form-grid__wide"><span className="ui-field__label">What happened?</span><textarea value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} placeholder="Describe the change, date, and effect on your work or income." minLength={20} required /></label>
          <div className="form-grid__wide"><Button type="submit" loading={submitting}>Submit grievance</Button></div>
        </form>
      </Card>}

      <section className="page-section">
        <div className="board-controls">
          <label className="search-field"><MagnifyingGlass size={19} /><span className="sr-only">Search grievances</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search platform, category, or text" /></label>
          <label className="filter-field"><span>Status</span><select value={status} onChange={(event) => setStatus(event.target.value)}><option value="all">All statuses</option><option value="submitted">Submitted</option><option value="reviewing">Reviewing</option><option value="escalated">Escalated</option><option value="resolved">Resolved</option><option value="closed">Closed</option></select></label>
        </div>
        {loading && <div className="grievance-grid"><Skeleton height="15rem" /><Skeleton height="15rem" /><Skeleton height="15rem" /></div>}
        {!loading && error && <EndpointUnavailable title="Could not load grievances" message={error} retry={load} />}
        {!loading && !error && !filtered.length && <EmptyState title="No grievances found" message="Adjust the search or status filter." />}
        {!loading && !error && filtered.length > 0 && <div className="grievance-grid">{filtered.map((item) => (
          <Card as="article" className="grievance-card" key={item.id}>
            <div className="grievance-card__top"><span>{item.platform}</span><StatusBadge status={item.status} /></div>
            <h2>{titleCase(item.category)}</h2>
            <p>{item.description}</p>
            <div className="tag-list">{(item.tags || []).map((tag) => <span key={tag}>{tag}</span>)}{item.cluster_id && <span>Cluster: {item.cluster_id}</span>}</div>
            <footer><span>{formatDate(item.created_at)}</span>{!workerView && <div className="workflow-actions"><Button size="small" variant="ghost" type="button" onClick={() => updateWorkflow(item, { tags: [...new Set([...(item.tags || []), "priority-review"])] }, "Priority tag added.")}>Tag</Button><Button size="small" variant="ghost" type="button" onClick={() => updateWorkflow(item, { cluster_id: item.cluster_id || `${item.category}-cluster` }, "Grievance clustered.")}>Cluster</Button><Button size="small" variant="secondary" type="button" disabled={["escalated", "resolved"].includes(item.status)} onClick={() => updateWorkflow(item, { status: "escalated" }, "Grievance escalated.")}>Escalate</Button><Button size="small" type="button" disabled={item.status === "resolved"} onClick={() => updateWorkflow(item, { status: "resolved" }, "Grievance resolved.")}>Resolve</Button></div>}</footer>
          </Card>
        ))}</div>}
      </section>
    </Page>
  );
}
