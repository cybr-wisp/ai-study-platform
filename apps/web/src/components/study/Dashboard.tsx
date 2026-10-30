"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { listCourses, listStudyKits } from "../../lib/api";
import AddMaterialsDialog from "../upload/AddMaterialsDialog";
import UploadTile from "../upload/UploadTile";
import CourseEditDialog from "./CourseEditDialog";
import CourseSection from "./CourseSection";
import MaterialCard from "./MaterialCard";
import styles from "./Dashboard.module.css";
import type { Course, StudyKit } from "./types";

type ViewMode = "class" | "study-kit";

/** A course's kits, oldest first (Lecture 1, Lecture 2, ...). */
function kitsForCourse(kits: StudyKit[], courseId: number): StudyKit[] {
  return kits
    .filter((kit) => kit.course === courseId)
    .sort((a, b) => a.created_at.localeCompare(b.created_at) || a.id - b.id);
}

export default function Dashboard() {
  const [courses, setCourses] = useState<Course[]>([]);
  const [kits, setKits] = useState<StudyKit[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");
  const [mode, setMode] = useState<ViewMode>("class");
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingCourse, setEditingCourse] = useState<Course | null>(null);

  const load = useCallback(async () => {
    try {
      const [c, k] = await Promise.all([listCourses(), listStudyKits()]);
      setCourses(c);
      setKits(k);
      setError(null);
    } catch {
      setError("Could not load your courses. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const q = query.trim().toLowerCase();
  const courseById = useMemo(
    () => new Map(courses.map((course) => [course.id, course])),
    [courses],
  );

  // Class view: kits grouped under their course. While searching, only
  // courses with a match are shown; otherwise empty courses stay visible.
  const sections = useMemo(
    () =>
      courses
        .map((course) => {
          const courseMatches = course.title.toLowerCase().includes(q);
          const own = kitsForCourse(kits, course.id);
          const matching = courseMatches
            ? own
            : own.filter((kit) => kit.title.toLowerCase().includes(q));
          return { course, kits: matching };
        })
        .filter(({ course, kits: matching }) => !q || matching.length > 0 || course.title.toLowerCase().includes(q)),
    [courses, kits, q],
  );

  // Study kit view: every kit, newest first (the API returns them that way).
  const flatKits = useMemo(
    () =>
      kits.filter((kit) => {
        const courseTitle = courseById.get(kit.course)?.title ?? "";
        return (
          kit.title.toLowerCase().includes(q) ||
          courseTitle.toLowerCase().includes(q)
        );
      }),
    [kits, courseById, q],
  );

  const isEmpty =
    mode === "class" ? sections.length === 0 : flatKits.length === 0;

  return (
    <main className={styles.page}>
      <div className={styles.upload}>
        <UploadTile onClick={() => setDialogOpen(true)} />
      </div>

      <div className={styles.toolbar}>
        <label className={styles.search}>
          <input
            type="search"
            className={styles.searchInput}
            placeholder="Search"
            aria-label="Search study kits"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <svg
            width="16"
            height="16"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2.5"
            strokeLinecap="round"
            aria-hidden="true"
          >
            <circle cx="11" cy="11" r="7" />
            <path d="m20 20-3.5-3.5" />
          </svg>
        </label>

        <div className={styles.classSelect}>
          <select
            className={styles.select}
            aria-label="View by"
            value={mode}
            onChange={(e) => setMode(e.target.value as ViewMode)}
          >
            <option value="class">Class</option>
            <option value="study-kit">Study Kit</option>
          </select>
          <svg
            className={styles.chevron}
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="m6 9 6 6 6-6" />
          </svg>
        </div>
      </div>

      <div className={styles.courses}>
        {loading ? (
          <p className={styles.empty}>Loading…</p>
        ) : error ? (
          <p className={styles.empty} role="alert">
            {error}
          </p>
        ) : isEmpty ? (
          <p className={styles.empty}>
            {q ? "No study kits found." : "No courses yet. Add one to get started."}
          </p>
        ) : mode === "class" ? (
          sections.map(({ course, kits: sectionKits }) => (
            <CourseSection
              key={course.id}
              course={course}
              kits={sectionKits}
              onEdit={setEditingCourse}
            />
          ))
        ) : (
          <div className={styles.flat}>
            {flatKits.map((kit) => (
              <MaterialCard
                key={kit.id}
                kit={kit}
                courseName={courseById.get(kit.course)?.title}
              />
            ))}
          </div>
        )}
      </div>

      <AddMaterialsDialog
        open={dialogOpen}
        courses={courses}
        onClose={() => setDialogOpen(false)}
        onChanged={load}
      />

      <CourseEditDialog
        course={editingCourse}
        kits={editingCourse ? kitsForCourse(kits, editingCourse.id) : []}
        onClose={() => setEditingCourse(null)}
        onSaved={load}
      />
    </main>
  );
}
