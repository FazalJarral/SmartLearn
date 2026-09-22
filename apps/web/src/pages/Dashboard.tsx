import { useRef, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Trash2 } from "lucide-react";

import { deleteDocument, listDocuments, retryDocument, type DocumentListItem } from "../lib/api";
import { formatRelativeTime } from "../lib/formatRelativeTime";
import { useAuth } from "../lib/auth";
import { TopBar } from "../components/TopBar";
import { PdfGlyph } from "../components/PdfGlyph";

function statusFor(document: DocumentListItem): { label: string; tint: "rust" | "success" | "warn" | "muted" } {
  if (document.package_id) return { label: "Ready", tint: "success" };
  if (document.stage === "failed") return { label: "Failed", tint: "warn" };
  return { label: "Processing", tint: "rust" };
}

const tintClasses: Record<string, string> = {
  rust: "text-rust",
  success: "text-success",
  warn: "text-warn-ink",
  muted: "text-muted",
};

const tintBarClasses: Record<string, string> = {
  rust: "bg-rust",
  success: "bg-success",
  warn: "bg-warn-border",
  muted: "bg-dark-muted",
};

function greeting() {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

export function Dashboard() {
  const { session, user } = useAuth();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const guestSession = localStorage.getItem("smartlearn_guest_session");
  const [dragOver, setDragOver] = useState(false);
  const [dropError, setDropError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const documents = useQuery({
    queryKey: ["documents", session?.access_token, guestSession],
    queryFn: () => listDocuments(session?.access_token, guestSession),
    refetchInterval: (query) => {
      const hasProcessingDocument = query.state.data?.some(
        (document) => !document.package_id && document.stage !== "failed",
      );
      return hasProcessingDocument ? 3000 : false;
    },
  });
  const removeDocument = useMutation({
    mutationFn: (documentId: string) => deleteDocument(documentId, session?.access_token, guestSession),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });
  const retry = useMutation({
    mutationFn: (documentId: string) => retryDocument(documentId, session?.access_token, guestSession),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["documents"] }),
  });

  const handleDelete = (documentId: string, label: string) => {
    if (window.confirm(`Delete "${label}" and its generated study package?`)) {
      removeDocument.mutate(documentId);
    }
  };

  const acceptFile = (file: File | undefined | null) => {
    if (!file) return;
    if (file.type !== "application/pdf") {
      setDropError("Choose a PDF file.");
      return;
    }
    setDropError(null);
    navigate("/upload", { state: { file } });
  };

  const displayName = (user?.user_metadata?.display_name as string | undefined) || user?.email?.split("@")[0] || "there";
  const readyCount = documents.data?.filter((doc) => doc.package_id).length ?? 0;

  return (
    <div className="min-h-screen bg-paper text-ink">
      <TopBar active="Library" />
      <main className="mx-auto max-w-[1120px] px-4 py-[48px] pb-[72px] sm:px-[28px]">
        <div className="mb-10 flex flex-wrap items-end justify-between gap-[30px]">
          <div>
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">
              {new Date().toLocaleDateString(undefined, { weekday: "long" })}
            </p>
            <h1 className="mt-2 font-serif text-[clamp(36px,5vw,58px)] leading-[1]">
              {greeting()}, {displayName}.
            </h1>
          </div>
          <div className="flex gap-[34px]">
            <div>
              <p className="font-serif text-[40px] leading-none text-ink">{documents.data?.length ?? 0}</p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted">Documents</p>
            </div>
            <div>
              <p className="font-serif text-[40px] leading-none text-ink">{readyCount}</p>
              <p className="mt-1 font-mono text-[10px] uppercase tracking-[0.14em] text-muted">Ready to study</p>
            </div>
          </div>
        </div>

        <label
          className={`mb-[46px] flex cursor-pointer flex-wrap items-center justify-between gap-[26px] rounded-[18px] border-[1.5px] border-dashed bg-paper-raised p-[32px] transition-colors ${
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
          <div className="flex items-center gap-[22px]">
            <PdfGlyph width={50} height={64} radius={6} variant="ink" />
            <div>
              <p className="font-serif text-[29px] leading-[1.1]">Drop a PDF to get started</p>
              <p className="mt-1 text-sm text-muted">Lecture slides, papers, textbook chapters — up to 20 pages.</p>
            </div>
          </div>
          <span className="whitespace-nowrap rounded-full bg-ink px-[22px] py-[13px] text-sm font-semibold text-paper-raised">
            Choose file
          </span>
          <input
            ref={fileInputRef}
            className="sr-only"
            type="file"
            accept="application/pdf,.pdf"
            onChange={(event) => acceptFile(event.target.files?.[0])}
          />
        </label>
        {dropError ? <p className="-mt-[38px] mb-8 text-sm font-medium text-warn-ink">{dropError}</p> : null}

        <div className="mb-4 flex flex-wrap items-baseline justify-between gap-2">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-muted">Your documents</p>
        </div>

        {documents.isLoading ? <p className="text-sm text-muted">Loading your study history...</p> : null}
        {documents.error ? <p className="text-sm text-warn-ink">Unable to load recent packages.</p> : null}
        {!documents.isLoading && !documents.data?.length ? (
          <p className="rounded-[16px] border border-line bg-paper-raised p-6 text-sm text-muted">
            {user
              ? "Your SmartLearn history will appear here as packages are generated."
              : "Sign in to keep generated packages until you delete them."}
          </p>
        ) : null}

        <div className="grid gap-4" style={{ gridTemplateColumns: "repeat(auto-fill, minmax(min(100%, 280px), 1fr))" }}>
          {documents.data?.map((document) => {
            const status = statusFor(document);
            const label = document.title ?? document.original_filename;
            return (
              <div
                key={document.id}
                className="group flex flex-col gap-4 rounded-card border border-line bg-paper-raised p-5 transition-all hover:-translate-y-0.5 hover:border-ink hover:shadow-card"
              >
                {document.package_id ? (
                  <Link to={`/packages/${document.package_id}`} className="flex flex-1 flex-col gap-4">
                    <DocumentCardBody document={document} status={status} label={label} />
                  </Link>
                ) : (
                  <div className="flex flex-1 flex-col gap-4">
                    <DocumentCardBody document={document} status={status} label={label} />
                  </div>
                )}
                <div className="flex items-center justify-between">
                  {document.stage === "failed" ? (
                    <button
                      className="text-sm font-semibold text-rust underline-offset-2 hover:underline"
                      disabled={retry.isPending}
                      onClick={() => retry.mutate(document.id)}
                      type="button"
                    >
                      Retry
                    </button>
                  ) : (
                    <span />
                  )}
                  <button
                    aria-label={`Delete ${label}`}
                    className="rounded-md p-2 text-muted hover:bg-fill-sunken hover:text-ink"
                    disabled={removeDocument.isPending}
                    onClick={() => handleDelete(document.id, label)}
                    type="button"
                  >
                    <Trash2 aria-hidden="true" className="h-4 w-4" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
        {removeDocument.error ? <p className="mt-4 text-sm text-warn-ink">{removeDocument.error.message}</p> : null}
        {retry.error ? <p className="mt-4 text-sm text-warn-ink">{retry.error.message}</p> : null}
      </main>
    </div>
  );
}

function DocumentCardBody({
  document,
  status,
  label,
}: {
  document: DocumentListItem;
  status: { label: string; tint: "rust" | "success" | "warn" | "muted" };
  label: string;
}) {
  return (
    <>
      <p className="font-serif text-[22px] leading-[1.16] text-pretty">{label}</p>
      <hr className="border-[#E2DDD0]" />
      <div className="flex items-center justify-between gap-2">
        <span className="font-mono text-[11px] text-muted">{formatRelativeTime(document.created_at)}</span>
        <span className={`text-xs font-semibold ${tintClasses[status.tint]}`}>{status.label}</span>
      </div>
      <div className="h-1 overflow-hidden rounded-full bg-[#E2DDD0]">
        <div
          className={`h-full rounded-full transition-all ${tintBarClasses[status.tint]}`}
          style={{ width: `${document.progress}%` }}
        />
      </div>
    </>
  );
}
