import styles from "./MaterialCard.module.css";
import type { StudyKit } from "./types";

interface MaterialCardProps {
  kit: StudyKit;
  /** Shown above the title when kits aren't grouped under their course. */
  courseName?: string;
}

export default function MaterialCard({ kit, courseName }: MaterialCardProps) {
  const progress = Math.round(Math.max(0, Math.min(100, kit.mastery_percent)));

  return (
    <div className={`${styles.card} ${styles[kit.kit_type]}`}>
      <div>
        {courseName && <span className={styles.course}>{courseName}</span>}
        <span className={styles.title}>{kit.title}</span>
      </div>
      <div className={styles.progress}>
        <div
          className={styles.track}
          role="progressbar"
          aria-label={`${kit.title} progress`}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-valuenow={progress}
        >
          <div className={styles.fill} style={{ width: `${progress}%` }} />
        </div>
        <span className={styles.percent}>{progress}%</span>
      </div>
    </div>
  );
}
