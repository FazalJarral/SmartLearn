import { useEffect, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useLocation } from "react-router-dom";

import { createGuestSession, getDocumentStatus, getUsage, uploadDocument } from "../lib/api";
import { useAuth } from "../lib/auth";
import { TopBar } from "../components/TopBar";
import { PdfGlyph } from "../components/PdfGlyph";

const MAX_CLIENT_BYTES = 15 * 1024 * 1024;

type Phase = {
  label: string;
  note: string;
  state: "complete" | "active" | "pending";
};

function phasesFor(stage: string | undefined, packageId: string | null | undefined, progress: number): Phase[] {
  const readingDone = Boolean(stage && !["uploaded", "validating", "extracting"].includes(stage)) || Boolean(packageId);
  const readingActive = !readingDone;
  const generatingDone = Boolean(packageId);
  const generatingActive = !generatingDone && stage === "generating_content";
  return [
    {
      label: "Reading your PDF",
      note: readingDone ? "Done" : "—",
      state: readingDone ? "complete" : readingActive ? "active" : "pending",
    },
    {
      label: "Writing your summary, quiz, cards & video",
      note: generatingDone ? "Done" : generatingActive ? `${progress}%` : "—",
      state: generatingDone ? "complete" : generatingActive ? "active" : "pending",
    },
  ];
}

export function Upload() {
  const location = useLocation() as { state?: { file?: File } };
  const [file, setFile] = useState<File | null>(location.state?.file ?? null);
  const [guestSession, setGuestSession] = useState(() => localStorage.getItem("smartlearn_guest_session"));
  const { session } = useAuth();
  const startedRef = useRef(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [dragOver, setDragOver] = useState(false);

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

  const clientError =
    file && file.size > MAX_CLIENT_BYTES
      ? "This file is larger than 15 MiB."
      : file && file.type !== "application/pdf"
        ? "Choose a PDF file."
        : null;

  useEffect(() => {
    if (file && !clientError && !startedRef.current) {
      startedRef.current = true;
      upload.mutate(file);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file, clientError]);

  const acceptFile = (picked: File | undefined | null) => {
    if (!picked) return;
    startedRef.current = false;
    setFile(picked);
  };

  const isProcessing = Boolean(upload.isPending || (currentStatus && !currentStatus.package_id && currentStatus.stage !== "failed"));

  if (isProcessing || currentStatus) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-ink px-4 py-12 text-paper-raised sm:px-[28px]">
        <div className="w-full max-w-[620px]">
          <div className="mb-10 flex items-center gap-[18px]">
            <PdfGlyph width={44} height={56} radius={5} variant="paper" />
            <div>
              <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-dark-muted">
                {file ? `Uploading · ${(file.size / (1024 * 1024)).toFixed(1)} MB` : "Uploading"}
              </p>
              <p className="font-serif text-[clamp(26px,4vw,36px)] leading-[1.12]">{file?.name ?? "Your document"}</p>
            </div>
          </div>

          {currentStatus?.stage === "failed" ? (
            <div className="rounded-[14px] border border-ink-line bg-ink-raised p-5">
              <p className="font-semibold text-warn-border">Processing failed</p>
              <p className="mt-1 text-sm text-dark-muted">{currentStatus.error_code ?? "Generation failed"}</p>
              <button
                type="button"
                className="mt-4 rounded-[11px] bg-paper-raised px-4 py-2 text-sm font-semibold text-ink"
                onClick={() => {
                  startedRef.current = false;
                  setFile(null);
                  upload.reset();
                }}
              >
                Try another file
              </button>
            </div>
          ) : (
            <>
              <div className="mb-10">
                <div className="flex items-baseline justify-between text-sm">
                  <span className="text-dark-body">
                    {currentStatus?.package_id ? "Ready." : currentStatus?.message ?? "Uploading..."}
                  </span>
                  <span className="font-serif text-[34px] leading-none">
                    {currentStatus?.package_id ? 100 : currentStatus?.progress ?? 0}%
                  </span>
                </div>
                <div className="mt-3 h-[3px] overflow-hidden rounded-full bg-ink-line">
                  <div
                    className="h-full rounded-full bg-rust-light transition-[width] duration-[120ms] ease-linear"
                    style={{ width: `${currentStatus?.package_id ? 100 : currentStatus?.progress ?? 0}%` }}
                  />
                </div>
              </div>

              <div className="grid gap-px overflow-hidden rounded-[14px] border border-ink-line bg-ink-line">
                {phasesFor(currentStatus?.stage, currentStatus?.package_id, currentStatus?.progress ?? 0).map((phase) => (
                  <div key={phase.label} className="flex items-center gap-[15px] bg-ink-raised px-5 py-4">
                    <span
                      className={`h-2 w-2 shrink-0 rounded-full ${
                        phase.state === "complete"
                          ? "bg-success"
                          : phase.state === "active"
                            ? "animate-blink bg-rust-light"
                            : "bg-ink-line-2"
                      }`}
                      aria-hidden="true"
                    />
                    <span className={`flex-1 text-[15px] ${phase.state === "pending" ? "text-muted" : "text-paper-raised"}`}>
                      {phase.label}
                    </span>
                    <span className="font-mono text-[11px] text-dark-muted">{phase.note}</span>
                  </div>
                ))}
              </div>

              {currentWarnings.map((warning) => (
                <p key={warning} className="mt-4 text-sm font-medium text-warn-border">
                  {warning}
                </p>
              ))}

              <p className="mt-7 max-w-[52ch] text-[14px] leading-[1.65] text-dark-muted">
                You can close this tab — check the library later and your document will be there. Most short PDFs
                finish in under a minute.
              </p>
            </>
          )}

          {currentStatus?.package_id ? (
            <Link
              to={`/packages/${currentStatus.package_id}`}
              className="mt-6 inline-block rounded-[11px] bg-paper-raised px-5 py-3 text-sm font-semibold text-ink"
            >
              Open document →
            </Link>
          ) : null}
          {upload.error ? <p className="mt-4 text-sm font-medium text-warn-border">{upload.error.message}</p> : null}
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-paper text-ink">
      <TopBar active="Upload" />
      <main className="mx-auto max-w-[620px] px-4 py-[48px] sm:px-[28px]">
        <h1 className="font-serif text-[clamp(34px,4.6vw,44px)]">Upload a study PDF</h1>
        <p className="mt-2 text-muted">Guests can process one accepted upload per UTC day. Guest results are temporary.</p>
        <div className="mt-4 rounded-[14px] border border-line bg-paper-raised px-4 py-3 text-sm text-muted">
          {usage.isLoading ? "Checking quota..." : `Remaining uploads today: ${usage.data?.remaining ?? 0}`}
        </div>
        <label
          className={`mt-6 flex cursor-pointer flex-col items-center justify-center rounded-[18px] border-[1.5px] border-dashed bg-paper-raised p-10 text-center transition-colors ${
            dragOver ? "border-rust bg-paper-input" : "border-line-strong"
          }`}
          onDragOver={(event) => {
            event.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragOver(false);
            acceptFile(event.dataTransfer.files?.[0]);
          }}
        >
          <PdfGlyph width={50} height={64} radius={6} variant="ink" />
          <span className="mt-4 font-serif text-[22px]">Select or drag a text-based PDF</span>
          <span className="mt-1 text-sm text-muted">Maximum 15 MiB. For longer PDFs, we process the first 20 pages.</span>
          <input
            ref={fileInputRef}
            className="sr-only"
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => acceptFile(event.target.files?.[0])}
          />
        </label>
        {file ? <p className="mt-3 text-sm">{file.name}</p> : null}
        {clientError ? <p className="mt-3 text-sm font-medium text-warn-ink">{clientError}</p> : null}
        {upload.error ? <p className="mt-3 text-sm font-medium text-warn-ink">{upload.error.message}</p> : null}
        <button
          className="mt-5 rounded-[11px] bg-ink px-5 py-[13px] text-sm font-semibold text-paper-raised transition-colors hover:bg-rust disabled:cursor-not-allowed disabled:opacity-50"
          disabled={!file || Boolean(clientError)}
          onClick={() => {
            if (file && !clientError) {
              startedRef.current = true;
              upload.mutate(file);
            }
          }}
        >
          Submit document
        </button>
      </main>
    </div>
  );
}
