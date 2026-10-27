import MaterialCard from "./MaterialCard";
import styles from "./CourseSection.module.css";
import type { Course, StudyKit } from "./types";

interface CourseSectionProps {
  course: Course;
  kits: StudyKit[];
  onEdit?: (course: Course) => void;
}

export default function CourseSection({
  course,
  kits,
  onEdit,
}: CourseSectionProps) {
  return (
    <section className={styles.section}>
      <div className={styles.header}>
        <h2 className={styles.name}>{course.title}</h2>
        <button
          type="button"
          className={styles.edit}
          aria-label={`Edit ${course.title}`}
          onClick={() => onEdit?.(course)}
        >
          <svg
            width="20"
            height="20"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
            aria-hidden="true"
          >
            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
          </svg>
        </button>
      </div>
      <div className={styles.cards}>
        {kits.map((kit) => (
          <MaterialCard key={kit.id} kit={kit} />
        ))}
      </div>
    </section>
  );
}
