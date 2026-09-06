import { useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";
import { UploadCloud } from "lucide-react";

import { createGuestSession, getDocumentStatus, getUsage, uploadDocument } from "../lib/api";
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
  const uploadStatus = useQuery({
    queryKey: ["document-status", upload.data?.document_id, session?.access_token, guestSession],
    queryFn: () => getDocumentStatus(upload.data!.document_id, session?.access_token, guestSession),
    enabled: Boolean(upload.data?.document_id && !upload.data?.package_id),
    refetchInterval: (query) => {
      const status = query.state.data;
      return status && (status.package_id || status.stage === "failed") ? false : 2500;
    },
  });
  const currentStatus = uploadStatus.data ?? upload.data;
  const currentWarnings = upload.data?.warnings ?? currentStatus?.warnings ?? [];
  const isProcessing = currentStatus && !currentStatus.package_id && currentStatus.stage !== "failed";

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
      {currentStatus ? (
        <div className="mt-4 space-y-2 text-sm">
          {currentWarnings.map((warning) => (
            <p key={warning} className="font-medium text-amber-700">
              {warning}
            </p>
          ))}
          <div className="rounded-md border border-mist bg-white p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-medium">{currentStatus.message}</p>
              <p className="text-slate-600">{currentStatus.progress}%</p>
            </div>
            <div className="mt-3 h-2 overflow-hidden rounded-full bg-mist">
              <div className="h-full rounded-full bg-sage transition-all" style={{ width: `${currentStatus.progress}%` }} />
            </div>
          </div>
          {currentStatus.package_id ? (
            <Link className="inline-block font-semibold text-sage underline" to={`/packages/${currentStatus.package_id}`}>
              Open package
            </Link>
          ) : null}
          {currentStatus.stage === "failed" ? <p className="font-medium text-red-700">{currentStatus.error_code ?? "Generation failed"}</p> : null}
          {isProcessing ? <p className="text-slate-600">You can leave this page and check the dashboard while it finishes.</p> : null}
        </div>
      ) : null}
    </section>
  );
}
