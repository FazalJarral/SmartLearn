import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { useParams } from "react-router-dom";

import {
  answerQuizQuestion,
  completeQuizAttempt,
  createQuizAttempt,
  getVideoUrl,
  getPackage,
  type QuizAnswerResult,
  type QuizAttempt,
  type QuizQuestion,
} from "../lib/api";
import { useAuth } from "../lib/auth";

const tabs = ["Summary", "Flashcards", "Quiz", "Video"] as const;

export function LearningPackage() {
  const { packageId = "" } = useParams();
  const [tab, setTab] = useState<(typeof tabs)[number]>("Summary");
  const { session } = useAuth();
  const guestSession = localStorage.getItem("smartlearn_guest_session");
  const result = useQuery({
    queryKey: ["package", packageId, session?.access_token, guestSession],
    queryFn: () => getPackage(packageId, session?.access_token, guestSession),
    enabled: Boolean(packageId),
    refetchInterval: (query) => {
      const status = query.state.data?.video_status;
      return status && !["completed", "partial_success", "failed"].includes(status) ? 3000 : false;
    },
  });

  if (result.isLoading) return <p>Loading package...</p>;
  if (result.error) return <p role="alert">Unable to load this learning package.</p>;
  if (!result.data) return <p role="alert">Package data is unavailable.</p>;

  const content = result.data.content;

  return (
    <section>
      <h1 className="text-3xl font-bold">{content.title}</h1>
      <div className="mt-6 flex flex-wrap gap-2" role="tablist" aria-label="Learning package sections">
        {tabs.map((item) => (
          <button
            key={item}
            role="tab"
            aria-selected={tab === item}
            className={`rounded-md px-4 py-2 text-sm font-semibold ${tab === item ? "bg-sage text-white" : "bg-mist text-ink"}`}
            onClick={() => setTab(item)}
          >
            {item}
          </button>
        ))}
      </div>
      <div className="mt-6">
        {tab === "Summary" && (
          <article className="prose max-w-none">
            <p>{content.summary.overview}</p>
            <ul>
              {content.summary.key_points.map((point: { heading: string; explanation: string }) => (
                <li key={point.heading}><strong>{point.heading}:</strong> {point.explanation}</li>
              ))}
            </ul>
          </article>
        )}
        {tab === "Flashcards" && <Flashcards cards={content.flashcards} />}
        {tab === "Quiz" && (
          <Quiz
            accessToken={session?.access_token}
            guestSession={guestSession}
            packageId={packageId}
            questions={content.quiz}
          />
        )}
        {tab === "Video" && (
          <VideoPlan
            accessToken={session?.access_token}
            guestSession={guestSession}
            packageTitle={content.title}
            video={content.video}
            videoAssetId={result.data.video_asset_id}
            videoAvailable={result.data.video_available}
            videoMessage={result.data.video_message}
            videoStatus={result.data.video_status}
            transcriptAvailable={result.data.transcript_available}
          />
        )}
      </div>
    </section>
  );
}

type VideoPlanProps = {
  accessToken?: string | null;
  guestSession?: string | null;
  packageTitle: string;
  video: {
    title: string;
    narration: string;
    scenes: Array<{ template: string; text: string[]; duration_seconds: number }>;
  };
  videoAssetId?: string | null;
  videoStatus?: string | null;
  videoMessage?: string | null;
  videoAvailable: boolean;
  transcriptAvailable: boolean;
};

function VideoPlan({
  accessToken,
  guestSession,
  packageTitle,
  video,
  videoAssetId,
  videoAvailable,
  videoMessage,
  videoStatus,
  transcriptAvailable,
}: VideoPlanProps) {
  const [playbackUrl, setPlaybackUrl] = useState<string | null>(null);
  const playback = useMutation({
    mutationFn: () => {
      if (!videoAssetId) throw new Error("Video asset is not ready");
      return getVideoUrl(videoAssetId, "playback", accessToken, guestSession);
    },
    onSuccess: setPlaybackUrl,
  });
  const download = useMutation({
    mutationFn: () => {
      if (!videoAssetId) throw new Error("Video asset is not ready");
      return getVideoUrl(videoAssetId, "download", accessToken, guestSession);
    },
    onSuccess: (url) => {
      window.location.href = url;
    },
  });
  const transcript = useMutation({
    mutationFn: () => {
      if (!videoAssetId) throw new Error("Video asset is not ready");
      return getVideoUrl(videoAssetId, "transcript", accessToken, guestSession);
    },
    onSuccess: (url) => {
      window.location.href = url;
    },
  });

  return (
    <article className="space-y-5">
      <div className="rounded-lg border border-mist bg-white p-5">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <h2 className="text-xl font-semibold">{video.title}</h2>
            <p className="mt-1 text-sm text-slate-600">{packageTitle}</p>
          </div>
          <div className="flex gap-2">
            <button
              className="rounded-md bg-sage px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!videoAvailable}
              onClick={() => playback.mutate()}
              type="button"
            >
              Play MP4
            </button>
            <button
              className="rounded-md bg-sage px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!videoAvailable}
              onClick={() => download.mutate()}
              type="button"
            >
              Download
            </button>
            <button
              className="rounded-md bg-ink px-3 py-2 text-sm font-semibold text-white disabled:cursor-not-allowed disabled:opacity-50"
              disabled={!transcriptAvailable}
              onClick={() => transcript.mutate()}
              type="button"
            >
              Transcript
            </button>
          </div>
        </div>
        {videoStatus ? (
          <p className="mt-3 text-sm text-slate-600">
            {videoStatus.replace("_", " ")}{videoMessage ? ` - ${videoMessage}` : ""}
          </p>
        ) : null}
        {playbackUrl ? (
          <video className="mt-4 w-full rounded-md border border-mist" controls src={playbackUrl}>
            <track kind="captions" />
          </video>
        ) : null}
        {playback.error ? <p className="mt-3 text-sm text-slate-600">{playback.error.message}</p> : null}
        {download.error ? <p className="mt-3 text-sm text-slate-600">{download.error.message}</p> : null}
        {transcript.error ? <p className="mt-3 text-sm text-slate-600">{transcript.error.message}</p> : null}
        <p className="mt-3 text-slate-700">{video.narration}</p>
      </div>
      <ol className="space-y-3">
        {video.scenes.map((scene, index) => (
          <li key={`${scene.template}-${index}`} className="rounded-md border border-mist bg-white p-4">
            <p className="text-sm font-semibold uppercase text-slate-500">
              Scene {index + 1} - {scene.template.replace("_", " ")} - {scene.duration_seconds}s
            </p>
            <ul className="mt-2 list-disc pl-5 text-slate-700">
              {scene.text.map((line) => <li key={line}>{line}</li>)}
            </ul>
          </li>
        ))}
      </ol>
    </article>
  );
}

type FlashcardsProps = {
  cards: Array<{ id?: string | null; front: string; back: string; source_pages: number[] }>;
};

function Flashcards({ cards }: FlashcardsProps) {
  const [index, setIndex] = useState(0);
  const [flipped, setFlipped] = useState(false);
  const active = cards[index];

  const move = (delta: number) => {
    setIndex((current) => (current + delta + cards.length) % cards.length);
    setFlipped(false);
  };

  useEffect(() => {
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "ArrowLeft") move(-1);
      if (event.key === "ArrowRight") move(1);
      if (event.key === " " || event.key === "Enter") {
        event.preventDefault();
        setFlipped((value) => !value);
      }
    };
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  });

  if (!active) return <p>No flashcards were generated for this package.</p>;

  return (
    <section className="max-w-2xl">
      <p className="text-sm text-slate-600">Card {index + 1} of {cards.length}</p>
      <button
        className="mt-3 min-h-52 w-full rounded-lg border border-mist bg-white p-6 text-left shadow-sm"
        onClick={() => setFlipped((value) => !value)}
        type="button"
      >
        <p className="text-sm font-semibold uppercase text-slate-500">{flipped ? "Back" : "Front"}</p>
        <p className="mt-4 text-xl font-semibold">{flipped ? active.back : active.front}</p>
        {active.source_pages.length ? <p className="mt-4 text-sm text-slate-500">Pages {active.source_pages.join(", ")}</p> : null}
      </button>
      <div className="mt-4 flex gap-3">
        <button className="rounded-md bg-mist px-4 py-2 font-semibold" onClick={() => move(-1)} type="button">Previous</button>
        <button className="rounded-md bg-sage px-4 py-2 font-semibold text-white" onClick={() => setFlipped((value) => !value)} type="button">Flip</button>
        <button className="rounded-md bg-mist px-4 py-2 font-semibold" onClick={() => move(1)} type="button">Next</button>
      </div>
    </section>
  );
}

type QuizProps = {
  accessToken?: string | null;
  guestSession?: string | null;
  packageId: string;
  questions: QuizQuestion[];
};

function Quiz({ accessToken, guestSession, packageId, questions }: QuizProps) {
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, QuizAnswerResult>>({});
  const active = questions[index];
  const answeredCount = Object.keys(answers).length;
  const complete = answeredCount === questions.length && questions.length > 0;
  const currentResult = active.id ? answers[active.id] : undefined;
  const score = useMemo(() => Object.values(answers).filter((answer) => answer.is_correct).length, [answers]);

  const startAttempt = useMutation({
    mutationFn: () => createQuizAttempt(packageId, accessToken, guestSession),
    onSuccess: setAttempt,
  });
  const submitAnswer = useMutation({
    mutationFn: async (selectedIndex: number) => {
      const activeAttempt = attempt ?? await createQuizAttempt(packageId, accessToken, guestSession);
      if (!attempt) setAttempt(activeAttempt);
      if (!active.id) throw new Error("Question is missing an ID");
      return answerQuizQuestion(activeAttempt.id, active.id, selectedIndex, accessToken, guestSession);
    },
    onSuccess: (answer) => {
      setAnswers((current) => ({ ...current, [answer.question_id]: answer }));
    },
  });
  const finishAttempt = useMutation({
    mutationFn: () => {
      if (!attempt) throw new Error("Start the quiz before completing it");
      return completeQuizAttempt(attempt.id, accessToken, guestSession);
    },
  });

  if (!active) return <p>No quiz questions were generated for this package.</p>;

  return (
    <section className="max-w-3xl">
      <div className="flex items-center justify-between gap-3">
        <p className="text-sm text-slate-600">Question {index + 1} of {questions.length}</p>
        <p className="text-sm font-semibold">Score {score}/{questions.length}</p>
      </div>
      {!attempt ? (
        <button
          className="mt-4 rounded-md bg-sage px-4 py-2 font-semibold text-white"
          disabled={startAttempt.isPending}
          onClick={() => startAttempt.mutate()}
          type="button"
        >
          {startAttempt.isPending ? "Starting..." : "Start quiz"}
        </button>
      ) : null}
      <div className="mt-4 rounded-lg border border-mist bg-white p-5">
        <h2 className="text-xl font-semibold">{active.question}</h2>
        <div className="mt-5 grid gap-3">
          {active.options.map((option, optionIndex) => {
            const isSelected = currentResult?.selected_index === optionIndex;
            const isCorrect = currentResult?.correct_index === optionIndex;
            const stateClass = currentResult
              ? isCorrect
                ? "border-green-600 bg-green-50"
                : isSelected
                  ? "border-red-600 bg-red-50"
                  : "border-mist"
              : "border-mist hover:bg-mist";
            return (
              <button
                key={option}
                className={`rounded-md border p-3 text-left ${stateClass}`}
                disabled={Boolean(currentResult) || submitAnswer.isPending}
                onClick={() => submitAnswer.mutate(optionIndex)}
                type="button"
              >
                {option}
              </button>
            );
          })}
        </div>
        {currentResult ? (
          <p className="mt-4 text-sm text-slate-700">
            <strong>{currentResult.is_correct ? "Correct." : "Not quite."}</strong> {currentResult.explanation}
          </p>
        ) : null}
        {submitAnswer.error ? <p className="mt-4 text-sm text-red-700">{submitAnswer.error.message}</p> : null}
      </div>
      <div className="mt-4 flex flex-wrap gap-3">
        <button className="rounded-md bg-mist px-4 py-2 font-semibold" disabled={index === 0} onClick={() => setIndex(index - 1)} type="button">
          Previous
        </button>
        <button className="rounded-md bg-mist px-4 py-2 font-semibold" disabled={index === questions.length - 1} onClick={() => setIndex(index + 1)} type="button">
          Next
        </button>
        {complete ? (
          <button
            className="rounded-md bg-ink px-4 py-2 font-semibold text-white"
            disabled={finishAttempt.isPending || Boolean(finishAttempt.data)}
            onClick={() => finishAttempt.mutate()}
            type="button"
          >
            {finishAttempt.data ? `Completed ${finishAttempt.data.score}/${finishAttempt.data.total}` : "Complete quiz"}
          </button>
        ) : null}
      </div>
      {finishAttempt.error ? <p className="mt-4 text-sm text-red-700">{finishAttempt.error.message}</p> : null}
    </section>
  );
}
