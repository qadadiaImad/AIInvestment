"use client";

import { useEffect, useRef } from "react";

// Embeds TradingView's free Advanced Chart widget (dark theme).
// https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js
export default function TradingViewChart({
  tvSymbol,
}: {
  tvSymbol?: string | null;
}) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!tvSymbol) return;
    const container = containerRef.current;
    if (!container) return;

    // Reset (handles symbol changes / re-renders).
    container.innerHTML = "";
    const widgetDiv = document.createElement("div");
    widgetDiv.className = "tradingview-widget-container__widget";
    widgetDiv.style.height = "100%";
    widgetDiv.style.width = "100%";
    container.appendChild(widgetDiv);

    const script = document.createElement("script");
    script.src =
      "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.type = "text/javascript";
    script.async = true;
    script.innerHTML = JSON.stringify({
      // Explicit width/height: autosize rendered a collapsed ~150px iframe.
      width: "100%",
      height: 520,
      symbol: tvSymbol,
      interval: "D",
      timezone: "Etc/UTC",
      theme: "dark",
      style: "1",
      locale: "en",
      backgroundColor: "#0e131d",
      gridColor: "rgba(31, 41, 55, 0.6)",
      hide_top_toolbar: false,
      allow_symbol_change: false,
      save_image: false,
      calendar: false,
      support_host: "https://www.tradingview.com",
    });
    container.appendChild(script);

    return () => {
      container.innerHTML = "";
    };
  }, [tvSymbol]);

  if (!tvSymbol) {
    return (
      <div className="h-[540px] flex items-center justify-center text-term-muted text-[11px]">
        Interactive chart unavailable (no symbol mapping).
      </div>
    );
  }

  return (
    <div
      ref={containerRef}
      className="tradingview-widget-container w-full"
      style={{ height: 540 }}
    />
  );
}
