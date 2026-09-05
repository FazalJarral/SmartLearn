import { Link } from "react-router-dom";
import { useState } from "react";

import { supabase } from "../lib/supabase";

export function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage(null);
    const { error } = await supabase.auth.signUp({
      email,
      password,
      options: { data: { display_name: displayName } },
    });
    setMessage(error ? error.message : "Account created. Check your email if confirmation is enabled.");
  }

  return (
    <section className="max-w-md">
      <h1 className="text-3xl font-bold">Create account</h1>
      <p className="mt-2 text-slate-700">Registered learners keep their generated packages until deletion.</p>
      <form className="mt-6 grid gap-4" onSubmit={submit}>
        <label className="grid gap-2 text-sm font-medium">
          Display name
          <input className="rounded-md border border-mist px-3 py-2" value={displayName} onChange={(event) => setDisplayName(event.target.value)} required />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Email
          <input className="rounded-md border border-mist px-3 py-2" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Password
          <input className="rounded-md border border-mist px-3 py-2" type="password" minLength={8} value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>
        <button className="rounded-md bg-sage px-4 py-3 font-semibold text-white">Create account</button>
      </form>
      {message ? <p className="mt-4 text-sm" role="status">{message}</p> : null}
      <Link className="mt-4 inline-block font-semibold text-sage underline" to="/login">Already registered?</Link>
    </section>
  );
}
