import { Warning } from "@phosphor-icons/react";
import { Button, Card, DataTable, EmptyState, StatusBadge } from "../components/ui";

export const chartColors = {
  primary: "var(--color-primary-700)",
  secondary: "var(--color-secondary)",
  muted: "var(--color-text-subtle)",
  grid: "var(--color-border)",
};

export const platformOptions = ["inDrive", "Foodpanda", "Bykea", "Upwork"];
export const grievanceCategories = [
  ["commission_change", "Commission change"],
  ["account_deactivation", "Account deactivation"],
  ["payment_delay", "Payment delay"],
  ["safety", "Safety"],
  ["other", "Other"],
];

export function formatPKR(value) {
  if (value == null || Number.isNaN(Number(value))) return "Unavailable";
  return `PKR ${Math.round(Number(value)).toLocaleString("en-PK")}`;
}

export function formatDate(value) {
  if (!value) return "Date unavailable";
  return new Intl.DateTimeFormat("en-PK", { day: "numeric", month: "short", year: "numeric" }).format(new Date(value));
}

export function titleCase(value = "") {
  return value.replaceAll("_", " ").replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export function Page({ eyebrow, title, description, action, children }) {
  return (
    <div className="page">
      <header className="page-header">
        <div className="page-header__copy">
          {eyebrow && <p className="eyebrow">{eyebrow}</p>}
          <h1>{title}</h1>
          <p>{description}</p>
        </div>
        {action}
      </header>
      {children}
    </div>
  );
}

export function DemoNotice() {
  return (
    <div className="data-note data-note--warning" role="note">
      <Warning size={19} weight="fill" aria-hidden="true" />
      <span><strong>Development sample data.</strong> Nothing shown in this view is a real worker record or persisted backend result.</span>
    </div>
  );
}

export function EndpointUnavailable({ title, message, retry }) {
  return <EmptyState title={title} message={message} icon={Warning} action={retry && <Button type="button" variant="secondary" onClick={retry}>Try again</Button>} />;
}

export function ChartCard({ title, subtitle, children, className = "" }) {
  return (
    <Card className={`chart-card ${className}`}>
      <div className="chart-card__head"><h2>{title}</h2><p>{subtitle}</p></div>
      <div className="chart-card__canvas">{children}</div>
    </Card>
  );
}

export function ChartTooltip({ active, payload, label, formatter = (value) => value }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="chart-tooltip"><strong>{label}</strong>{payload.map((item) => <span key={item.dataKey} style={{ color: item.color }}>{item.name}: {formatter(item.value, item.dataKey)}</span>)}</div>
  );
}

export function ShiftTable({ shifts, onEdit, onDelete }) {
  const columns = [
    { key: "date", label: "Date", render: (row) => formatDate(row.date) },
    { key: "platform", label: "Platform" },
    { key: "hours_worked", label: "Hours" },
    { key: "gross_earned", label: "Gross", render: (row) => formatPKR(row.gross_earned) },
    { key: "deductions", label: "Deductions", render: (row) => formatPKR(row.deductions) },
    { key: "net_received", label: "Net", render: (row) => <strong>{formatPKR(row.net_received)}</strong> },
    { key: "verification_status", label: "Status", render: (row) => <StatusBadge status={row.verification_status} /> },
  ];
  if (onEdit || onDelete) columns.push({
    key: "actions",
    label: "Actions",
    render: (row) => <div className="table-actions"><button type="button" onClick={() => onEdit?.(row)}>Edit</button><button type="button" onClick={() => onDelete?.(row.id)}>Delete</button></div>,
  });
  return <DataTable columns={columns} rows={shifts} emptyTitle="No shifts yet" />;
}
