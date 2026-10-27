"use client";

import { useMemo, useState } from "react";
import UploadTile from "../upload/UploadTile";
import CourseSection from "./CourseSection";
import styles from "./Dashboard.module.css";
import type { Course, Material } from "./types";

const ALL_CLASSES = "all";

interface DashboardProps {
  courses: Course[];
}

export default function Dashboard({ courses }: DashboardProps) {
  const [query, setQuery] = useState("");
  const [classId, setClassId] = useState(ALL_CLASSES);

  const visible = useMemo(() => {
    const q = query.trim().toLowerCase();
    return courses
      .filter((course) => classId === ALL_CLASSES || course.id === classId)
      .map((course): { course: Course; materials: Material[] } => {
        const courseMatches = course.name.toLowerCase().includes(q);
        const materials = courseMatches
          ? course.materials
          : course.materials.filter((m) => m.title.toLowerCase().includes(q));
        return { course, materials };
      })
      .filter(({ materials }) => materials.length > 0);
  }, [courses, query, classId]);

  return (
    <main className={styles.page}>
      <div className={styles.upload}>
        <UploadTile />
      </div>

      <div className={styles.toolbar}>
        <label className={styles.search}>
          <input
            type="search"
            className={styles.searchInput}
            placeholder="Search"
            aria-label="Search materials"
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
            aria-label="Filter by class"
            value={classId}
            onChange={(e) => setClassId(e.target.value)}
          >
            <option value={ALL_CLASSES}>Class</option>
            {courses.map((course) => (
              <option key={course.id} value={course.id}>
                {course.name}
              </option>
            ))}
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
        {visible.length === 0 ? (
          <p className={styles.empty}>No materials found.</p>
        ) : (
          visible.map(({ course, materials }) => (
            <CourseSection key={course.id} course={course} materials={materials} />
          ))
        )}
      </div>
    </main>
  );
}
