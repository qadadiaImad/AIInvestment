import { SourceRef } from "@/lib/data";

export default function Footer({
  disclaimer,
  sources,
  generatedAt,
}: {
  disclaimer: string;
  sources: SourceRef[];
  generatedAt: string;
}) {
  return (
    <footer className="mt-auto border-t border-term-border px-3 py-3 text-[10.5px] text-term-muted">
      <p className="text-zinc-300 font-semibold mb-1">
        Educational research only — not financial advice.
      </p>
      <p className="max-w-4xl leading-relaxed">{disclaimer}</p>
      <div className="mt-2 flex flex-wrap items-center gap-x-3 gap-y-1">
        <span className="text-term-muted">Sources:</span>
        {sources.map((s) => (
          <a
            key={s.name}
            href={s.url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-blue-400 hover:text-blue-300 underline-offset-2 hover:underline"
          >
            {s.name}
          </a>
        ))}
        <span className="ml-auto">Updated {generatedAt}</span>
      </div>
    </footer>
  );
}
