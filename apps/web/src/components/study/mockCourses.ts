import type { Course } from "./types";

// Placeholder data until the dashboard is wired to the API.
export const mockCourses: Course[] = [
  {
    id: "calculus-ii",
    name: "Calculus II",
    materials: [
      { id: "calc-l1", title: "Lecture 1", type: "lecture", progress: 75 },
      { id: "calc-l2", title: "Lecture 2", type: "lecture", progress: 75 },
      { id: "calc-t1", title: "Tutorial 1", type: "tutorial", progress: 75 },
    ],
  },
  {
    id: "physics-ii",
    name: "Physics II",
    materials: [
      { id: "phys-l1", title: "Lecture 1", type: "lecture", progress: 75 },
      { id: "phys-t1", title: "Tutorial 1", type: "tutorial", progress: 75 },
    ],
  },
];
