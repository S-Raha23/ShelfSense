import { useState } from "react";
import { Link, Navigate, useLocation, useNavigate } from "react-router-dom";

import { errorMessage } from "../api/client";
import { useAuth } from "../auth/AuthContext";

export default function LoginPage() {
  const { login, status } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [form, setForm] = useState({ username: "", password: "" });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated") return <Navigate to="/dashboard" replace />;

  const submit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(form.username, form.password);
      navigate(location.state?.from?.pathname ?? "/dashboard", { replace: true });
    } catch (err) {
      setError(err.response?.status === 401 ? "Incorrect username or password." : errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  const fillDemo = () => setForm({ username: "demo", password: "shelfsense-demo" });

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to see what to do next for your Amazon business.">
      <form onSubmit={submit} className="form">
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Username
          <input
            autoFocus
            autoComplete="username"
            value={form.username}
            onChange={(e) => setForm({ ...form, username: e.target.value })}
            required
          />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="current-password"
            value={form.password}
            onChange={(e) => setForm({ ...form, password: e.target.value })}
            required
          />
        </label>
        <button className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>
      <div className="demo-hint">
        Just exploring?{" "}
        <button type="button" className="link-button" onClick={fillDemo}>
          Use the demo account
        </button>
      </div>
      <p className="auth-switch">
        New brand? <Link to="/register">Create an account</Link>
      </p>
    </AuthLayout>
  );
}

export function AuthLayout({ title, subtitle, children }) {
  return (
    <div className="auth-page">
      <section className="auth-hero">
        <div className="brand-mark brand-mark-lg">
          <img src="/favicon.svg" alt="" width="36" height="36" />
          <span>ShelfSense</span>
        </div>
        <h1>Turn Amazon data into your next best action.</h1>
        <ul className="hero-points">
          <li>Sales, traffic and conversion trends for every ASIN</li>
          <li>Restock alerts before you run out</li>
          <li>Pricing and listing fixes, ranked by revenue at stake</li>
        </ul>
      </section>
      <section className="auth-panel">
        <div className="auth-card">
          <h2>{title}</h2>
          <p className="muted">{subtitle}</p>
          {children}
        </div>
      </section>
    </div>
  );
}
