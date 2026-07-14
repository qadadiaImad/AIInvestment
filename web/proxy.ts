import { NextRequest, NextResponse } from "next/server";

// NOTE ON FILE NAME: Next.js 16 deprecated the `middleware.ts` file
// convention and renamed it to `proxy.ts` (function name `middleware` ->
// `proxy`). Both conventions are still recognized by the build (backward
// compat), but AGENTS.md requires following current, non-deprecated
// conventions — so this file is `proxy.ts`, not `middleware.ts`. Logic,
// matcher, and behavior are otherwise identical to the merged spec's
// `middleware.ts` draft. This is the one documented, deliberate deviation
// from the build brief's literal file list.

export const config = { matcher: ["/terminal/:path*"] };

const COOKIE_NAME = "terminal_key";
const MAX_AGE = 60 * 60 * 24 * 400;

function withNoIndex(res: NextResponse) {
  res.headers.set("X-Robots-Tag", "noindex, nofollow");
  res.headers.set("Referrer-Policy", "strict-origin");
  return res;
}

function maybeSetCaptureHeader(req: NextRequest, res: NextResponse) {
  const isCard = req.nextUrl.pathname.startsWith("/terminal/card/");
  if (isCard && req.nextUrl.searchParams.get("capture") === "1") {
    const headers = new Headers(req.headers);
    headers.set("x-capture-mode", "1");
    return NextResponse.next({ request: { headers } });
  }
  return res;
}

export function proxy(req: NextRequest) {
  const key = process.env.TERMINAL_KEY;
  if (!key) return withNoIndex(maybeSetCaptureHeader(req, NextResponse.next()));

  const cookieVal = req.cookies.get(COOKIE_NAME)?.value;
  if (cookieVal === key) return withNoIndex(maybeSetCaptureHeader(req, NextResponse.next()));

  const queryKey = req.nextUrl.searchParams.get("key");
  if (queryKey === key) {
    // Apply the capture-header rewrite FIRST, then set the cookie on that
    // same response object — constructing two separate NextResponse.next()
    // calls here would clobber one another (the capture-mode request-header
    // rewrite from maybeSetCaptureHeader would be silently dropped if we
    // built a second NextResponse.next() afterward just to set cookies).
    // This matters because the real capture script always passes
    // `?key=...&capture=1` together in one request (see §G) — key-in-query
    // and capture=1 in the same request is the common case, not an edge
    // case.
    const res = maybeSetCaptureHeader(req, NextResponse.next());
    res.cookies.set(COOKIE_NAME, key, {
      httpOnly: true,
      secure: req.nextUrl.protocol === "https:",
      sameSite: "lax",
      path: "/terminal",
      maxAge: MAX_AGE,
    });
    return withNoIndex(res);
  }
  return withNoIndex(new NextResponse("Not found", { status: 404 }));
}
