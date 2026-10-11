import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";

function destinationFor(role) {
  if (role === "verifier") return "/verifier";
  if (role === "advocate") return "/analytics";
  return "/worker";
}

export function LoginPage() {
  const { user, login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to={destinationFor(user.role)} replace />;

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const signedInUser = await login(form.email, form.password);
      navigate(destinationFor(signedInUser.role), { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthFrame title="Welcome back" subtitle="Sign in to manage verified income and workplace concerns.">
      <form onSubmit={submit} className="auth-form">
        <Field label="Email address" name="email" type="email" value={form.email} onChange={setForm} autoComplete="email" />
        <Field label="Password" name="password" type="password" value={form.password} onChange={setForm} autoComplete="current-password" />
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="primary-button" disabled={submitting} type="submit">
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
      <p className="auth-switch">New to FairGig? <Link to="/register">Create a worker account</Link></p>
      <div className="demo-note">
        <strong>Seeded staff accounts</strong>
        <span>verifier@fairgig.test or advocate@fairgig.test</span>
        <span>Password: FairGig123!</span>
      </div>
    </AuthFrame>
  );
}

export function RegisterPage() {
  const { user, register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    city_zone: "Karachi Central",
    category: "ride_hailing",
  });
  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  if (user) return <Navigate to={destinationFor(user.role)} replace />;

  async function submit(event) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      const newUser = await register(form);
      navigate(destinationFor(newUser.role), { replace: true });
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <AuthFrame title="Create your record" subtitle="Start a private, portable history of your gig income.">
      <form onSubmit={submit} className="auth-form">
        <Field label="Full name" name="name" value={form.name} onChange={setForm} autoComplete="name" />
        <Field label="Email address" name="email" type="email" value={form.email} onChange={setForm} autoComplete="email" />
        <Field label="Password" name="password" type="password" value={form.password} onChange={setForm} autoComplete="new-password" minLength="8" />
        <label className="field">
          <span>City zone</span>
          <select name="city_zone" value={form.city_zone} onChange={(event) => setForm((current) => ({ ...current, city_zone: event.target.value }))}>
            <option>Karachi Central</option>
            <option>Lahore North</option>
            <option>Islamabad-Rawalpindi</option>
            <option>Faisalabad Urban</option>
          </select>
        </label>
        <label className="field">
          <span>Work category</span>
          <select name="category" value={form.category} onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))}>
            <option value="ride_hailing">Ride hailing</option>
            <option value="delivery">Delivery</option>
            <option value="freelancing">Freelancing</option>
          </select>
        </label>
        {error && <p className="form-error" role="alert">{error}</p>}
        <button className="primary-button" disabled={submitting} type="submit">
          {submitting ? "Creating account..." : "Create account"}
        </button>
      </form>
      <p className="auth-switch">Already registered? <Link to="/login">Sign in</Link></p>
    </AuthFrame>
  );
}

function Field({ label, name, onChange, ...inputProps }) {
  return (
    <label className="field">
      <span>{label}</span>
      <input
        name={name}
        required
        onChange={(event) => onChange((current) => ({ ...current, [name]: event.target.value }))}
        {...inputProps}
      />
    </label>
  );
}

function AuthFrame({ title, subtitle, children }) {
  return (
    <main className="auth-shell">
      <section className="auth-intro">
        <Link className="brand" to="/">
          <span className="brand-mark" aria-hidden="true">FG</span>
          <span>FairGig</span>
        </Link>
        <div>
          <p className="section-label">Income evidence for independent work</p>
          <h1>Keep the record.<br />Know your rights.</h1>
          <p>One dependable place for earnings, verification, certificates, and collective concerns.</p>
        </div>
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <h2>{title}</h2>
          <p>{subtitle}</p>
          {children}
        </div>
      </section>
    </main>
  );
}

