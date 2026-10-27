import type { NextRequest } from "next/server";

// Server-side proxy to the Django API. It avoids CORS and keeps the dev token
// out of the browser. Replace the token injection once real sign-in exists.
const API_BASE_URL = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";

type RouteContext = { params: Promise<{ path: string[] }> };

async function proxy(req: NextRequest, { params }: RouteContext) {
  const { path } = await params;
  const url = `${API_BASE_URL}/api/v1/${path.join("/")}${req.nextUrl.search}`;

  const headers = new Headers(req.headers);
  for (const name of ["host", "connection", "content-length", "expect", "transfer-encoding"]) {
    headers.delete(name);
  }
  const token = process.env.API_DEV_TOKEN;
  if (token && !headers.has("authorization")) {
    headers.set("authorization", `Bearer ${token}`);
  }

  const hasBody = req.method !== "GET" && req.method !== "HEAD";
  const upstream = await fetch(url, {
    method: req.method,
    headers,
    body: hasBody ? await req.arrayBuffer() : undefined,
    redirect: "manual",
  });

  // fetch() has already decoded the body, so drop the stale encoding headers.
  const responseHeaders = new Headers(upstream.headers);
  responseHeaders.delete("content-encoding");
  responseHeaders.delete("content-length");
  return new Response(upstream.body, {
    status: upstream.status,
    headers: responseHeaders,
  });
}

export {
  proxy as GET,
  proxy as POST,
  proxy as PUT,
  proxy as PATCH,
  proxy as DELETE,
};
