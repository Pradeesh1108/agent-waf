import { useContext } from "react";
import { CursorContext } from "@/context/cursor-context";

export function useCursor() {
  const ctx = useContext(CursorContext);
  if (!ctx) throw new Error("useCursor must be used within a CursorProvider");
  return ctx;
}

/**
 * Returns onMouseEnter/onMouseLeave handlers that expand the custom cursor
 * into a labeled ring while hovering the wrapped element.
 */
export function useCursorHover(label: string) {
  const { setHoverLabel } = useCursor();
  return {
    onMouseEnter: () => setHoverLabel(label),
    onMouseLeave: () => setHoverLabel(null),
  };
}
