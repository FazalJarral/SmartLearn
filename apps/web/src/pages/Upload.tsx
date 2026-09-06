import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { UploadCloud } from "lucide-react";

import { createGuestSession, getUsage, uploadDocument } from "../lib/api";
import { useAuth } from "../lib/auth";

const MAX_CLIENT_BYTES = 15 * 1024 * 1024;

export function Upload() {
  const [file, setFile] = useState<File | null>(null);
  const [guestSession, setGuestSession] = useState(() => localStorage.getItem("smartlearn_guest_session"));
  const { session } = useAuth();
  const usage = useQuery({
    queryKey: ["usage", session?.access_token, guestSession],
    queryFn: () => getUsage(session?.access_token, guestSession),
  });
  const upload = useMutation({
    mutationFn: async (selectedFile: File) => {
      let activeGuestSession = guestSession;
      if (!session?.access_token && !activeGuestSession) {
        const created = await createGuestSession();
        activeGuestSession = created.guest_session_id;
        localStorage.setItem("smartlearn_guest_session", created.guest_session_id);
        setGuestSession(activeGuestSession);
      }
      return uploadDocument(selectedFile, session?.access_token, activeGuestSession);
    },
  });

  const clientError =
    file && file.size > MAX_CLIENT_BYTES
      ? "This file is larger than 15 MiB."
      : file && file.type !== "application/pdf"
        ? "Choose a PDF file."
        : null;

  return (
    <section className="max-w-3xl">
      <h1 className="text-3xl font-bold">Upload a study PDF</h1>
      <p className="mt-2 text-slate-700">Guests can process one accepted upload per UTC day. Guest results are temporary.</p>
      <div className="mt-4 rounded-md border border-mist bg-white p-4 text-sm">
        {usage.isLoading ? "Checking quota..." : `Remaining uploads today: ${usage.data?.remaining ?? 0}`}
      </div>
      <label className="mt-6 flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-sage bg-white p-10 text-center">
        <UploadCloud aria-hidden="true" className="h-10 w-10 text-sage" />
        <span className="mt-3 font-semibold">Select or drag a text-based PDF</span>
        <span className="mt-1 text-sm text-slate-600">Maximum 15 MiB. For longer PDFs, we process the first 20 pages.</span>
        <input
          className="sr-only"
          type="file"
          accept="application/pdf,.pdf"
          onChange={(event) => setFile(event.target.files?.[0] ?? null)}
        />
      </label>
      {file ? <p className="mt-3 text-sm">{file.name}</p> : null}
      {clientError ? <p className="mt-3 text-sm font-medium text-red-700">{clientError}</p> : null}
      <button
        className="mt-5 rounded-md bg-ink px-4 py-3 font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
        disabled={!file || Boolean(clientError) || upload.isPending}
        onClick={() => file && upload.mutate(file)}
      >
        {upload.isPending ? "Submitting..." : "Submit document"}
      </button>
      {upload.error ? <p className="mt-4 text-sm font-medium text-red-700">{upload.error.message}</p> : null}
      {upload.data?.package_id ? (
        <div className="mt-4 space-y-2 text-sm">
          {upload.data.warnings.map((warning) => (
            <p key={warning} className="font-medium text-amber-700">
              {warning}
            </p>
          ))}
          <p>
            {upload.data.message} <Link className="font-semibold text-sage underline" to={`/packages/${upload.data.package_id}`}>Open package</Link>
          </p>
        </div>
      ) : null}
    </section>
  );
}
