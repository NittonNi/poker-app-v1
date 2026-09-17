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

The charts are simplified teaching ranges, not solver output, and all of them live
in [`ranges.json`](#rangesjson), which both the app and the terminal trainer read.
Opening ranges are per seat. The vs-open, vs-3-bet and vs-4-bet charts come from
position tiers (early/middle, late, blinds), so today every opponent seat gets the
same chart; the file has one grid per opponent seat, so they can be told apart just
by editing it. The drill grades each spot against the chart for the seat that
actually raised; the explorer, which shows one chart per seat, uses the first
opponent seat that has one. The tests in `rejilla/tests` check the file for internal
consistency: a later seat opens a superset of an earlier one, a weaker pair is never
played more aggressively than a stronger one, and a suited hand is never played
weaker than the same offsuit hand.

## Grid memorization (terminal)

A separate trainer in `rejilla/` for learning the 13×13 charts by heart: not
deciding single hands, but drawing any chart from memory and knowing exactly where
each border is. Python 3.10+, standard library only, interface in Spanish.

```bash
python -m rejilla                                  # menu
python -m rejilla repaso                           # mixed review, 20 questions
python -m rejilla fronteras --pos CO --rama RFI -n 15
python -m rejilla ver BTN RFI                      # just look at a chart
```

| Command | Exercise | What you answer |
| --- | --- | --- |
| `fronteras` | Borders (the main one) | "UTG, fila de la K, suited: ¿hasta dónde llega?" → `K9s`. Every row: pairs, and each suited and offsuit row. Charts with calls get one answer per action. |
| `salto` | Suited/offsuit gap | Last suited and last offsuit of a row. The number of steps between them is scored too. |
| `diferencial` | Between seats | The hands added from one opening seat to the next. Bigger jumps come up more, so CO→BTN is the most frequent. |
| `identifica` | Name the chart | A painted chart with no name: say seat and branch. Any identical chart counts as right. |
| `reloj` | In or out, against the clock | One key within 3 s (`d`/`f`, or `r c a f` when the chart has calls). The result is a map of your misses grouped by zone, not a percentage. |
| `blanco` | Blank grid | Fill an empty grid with ranges (`22+ r`, `KQs-K9s raise`, `AKo c`). Then yours and the real one side by side with the misses marked, the hits, and the % your version plays against the real %. |

`repaso` mixes them: borders 40 %, between seats 20 %, suited/offsuit gap 15 %,
clock 15 % (5 hands at a time), name the chart 10 %. The blank grid is long, so it
only runs on its own.

**Writing hands.** In a border answer a single hand means that hand and everything
above it (`K9s`); loose pieces go after it (`ATs+ A5s-A4s`); an empty row is
`nada`. The `s`/`o` can be left out when the row already says it. `salir` ends the
session (Esc on the clock).

**Spaced repetition.** Leitner boxes on the triple (hand, seat, branch), not on the
bare hand. A miss sends the card back to box 1 and it comes back a few questions
later; two hits in a row move it up: box 1 is due the same day, box 2 the next day,
then 3, 7 and 16 days. Every exercise that says something about specific cells feeds
the boxes (naming the chart doesn't). Progress is saved after each answer in
`~/.poker-trainer/rejilla.json`, outside the repo.

**On exit.** Your three worst zones (seat · branch · row) and, per seat, the % you
would play — your answers laid over the real chart — next to the chart's own %.

Options: `--pos`, `--rama` (`RFI`, `vs_open`, `vs_3bet`, or a specific one such as
`vs_open_CO`), `-n`, `--limite` (seconds on the clock), `--estado`, `--rangos`,
`--sin-color` (or set `NO_COLOR`).

Tests: `python -m unittest discover -s rejilla/tests -t .`

## `ranges.json`

One 13×13 grid per (seat, branch), per table size. Rows and columns go A→2, pairs
on the diagonal, suited above it, offsuit below; one letter per cell: `R` raise,
`C` call, `F` fold, `A` all-in.

```json
{ "version": 1,
  "6max": { "BTN": { "RFI": ["RRRRRRRRRRRRR", "..."], "vs_open_CO": ["..."] } } }
```

| Branch | Spot |
| --- | --- |
| `RFI` | first in |
| `vs_open_X` | X opened before you |
| `vs_3bet_X` | you opened and X 3-bet |
| `vs_4bet_X` | you 3-bet X's open and X 4-bet |

A branch that isn't in the file isn't shown anywhere. The trainer checks the file
when it loads it (13×13, valid letters, and seats that can actually be in that spot),
and `python -m unittest discover -s rejilla/tests -t .` runs the same checks plus
the consistency rules above, so run it after editing a chart. The 6-max seat the
app shows as `MP` is `HJ` in the file.

## Tech

- Pure HTML/CSS/JS, no frameworks, no build step — the whole app is `index.html`,
  plus the charts in `ranges.json`, loaded at startup. If that file can't be loaded
  the home screen says so and the range drill and explorer stay off.
- Light, iOS-flavoured design system driven by CSS custom properties.
- Service worker for offline use, with the page and `ranges.json` always fetched
  from the network so a deploy is never stuck behind a cache.
- Cards dealt client-side with `crypto.getRandomValues` + Fisher–Yates shuffle.
- Hand evaluator ranks any 7-card board for the equity simulator.

## Deploying

Bump `BUILD` at the top of the script in `index.html`, then push:

```js
const BUILD = '2026.09.17';
```

That value goes on the service worker's registration URL (`./sw.js?v=…`), so a
new one makes the browser install a fresh worker, drop the previous cache and
reload anything that is open. It is the only thing to change — nothing else
carries a version.

The page and `ranges.json` are fetched network-first with `cache: 'no-store'`, so
an update lands even though GitHub Pages puts a `max-age` on every file; the cached
copy only serves when you are offline. That also means an edit that only touches
`ranges.json` shows up on the next load without bumping `BUILD`. Settings shows the
running build and has a **Check** button that forces the update check by hand.

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
├── ranges.json               # every chart, 13×13 per seat and branch (app + trainer)
├── rejilla/                  # terminal trainer for memorizing the charts
│   ├── __main__.py           # menu and commands
│   ├── rangos.py             # loads and checks ranges.json
│   ├── manos.py              # hand notation, rows, ranges like KQs-K9s
│   ├── analisis.py           # grading, without screen or disk
│   ├── leitner.py            # spaced repetition, saved to disk
│   ├── pantalla.py           # ASCII grid with a colour per action
│   ├── informe.py            # end-of-session report
│   ├── ejercicios/           # one module per exercise
│   └── tests/
├── README.md
└── .gitignore
```
