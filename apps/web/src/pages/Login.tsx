import { Link } from "react-router-dom";
import { useState } from "react";

import { supabase } from "../lib/supabase";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [message, setMessage] = useState<string | null>(null);

  async function submit(event: React.FormEvent) {
    event.preventDefault();
    setMessage(null);
    const { error } = await supabase.auth.signInWithPassword({ email, password });
    setMessage(error ? error.message : "Signed in. You can return to your dashboard.");
  }

  return (
    <section className="max-w-md">
      <h1 className="text-3xl font-bold">Sign in</h1>
      <form className="mt-6 grid gap-4" onSubmit={submit}>
        <label className="grid gap-2 text-sm font-medium">
          Email
          <input className="rounded-md border border-mist px-3 py-2" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
        </label>
        <label className="grid gap-2 text-sm font-medium">
          Password
          <input className="rounded-md border border-mist px-3 py-2" type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>
        <button className="rounded-md bg-sage px-4 py-3 font-semibold text-white">Sign in</button>
      </form>
      {message ? <p className="mt-4 text-sm" role="status">{message}</p> : null}
      <Link className="mt-4 inline-block font-semibold text-sage underline" to="/register">Create an account</Link>
    </section>
  );
}
