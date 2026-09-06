import { Link } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { FileUp, Trash2 } from "lucide-react";

import { deleteDocument, listDocuments, retryDocument } from "../lib/api";
import { useAuth } from "../lib/auth";

export function Dashboard() {
  const { session, user } = useAuth();
  const queryClient = useQueryClient();
  const guestSession = localStorage.getItem("smartlearn_guest_session");
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

  const handleDelete = (documentId: string) => {
    if (window.confirm("Delete this document and its generated study package?")) {
      removeDocument.mutate(documentId);
    }
  };

  return (
    <section className="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
      <div>
        <p className="text-sm font-semibold uppercase tracking-wide text-sage">Academic study workspace</p>
        <h1 className="mt-3 max-w-3xl text-4xl font-bold leading-tight">Turn dense PDF readings into active recall sessions.</h1>
        <p className="mt-4 max-w-2xl text-lg text-slate-700">
          Upload one text-based academic PDF and SmartLearn prepares a summary, flashcards, quiz feedback, and a short instructional video.
        </p>
        <Link to="/upload" className="mt-6 inline-flex items-center gap-2 rounded-md bg-sage px-4 py-3 font-semibold text-white">
          <FileUp aria-hidden="true" className="h-5 w-5" />
          Upload PDF
        </Link>
      </div>
      <aside className="rounded-lg border border-mist bg-white p-5">
        <h2 className="text-lg font-semibold">Recent packages</h2>
        {documents.isLoading ? <p className="mt-3 text-sm text-slate-600">Loading your study history...</p> : null}
        {documents.error ? <p className="mt-3 text-sm text-red-700">Unable to load recent packages.</p> : null}
        {documents.data?.length ? (
          <ul className="mt-4 space-y-3">
            {documents.data.map((document) => (
              <li key={document.id} className="rounded-md border border-mist p-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold">{document.title ?? document.original_filename}</p>
                    <p className="mt-1 text-xs uppercase text-slate-500">{document.stage.replace("_", " ")} - {document.progress}%</p>
                  </div>
                  <button
                    aria-label={`Delete ${document.title ?? document.original_filename}`}
                    className="rounded-md p-2 text-slate-600 hover:bg-mist"
                    disabled={removeDocument.isPending}
                    onClick={() => handleDelete(document.id)}
                    type="button"
                  >
                    <Trash2 aria-hidden="true" className="h-4 w-4" />
                  </button>
                </div>
                {document.package_id ? (
                  <Link className="mt-3 inline-block text-sm font-semibold text-sage underline" to={`/packages/${document.package_id}`}>
                    Open package
                  </Link>
                ) : document.stage === "failed" ? (
                  <button
                    className="mt-3 text-sm font-semibold text-sage underline"
                    disabled={retry.isPending}
                    onClick={() => retry.mutate(document.id)}
                    type="button"
                  >
                    Retry
                  </button>
                ) : (
                  <p className="mt-3 text-sm text-slate-600">Package is still processing.</p>
                )}
              </li>
            ))}
          </ul>
        ) : null}
        {!documents.isLoading && !documents.data?.length ? (
          <p className="mt-3 text-sm text-slate-600">
            {user ? "Your SmartLearn history will appear here as packages are generated." : "Sign in to keep generated packages until you delete them."}
          </p>
        ) : null}
        {removeDocument.error ? <p className="mt-3 text-sm text-red-700">{removeDocument.error.message}</p> : null}
        {retry.error ? <p className="mt-3 text-sm text-red-700">{retry.error.message}</p> : null}
      </aside>
    </section>
  );
}
