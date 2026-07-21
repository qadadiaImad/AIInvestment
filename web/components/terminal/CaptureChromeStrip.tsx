// Server-rendered global style for ?capture=1 card requests: hides the site
// Header/Footer chrome so a Playwright screenshot is chrome-free with ZERO
// hydration flash (pure CSS in the initial HTML — no client JS involved).
// This exists so the ROOT layout can stay fully static: it must never call
// headers()/searchParams itself, or every SSG route in the app (e.g.
// /stocks/[symbol]) is dragged into dynamic rendering and 404s become 500s
// (DYNAMIC_SERVER_USAGE) — the Round-4 integration verifier caught exactly
// that regression.
export default function CaptureChromeStrip() {
  return (
    <style>{`
      body > header, body > footer { display: none !important; }
      * { animation: none !important; transition: none !important; }
    `}</style>
  );
}
