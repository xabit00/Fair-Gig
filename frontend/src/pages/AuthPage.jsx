import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import {
  CheckCircle,
  FileText,
  LockKey,
  ShieldCheck,
  UsersThree,
} from "@phosphor-icons/react";
import { useAuth } from "../auth/AuthContext";
import { Button, Input, StatusBadge } from "../components/ui";
import LanguageToggle from "../components/LanguageToggle";
import { useLanguage } from "../i18n/LanguageContext";

const demoAccounts = [
  { role: "Worker", email: "ahsan.raza@example.com" },
  { role: "Verifier", email: "verifier@fairgig.test" },
  { role: "Advocate", email: "advocate@fairgig.test" },
];

export function destinationFor(role) {
  if (role === "verifier") return "/verifier";
  if (role === "advocate") return "/analytics";
  return "/worker";
}

export function LoginPage() {
  const { user, login } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to={destinationFor(user.role)} replace />;

  function update(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: "" }));
  }

  async function submit(event) {
    event.preventDefault();
    const nextErrors = {
      email: form.email ? "" : "Enter your email address.",
      password: form.password ? "" : "Enter your password.",
    };
    setErrors(nextErrors);
    if (nextErrors.email || nextErrors.password) return;
    setFormError("");
    setSubmitting(true);
    try {
      const signedInUser = await login(form.email, form.password);
      navigate(destinationFor(signedInUser.role), { replace: true });
    } catch (error) {
      setFormError(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  function chooseDemo(account) {
    setForm({ email: account.email, password: "FairGig123!" });
    setErrors({});
    setFormError("");
  }

  return (
    <AuthFrame title={t("welcomeBack")} subtitle={t("signInDescription")}>
      <form onSubmit={submit} className="auth-form" noValidate>
        <Input label={t("email")} name="email" type="email" value={form.email} error={errors.email} onChange={(event) => update("email", event.target.value)} autoComplete="email" required />
        <Input label={t("password")} name="password" type="password" value={form.password} error={errors.password} onChange={(event) => update("password", event.target.value)} autoComplete="current-password" required />
        {formError && <p className="form-error" role="alert">{formError}</p>}
        <Button type="submit" block loading={submitting}>{submitting ? t("signingIn") : t("signIn")}</Button>
      </form>
      <p className="auth-switch">New to FairGig? <Link to="/register">Create a worker account</Link></p>
      {import.meta.env.DEV && (
        <div className="demo-logins">
          <div><strong>Local demo accounts</strong><span>Choose a role to fill the seeded credentials.</span></div>
          <div className="demo-logins__buttons">
            {demoAccounts.map((account) => (
              <Button key={account.role} type="button" variant="secondary" size="small" onClick={() => chooseDemo(account)} aria-pressed={form.email === account.email}>{account.role}</Button>
            ))}
          </div>
        </div>
      )}
    </AuthFrame>
  );
}

export function RegisterPage() {
  const { user, register } = useAuth();
  const { t } = useLanguage();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    city_zone: "Karachi Central",
    category: "ride_hailing",
  });
  const [errors, setErrors] = useState({});
  const [formError, setFormError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to={destinationFor(user.role)} replace />;

  function update(name, value) {
    setForm((current) => ({ ...current, [name]: value }));
    setErrors((current) => ({ ...current, [name]: "" }));
  }

  async function submit(event) {
    event.preventDefault();
    const nextErrors = {
      name: form.name.trim().length >= 2 ? "" : "Enter your full name.",
      email: form.email ? "" : "Enter your email address.",
      password: form.password.length >= 8 ? "" : "Use at least 8 characters.",
    };
    setErrors(nextErrors);
    if (Object.values(nextErrors).some(Boolean)) return;
    setFormError("");
    setSubmitting(true);
    try {
      const newUser = await register(form);
      navigate(destinationFor(newUser.role), { replace: true });
    } catch (error) {
      setFormError(error.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthFrame title={t("createRecord")} subtitle={t("createDescription")}>
      <form onSubmit={submit} className="auth-form" noValidate>
        <Input label={t("fullName")} name="name" value={form.name} error={errors.name} onChange={(event) => update("name", event.target.value)} autoComplete="name" required />
        <Input label={t("email")} name="email" type="email" value={form.email} error={errors.email} onChange={(event) => update("email", event.target.value)} autoComplete="email" required />
        <Input label={t("password")} name="password" type="password" value={form.password} error={errors.password} hint="Use at least 8 characters." onChange={(event) => update("password", event.target.value)} autoComplete="new-password" required />
        <label className="ui-field">
          <span className="ui-field__label">City zone</span>
          <select value={form.city_zone} onChange={(event) => update("city_zone", event.target.value)}>
            <option>Karachi Central</option>
            <option>Lahore North</option>
            <option>Islamabad-Rawalpindi</option>
            <option>Faisalabad Urban</option>
          </select>
        </label>
        <label className="ui-field">
          <span className="ui-field__label">Work category</span>
          <select value={form.category} onChange={(event) => update("category", event.target.value)}>
            <option value="ride_hailing">Ride hailing</option>
            <option value="delivery">Delivery</option>
            <option value="freelancing">Freelancing</option>
          </select>
        </label>
        {formError && <p className="form-error" role="alert">{formError}</p>}
        <Button type="submit" block loading={submitting}>{submitting ? t("creatingAccount") : t("createAccount")}</Button>
      </form>
      <p className="auth-switch">Already registered? <Link to="/login">Sign in</Link></p>
    </AuthFrame>
  );
}

function AuthFrame({ title, subtitle, children }) {
  return (
    <main className="auth-shell">
      <section className="auth-intro">
        <Brand />
        <div className="auth-intro__copy">
          <p className="section-label">Income evidence for independent work</p>
          <h1>Keep the record. Know your rights.</h1>
          <p>Track earnings, document deductions, and carry proof of your work between platforms.</p>
        </div>
        <div className="auth-preview" aria-label="Sample income preview">
          <div className="auth-preview__header"><div><span>Sample preview</span><strong>Verified income summary</strong></div><StatusBadge status="verified"><CheckCircle size={14} weight="fill" /> Verified</StatusBadge></div>
          <strong className="auth-preview__amount">PKR 68,450</strong>
          <p>Example monthly income from reviewed shift records. This is sample data, not a worker record.</p>
        </div>
        <div className="trust-list" aria-label="FairGig product principles">
          <span><LockKey size={18} />Private by role</span>
          <span><ShieldCheck size={18} />Evidence attached</span>
          <span><FileText size={18} />Printable record</span>
        </div>
      </section>
      <section className="auth-panel">
        <div className="auth-mobile-brand"><Brand compact /></div>
        <div className="auth-card">
          <LanguageToggle className="auth-language" />
          <div className="auth-card__icon"><UsersThree size={24} /></div>
          <h2>{title}</h2>
          <p>{subtitle}</p>
          {children}
        </div>
      </section>
    </main>
  );
}

function Brand({ compact = false }) {
  return <Link className={`brand ${compact ? "brand--compact" : ""}`} to="/" aria-label="FairGig home"><span className="brand-mark" aria-hidden="true">FG</span><span>FairGig</span></Link>;
}
