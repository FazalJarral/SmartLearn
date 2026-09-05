import { z } from "zod";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

export const documentStatusSchema = z.object({
  document_id: z.string(),
  stage: z.string(),
  progress: z.number(),
  message: z.string(),
  error_code: z.string().nullable(),
  package_id: z.string().nullable(),
});

export type DocumentStatus = z.infer<typeof documentStatusSchema>;

export const documentListItemSchema = z.object({
  id: z.string(),
  original_filename: z.string(),
  stage: z.string(),
  progress: z.number(),
  created_at: z.string(),
  deleted_at: z.string().nullable(),
  package_id: z.string().nullable(),
  title: z.string().nullable(),
});

export type DocumentListItem = z.infer<typeof documentListItemSchema>;

const quizAttemptSchema = z.object({
  id: z.string(),
  package_id: z.string(),
  score: z.number(),
  total: z.number(),
  started_at: z.string(),
  completed_at: z.string().nullable(),
});

export type QuizAttempt = z.infer<typeof quizAttemptSchema>;

const quizAnswerResultSchema = z.object({
  attempt_id: z.string(),
  question_id: z.string(),
  selected_index: z.number(),
  correct_index: z.number(),
  is_correct: z.boolean(),
  explanation: z.string(),
  score: z.number(),
  total: z.number(),
});

export type QuizAnswerResult = z.infer<typeof quizAnswerResultSchema>;

export type SourcePages = {
  source_pages: number[];
};

export type KeyPoint = SourcePages & {
  heading: string;
  explanation: string;
};

export type Flashcard = SourcePages & {
  id?: string | null;
  front: string;
  back: string;
};

export type QuizQuestion = SourcePages & {
  id?: string | null;
  question: string;
  options: string[];
  correct_option_index: number;
  explanation: string;
};

export type VideoScene = {
  template: string;
  text: string[];
  duration_seconds: number;
};

export type LearningPackageContent = {
  schema_version: "1.0";
  title: string;
  summary: {
    overview: string;
    key_points: KeyPoint[];
  };
  flashcards: Flashcard[];
  quiz: QuizQuestion[];
  video: {
    title: string;
    narration: string;
    scenes: VideoScene[];
  };
};

export type LearningPackageResponse = {
  id: string;
  document_id: string;
  content: LearningPackageContent;
  video_asset_id: string | null;
};

export async function createGuestSession() {
  const response = await fetch(`${API_BASE_URL}/guest/session`, { method: "POST" });
  if (!response.ok) throw new Error("Unable to start guest session");
  return response.json();
}

function authHeaders(accessToken?: string | null, guestSession?: string | null) {
  const headers: Record<string, string> = {};
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  if (guestSession) headers["X-Guest-Session"] = guestSession;
  return headers;
}

export async function getUsage(accessToken?: string | null, guestSession?: string | null) {
  const response = await fetch(`${API_BASE_URL}/me/usage`, {
    headers: authHeaders(accessToken, guestSession),
  });
  if (!response.ok) throw new Error("Unable to load usage");
  return response.json();
}

export async function listDocuments(accessToken?: string | null, guestSession?: string | null): Promise<DocumentListItem[]> {
  const response = await fetch(`${API_BASE_URL}/documents`, {
    headers: authHeaders(accessToken, guestSession),
  });
  if (!response.ok) {
    if (response.status === 401) return [];
    throw new Error("Unable to load documents");
  }
  return z.array(documentListItemSchema).parse(await response.json());
}

export async function uploadDocument(file: File, accessToken?: string | null, guestSession?: string | null): Promise<DocumentStatus> {
  const form = new FormData();
  form.append("file", file);
  const response = await fetch(`${API_BASE_URL}/documents`, {
    method: "POST",
    headers: { "Idempotency-Key": crypto.randomUUID(), ...authHeaders(accessToken, guestSession) },
    body: form,
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? "Upload failed");
  }
  return documentStatusSchema.parse(await response.json());
}

export async function deleteDocument(documentId: string, accessToken?: string | null, guestSession?: string | null) {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}`, {
    method: "DELETE",
    headers: authHeaders(accessToken, guestSession),
  });
  if (!response.ok) throw new Error("Unable to delete document");
}

export async function retryDocument(
  documentId: string,
  accessToken?: string | null,
  guestSession?: string | null,
): Promise<DocumentStatus> {
  const response = await fetch(`${API_BASE_URL}/documents/${documentId}/retry`, {
    method: "POST",
    headers: authHeaders(accessToken, guestSession),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? "Unable to retry document");
  }
  return documentStatusSchema.parse(await response.json());
}

export async function getPackage(
  packageId: string,
  accessToken?: string | null,
  guestSession?: string | null,
): Promise<LearningPackageResponse> {
  const response = await fetch(`${API_BASE_URL}/learning-packages/${packageId}`, {
    headers: authHeaders(accessToken, guestSession),
  });
  if (!response.ok) throw new Error("Unable to load package");
  return response.json();
}

export async function createQuizAttempt(
  packageId: string,
  accessToken?: string | null,
  guestSession?: string | null,
): Promise<QuizAttempt> {
  const response = await fetch(`${API_BASE_URL}/learning-packages/${packageId}/quiz-attempts`, {
    method: "POST",
    headers: authHeaders(accessToken, guestSession),
  });
  if (!response.ok) throw new Error("Unable to start quiz");
  return quizAttemptSchema.parse(await response.json());
}

export async function answerQuizQuestion(
  attemptId: string,
  questionId: string,
  selectedIndex: number,
  accessToken?: string | null,
  guestSession?: string | null,
): Promise<QuizAnswerResult> {
  const response = await fetch(`${API_BASE_URL}/quiz-attempts/${attemptId}/answers`, {
    method: "PATCH",
    headers: { "content-type": "application/json", ...authHeaders(accessToken, guestSession) },
    body: JSON.stringify({ question_id: questionId, selected_index: selectedIndex }),
  });
  if (!response.ok) throw new Error("Unable to submit answer");
  return quizAnswerResultSchema.parse(await response.json());
}

export async function completeQuizAttempt(
  attemptId: string,
  accessToken?: string | null,
  guestSession?: string | null,
): Promise<QuizAttempt> {
  const response = await fetch(`${API_BASE_URL}/quiz-attempts/${attemptId}/complete`, {
    method: "POST",
    headers: authHeaders(accessToken, guestSession),
  });
  if (!response.ok) throw new Error("Unable to complete quiz");
  return quizAttemptSchema.parse(await response.json());
}

export async function getVideoUrl(
  videoAssetId: string,
  mode: "playback" | "download",
  accessToken?: string | null,
  guestSession?: string | null,
): Promise<string> {
  const response = await fetch(`${API_BASE_URL}/video-assets/${videoAssetId}/${mode}-url`, {
    headers: authHeaders(accessToken, guestSession),
  });
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    throw new Error(body?.error?.message ?? "Video is not available yet");
  }
  const body = z.object({ url: z.string(), expires_in: z.number() }).parse(await response.json());
  return body.url;
}
