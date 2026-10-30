"use client";

import { useEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import {
  deleteCourse,
  deleteStudyKit,
  updateCourse,
  updateStudyKit,
} from "../../lib/api";
import dialogStyles from "../layout/Dialog.module.css";
import styles from "./CourseEditDialog.module.css";
import type { Course, StudyKit, StudyKitType } from "./types";

interface KitDraft {
  id: number;
  title: string;
  kit_type: StudyKitType;
  deleted: boolean;
}

interface CourseEditDialogProps {
  /** The course being edited; the dialog is open while this is set. */
  course: Course | null;
  kits: StudyKit[];
  onClose: () => void;
  onSaved: () => void;
}

export default function CourseEditDialog({
  course,
  kits,
  onClose,
  onSaved,
}: CourseEditDialogProps) {
  const dialogRef = useRef<HTMLDialogElement>(null);
  const [title, setTitle] = useState("");
  const [drafts, setDrafts] = useState<KitDraft[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [confirmingDelete, setConfirmingDelete] = useState(false);

  // Start from fresh drafts each time a course is opened. Not keyed on kits,
  // so a background refresh doesn't wipe edits in progress.
  useEffect(() => {
    const dialog = dialogRef.current;
    if (!dialog) return;
    if (course && !dialog.open) {
      setTitle(course.title);
      setDrafts(
        kits.map((kit) => ({
          id: kit.id,
          title: kit.title,
          kit_type: kit.kit_type,
          deleted: false,
        })),
      );
      setError(null);
      setConfirmingDelete(false);
      dialog.showModal();
    } else if (!course && dialog.open) {
      dialog.close();
    }
  }, [course]);

  function updateDraft(id: number, change: Partial<KitDraft>) {
    setDrafts((current) =>
      current.map((draft) => (draft.id === id ? { ...draft, ...change } : draft)),
    );
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    if (!course) return;
    setSaving(true);
    setError(null);

    const original = new Map(kits.map((kit) => [kit.id, kit]));
    const requests: Promise<unknown>[] = [];
    if (title.trim() !== course.title) {
      requests.push(updateCourse(course.id, { title: title.trim() }));
    }
    for (const draft of drafts) {
      const kit = original.get(draft.id);
      if (!kit) continue;
      if (draft.deleted) {
        requests.push(deleteStudyKit(draft.id));
      } else if (draft.title.trim() !== kit.title || draft.kit_type !== kit.kit_type) {
        requests.push(
          updateStudyKit(draft.id, { title: draft.title.trim(), kit_type: draft.kit_type }),
        );
      }
    }

    const results = await Promise.allSettled(requests);
    setSaving(false);
    onSaved();
    if (results.some((result) => result.status === "rejected")) {
      setError("Some changes could not be saved. Please review and try again.");
      return;
    }
    onClose();
  }

  async function handleDeleteCourse() {
    if (!course) return;
    setSaving(true);
    setError(null);
    try {
      await deleteCourse(course.id);
      onSaved();
      onClose();
    } catch {
      setError("Could not delete the course. Please try again.");
      setConfirmingDelete(false);
    } finally {
      setSaving(false);
    }
  }

  const invalid =
    !title.trim() || drafts.some((draft) => !draft.deleted && !draft.title.trim());

  return (
    <dialog
      ref={dialogRef}
      className={`${dialogStyles.dialog} ${styles.dialog}`}
      aria-labelledby="edit-course-title"
      onClose={onClose}
    >
      <form onSubmit={handleSubmit}>
        <h2 id="edit-course-title" className={dialogStyles.title}>
          Edit course
        </h2>
        <label className={dialogStyles.field}>
          Course name
          <input
            className={dialogStyles.input}
            value={title}
            maxLength={200}
            required
            onChange={(e) => setTitle(e.target.value)}
          />
        </label>

        <h3 className={styles.sectionLabel}>Study kits</h3>
        {drafts.length === 0 ? (
          <p className={styles.empty}>This course has no study kits yet.</p>
        ) : (
          <ul className={styles.kits}>
            {drafts.map((draft) => (
              <li
                key={draft.id}
                className={`${styles.kit} ${draft.deleted ? styles.deleted : ""}`}
              >
                <input
                  className={`${dialogStyles.input} ${styles.kitTitle}`}
                  aria-label="Study kit name"
                  value={draft.title}
                  maxLength={200}
                  disabled={draft.deleted}
                  required={!draft.deleted}
                  onChange={(e) => updateDraft(draft.id, { title: e.target.value })}
                />
                <select
                  className={dialogStyles.input}
                  aria-label={`${draft.title} type`}
                  value={draft.kit_type}
                  disabled={draft.deleted}
                  onChange={(e) =>
                    updateDraft(draft.id, { kit_type: e.target.value as StudyKitType })
                  }
                >
                  <option value="lecture">Lecture</option>
                  <option value="tutorial">Tutorial</option>
                </select>
                <button
                  type="button"
                  className={`${dialogStyles.button} ${styles.kitAction}`}
                  onClick={() => updateDraft(draft.id, { deleted: !draft.deleted })}
                >
                  {draft.deleted ? "Undo" : "Delete"}
                </button>
              </li>
            ))}
          </ul>
        )}

        {error && (
          <p className={dialogStyles.error} role="alert">
            {error}
          </p>
        )}
        {confirmingDelete ? (
          <div className={styles.confirm} role="alert">
            <p className={styles.confirmText}>
              Delete {course?.title} and all of its study kits and materials? This
              can&apos;t be undone.
            </p>
            <div className={dialogStyles.actions}>
              <button
                type="button"
                className={dialogStyles.button}
                disabled={saving}
                onClick={() => setConfirmingDelete(false)}
              >
                Keep course
              </button>
              <button
                type="button"
                className={`${dialogStyles.button} ${styles.danger}`}
                disabled={saving}
                onClick={handleDeleteCourse}
              >
                {saving ? "Deleting…" : "Delete course"}
              </button>
            </div>
          </div>
        ) : (
          <div className={dialogStyles.actions}>
            <button
              type="button"
              className={`${dialogStyles.button} ${styles.dangerOutline}`}
              disabled={saving}
              onClick={() => setConfirmingDelete(true)}
            >
              Delete course
            </button>
            <button type="button" className={dialogStyles.button} onClick={onClose}>
              Cancel
            </button>
            <button
              type="submit"
              className={`${dialogStyles.button} ${dialogStyles.primary}`}
              disabled={saving || invalid}
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        )}
      </form>
    </dialog>
  );
}
