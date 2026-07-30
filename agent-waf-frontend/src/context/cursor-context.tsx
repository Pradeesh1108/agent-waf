import { createContext, useEffect, useState, type ReactNode } from "react";

interface CursorContextValue {
  position: { x: number; y: number };
  hoverLabel: string | null;
  setHoverLabel: (label: string | null) => void;
}

export const CursorContext = createContext<CursorContextValue | null>(null);

export function CursorProvider({ children }: { children: ReactNode }) {
  const [position, setPosition] = useState({ x: -100, y: -100 });
  const [hoverLabel, setHoverLabel] = useState<string | null>(null);

  useEffect(() => {
    const handleMove = (e: MouseEvent) => setPosition({ x: e.clientX, y: e.clientY });
    window.addEventListener("mousemove", handleMove);
    return () => window.removeEventListener("mousemove", handleMove);
  }, []);

  return (
    <CursorContext.Provider value={{ position, hoverLabel, setHoverLabel }}>
      {children}
    </CursorContext.Provider>
  );
}
