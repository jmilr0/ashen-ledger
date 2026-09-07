# Ashen Ledger

Isometric-ish CRPG vertical slice set in **Merrowgate**, a canal city where the **Ashen Ledger** turns unpaid debts into living curses. A drowned creditor washes ashore listing your party as collateral. Investigate forgeries, recruit a companion, and choose how to face the Ledger — gothic intrigue, moral gray. Original setting (not Baldur's Gate IP).

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
- Merrowgate hub (Three.js): click-to-move, wall/prop collision with slide, orbit camera
- Right-click NPCs to talk (E/F nearby interact backup)
- Dialogue with 2 NPCs; branching debt consequence with Mirelle
- One companion recruit (**Mirelle Quill**)
- One turn-based combat encounter (Blot-Wraith)
- Party & inventory UI
- `localStorage` save / load

## Controls

| Input | Action |
|-|--|
| **Left click** | Move on the ground |
| **Right click** on NPC | Open dialogue / engage wraith |
| **Right-drag** (empty) | Orbit camera around player |
| **Q** / **R** | Rotate camera left / right |
| **E** / **F** | Interact with nearby NPC (backup) |
| **E** | Interact with nearby NPC / start combat at wraith |
| **I** | Inventory |
| **C** / **P** | Party |
| **Ctrl+S** | Save |
| **Esc** | Close party/inventory overlay |

## Tech

Vite + TypeScript + Three.js. Orthographic orbit camera (yaw/pitch), AABB collision with wall slide. Gothic lighting (hemisphere + moon soft shadows, lanterns, fog, ACES). Characters are Blender-authored smooth low-poly humanoids; environment uses Kenney CC0 kits.

## Assets & licenses

| Source | Use |
|--------|-----|
| **Blender-authored** (`public/models/characters/`, `tools/make_characters.py`) | Rowan, Mirelle, Brin — smooth low-poly fantasy (not voxel/blocky) |
| [Kenney Fantasy Town Kit](https://kenney.nl/assets/fantasy-town-kit) (CC0) | Walls, roofs, stalls, lantern, cart, fountain |
| [Kenney Graveyard Kit](https://kenney.nl/assets/graveyard-kit) (CC0) | Ghost (Blot-Wraith), crypt, lightposts, fence, pine, bench |
| [Kenney Pirate Kit](https://kenney.nl/assets/pirate-kit) (CC0) | Dock, boat, barrels, crates |

Kenney **Blocky Characters** were removed. See `public/models/CREDITS.txt`.
