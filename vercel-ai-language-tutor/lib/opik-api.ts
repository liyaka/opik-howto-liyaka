// Minimal REST helper for the Opik calls the SDK has no one-liner for
// (online-evaluation rules, trace cleanup). Works against local Opik and Cloud.
export function opikBase(env: NodeJS.ProcessEnv = process.env): string {
  const base = env.OPIK_URL_OVERRIDE ?? "http://localhost:5173/api/";
  return base.replace(/\/+$/, "");
}

export function opikHeaders(env: NodeJS.ProcessEnv = process.env): Record<string, string> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    "Comet-Workspace": env.OPIK_WORKSPACE ?? "default",
  };
  if (env.OPIK_API_KEY) headers.Authorization = env.OPIK_API_KEY;
  return headers;
}

export type Fetch = typeof fetch;

export async function opikRequest<T>(
  path: string,
  init: RequestInit = {},
  fetchImpl: Fetch = fetch,
): Promise<T> {
  const res = await fetchImpl(`${opikBase()}${path}`, {
    ...init,
    headers: { ...opikHeaders(), ...(init.headers as Record<string, string> | undefined) },
  });
  if (!res.ok) throw new Error(`Opik ${init.method ?? "GET"} ${path} -> ${res.status}: ${await res.text()}`);
  const text = await res.text();
  return (text ? JSON.parse(text) : undefined) as T;
}
