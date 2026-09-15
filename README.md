# Poker Trainer

A Progressive Web App for poker training: preflop ranges down the whole 3-bet /
4-bet / 5-bet tree, pot odds, postflop fundamentals, and an equity simulator.
Works offline, installable on mobile.

## Features

**Preflop ranges (drill)**

Random hole cards in a random seat, with the table showing the action that led
to the spot. Four scenarios are mixed in:

| Scenario | You are | Decision |
| --- | --- | --- |
| Open | first in, folded to you | raise / fold |
| vs Open | someone opened before you | 3-bet / call / fold |
| vs 3-Bet | you opened and got 3-bet | 4-bet / call / fold |
| vs 4-Bet | you 3-bet and got 4-bet | 5-bet / call / fold |

Feedback names the seat that actually raised, the hand category, and why the
chart plays it that way. The range grid for the current spot is one tap away.

**Ranges Explorer (study)**

The same four scenarios as interactive 13×13 grids. Single seat, two seats
compared side by side with the differing hands outlined, or every seat at a
glance. Percentages are combo-weighted.

**Pot odds (drill)**

- *Sub-mode A*: pick which of three pot-odds percentages you are getting, with
  the full division worked out afterwards.
- *Sub-mode B* (unlocks after 10 correct in a row in Sub-mode A): a random draw
  and street — call or fold, judged on equity vs pot odds with the rule-of-2/4
  shown.

**Postflop basics** — six lessons on board texture, c-betting, SPR, range
reading, floats and donk bets, with a wet-or-dry quiz.

**Glossary & calculator** — positions, betting actions, sizings, hand rankings,
probability tables, key terms, and a Monte-Carlo equity simulator (5,000 hands
per run, hero vs a specific hand or vs a random one, any board).

**Everything else**

- 6-max and full-ring (9-max); the seat list and every chart follow the setting
- Per-position accuracy, streak and best streak, every-10-hand milestone card
- Session summary with a filterable list of the hands you got wrong
- € ⇄ BB display toggle, auto-advance on correct answers, reset stats
- All stats saved to `localStorage`

## About the ranges

The charts are simplified teaching ranges, not solver output. Opening ranges are
per seat; the vs-open, vs-3-bet and vs-4-bet charts are grouped by position tier
(early/middle, late, blinds) rather than being conditioned on the exact opponent
seat. They are checked for internal consistency: a later seat opens a superset of
an earlier one, a weaker pair is never played more aggressively than a stronger
one, and a suited hand is never played weaker than the same offsuit hand.

## Tech

- Pure HTML/CSS/JS, no frameworks, no build step — the whole app is `index.html`.
- Light, iOS-flavoured design system driven by CSS custom properties.
- Service worker for offline use, with the page itself always fetched from the
  network so a deploy is never stuck behind a cache.
- Cards dealt client-side with `crypto.getRandomValues` + Fisher–Yates shuffle.
- Hand evaluator ranks any 7-card board for the equity simulator.

## Deploying

Bump `BUILD` at the top of the script in `index.html`, then push:

```js
const BUILD = '2026.09.12';
```

That value goes on the service worker's registration URL (`./sw.js?v=…`), so a
new one makes the browser install a fresh worker, drop the previous cache and
reload anything that is open. It is the only thing to change — nothing else
carries a version.

The page is fetched network-first with `cache: 'no-store'`, so an update lands
even though GitHub Pages puts a `max-age` on every file; the cached copy only
serves when you are offline. Settings shows the running build and has a
**Check** button that forces the update check by hand.

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
├── index.html                # the entire app (HTML + CSS + JS)
├── sw.js                     # service worker: offline shell, update handling
├── manifest.webmanifest      # PWA manifest
├── icon-192.png              # app icons
├── icon-512.png
├── icon-512-maskable.png
├── apple-touch-icon.png
├── README.md
└── .gitignore
```
