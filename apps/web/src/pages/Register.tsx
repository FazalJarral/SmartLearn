import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import { AuthLayout } from "../components/AuthLayout";
import { supabase } from "../lib/supabase";
import { useAuth } from "../lib/auth";

export function Register() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (user) navigate("/", { replace: true });
  }, [user, navigate]);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage(null);
    setSubmitting(true);
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { display_name: displayName } },
    });
    setSubmitting(false);
    setMessage(error ? error.message : "Account created. Check your email if confirmation is enabled.");
  }

  return (
    <AuthLayout mode="signup" heading="Start with one PDF" sub="Free for your first three documents.">
      <form className="mt-6 grid gap-4" onSubmit={submit}>
        <label className="grid gap-[7px]">
          <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Full name</span>
          <input
            className="rounded-[11px] border border-line bg-paper-input px-[15px] py-[13px] text-[15px] text-ink outline-none transition-colors focus:border-ink"
            placeholder="Amara Osei"
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            required
          />
        </label>
        <label className="grid gap-[7px]">
          <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Email</span>
          <input
            className="rounded-[11px] border border-line bg-paper-input px-[15px] py-[13px] text-[15px] text-ink outline-none transition-colors focus:border-ink"
            type="email"
            placeholder="amara@uni.edu"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />
        </label>
        <label className="grid gap-[7px]">
          <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">Password</span>
          <input
            className="rounded-[11px] border border-line bg-paper-input px-[15px] py-[13px] text-[15px] text-ink outline-none transition-colors focus:border-ink"
            type="password"
            placeholder="••••••••"
            minLength={8}
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        <button
          className="mt-2 rounded-[11px] bg-ink px-[15px] py-[15px] text-[15px] font-semibold text-paper-raised transition-colors hover:bg-rust disabled:cursor-not-allowed disabled:opacity-60"
          disabled={submitting}
        >
          {submitting ? "Creating account..." : "Create account"}
        </button>
      </form>
      {message ? (
        <p className="mt-4 text-sm" role="status">
          {message}
        </p>
      ) : null}
    </AuthLayout>
  );
}
