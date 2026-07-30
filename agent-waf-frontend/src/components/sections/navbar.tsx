import { Radar, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { useCursorHover } from "@/hooks/use-cursor";

const NAV_LINKS = ["Pipeline", "Rule engine", "Live traffic"];

export function Navbar() {
  const brandHover = useCursorHover("home");
  const deployHover = useCursorHover("deploy");
  const linkHover = useCursorHover("view");

  return (
    <nav className="relative z-10 flex items-center justify-between border-b border-waf-border px-8 py-5">
      <div className="flex items-center gap-2" {...brandHover}>
        <Radar size={20} className="text-waf-teal" />
        <span className="font-display text-lg font-semibold">Agent WAF</span>
      </div>

      <div className="hidden items-center gap-8 text-sm text-waf-text-secondary md:flex">
        {NAV_LINKS.map((link) => (
          <a
            key={link}
            href={`#${link.toLowerCase().replace(" ", "-")}`}
            className="transition-colors hover:text-waf-text"
            {...linkHover}
          >
            {link}
          </a>
        ))}
      </div>

      <Button size="default" {...deployHover}>
        Deploy <ArrowRight size={14} />
      </Button>
    </nav>
  );
}
