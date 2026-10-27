import styles from "./UploadTile.module.css";

interface UploadTileProps {
  onClick?: () => void;
}

export default function UploadTile({ onClick }: UploadTileProps) {
  return (
    <button type="button" className={styles.tile} onClick={onClick}>
      <svg
        width="22"
        height="22"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        aria-hidden="true"
      >
        <path d="M12 4v16M4 12h16" />
      </svg>
      <span className={styles.label}>Click to add course materials</span>
    </button>
  );
}
