import { useState } from "react";
import { Link, Navigate, useNavigate } from "react-router-dom";

import { errorMessage } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { AuthLayout } from "./LoginPage";

export default function RegisterPage() {
  const { register, status } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ brand_name: "", username: "", email: "", password: "" });
  const [error, setError] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  if (status === "authenticated") return <Navigate to="/dashboard" replace />;

  const update = (field) => (e) => setForm({ ...form, [field]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await register(form);
      navigate("/dashboard", { replace: true });
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout title="Create your brand" subtitle="Connect your catalog and get recommendations in seconds.">
      <form onSubmit={submit} className="form">
        {error && <div className="alert alert-error">{error}</div>}
        <label>
          Brand name
          <input autoFocus value={form.brand_name} onChange={update("brand_name")} required maxLength={120} />
        </label>
        <label>
          Username
          <input autoComplete="username" value={form.username} onChange={update("username")} required />
        </label>
        <label>
          Email <span className="muted">(optional)</span>
          <input type="email" autoComplete="email" value={form.email} onChange={update("email")} />
        </label>
        <label>
          Password
          <input
            type="password"
            autoComplete="new-password"
            value={form.password}
            onChange={update("password")}
            required
            minLength={8}
          />
        </label>
        <button className="btn btn-primary btn-block" disabled={submitting}>
          {submitting ? "Creating…" : "Create account"}
        </button>
      </form>
      <p className="auth-switch">
        Already have an account? <Link to="/login">Log in</Link>
      </p>
    </AuthLayout>
  );
}
