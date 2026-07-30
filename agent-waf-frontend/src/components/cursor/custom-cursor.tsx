import { useCursor } from "@/hooks/use-cursor";

export function CustomCursor() {
  const { position, hoverLabel } = useCursor();
  const hovering = hoverLabel !== null;

  return (
    <>
      <div
        className="pointer-events-none fixed z-50 rounded-full bg-waf-teal"
        style={{
          left: position.x,
          top: position.y,
          width: 6,
          height: 6,
          transform: "translate(-50%,-50%)",
        }}
      />
      <div
        className="pointer-events-none fixed z-50 flex items-center justify-center rounded-full transition-all duration-150 ease-out"
        style={{
          left: position.x,
          top: position.y,
          width: hovering ? 76 : 30,
          height: hovering ? 76 : 30,
          border: `1px solid ${hovering ? "var(--color-waf-teal)" : "rgba(255,255,255,0.35)"}`,
          background: hovering ? "rgba(45,212,191,0.08)" : "transparent",
          transform: "translate(-50%,-50%)",
        }}
      >
        {hovering && (
          <span className="font-mono text-[9px] uppercase tracking-wider text-waf-teal">
            {hoverLabel}
          </span>
        )}
      </div>
    </>
  );
}
