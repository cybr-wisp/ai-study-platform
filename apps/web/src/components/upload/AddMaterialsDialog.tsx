"use client";

import { useEffect, useRef, useState } from "react";
import type { DragEvent, FormEvent } from "react";
import { ApiError, createCourse, uploadDocument } from "../../lib/api";
import type { Course } from "../study/types";
import dialogStyles from "../layout/Dialog.module.css";
import styles from "./AddMaterialsDialog.module.css";

const ACCEPTED_EXTENSIONS = ["pdf", "pptx", "docx", "txt", "md"];
const MAX_BYTES = 50 * 1024 * 1024;
const NEW_COURSE = "new";

interface AddMaterialsDialogProps {
  open: boolean;
  courses: Course[];
  onClose: () => void;
  /** Called after anything changed server-side (a course was created). */
  onChanged: () => void;
}

function fileError(file: File): string | null {
  const ext = file.name.split(".").pop()?.toLowerCase() ?? "";
  if (!ACCEPTED_EXTENSIONS.includes(ext)) {
    return "Unsupported file type. Use PDF, PPTX, DOCX, TXT or MD.";
  }
  if (file.size > MAX_BYTES) return "That file is larger than the 50 MB limit.";
  return null;
}

function uploadErrorMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 409) return "This file was already uploaded to that course.";
    if (err.status === 413) return "That file is larger than the 50 MB limit.";
    if (err.status === 415) return "Unsupported file type. Use PDF, PPTX, DOCX, TXT or MD.";
  }
  return "Could not upload the file. Please try again.";
}

// The student picks (or creates) the course for now. Once uploads are
// classified into courses automatically, the course step can go away.
export default function AddMaterialsDialog({
  open,
  courses,
  onClose,
  onChanged,
}: AddMaterialsDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [dragging, setDragging] = useState(false);
  const [courseChoice, setCourseChoice] = useState(NEW_COURSE);
  const [newCourseTitle, setNewCourseTitle] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [uploadedName, setUploadedName] = useState<string | null>(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (open && !dialog.open) {
      setFile(null);
      setCourseChoice(courses[0] ? String(courses[0].id) : NEW_COURSE);
      setNewCourseTitle("");
      setError(null);
      setUploadedName(null);
      dialog.showModal();
    } else if (!open && dialog.open) {
      dialog.close();
    }
  }, [open, courses]);

  function pickFile(picked: File | undefined) {
    if (!picked) return;
    const problem = fileError(picked);
    setError(problem);
    setFile(problem ? null : picked);
  }

  function handleDrop(e: DragEvent) {
    e.preventDefault();
    setDragging(false);
    pickFile(e.dataTransfer.files[0]);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!file) return;
    setSubmitting(true);
    setError(null);
    try {
      let courseId = Number(courseChoice);
      if (courseChoice === NEW_COURSE) {
        const course = await createCourse({ title: newCourseTitle.trim() });
        courseId = course.id;
        // If the upload below fails, a retry reuses this course.
        setCourseChoice(String(course.id));
        onChanged();
      }
      const doc = await uploadDocument({ courseId, file });
      setUploadedName(doc.original_filename);
    } catch (err) {
      setError(uploadErrorMessage(err));
    } finally {
      setSubmitting(false);
    }
  }

  const needsTitle = courseChoice === NEW_COURSE && !newCourseTitle.trim();

  return (
    <dialog
      ref={dialogRef}
      className={dialogStyles.dialog}
      aria-labelledby="add-materials-title"
      onClose={onClose}
    >
      <h2 id="add-materials-title" className={dialogStyles.title}>
        Add course materials
      </h2>

      {uploadedName ? (
        <div>
          <p className={styles.success} role="status">
            Uploaded {uploadedName}.
          </p>
          <div className={dialogStyles.actions}>
            <button type="button" className={dialogStyles.button} onClick={onClose}>
              Done
            </button>
          </div>
        </div>
      ) : (
        <form onSubmit={handleSubmit}>
          <button
            type="button"
            className={`${styles.dropzone} ${dragging ? styles.dragging : ""}`}
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => {
              e.preventDefault();
              setDragging(true);
            }}
            onDragLeave={() => setDragging(false)}
            onDrop={handleDrop}
          >
            {file ? (
              <>
                <span className={styles.fileName}>{file.name}</span>
                <span className={styles.hint}>Click or drop to replace</span>
              </>
            ) : (
              <>
                <span className={styles.dropTitle}>
                  Drag a file here or click to upload
                </span>
                <span className={styles.hint}>PDF, PPTX, DOCX, TXT or MD, up to 50 MB</span>
              </>
            )}
          </button>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_EXTENSIONS.map((ext) => `.${ext}`).join(",")}
            hidden
            onChange={(e) => {
              pickFile(e.target.files?.[0]);
              e.target.value = "";
            }}
          />

          <label className={dialogStyles.field}>
            Course
            <select
              className={dialogStyles.input}
              value={courseChoice}
              onChange={(e) => setCourseChoice(e.target.value)}
            >
              {courses.map((course) => (
                <option key={course.id} value={course.id}>
                  {course.title}
                </option>
              ))}
              <option value={NEW_COURSE}>+ New course…</option>
            </select>
          </label>
          {courseChoice === NEW_COURSE && (
            <label className={dialogStyles.field}>
              New course name
              <input
                className={dialogStyles.input}
                value={newCourseTitle}
                maxLength={200}
                required
                onChange={(e) => setNewCourseTitle(e.target.value)}
              />
            </label>
          )}

          {error && (
            <p className={dialogStyles.error} role="alert">
              {error}
            </p>
          )}
          <div className={dialogStyles.actions}>
            <button type="button" className={dialogStyles.button} onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className={`${dialogStyles.button} ${dialogStyles.primary}`}
              disabled={submitting || !file || needsTitle}
            >
              {submitting ? "Uploading…" : "Upload"}
            </button>
          </div>
        </form>
      )}
    </dialog>
  );
}
