"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { createCourse } from "../../lib/api";
import type { Course } from "../study/types";
import styles from "./AddCourseDialog.module.css";

interface AddCourseDialogProps {
  open: boolean;
  onClose: () => void;
  onCreated: (course: Course) => void;
}

// For now this only creates a course. Once uploaded materials are classified
// into courses automatically, the material upload step belongs in this dialog.
export default function AddCourseDialog({
  open,
  onClose,
  onCreated,
}: AddCourseDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [title, setTitle] = useState("");
  const [code, setCode] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      setTitle("");
      setCode("");
      setError(null);
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const course = await createCourse({
        title: title.trim(),
        ...(code.trim() && { code: code.trim() }),
      });
      onCreated(course);
      onClose();
    } catch {
      setError("Could not create the course. Check the details and try again.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className={styles.dialog}
      aria-labelledby="add-course-title"
      onClose={onClose}
    >
      <form onSubmit={handleSubmit}>
        <h2 id="add-course-title" className={styles.title}>
          Add course
        </h2>
        <label className={styles.field}>
          Course name
          <input
            className={styles.input}
            value={title}
            maxLength={200}
            required
            autoFocus
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>
        <label className={styles.field}>
          Course code (optional)
          <input
            className={styles.input}
            value={code}
            maxLength={32}
            onChange={(e) => setCode(e.target.value)}
          />
        </label>
        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}
        <div className={styles.actions}>
          <button type="button" className={styles.button} onClick={onClose}>
            Cancel
          </button>
          <button
            type="submit"
            className={`${styles.button} ${styles.primary}`}
            disabled={submitting || !title.trim()}
          >
            {submitting ? "Adding…" : "Add course"}
          </button>
        </div>
      </form>
    </dialog>
  );
}
