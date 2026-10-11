import { useState } from "react";
import { FileCsv, UploadSimple, Warning } from "@phosphor-icons/react";
import { useAuth } from "../auth/AuthContext";
import { Button, Card, Input, useToast } from "../components/ui";
import { isDemoMode, sampleShifts } from "../mocks/data";
import { DemoNotice, EndpointUnavailable, Page, ShiftTable, formatPKR, platformOptions } from "./shared";

const emptyShift = {
  platform: "inDrive",
  date: new Date().toISOString().slice(0, 10),
  hours_worked: "",
  gross_earned: "",
  deductions: "",
  screenshot_url: "",
};

export default function EarningsLogger() {
  const { api } = useAuth();
  const { notify } = useToast();
  const demo = isDemoMode();
  const [form, setForm] = useState(emptyShift);
  const [errors, setErrors] = useState({});
  const [shifts, setShifts] = useState(demo ? sampleShifts : []);
  const [editingId, setEditingId] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [csvRows, setCsvRows] = useState([]);
  const [csvText, setCsvText] = useState("");
  const [csvError, setCsvError] = useState("");
  const net = Math.max(0, Number(form.gross_earned || 0) - Number(form.deductions || 0));

  function update(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: "" }));
  }

  async function submit(event) {
    event.preventDefault();
    const nextErrors = {
      hours_worked: Number(form.hours_worked) > 0 ? "" : "Enter hours greater than zero.",
      gross_earned: Number(form.gross_earned) > 0 ? "" : "Enter gross earnings.",
      deductions: Number(form.deductions) >= 0 ? "" : "Deductions cannot be negative.",
    };
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) return;
    const payload = { ...form, hours_worked: Number(form.hours_worked), gross_earned: Number(form.gross_earned), deductions: Number(form.deductions), net_received: net, screenshot_url: form.screenshot_url || null };
    setSubmitting(true);
    try {
      if (demo) {
        if (editingId) setShifts((items) => items.map((item) => item.id === editingId ? { ...item, ...payload } : item));
        else setShifts((items) => [{ id: crypto.randomUUID(), ...payload, verification_status: "pending" }, ...items]);
        notify(editingId ? "Sample shift updated locally." : "Sample shift added locally.", "success");
        setForm(emptyShift);
        setEditingId(null);
      } else if (editingId) {
        notify("Editing is unavailable until the earnings service adds PATCH /shifts/{id}.", "info");
      } else {
        const response = await api.post("earnings", "/shifts", payload);
        if (response?.stub) notify("The backend validated this shift but did not persist it because the endpoint is still a Level 1 stub.", "info");
        else { notify("Shift saved.", "success"); setForm(emptyShift); }
      }
    } catch (error) {
      notify(error.message, "error");
    } finally {
      setSubmitting(false);
    }
  }

  function editShift(shift) {
    setEditingId(shift.id);
    setForm({ platform: shift.platform, date: shift.date, hours_worked: shift.hours_worked, gross_earned: shift.gross_earned, deductions: shift.deductions, screenshot_url: shift.screenshot_url || "" });
    document.querySelector("#shift-form")?.scrollIntoView({ behavior: "smooth" });
  }

  function deleteShift(id) {
    setShifts((items) => items.filter((item) => item.id !== id));
    notify("Sample shift removed locally.", "info");
  }

  function parseCsv(text) {
    setCsvText(text);
    setCsvError("");
    const lines = text.trim().split(/\r?\n/).filter(Boolean);
    if (lines.length < 2) { setCsvRows([]); setCsvError("The CSV needs a header and at least one data row."); return; }
    const headers = lines[0].split(",").map((value) => value.trim());
    const required = ["date", "hours_worked", "gross_earned", "deductions", "net_received"];
    const missing = required.filter((header) => !headers.includes(header));
    if (missing.length) { setCsvRows([]); setCsvError(`Missing columns: ${missing.join(", ")}.`); return; }
    const rows = lines.slice(1, 6).map((line) => Object.fromEntries(headers.map((header, column) => [header, line.split(",")[column]?.trim() || ""])));
    const invalid = rows.some((row) => !/^\d{4}-\d{2}-\d{2}$/.test(row.date) || ["hours_worked", "gross_earned", "deductions", "net_received"].some((key) => row[key] === "" || Number.isNaN(Number(row[key]))));
    if (invalid) { setCsvRows([]); setCsvError("Dates must use YYYY-MM-DD and earnings fields must contain numbers."); return; }
    setCsvRows(rows);
  }

  function readCsvFile(file) {
    if (!file) return;
    if (!file.name.toLowerCase().endsWith(".csv")) { setCsvError("Choose a .csv file."); setCsvRows([]); return; }
    file.text().then(parseCsv);
  }

  async function importCsv() {
    if (!csvRows.length) return notify("Choose a CSV file with at least one data row.", "error");
    if (demo) return notify(`${csvRows.length} sample rows previewed locally. No records were uploaded.`, "info");
    try {
      const response = await api.post("earnings", "/shifts/import-csv", { csv_text: csvText, platform: form.platform });
      notify(response?.stub ? "The CSV was validated by a Level 1 stub and was not persisted." : "CSV imported.", response?.stub ? "info" : "success");
    } catch (error) { notify(error.message, "error"); }
  }

  return (
    <Page eyebrow="Income records" title="Earnings logger" description="Record a shift, keep its evidence reference, or preview a CSV import.">
      {demo && <DemoNotice />}
      {!demo && <div className="data-note"><Warning size={18} /><span>The Level 1 earnings endpoints validate submissions but currently return <strong>stub: true</strong>. FairGig will never label a stub response as saved.</span></div>}
      <div className="two-column earnings-layout">
        <Card id="shift-form">
          <div className="section-head"><div><h2>{editingId ? "Edit sample shift" : "Log a shift"}</h2><p>Net earnings are calculated automatically.</p></div></div>
          <form className="form-grid" onSubmit={submit} noValidate>
            <label className="ui-field"><span className="ui-field__label">Platform</span><select value={form.platform} onChange={(event) => update("platform", event.target.value)}>{platformOptions.map((item) => <option key={item}>{item}</option>)}</select></label>
            <Input label="Date" name="date" type="date" value={form.date} onChange={(event) => update("date", event.target.value)} required />
            <Input label="Hours worked" name="hours_worked" type="number" min="0.1" step="0.1" value={form.hours_worked} error={errors.hours_worked} onChange={(event) => update("hours_worked", event.target.value)} />
            <Input label="Gross earnings (PKR)" name="gross_earned" type="number" min="0" step="0.01" value={form.gross_earned} error={errors.gross_earned} onChange={(event) => update("gross_earned", event.target.value)} />
            <Input label="Deductions (PKR)" name="deductions" type="number" min="0" step="0.01" value={form.deductions} error={errors.deductions} onChange={(event) => update("deductions", event.target.value)} />
            <Input label="Net received (PKR)" name="net_received" type="number" value={net} readOnly hint="Gross earnings minus deductions." />
            <Input className="form-grid__wide" label="Screenshot URL" name="screenshot_url" type="url" value={form.screenshot_url} onChange={(event) => update("screenshot_url", event.target.value)} placeholder="https://..." hint="The current API stores a reference URL, not a binary upload." />
            <div className="button-row form-grid__wide"><Button type="submit" loading={submitting}>{editingId ? "Update sample" : "Submit shift"}</Button>{editingId && <Button type="button" variant="ghost" onClick={() => { setEditingId(null); setForm(emptyShift); }}>Cancel</Button>}</div>
          </form>
        </Card>

        <Card>
          <div className="section-head"><div><h2>CSV import</h2><p>Preview the first five rows before submission.</p></div><FileCsv size={28} /></div>
          <label className="drop-zone" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); readCsvFile(event.dataTransfer.files?.[0]); }}>
            <UploadSimple size={30} />
            <strong>Choose a CSV file</strong>
            <span>Required columns: date, hours_worked, gross_earned, deductions, net_received</span>
            <input type="file" accept=".csv,text/csv" onChange={(event) => readCsvFile(event.target.files?.[0])} />
          </label>
          {csvError && <p className="ui-field__error" role="alert">{csvError}</p>}
          {csvRows.length > 0 && <div className="csv-preview"><strong>{csvRows.length} preview rows</strong>{csvRows.map((row, index) => <span key={`${row.date}-${index}`}>{row.date || "No date"} · {formatPKR(row.net_received)}</span>)}</div>}
          <Button type="button" variant="secondary" block disabled={!csvRows.length} onClick={importCsv}>Submit CSV preview</Button>
        </Card>
      </div>

      <section className="page-section">
        <div className="section-head"><div><h2>Shift history</h2><p>{demo ? "Development sample records stored only in this page session." : "A history endpoint is not available yet."}</p></div></div>
        {demo ? <Card padded={false}><ShiftTable shifts={shifts} onEdit={editShift} onDelete={deleteShift} /></Card> : <EndpointUnavailable title="Shift history is unavailable" message="Ask the Backend Services teammate to add GET /shifts, PATCH /shifts/{id}, and DELETE /shifts/{id}. The submission form remains connected to the documented POST endpoint." />}
      </section>
    </Page>
  );
}
