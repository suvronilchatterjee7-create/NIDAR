# RescueSwarm Pose Dataset — project website

Single-page site for the NIDAR 2.0 RescueSwarm Pose Dataset v0.1, built with Vite + React (no other runtime dependencies).

## Run

```bash
npm install
npm run dev        # http://localhost:5173
npm run build      # static site in dist/
npm run preview    # serve dist/ on http://localhost:4173
```

`dist/` is plain static files and can go on any static host.

## Deploy on Vercel

The site lives in the `website/` folder of this repo, and `website/vercel.json` holds the build settings.

1. In Vercel, choose **Add New → Project** and import `suvronilchatterjee7-create/NIDAR`.
2. Set **Root Directory** to `website`. Vercel then reads `vercel.json`: framework Vite, install `npm ci`, build `npm run build`, output `dist`.
3. Click **Deploy**. Every push to the production branch redeploys automatically, and other branches get preview URLs.

No environment variables are needed.

## Structure

- `src/App.jsx`: all sections (hero, pipeline, viewer, data, real vs synthetic, quality, get started, roadmap, footer)
- `src/data.js`: every number and string taken from the NIDAR repo
- `src/viewer.json`: keypoints, outlines and posture labels for the 8 viewer frames, exported from `annotations/coco/*.json`
- `src/components/`: annotation viewer, charts, buttons, count-up chips, copy buttons
- `src/effects.js`: scroll reveal, parallax, scroll progress, active nav section, count-up
- `public/images/`: compressed dataset images, hero image and drone cut-out

All motion is turned off for visitors whose system is set to reduce motion.
