import type { Course, Page, StudyKit } from "../components/study/types";

// Requests go through the Next.js proxy at /api/v1 (see app/api/v1/[...path]).
const BASE_URL = "/api/v1";
const PAGE_SIZE = 100;

export class ApiError extends Error {
  constructor(
    public status: number,
    public body: unknown,
  ) {
    super(`API request failed with status ${status}`);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  const body = res.status === 204 ? null : await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, body);
  return body as T;
}

export async function listCourses(): Promise<Course[]> {
  const page = await request<Page<Course>>(
    `/courses?is_archived=false&page_size=${PAGE_SIZE}`,
  );
  return page.results;
}

/** Study kits, newest first. */
export async function listStudyKits(): Promise<StudyKit[]> {
  const page = await request<Page<StudyKit>>(`/study-kits?page_size=${PAGE_SIZE}`);
  return page.results;
}

export function createCourse(input: { title: string; code?: string }): Promise<Course> {
  return request<Course>("/courses", {
    method: "POST",
    body: JSON.stringify(input),
  });
}
