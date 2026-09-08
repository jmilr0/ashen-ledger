# Open map — Act I contiguous outdoor extents

**Owner:** Game Design · **For:** Engineering / Art  
**Goal:** Kill zone-teleport feel on Fontfroide → Narbonne. One walkable outdoor. Corbières / Act III expand later.

## Scale (first merge)

| | Now | Target Act I outdoor |
|---|---|---|
| Playable footprint | ~13 m square (`GRID=11`, `TILE=1.2`) | **~100 m north–south × ~32 m east–west** |
| Suggested | — | `TILE=1.2`, **GRID ≈ 84 along Z / 28 along X** *or* keep TILE and set world half-extents: **Z ±50 m, X ±16 m** |

Orbit cam: bump `ORBIT_DIST` ~22–26 so the strip reads; fog slightly thinner on Act I only.

## Road strip (locked)

- Crown of road: **x ∈ [-1.2, 1.2]** (2.4 m clear) full Z length.
- Follower trail lives here — **no** cart/fence/building colliders in strip.
- Soft shoulders: dressing OK in **|x| 1.2–4**; heavy shells **|x| ≥ 4**.
- Doorways into hubs ≥ **1.2 m** clear (parish arch already ~2.1 m OK).

## Hub layout (world meters, road along +Z north → south)

Origin ≈ mid-road. Player start near Fontfroide.

| Hub | Anchor (x, z) | Notes |
|---|---|---|
| **Fontfroide cloister** | (−6, +38) | Yard west of road; Guiraut; chest; cloister arcade/well |
| **Mile marker / column** | (0, +22) | Mairia + road NPCs (monk, cart widow) on shoulders |
| **Ambush bend** | (0, +8) | Bandits; slight road kink OK if strip stays 2.4 m |
| **Parish porch** | (+7, −2) | Ramon east of road; burial gate behind |
| **Goldsmith / mold** | (−7, −14) | West pocket; mold cavity; viscount rider |
| **Ferry** | (0, −32) | Rope + boat on water south; Hold/Cut encounter |
| **Narbonne gate pocket** | (+5, −44) | Agent; not a full city — gate/stalls reading |
| **Corbières turnoff** | (−4, −28) | Sign/NPC only until Act II merge — walk trigger or talk, **no** instant teleport prefer: optional short spur west then load Corbières *or* contiguous stub path |

Numbers are ±2 m flexible for Art shells.

## Walk rules

1. Player can walk the full Act I Z range without a zone swap.
2. Entering Corbières / Act III may still swap maps **until** those hubs expand — but Act I internal beats must not.
3. Save stores world x,z + `map_zone: 'act1_outdoor'` (rename from `act1_road` OK).
4. NPC ids / flags unchanged; only positions + density.

## Interactive cast (wire with merge)

From `13-interactive-cast.md`: RMB party followers + wayside NPCs along shoulders (monk, widow, idler near ferry, etc.). Capsules ~0.6 m, off strip.

## Art stockpile

Extra cloister bays, ruin debris, village shells — place in |x|≥4 bands and hub pockets so the 100 m strip doesn’t feel empty fog.

## Acceptance

- Walk Fontfroide → ferry without loading screen / zone fade.
- Party trail survives parish doorway and ferry approach.
- Orbit can see ~2 hubs at once from mid-road pitch.
- No corking on 2.4 m crown.

## Out of scope this merge

Full Corbières outdoor, Narbonne city block, new combat. Extents for those in a later doc after Act I lands.
