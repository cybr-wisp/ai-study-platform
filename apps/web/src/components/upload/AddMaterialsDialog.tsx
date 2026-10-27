"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { ApiError, uploadDocument } from "../../lib/api";
import type { Course } from "../study/types";
import styles from "./AddMaterialsDialog.module.css";

const ACCEPTED_TYPES = ".pdf,.pptx,.docx,.txt,.md";

interface AddMaterialsDialogProps {
  open: boolean;
  courses: Course[];
  onClose: () => void;
}

function uploadErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 409) return "This file was already uploaded to that course.";
    if (err.status === 413) return "That file is larger than the 50 MB limit.";
    if (err.status === 415) return "Unsupported file type. Use PDF, PPTX, DOCX, TXT or MD.";
  }
  return "Could not upload the file. Please try again.";
}

// The student picks the course for now. Once uploads are classified into
// courses automatically, the course select can go away.
export default function AddMaterialsDialog({
  open,
  courses,
  onClose,
}: AddMaterialsDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [courseId, setCourseId] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [uploadedName, setUploadedName] = useState<string | null>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      setCourseId(courses[0] ? String(courses[0].id) : "");
      setFile(null);
      setError(null);
      setUploadedName(null);
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open, courses]);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file || !courseId) return;
    setSubmitting(true);
    setError(null);
    try {
      const doc = await uploadDocument({ courseId: Number(courseId), file });
      setUploadedName(doc.original_filename);
    } catch (err) {
      setError(uploadErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <dialog
      ref={dialogRef}
      className={styles.dialog}
      aria-labelledby="add-materials-title"
      onClose={onClose}
    >
      <h2 id="add-materials-title" className={styles.title}>
        Add course materials
      </h2>

      {uploadedName ? (
        <div>
          <p className={styles.success} role="status">
            Uploaded {uploadedName}.
          </p>
          <div className={styles.actions}>
            <button type="button" className={styles.button} onClick={onClose}>
              Done
            </button>
          </div>
        </div>
      ) : courses.length === 0 ? (
        <div>
          <p className={styles.error}>Create a course before adding materials.</p>
          <div className={styles.actions}>
            <button type="button" className={styles.button} onClick={onClose}>
              Close
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <label className={styles.field}>
            Course
            <select
              className={styles.input}
              value={courseId}
              required
              onChange={(e) => setCourseId(e.target.value)}
            >
              {courses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.title}
                </option>
              ))}
            </select>
          </label>
          <label className={styles.field}>
            File (PDF, PPTX, DOCX, TXT or MD, up to 50 MB)
            <input
              className={styles.input}
              type="file"
              accept={ACCEPTED_TYPES}
              required
              onChange={(e) => setFile(e.target.files?.[0] ?? null)}
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
              disabled={submitting || !file}
            >
              {submitting ? "Uploading…" : "Upload"}
            </button>
          </div>
        </form>
      )}
    </dialog>
  );
}
