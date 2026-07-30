# Agent WAF — frontend

Landing page + live dashboard for the Agent WAF project. Vite + React 19 + TypeScript +
Tailwind CSS v4 + shadcn/ui primitives + Framer Motion + lucide-react.

## Run locally

```bash
npm install
npm run dev
```

Open the printed localhost URL. `npm run build` produces a production bundle in `dist/`,
and `npm run preview` serves that build locally.

## Project structure

```
src/
  App.tsx                    # composes the page, wires the live-feed hook
  main.tsx                   # entry point

  components/
    ui/                      # shadcn/ui primitives (button, badge, switch, card)
    cursor/
      custom-cursor.tsx      # the dot + labeled ring cursor
    shared/
      spotlight-card.tsx     # cursor-tracking highlight card (Aceternity-style)
      stat-card.tsx
    sections/                # one file per page section
      navbar.tsx
      hero.tsx
      pipeline.tsx           # 5-stage architecture diagram
      rule-engine.tsx        # 4 rule cards with enforce/shadow toggles
      live-traffic.tsx       # traffic table + block feed
      footer.tsx

  context/
    cursor-context.tsx       # app-wide cursor position + hover label

  hooks/
    use-cursor.ts            # useCursor(), useCursorHover(label)
    use-live-feed.ts         # simulated live traffic feed (swap for real API)

  lib/
    mock-data.ts             # rule metadata, pipeline stages, event generator
    api.ts                   # fetchRecentLogs()/checkHealth() stubs for the real backend
    utils.ts                 # cn() classname helper

  types/
    index.ts                 # shared TypeScript types
```

Every section is its own file so you can add/remove/reorder sections in `App.tsx`
without touching the rest. Shared UI (`SpotlightCard`, `StatCard`, the shadcn
primitives) is reusable across sections.

## Wiring to the real backend

Right now `useLiveFeed` (`src/hooks/use-live-feed.ts`) simulates traffic client-side so
the UI is demoable without the backend running. To connect it to the deployed Agent WAF:

1. Copy `.env.example` to `.env` and set `VITE_API_BASE_URL` to your API Gateway stage URL
   from `sam deploy`'s output.
2. In `use-live-feed.ts`, replace the `setInterval` body that calls `randomEvent()` with a
   call to `fetchRecentLogs(lastSeenTs)` from `src/lib/api.ts`, and append the real records
   instead.
3. Everything downstream (the table, the block feed, the stat cards) already consumes the
   same `ToolCallEvent[]` / `LiveFeedTotals` shape, so no other component needs to change.

## Deploying

This is a static Vite build (`npm run build` → `dist/`), so any static host works:

- **Vercel / Netlify** — connect the repo, build command `npm run build`, output `dist`.
- **AWS S3 + CloudFront** — `aws s3 sync dist/ s3://<bucket>` behind a CloudFront
  distribution, keeping the whole stack (frontend + Lambda + API Gateway + DynamoDB) in
  AWS, which is the stronger story for the production-readiness rubric.
- **AWS Amplify Hosting** — point it at the repo for CI build + deploy in one step.

Set `VITE_API_BASE_URL` as a build-time environment variable on whichever host you pick.

## Design notes

- Fonts: Space Grotesk (display), Manrope (body), JetBrains Mono (logs/data).
- Palette: near-black base with three functional accents — teal (allow), coral (block),
  amber (shadow mode) — defined once in `src/index.css` under `@theme`.
- The Aceternity/Magic UI npm packages aren't used; the spotlight-card effect is a small
  hand-built component (`src/components/shared/spotlight-card.tsx`) using local mouse
  tracking, so there's no dependency on a package that may change or disappear.
- shadcn/ui components were hand-added (not via the CLI) so they map directly onto the
  custom theme tokens instead of the default shadcn palette.
