import styles from "./MaterialCard.module.css";
import type { Material } from "./types";

export default function MaterialCard({ material }: { material: Material }) {
  const progress = Math.max(0, Math.min(100, material.progress));

  return (
    <div className={`${styles.card} ${styles[material.type]}`}>
      <span className={styles.title}>{material.title}</span>
      <div className={styles.progress}>
        <div
          className={styles.track}
          role="progressbar"
          aria-label={`${material.title} progress`}
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
