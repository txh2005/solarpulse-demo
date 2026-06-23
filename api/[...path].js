const DEFAULT_TIMEOUT_MS = 60000;
const ALLOWED_METHODS = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"];

function normalizeOrigin(value) {
  return (value || "").trim().replace(/\/+$/, "");
}

function buildTargetUrl(request, backendOrigin) {
  const incomingUrl = new URL(request.url);
  const proxyPath = incomingUrl.pathname.replace(/^\/api/, "");
  const apiPath = proxyPath.startsWith("/") ? proxyPath : `/${proxyPath}`;
  return `${backendOrigin}/api${apiPath}${incomingUrl.search}`;
}

async function readRequestBody(request) {
  if (request.method === "GET" || request.method === "HEAD") {
    return undefined;
  }

  return Buffer.from(await request.arrayBuffer());
}

export default async function handler(request) {
  if (!ALLOWED_METHODS.includes(request.method)) {
    return Response.json(
      { detail: "Method Not Allowed" },
      {
        status: 405,
        headers: {
          Allow: ALLOWED_METHODS.join(", "),
        },
      },
    );
  }

  if (request.method === "OPTIONS") {
    return new Response(null, { status: 204 });
  }

  const backendOrigin = normalizeOrigin(process.env.BACKEND_API_ORIGIN);

  if (!backendOrigin) {
    return Response.json(
      { detail: "Missing BACKEND_API_ORIGIN environment variable on Vercel." },
      { status: 500 },
    );
  }

  const controller = new AbortController();
  const timeout = setTimeout(
    () => controller.abort(),
    Number(process.env.PROXY_TIMEOUT_MS || DEFAULT_TIMEOUT_MS),
  );

  try {
    const targetUrl = buildTargetUrl(request, backendOrigin);
    const body = await readRequestBody(request);
    const upstreamResponse = await fetch(targetUrl, {
      method: request.method,
      headers: {
        "Content-Type": request.headers.get("content-type") || "application/json",
        Accept: request.headers.get("accept") || "application/json",
      },
      body,
      signal: controller.signal,
    });

    const contentType = upstreamResponse.headers.get("content-type") || "application/json; charset=utf-8";
    const rawBody = await upstreamResponse.arrayBuffer();

    return new Response(rawBody, {
      status: upstreamResponse.status,
      headers: {
        "Content-Type": contentType,
        "Cache-Control": "no-store",
      },
    });
  } catch (error) {
    const isAbortError = error?.name === "AbortError";

    return Response.json(
      {
        detail: isAbortError ? "Upstream API request timed out." : "Failed to reach Django backend service.",
      },
      { status: isAbortError ? 504 : 502 },
    );
  } finally {
    clearTimeout(timeout);
  }
}
