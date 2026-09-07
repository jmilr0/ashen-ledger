# Ashen Ledger

Isometric CRPG vertical slice set in **Merrowgate**, a canal city where the **Ashen Ledger** turns unpaid debts into living curses. A drowned creditor washes ashore listing your party as collateral. Investigate forgeries, recruit a companion, and choose how to face the Ledger — gothic intrigue, moral gray. Original setting (not Baldur's Gate IP).

## Run

```bash
npm install
npm run dev
```

Then open the URL Vite prints (usually `http://localhost:5173`).

```bash
npm run build    # production build to dist/
npm run preview  # preview production build
```

## Story (slice)

You play **Rowan Vale**, debt-marked investigator. Speak with **Dockhand Brin**, then **Mirelle Quill**. Your dialogue choice — claim the names were **forged**, or **confess** the debt is real — changes how Mirelle frames the path and which spoil you earn after combat. Recruit her, then defeat the **Blot-Wraith** at the east arch.

## Vertical slice features

- Title screen (new / continue)
- Isometric Merrowgate hub (Three.js), click-to-move
- Dialogue with 2 NPCs; branching debt consequence with Mirelle
- One companion recruit (**Mirelle Quill**)
- One turn-based combat encounter (Blot-Wraith)
- Party & inventory UI
- `localStorage` save / load

## Controls

| Input | Action |
|-|--|
| Left click | Move on the ground |
| **E** | Interact with nearby NPC / start combat at wraith |
| **I** | Inventory |
| **C** / **P** | Party |
| **Ctrl+S** | Save |
| **Esc** | Close party/inventory overlay |

## Tech

Vite + TypeScript + Three.js. Placeholder geometry and colors by design.
