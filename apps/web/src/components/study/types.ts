export type MaterialType = "lecture" | "tutorial";

export interface Material {
  id: string;
  title: string;
  type: MaterialType;
  /** Mastery / completion, 0-100. */
  progress: number;
}

export interface Course {
  id: string;
  name: string;
  materials: Material[];
}
