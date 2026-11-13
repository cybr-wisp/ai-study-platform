"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ApiError, getCourse, getStudyKit, listCourseDocuments } from "../../lib/api";
import styles from "./StudyKitHome.module.css";
import type { Course, Document, StudyKit, StudyKitStatus } from "./types";

interface Mode {
  slug: string;
  title: string;
  /** What the mode offers, or null when the kit has nothing for it yet. */
  detail: (kit: StudyKit) => string | null;
}

const MODES: Mode[] = [
  {
    slug: "summary",
    title: "Summary",
    detail: (kit) => (kit.summary ? "Read the key points" : null),
  },
  {
    slug: "study-guide",
    title: "Study Guide",
    detail: (kit) => (kit.study_guide ? "Work through the material" : null),
  },
  {
    slug: "flashcards",
    title: "Flashcards",
    detail: (kit) =>
      kit.flashcard_count > 0
        ? `${kit.flashcard_count} ${kit.flashcard_count === 1 ? "card" : "cards"}`
        : null,
  },
  {
    slug: "smart-study",
    title: "Smart Study",
    detail: (kit) => (kit.flashcard_count > 0 ? "Review what you're weakest on" : null),
  },
  {
    slug: "practice-test",
    title: "Practice Test",
    // The API can't list a kit's practice tests yet (no study_kit filter).
    detail: () => null,
  },
];

const STATUS_MESSAGES: Record<Exclude<StudyKitStatus, "ready">, string> = {
  pending: "This study kit is waiting to be generated.",
  generating: "This study kit is being generated. Check back soon.",
  failed: "We couldn't generate this study kit.",
};

const DOCUMENT_STATUS_LABELS: Record<Document["status"], string> = {
  uploaded: "Uploaded",
  queued: "Queued",
  processing: "Processing",
  processed: "Processed",
  failed: "Failed",
};

interface StudyKitHomeProps {
  kitId: number;
}

export default function StudyKitHome({ kitId }: StudyKitHomeProps) {
  const [kit, setKit] = useState<StudyKit | null>(null);
  const [course, setCourse] = useState<Course | null>(null);
  const [documents, setDocuments] = useState<Document[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const k = await getStudyKit(kitId);
        const [c, docs] = await Promise.all([
          getCourse(k.course),
          listCourseDocuments(k.course),
        ]);
        if (cancelled) return;
        const ids = new Set(k.documents);
        setKit(k);
        setCourse(c);
        setDocuments(docs.filter((doc) => ids.has(doc.id)));
      } catch (err) {
        if (cancelled) return;
        setError(
          err instanceof ApiError && err.status === 404
            ? "This study kit doesn't exist."
            : "Could not load this study kit. Please try again.",
        );
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [kitId]);

  if (error || !kit) {
    return (
      <main className={styles.page}>
        <Link href="/dashboard" className={styles.back}>
          ← Dashboard
        </Link>
        <p className={styles.empty} role={error ? "alert" : undefined}>
          {error ?? "Loading…"}
        </p>
      </main>
    );
  }

  const progress = Math.round(Math.max(0, Math.min(100, kit.mastery_percent ?? 0)));
  const ready = kit.status === "ready";

  return (
    <main className={styles.page}>
      <Link href="/dashboard" className={styles.back}>
        ← Dashboard
      </Link>

      <header className={`${styles.header} ${styles[kit.kit_type]}`}>
        {course && <span className={styles.course}>{course.title}</span>}
        <h1 className={styles.title}>{kit.title}</h1>
        <span className={styles.type}>
          {kit.kit_type === "lecture" ? "Lecture" : "Tutorial"}
        </span>
        <div className={styles.progress}>
          <div
            className={styles.track}
            role="progressbar"
            aria-label={`${kit.title} mastery`}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={progress}
          >
            <div className={styles.fill} style={{ width: `${progress}%` }} />
          </div>
          <span className={styles.percent}>{progress}% mastered</span>
        </div>
      </header>

      {kit.status !== "ready" && (
        <p
          className={`${styles.status} ${kit.status === "failed" ? styles.failed : ""}`}
          role="status"
        >
          {STATUS_MESSAGES[kit.status]}
        </p>
      )}

      <section className={styles.section}>
        <h2 className={styles.heading}>Study</h2>
        <div className={styles.modes}>
          {MODES.map((mode) => {
            const detail = ready ? mode.detail(kit) : null;
            return detail ? (
              <Link
                key={mode.slug}
                href={`/study-kits/${kit.id}/${mode.slug}`}
                className={styles.mode}
              >
                <span className={styles.modeTitle}>{mode.title}</span>
                <span className={styles.modeDetail}>{detail}</span>
              </Link>
            ) : (
              <div
                key={mode.slug}
                className={`${styles.mode} ${styles.disabled}`}
                aria-disabled="true"
              >
                <span className={styles.modeTitle}>{mode.title}</span>
                <span className={styles.modeDetail}>Not available yet</span>
              </div>
            );
          })}
        </div>
      </section>

      <section className={styles.section}>
        <h2 className={styles.heading}>Source materials</h2>
        {documents.length === 0 ? (
          <p className={styles.empty}>No source materials linked to this kit.</p>
        ) : (
          <ul className={styles.documents}>
            {documents.map((doc) => (
              <li key={doc.id} className={styles.document}>
                <span className={styles.docName}>{doc.original_filename}</span>
                <span className={`${styles.docStatus} ${styles[doc.status]}`}>
                  {DOCUMENT_STATUS_LABELS[doc.status]}
                </span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  );
}
