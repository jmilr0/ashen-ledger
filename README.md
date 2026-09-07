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

Vite + TypeScript + Three.js. Merrowgate hub uses Kenney CC0 low-poly GLTF props with improved lighting (hemisphere + moon directional soft shadows, warm lantern point lights, exponential fog, ACES tone mapping). Procedural capsules remain as fallback if models fail to load.

## Assets & licenses

All 3D models are **CC0 1.0** by [Kenney](https://kenney.nl) (attribution not required; credited with appreciation):

| Pack | Use in slice |
|------|----------------|
| [Fantasy Town Kit](https://kenney.nl/assets/fantasy-town-kit) | Walls, roofs, stalls, lantern, cart, fountain |
| [Graveyard Kit](https://kenney.nl/assets/graveyard-kit) | Ghost (Blot-Wraith), crypt, lightposts, fence, pine, bench |
| [Blocky Characters](https://kenney.nl/assets/blocky-characters) | Player + NPC humanoids |
| [Pirate Kit](https://kenney.nl/assets/pirate-kit) | Dock, boat, barrels, crates |

Curated GLBs live under `public/models/` with license copies and `CREDITS.txt`.
