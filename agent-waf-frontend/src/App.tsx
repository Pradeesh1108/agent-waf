import { CursorProvider } from "@/context/cursor-context";
import { CustomCursor } from "@/components/cursor/custom-cursor";
import { Navbar } from "@/components/sections/navbar";
import { Hero } from "@/components/sections/hero";
import { Pipeline } from "@/components/sections/pipeline";
import { RuleEngine } from "@/components/sections/rule-engine";
import { LiveTraffic } from "@/components/sections/live-traffic";
import { Footer } from "@/components/sections/footer";
import { useLiveFeed } from "@/hooks/use-live-feed";

function AppShell() {
  const { events, totals, now, blockRate, blockedFeed } = useLiveFeed();

  return (
    <div className="waf-cursor-none min-h-screen w-full bg-waf-bg text-waf-text">
      <CustomCursor />
      <Navbar />
      <Hero totals={totals} blockRate={blockRate} />
      <Pipeline />
      <RuleEngine />
      <LiveTraffic events={events} blockedFeed={blockedFeed} now={now} />
      <Footer />
    </div>
  );
}

export default function App() {
  return (
    <CursorProvider>
      <AppShell />
    </CursorProvider>
  );
}
