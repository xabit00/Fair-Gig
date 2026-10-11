import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from "react";
import {
  CheckCircle,
  Eye,
  EyeSlash,
  Tray,
  Info,
  SpinnerGap,
  WarningCircle,
  X,
} from "@phosphor-icons/react";

export function Button({ children, variant = "primary", size, block = false, loading = false, className = "", ...props }) {
  const classes = ["ui-button", `ui-button--${variant}`, size && `ui-button--${size}`, block && "ui-button--block", className].filter(Boolean).join(" ");
  return (
    <button {...props} className={classes} disabled={loading || props.disabled} aria-busy={loading || undefined}>
      {loading && <SpinnerGap className="ui-spinner" size={18} aria-hidden="true" />}
      {children}
    </button>
  );
}

export function Input({ label, error, hint, type = "text", id, className = "", ...props }) {
  const [visible, setVisible] = useState(false);
  const inputId = id || props.name;
  const password = type === "password";
  return (
    <label className={`ui-field ${className}`} htmlFor={inputId}>
      <span className="ui-field__label">{label}</span>
      <span className="ui-field__control">
        <input id={inputId} type={password && visible ? "text" : type} data-password={password || undefined} aria-invalid={Boolean(error)} aria-describedby={error ? `${inputId}-error` : hint ? `${inputId}-hint` : undefined} {...props} />
        {password && (
          <button className="ui-field__toggle" type="button" onClick={() => setVisible((value) => !value)} aria-label={visible ? "Hide password" : "Show password"}>
            {visible ? <EyeSlash size={19} /> : <Eye size={19} />}
          </button>
        )}
      </span>
      {hint && !error && <span className="ui-field__hint" id={`${inputId}-hint`}>{hint}</span>}
      {error && <span className="ui-field__error" id={`${inputId}-error`}>{error}</span>}
    </label>
  );
}

export function Card({ children, padded = true, className = "", as: Component = "section", ...props }) {
  return <Component className={`ui-card ${padded ? "ui-card--padded" : ""} ${className}`.trim()} {...props}>{children}</Component>;
}

export function KpiCard({ label, value, trend, trendTone = "neutral", icon: Icon }) {
  return (
    <Card className="ui-kpi">
      <div className="ui-kpi__head"><span>{label}</span>{Icon && <span className="ui-kpi__icon"><Icon size={20} /></span>}</div>
      <div><strong className="ui-kpi__value">{value}</strong>{trend && <p className={`ui-kpi__trend ui-kpi__trend--${trendTone}`}>{trend}</p>}</div>
    </Card>
  );
}

const statusMap = {
  confirmed: "verified",
  verified: "verified",
  pending: "pending",
  discrepancy_flagged: "flagged",
  flagged: "flagged",
  escalated: "flagged",
  unverifiable: "unverifiable",
  resolved: "verified",
  reviewing: "pending",
  submitted: "pending",
  closed: "neutral",
};

export function StatusBadge({ status, children }) {
  const tone = statusMap[status] || "neutral";
  const label = children || String(status || "unknown").replaceAll("_", " ");
  return <span className={`ui-status ui-status--${tone}`}>{label}</span>;
}

export function Skeleton({ width = "100%", height = "1rem", className = "" }) {
  return <div className={`ui-skeleton ${className}`} style={{ width, height }} aria-hidden="true" />;
}

export function EmptyState({ title, message, action, icon: Icon = Tray }) {
  return (
    <Card className="ui-empty">
      <span className="ui-empty__icon"><Icon size={24} /></span>
      <h2>{title}</h2>
      <p>{message}</p>
      {action}
    </Card>
  );
}

const ToastContext = createContext(null);

export function ToastProvider({ children }) {
  const [toasts, setToasts] = useState([]);
  const dismiss = useCallback((id) => setToasts((items) => items.filter((item) => item.id !== id)), []);
  const notify = useCallback((message, tone = "info") => {
    const id = `${Date.now()}-${Math.random()}`;
    setToasts((items) => [...items, { id, message, tone }]);
    window.setTimeout(() => dismiss(id), 4500);
  }, [dismiss]);
  const value = useMemo(() => ({ notify }), [notify]);
  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="ui-toast-stack" aria-live="polite" aria-atomic="true">
        {toasts.map((toast) => {
          const Icon = toast.tone === "success" ? CheckCircle : toast.tone === "error" ? WarningCircle : Info;
          return (
            <div className={`ui-toast ui-toast--${toast.tone}`} key={toast.id} role="status">
              <Icon size={21} weight="fill" />
              <p>{toast.message}</p>
              <button type="button" onClick={() => dismiss(toast.id)} aria-label="Dismiss notification"><X size={17} /></button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) throw new Error("useToast must be used inside ToastProvider");
  return context;
}

export function Modal({ open, title, onClose, children }) {
  const dialogRef = useRef(null);
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) dialog.showModal();
    if (!open && dialog.open) dialog.close();
  }, [open]);
  return (
    <dialog className="ui-modal" ref={dialogRef} onCancel={(event) => { event.preventDefault(); onClose(); }}>
      <header className="ui-modal__header"><h2>{title}</h2><button className="ui-modal__close" type="button" onClick={onClose} aria-label="Close dialog"><X size={20} /></button></header>
      <div className="ui-modal__body">{children}</div>
    </dialog>
  );
}

export function DataTable({ columns, rows, rowKey = "id", emptyTitle = "No records available" }) {
  if (!rows.length) return <EmptyState title={emptyTitle} message="Records will appear here when they are available." />;
  return (
    <div className="ui-table-wrap">
      <table className="ui-table">
        <thead><tr>{columns.map((column) => <th key={column.key} scope="col">{column.label}</th>)}</tr></thead>
        <tbody>
          {rows.map((row, index) => (
            <tr key={typeof rowKey === "function" ? rowKey(row, index) : row[rowKey] || index}>
              {columns.map((column) => <td key={column.key} data-label={column.label}>{column.render ? column.render(row) : row[column.key]}</td>)}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
