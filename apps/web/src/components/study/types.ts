export type StudyKitType = "lecture" | "tutorial";

export type StudyKitStatus = "pending" | "generating" | "ready" | "failed";

export interface Course {
  id: number;
  title: string;
  code: string;
  color: string;
  position: number;
  is_archived: boolean;
}

export interface StudyKit {
  id: number;
  course: number;
  title: string;
  kit_type: StudyKitType;
  status: StudyKitStatus;
  summary: string;
  study_guide: string;
  /** IDs of the documents the kit was generated from. */
  documents: number[];
  flashcard_count: number;
  /** Mastery of the kit's flashcards, 0-100. */
  mastery_percent: number;
  created_at: string;
}

export interface Document {
  id: number;
  course: number;
  title: string;
  original_filename: string;
  status: "uploaded" | "queued" | "processing" | "processed" | "failed";
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}
