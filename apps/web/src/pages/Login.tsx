import { useState } from "react";

import { AuthLayout } from "../components/AuthLayout";
import { supabase } from "../lib/supabase";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage(null);
    setSubmitting(true);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setSubmitting(false);
    setMessage(error ? error.message : "Signed in. You can return to your dashboard.");
  }

  async function forgotPassword() {
    if (!email) {
      setMessage("Enter your email above first.");
      return;
    }
    const { error } = await supabase.auth.resetPasswordForEmail(email);
    setMessage(error ? error.message : "Check your email for a reset link.");
  }

  async function continueWithGoogle() {
    const { error } = await supabase.auth.signInWithOAuth({ provider: "google" });
    if (error) setMessage(error.message);
  }

  return (
    <AuthLayout mode="signin" heading="Welcome back" sub="Pick up where you left off.">
      <form className="mt-6 grid gap-4" onSubmit={submit}>
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
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />
        </label>
        <button
          type="button"
          onClick={forgotPassword}
          className="mb-[6px] mt-[-4px] text-right text-[13px] text-muted"
        >
          Forgot password?
        </button>
        <button
          className="rounded-[11px] bg-ink px-[15px] py-[15px] text-[15px] font-semibold text-paper-raised transition-colors hover:bg-rust disabled:cursor-not-allowed disabled:opacity-60"
          disabled={submitting}
        >
          {submitting ? "Signing in..." : "Sign in"}
        </button>
      </form>
      <div className="my-6 flex items-center gap-[13px]">
        <hr className="flex-1 border-line" />
        <span className="font-mono text-[10px] uppercase tracking-[0.12em] text-muted">OR</span>
        <hr className="flex-1 border-line" />
      </div>
      <button
        type="button"
        onClick={continueWithGoogle}
        className="w-full rounded-[11px] border border-line bg-paper-input px-[13px] py-[13px] text-[14px] font-medium text-ink transition-colors hover:border-ink"
      >
        Continue with Google
      </button>
      {message ? (
        <p className="mt-4 text-sm" role="status">
          {message}
        </p>
      ) : null}
    </AuthLayout>
  );
}
