import { useEffect, useMemo, useRef, useState } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";
import { Pause, Play } from "lucide-react";

import {
  answerQuizQuestion,
  completeQuizAttempt,
  createQuizAttempt,
  getVideoUrl,
  getPackage,
  retryVideo,
  type QuizAnswerResult,
  type QuizAttempt,
  type QuizQuestion,
} from "../lib/api";
import { useAuth } from "../lib/auth";
import { initialsFor } from "../lib/initials";

const tabs = ["Summary", "Topics", "Flashcards", "Quiz", "Video"] as const;
type Tab = (typeof tabs)[number];

export function LearningPackage() {
  const { packageId = "" } = useParams();
  const [tab, setTab] = useState<Tab>("Summary");
  const { session, user, signOut } = useAuth();
  const displayName = (user?.user_metadata?.display_name as string | undefined) || user?.email || "";
  const guestSession = localStorage.getItem("smartlearn_guest_session");
  const result = useQuery({
    queryKey: ["package", packageId, session?.access_token, guestSession],
    queryFn: () => getPackage(packageId, session?.access_token, guestSession),
    enabled: Boolean(packageId),
    refetchInterval: (query) => {
      const status = query.state.data?.video_status;
      return status && !["completed", "partial_success", "failed"].includes(status) ? 1500 : false;
    },
  });

  useEffect(() => {
    if (tab === "Video") {
      result.refetch();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  if (result.isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center text-muted">
        <p>Loading package...</p>
      </div>
    );
  }
  if (result.error || !result.data) {
    return (
      <div className="flex min-h-screen items-center justify-center text-warn-ink">
        <p role="alert">Unable to load this learning package.</p>
      </div>
    );
  }

  const content = result.data.content;

  return (
    <div className="min-h-screen bg-paper text-ink">
      <header className="sticky top-0 z-20 border-b border-line bg-paper-raised">
        <div className="flex flex-wrap items-center justify-between gap-3 px-4 py-[13px] sm:px-[28px]">
          <div className="flex min-w-0 flex-1 items-center gap-3">
            <Link to="/" className="shrink-0 whitespace-nowrap font-mono text-[11px] uppercase tracking-[0.14em] text-muted hover:text-ink">
              ← Library
            </Link>
            <span className="h-[18px] w-px shrink-0 bg-line" aria-hidden="true" />
            <p className="min-w-0 truncate text-sm font-medium" style={{ maxWidth: "42ch" }}>
              {content.title}
            </p>
          </div>
          {user ? (
            <button
              type="button"
              onClick={signOut}
              className="flex h-[30px] w-[30px] shrink-0 items-center justify-center rounded-full bg-ink text-[12px] font-semibold text-paper-raised"
              title="Sign out"
              aria-label="Sign out"
            >
              {initialsFor(displayName)}
            </button>
          ) : null}
        </div>
        <div className="flex gap-1 overflow-x-auto px-2 sm:px-6" role="tablist" aria-label="Learning package sections">
          {tabs.map((item) => (
            <button
              key={item}
              role="tab"
              aria-selected={tab === item}
              className={`whitespace-nowrap border-b-2 px-4 pb-[13px] pt-3 text-sm transition-colors ${
                tab === item ? "border-ink font-semibold text-ink" : "border-transparent font-normal text-muted hover:text-ink"
              }`}
              onClick={() => setTab(item)}
            >
              {item}
            </button>
          ))}
        </div>
      </header>
      <div>
        {tab === "Summary" && (
          <Summary
            content={content}
            onQuizMe={() => setTab("Quiz")}
            onStudyCards={() => setTab("Flashcards")}
          />
        )}
        {tab === "Topics" && <Topics topics={content.topics} />}
        {tab === "Flashcards" && <Flashcards cards={content.flashcards} />}
        {tab === "Quiz" && (
          <Quiz
            accessToken={session?.access_token}
            guestSession={guestSession}
            packageId={packageId}
            questions={content.quiz}
            onDrillMisses={() => setTab("Flashcards")}
          />
        )}
        <div className={tab === "Video" ? undefined : "hidden"}>
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
            narrationAvailable={result.data.narration_available}
            onRetry={() => void result.refetch()}
          />
        </div>
      </div>
    </div>
  );
}

// ---------- Summary ----------

type SummaryProps = {
  content: {
    title: string;
    summary: {
      overview: string;
      key_points: Array<{ heading: string; explanation: string; source_pages: number[] }>;
      definitions: Array<{ term: string; definition: string; example?: string | null; source_pages: number[] }>;
    };
    flashcards: unknown[];
    quiz: unknown[];
  };
  onQuizMe: () => void;
  onStudyCards: () => void;
};

function Summary({ content, onQuizMe, onStudyCards }: SummaryProps) {
  const sectionIds = useMemo(
    () => content.summary.key_points.map((_, index) => `takeaway-${index}`).concat(["definitions"]),
    [content.summary.key_points],
  );
  const [activeId, setActiveId] = useState(sectionIds[0]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries.find((entry) => entry.isIntersecting);
        if (visible) setActiveId(visible.target.id);
      },
      { rootMargin: "-120px 0px -70% 0px" },
    );
    sectionIds.forEach((id) => {
      const el = document.getElementById(id);
      if (el) observer.observe(el);
    });
    return () => observer.disconnect();
  }, [sectionIds]);

  return (
    <div className="mx-auto flex max-w-[1120px] flex-wrap items-start gap-10 px-4 pb-20 pt-11 sm:px-[28px]">
      <aside className="sticky top-[112px] hidden flex-[1_1_210px] max-w-[250px] lg:block">
        <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted">On this page</p>
        <nav className="mt-2 grid gap-[2px]">
          {content.summary.key_points.map((point, index) => (
            <a
              key={point.heading}
              href={`#takeaway-${index}`}
              className={`rounded-lg px-[11px] py-2 text-[13px] transition-colors ${
                activeId === `takeaway-${index}` ? "bg-fill-sunken font-semibold text-ink" : "font-normal text-muted hover:text-ink"
              }`}
            >
              {point.heading}
            </a>
          ))}
          <a
            href="#definitions"
            className={`rounded-lg px-[11px] py-2 text-[13px] transition-colors ${
              activeId === "definitions" ? "bg-fill-sunken font-semibold text-ink" : "font-normal text-muted hover:text-ink"
            }`}
          >
            Key terms
          </a>
        </nav>
      </aside>
      <article className="min-w-0 flex-[999_1_460px]">
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-rust">Summary</p>
        <h1 className="mt-3 text-balance font-serif text-[clamp(34px,4.6vw,54px)] leading-[1.04] tracking-[-0.015em]">
          {content.title}
        </h1>
        <p className="mb-9 mt-5 max-w-[62ch] text-[19px] leading-[1.6] text-ink-soft">{content.summary.overview}</p>

        <div className="mb-11 grid gap-px overflow-hidden rounded-card border border-line bg-line">
          {content.summary.key_points.map((point, index) => (
            <div id={`takeaway-${index}`} key={point.heading} className="flex scroll-mt-32 gap-[18px] bg-paper-raised px-[22px] py-5">
              <span className="w-[26px] shrink-0 font-serif text-[26px] text-rust">{index + 1}</span>
              <div>
                <p className="text-[16px] font-medium leading-[1.55]">
                  {point.heading}. {point.explanation}
                </p>
                {point.source_pages.length ? (
                  <p className="mt-2 font-mono text-[11px] text-muted">
                    {point.source_pages.map((page) => `p. ${page}`).join(", ")}
                  </p>
                ) : null}
              </div>
            </div>
          ))}
        </div>

        {content.summary.definitions.length ? (
          <section id="definitions" className="scroll-mt-32 border-t border-line py-[30px]">
            <h2 className="font-serif text-[clamp(24px,3vw,32px)]">Key terms</h2>
            <dl className="mt-4 grid gap-3 sm:grid-cols-2">
              {content.summary.definitions.map((item) => (
                <div key={item.term} className="rounded-[14px] border border-line bg-paper-raised p-4">
                  <dt className="font-serif text-[18px]">{item.term}</dt>
                  <dd className="mt-1 text-[15px] leading-[1.55] text-ink-soft">{item.definition}</dd>
                  {item.example ? (
                    <dd className="mt-2 text-sm text-muted">
                      <strong className="text-ink-softer">Example:</strong> {item.example}
                    </dd>
                  ) : null}
                </div>
              ))}
            </dl>
          </section>
        ) : null}

        <div className="flex flex-wrap gap-[14px] border-t border-line pt-[34px]">
          {content.quiz.length ? (
            <button
              type="button"
              onClick={onQuizMe}
              className="rounded-full bg-ink px-6 py-[14px] text-[15px] font-semibold text-paper-raised transition-colors hover:bg-rust"
            >
              Quiz me on this →
            </button>
          ) : null}
          {content.flashcards.length ? (
            <button
              type="button"
              onClick={onStudyCards}
              className="rounded-full border border-line-strong px-6 py-[14px] text-[15px] font-medium transition-colors hover:border-ink"
            >
              Study {content.flashcards.length} cards
            </button>
          ) : null}
        </div>
      </article>
    </div>
  );
}

// ---------- Topics ----------

type TopicsProps = {
  topics: Array<{
    name: string;
    description: string;
    source_pages: number[];
    further_learning: Array<{
      title: string;
      resource_type: string;
      search_query: string;
      why_it_helps: string;
    }>;
  }>;
};

function Topics({ topics }: TopicsProps) {
  return (
    <section className="mx-auto max-w-[1120px] space-y-4 px-4 pb-20 pt-11 sm:px-[28px]">
      <div>
        <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-rust">Topics</p>
        <h1 className="mt-2 font-serif text-[clamp(28px,3.6vw,40px)]">Topics and further learning</h1>
        <p className="mt-1 text-muted">Every topic in the material, plus focused suggestions for going deeper.</p>
      </div>
      {topics.map((topic) => (
        <article key={topic.name} className="rounded-card border border-line bg-paper-raised p-5">
          <div className="flex flex-wrap items-baseline justify-between gap-2">
            <h3 className="font-serif text-[20px]">{topic.name}</h3>
            {topic.source_pages.length ? (
              <span className="font-mono text-[11px] text-muted">Pages {topic.source_pages.join(", ")}</span>
            ) : null}
          </div>
          <p className="mt-1 text-[15px] leading-[1.6] text-ink-soft">{topic.description}</p>
          <ul className="mt-4 grid gap-3 sm:grid-cols-2">
            {topic.further_learning.map((resource) => (
              <li key={`${resource.title}-${resource.search_query}`} className="rounded-[12px] bg-fill-sunken p-3">
                <span className="font-mono text-[10px] uppercase tracking-[0.1em] text-muted">{resource.resource_type}</span>
                <a
                  className="mt-1 block font-medium text-rust underline-offset-2 hover:underline"
                  href={`https://www.google.com/search?q=${encodeURIComponent(resource.search_query)}`}
                  rel="noreferrer"
                  target="_blank"
                >
                  {resource.title}
                </a>
                <p className="mt-1 text-sm text-ink-softer">{resource.why_it_helps}</p>
              </li>
            ))}
          </ul>
        </article>
      ))}
    </section>
  );
}

// ---------- Flashcards ----------

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

  if (!active) {
    return (
      <div className="mx-auto max-w-[760px] px-4 py-20 sm:px-[28px]">
        <p className="text-muted">No flashcards were generated for this package.</p>
      </div>
    );
  }

  return (
    <section className="mx-auto max-w-[760px] px-4 pb-20 pt-11 sm:px-[28px]">
      <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">
        Card {index + 1} of {cards.length}
      </p>
      <button
        className={`mt-4 flex min-h-[260px] w-full flex-col justify-between gap-[22px] rounded-xl2 border p-7 text-left shadow-flashcard transition-colors duration-200 ${
          flipped ? "border-line-strong bg-paper-input" : "border-line bg-paper-raised"
        }`}
        onClick={() => setFlipped((value) => !value)}
        type="button"
      >
        <div className="flex items-center justify-between">
          <span className="font-mono text-[10px] uppercase tracking-[0.16em] text-muted">{flipped ? "Answer" : "Prompt"}</span>
          {active.source_pages.length ? (
            <span className="font-mono text-[10px] text-muted">p. {active.source_pages.join(", ")}</span>
          ) : null}
        </div>
        <p className="text-pretty font-serif text-[clamp(24px,3.4vw,34px)] leading-[1.22]">
          {flipped ? active.back : active.front}
        </p>
        <p className="font-mono text-[11px] text-muted">Tap to flip</p>
      </button>
      <div className="mt-4 flex gap-3">
        <button className="rounded-[13px] bg-fill-sunken px-4 py-3 text-sm font-semibold" onClick={() => move(-1)} type="button">
          Previous
        </button>
        <button
          className="rounded-[13px] bg-ink px-4 py-3 text-sm font-semibold text-paper-raised"
          onClick={() => setFlipped((value) => !value)}
          type="button"
        >
          Flip
        </button>
        <button className="rounded-[13px] bg-fill-sunken px-4 py-3 text-sm font-semibold" onClick={() => move(1)} type="button">
          Next
        </button>
      </div>
      <div className="mt-8 flex flex-wrap gap-[22px] font-mono text-[11px] text-muted">
        <span>{cards.length} cards in deck</span>
        <span>Space to flip · ←/→ to move</span>
      </div>
    </section>
  );
}

// ---------- Quiz ----------

type QuizProps = {
  accessToken?: string | null;
  guestSession?: string | null;
  packageId: string;
  questions: QuizQuestion[];
  onDrillMisses: () => void;
};

const letters = ["A", "B", "C", "D", "E", "F"];

function Quiz({ accessToken, guestSession, packageId, questions, onDrillMisses }: QuizProps) {
  const [attempt, setAttempt] = useState<QuizAttempt | null>(null);
  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, QuizAnswerResult>>({});
  const active = questions[index];
  const answeredCount = Object.keys(answers).length;
  const complete = answeredCount === questions.length && questions.length > 0;
  const currentResult = active?.id ? answers[active.id] : undefined;
  const score = useMemo(() => Object.values(answers).filter((answer) => answer.is_correct).length, [answers]);
  const isLast = index === questions.length - 1;

  const submitAnswer = useMutation({
    mutationFn: async (selectedIndex: number) => {
      const activeAttempt = attempt ?? (await createQuizAttempt(packageId, accessToken, guestSession));
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

  const retake = () => {
    setAttempt(null);
    setIndex(0);
    setAnswers({});
    finishAttempt.reset();
  };

  if (!active) {
    return (
      <div className="mx-auto max-w-[760px] px-4 py-20 sm:px-[28px]">
        <p className="text-muted">No quiz questions were generated for this package.</p>
      </div>
    );
  }

  if (finishAttempt.data) {
    const total = finishAttempt.data.total || questions.length;
    const note =
      score === total
        ? "Clean sweep. Great grasp of this document."
        : score >= total - 1
          ? "Strong work. One gap worth reviewing."
          : "A few gaps worth reviewing with the flashcards.";
    return (
      <section className="mx-auto max-w-[760px] px-4 pb-20 pt-11 sm:px-[28px]">
        <div className="animate-rise rounded-xl2 bg-ink px-[34px] py-10 text-paper-raised">
          <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-rust-light">Quiz complete</p>
          <div className="mt-3 flex items-baseline gap-3">
            <span className="font-serif text-[clamp(64px,11vw,104px)] leading-[0.85]">
              {score}/{total}
            </span>
            <span className="text-[17px] text-dark-body">correct</span>
          </div>
          <p className="mt-5 max-w-[46ch] text-[17px] leading-[1.6] text-dark-body">{note}</p>
          <div className="mt-8 flex flex-wrap gap-3">
            <button
              type="button"
              onClick={onDrillMisses}
              className="rounded-full bg-paper-raised px-6 py-[13px] text-sm font-semibold text-ink transition-colors hover:bg-rust-light"
            >
              Drill the misses as cards
            </button>
            <button
              type="button"
              onClick={retake}
              className="rounded-full border border-ink-line-2 px-6 py-[13px] text-sm font-semibold text-paper-raised transition-colors hover:border-paper-raised"
            >
              Retake
            </button>
          </div>
        </div>
      </section>
    );
  }

  return (
    <section className="mx-auto max-w-[760px] px-4 pb-20 pt-11 sm:px-[28px]">
      <div className="mb-[26px] flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="font-mono text-[11px] uppercase tracking-[0.16em] text-muted">
            Question {index + 1} of {questions.length}
          </p>
          <div className="mt-2 flex gap-1">
            {questions.map((question, pipIndex) => (
              <span
                key={question.id ?? pipIndex}
                className={`h-1 w-[22px] rounded-full ${
                  question.id && answers[question.id]
                    ? "bg-rust"
                    : pipIndex === index
                      ? "bg-ink"
                      : "bg-line"
                }`}
              />
            ))}
          </div>
        </div>
        <p className="text-sm font-semibold">
          Score {score}/{questions.length}
        </p>
      </div>

      <div className="rounded-xl2 border border-line bg-paper-raised p-[32px]">
        {active.source_pages.length ? (
          <p className="font-mono text-[11px] text-muted">{active.source_pages.map((p) => `p. ${p}`).join(", ")}</p>
        ) : null}
        <h2 className="mb-[30px] mt-[14px] text-balance font-serif text-[clamp(26px,3.6vw,38px)] leading-[1.15]">
          {active.question}
        </h2>
        <div className="grid gap-[10px]">
          {active.options.map((option, optionIndex) => {
            const isSelected = currentResult?.selected_index === optionIndex;
            const isCorrect = currentResult?.correct_index === optionIndex;
            const stateClass = currentResult
              ? isCorrect
                ? "border-success-border bg-success-bg"
                : isSelected
                  ? "border-warn-border bg-warn-bg"
                  : "border-line text-dark-muted"
              : "border-line bg-paper-input hover:border-line-strong";
            return (
              <button
                key={option}
                className={`flex items-center gap-[14px] rounded-[13px] border p-4 text-left text-[16px] transition-colors ${stateClass}`}
                disabled={Boolean(currentResult) || submitAnswer.isPending}
                onClick={() => submitAnswer.mutate(optionIndex)}
                type="button"
              >
                <span className="flex h-[22px] w-[22px] shrink-0 items-center justify-center rounded-[6px] bg-fill-sunken font-mono text-[11px] text-muted">
                  {letters[optionIndex] ?? optionIndex + 1}
                </span>
                <span className="flex-1">{option}</span>
                {currentResult ? (
                  <span className="font-mono text-[11px] text-muted">
                    {isCorrect ? "Correct" : isSelected ? "Your pick" : ""}
                  </span>
                ) : null}
              </button>
            );
          })}
        </div>
        {submitAnswer.error ? <p className="mt-4 text-sm text-warn-ink">{submitAnswer.error.message}</p> : null}

        {currentResult ? (
          <div
            className={`animate-rise mt-[26px] rounded-[14px] p-[22px] ${
              currentResult.is_correct ? "bg-success-bg" : "bg-warn-bg"
            }`}
          >
            <p
              className={`font-mono text-[11px] uppercase tracking-[0.16em] ${
                currentResult.is_correct ? "text-success-ink" : "text-warn-ink"
              }`}
            >
              {currentResult.is_correct ? "Correct" : "Not quite"}
            </p>
            <p className="mt-2 text-[16px] leading-[1.6] text-[#2A281F]">{currentResult.explanation}</p>
            <div className="mt-4 flex items-center gap-4">
              <button
                type="button"
                className="rounded-full bg-ink px-6 py-3 text-sm font-semibold text-paper-raised transition-colors hover:bg-rust"
                onClick={() => (isLast ? finishAttempt.mutate() : setIndex(index + 1))}
                disabled={isLast && finishAttempt.isPending}
              >
                {isLast ? (finishAttempt.isPending ? "Scoring..." : "See results") : "Next question"}
              </button>
            </div>
            {finishAttempt.error ? <p className="mt-3 text-sm text-warn-ink">{finishAttempt.error.message}</p> : null}
          </div>
        ) : null}
      </div>

      {!complete ? (
        <div className="mt-4 flex flex-wrap gap-3">
          <button
            className="rounded-full bg-fill-sunken px-4 py-2 text-sm font-semibold disabled:opacity-50"
            disabled={index === 0}
            onClick={() => setIndex(index - 1)}
            type="button"
          >
            Previous
          </button>
          <button
            className="rounded-full bg-fill-sunken px-4 py-2 text-sm font-semibold disabled:opacity-50"
            disabled={index === questions.length - 1}
            onClick={() => setIndex(index + 1)}
            type="button"
          >
            Next
          </button>
        </div>
      ) : null}
    </section>
  );
}

// ---------- Video ----------

type VideoPlanProps = {
  accessToken?: string | null;
  guestSession?: string | null;
  packageTitle: string;
  video: {
    title: string;
    narration: string;
    scenes: Array<{
      template: string;
      heading: string;
      visual_elements: string[];
      connection_label?: string | null;
      narration: string;
      duration_seconds: number;
    }>;
  };
  videoAssetId?: string | null;
  videoStatus?: string | null;
  videoMessage?: string | null;
  videoAvailable: boolean;
  transcriptAvailable: boolean;
  narrationAvailable: boolean;
  onRetry: () => void;
};

function formatTimecode(totalSeconds: number) {
  const minutes = Math.floor(totalSeconds / 60);
  const seconds = Math.floor(totalSeconds % 60);
  return `${minutes}:${seconds.toString().padStart(2, "0")}`;
}

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
  narrationAvailable,
  onRetry,
}: VideoPlanProps) {
  const [playbackUrl, setPlaybackUrl] = useState<string | null>(null);
  const [playing, setPlaying] = useState(false);
  const videoRef = useRef<HTMLVideoElement | null>(null);

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
  const retry = useMutation({
    mutationFn: () => {
      if (!videoAssetId) throw new Error("Video asset is not ready");
      return retryVideo(videoAssetId, accessToken, guestSession);
    },
    onSuccess: () => {
      setPlaybackUrl(null);
      onRetry();
    },
  });

  const sceneStarts = useMemo(() => {
    let cumulative = 0;
    return video.scenes.map((scene) => {
      const start = cumulative;
      cumulative += scene.duration_seconds;
      return start;
    });
  }, [video.scenes]);

  const seekTo = (seconds: number) => {
    if (videoRef.current) {
      videoRef.current.currentTime = seconds;
      void videoRef.current.play();
    }
  };

  return (
    <section className="mx-auto max-w-[1000px] space-y-8 px-4 pb-20 pt-11 sm:px-[28px]">
      <div className="overflow-hidden rounded-xl2 border border-ink-line bg-ink">
        {playbackUrl ? (
          <video
            ref={videoRef}
            className="aspect-video w-full bg-black"
            controls
            playsInline
            src={playbackUrl}
            onPlay={() => setPlaying(true)}
            onPause={() => setPlaying(false)}
          >
            <track kind="captions" />
          </video>
        ) : (
          <div className="relative flex aspect-video flex-col items-center justify-center gap-4 px-6 text-center text-paper-raised">
            <p className="font-mono text-[11px] uppercase tracking-[0.18em] text-rust-light">{packageTitle}</p>
            <p className="max-w-[20ch] text-balance font-serif text-[clamp(26px,4.4vw,44px)] leading-[1.06]">{video.title}</p>
            {videoStatus ? (
              <p className="font-mono text-[12px] text-dark-muted">
                {videoStatus.replace(/_/g, " ")}
                {videoMessage ? ` · ${videoMessage}` : ""}
              </p>
            ) : null}
          </div>
        )}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-ink-line bg-ink-raised px-5 py-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              disabled={!videoAvailable}
              onClick={() => (playbackUrl ? (playing ? videoRef.current?.pause() : videoRef.current?.play()) : playback.mutate())}
              className="flex h-[42px] w-[42px] items-center justify-center rounded-full bg-paper-raised text-ink transition-colors hover:bg-rust-light disabled:cursor-not-allowed disabled:opacity-40"
              aria-label={playing ? "Pause" : "Play"}
            >
              {playing ? <Pause className="h-4 w-4" /> : <Play className="h-4 w-4" />}
            </button>
            <span className="font-mono text-[12px] text-dark-body">
              {video.scenes.length} scenes · {formatTimecode(sceneStarts.at(-1) ?? 0)} total
            </span>
          </div>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              disabled={!videoAvailable}
              onClick={() => download.mutate()}
              className="rounded-[8px] border border-ink-line px-[11px] py-[7px] font-mono text-[11px] text-dark-muted transition-colors hover:border-rust-light hover:text-rust-light disabled:cursor-not-allowed disabled:opacity-40"
            >
              Download
            </button>
            <button
              type="button"
              disabled={!transcriptAvailable}
              onClick={() => transcript.mutate()}
              className="rounded-[8px] border border-ink-line px-[11px] py-[7px] font-mono text-[11px] text-dark-muted transition-colors hover:border-rust-light hover:text-rust-light disabled:cursor-not-allowed disabled:opacity-40"
            >
              Transcript
            </button>
            {videoStatus === "failed" ? (
              <button
                type="button"
                disabled={retry.isPending}
                onClick={() => retry.mutate()}
                className="rounded-[8px] border border-warn-border px-[11px] py-[7px] font-mono text-[11px] text-warn-border"
              >
                {retry.isPending ? "Retrying..." : "Retry video"}
              </button>
            ) : null}
          </div>
        </div>
      </div>
      {playback.error ? <p className="text-sm text-warn-ink">{playback.error.message}</p> : null}
      {download.error ? <p className="text-sm text-warn-ink">{download.error.message}</p> : null}
      {transcript.error ? <p className="text-sm text-warn-ink">{transcript.error.message}</p> : null}
      {retry.error ? <p className="text-sm text-warn-ink">{retry.error.message}</p> : null}
      {videoAvailable && !narrationAvailable ? (
        <p className="font-mono text-[11px] uppercase tracking-[0.1em] text-muted">
          No narration audio for this video — read along with the script below.
        </p>
      ) : null}

      <p className="max-w-[70ch] text-[17px] leading-[1.68] text-ink-soft">{video.narration}</p>

      <div className="flex flex-wrap items-start gap-8">
        <div className="min-w-0 flex-[999_1_380px]">
          <p className="font-mono text-[10px] uppercase tracking-[0.18em] text-muted">Scenes</p>
          <div className="mt-2 grid gap-[2px]">
            {video.scenes.map((scene, index) => (
              <button
                key={`${scene.template}-${index}`}
                type="button"
                onClick={() => seekTo(sceneStarts[index])}
                disabled={!playbackUrl}
                className="flex items-baseline gap-[14px] rounded-[10px] px-[13px] py-[11px] text-left transition-colors hover:bg-paper-raised disabled:cursor-default disabled:hover:bg-transparent"
              >
                <span className="w-[38px] shrink-0 font-mono text-[11px] text-muted">{formatTimecode(sceneStarts[index])}</span>
                <span>
                  <span className="text-[15px] leading-[1.55] text-ink-softer">{scene.heading}</span>
                  <span className="block text-[13px] leading-[1.5] text-muted">{scene.narration}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
