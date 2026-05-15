# Poker Trainer

A Progressive Web App for poker training. Two modules: preflop range decisions and pot odds calculations. Works offline, installable on mobile.

## Features

- **Module 1 — Preflop ranges**: random hole cards + position (UTG / UTG+1 / MP / HJ / CO / BTN / SB / BB). Decide raise, call, or fold. Feedback shows the correct action, the hand category, and an interactive 13×13 range grid with the current hand highlighted.
- **Module 2 — Pot odds**:
  - *Sub-mode A*: enter the pot odds % (±3% tolerance). Full step-by-step breakdown.
  - *Sub-mode B* (unlocks after 10 correct in a row in Sub-mode A): random draw + street, decide call or fold. Shows equity vs pot odds and the rule-of-2/4 math.
- **Reference overlay**: outs/equity table and pot odds table, togglable.
- **Per-position accuracy tracking** in Settings, € ⇄ BB toggle, reset stats.
- **Streak counter**, best streak, every-10-hand milestone card with weakest position and encouragement.
- **Persistence**: all stats saved to `localStorage`.

## Tech

- Pure HTML/CSS/JS, single file, no frameworks, no build step.
- Service worker registered inline via Blob URL for offline support.
- Web App Manifest generated at runtime (192/512 PNG icons drawn on `<canvas>`).
- Cards generated client-side with `crypto.getRandomValues` + Fisher–Yates shuffle.

## Running locally

Service workers don't run from `file://`, so serve over HTTP:

```bash
# Python
python -m http.server 8080

# Node
npx serve .
```

Then open `http://localhost:8080`.

## Installing as a PWA

- **iOS Safari**: Share → Add to Home Screen.
- **Android Chrome / Edge**: install prompt appears, or use the browser menu → Install app.

## File structure

```
.
├── index.html      # the entire app (HTML + CSS + JS + manifest + SW)
├── README.md
└── .gitignore
```
