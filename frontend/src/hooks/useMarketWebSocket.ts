"use client";

import { useEffect, useRef, useState } from "react";
import { IndexQuote, MarketSessionStatus, Quote } from "../types";

export type ConnectionState = "CONNECTING" | "LIVE" | "DISCONNECTED" | "ERROR";

export function useMarketWebSocket(subscribedSymbols: string[] = []) {
  const [connectionState, setConnectionState] = useState<ConnectionState>("CONNECTING");
  const [marketStatus, setMarketStatus] = useState<MarketSessionStatus | null>(null);
  const [indices, setIndices] = useState<IndexQuote[]>([]);
  const [quotes, setQuotes] = useState<Record<string, Quote>>({});
  const [lastUpdated, setLastUpdated] = useState<string>("");

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    let isMounted = true;

    function connect() {
      // Determine WebSocket URL
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000/api/v1";
      const wsUrl = apiUrl.replace(/^http/, "ws") + "/ws/market";

      try {
        setConnectionState("CONNECTING");
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (!isMounted) return;
          setConnectionState("LIVE");
          // Send initial subscription
          if (subscribedSymbols.length > 0) {
            ws.send(
              JSON.stringify({
                action: "subscribe",
                symbols: subscribedSymbols,
                include_indices: true,
              })
            );
          }
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const msg = JSON.parse(event.data);
            if (msg.timestamp) {
              setLastUpdated(msg.timestamp);
            }

            if (msg.type === "market_status") {
              setMarketStatus(msg.data);
            } else if (msg.type === "indices_update") {
              setIndices(msg.data);
            } else if (msg.type === "quotes_update") {
              const quotesMap: Record<string, Quote> = {};
              (msg.data as Quote[]).forEach((q) => {
                quotesMap[q.symbol] = q;
              });
              setQuotes((prev) => ({ ...prev, ...quotesMap }));
            }
          } catch (err) {
            console.error("Error parsing WebSocket message:", err);
          }
        };

        ws.onclose = () => {
          if (!isMounted) return;
          setConnectionState("DISCONNECTED");
          // Reconnect with backoff
          reconnectTimeoutRef.current = setTimeout(connect, 4000);
        };

        ws.onerror = () => {
          if (!isMounted) return;
          setConnectionState("ERROR");
        };
      } catch (err) {
        if (!isMounted) return;
        setConnectionState("ERROR");
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      }
    }

    connect();

    return () => {
      isMounted = false;
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [subscribedSymbols.join(",")]);

  return {
    connectionState,
    marketStatus,
    indices,
    quotes,
    lastUpdated,
  };
}