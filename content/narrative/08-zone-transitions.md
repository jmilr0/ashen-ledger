# Act I→III transition lines (journal + toast)

For Engineering’s zone-hop / save-across-zones pass. Short, sticky, no new systems.

## Journal auto-entries on zone enter

| From → to | Condition | Journal title | Body |
|---|---|---|---|
| Act I → Corbières | `talked_narbonne` \|\| `ferry_done` | Hill road | “Priory stones ahead. Berna’s box and Hugues’s warrant wait in the same mud.” |
| Act I → Corbières | `narbonne_outcome==refused_forger` | Ugly exit | “Gate kept us out. Priory is still the only road that matters.” |
| Act I → Corbières | `narbonne_outcome==deferred_gate` | Past the gate | “We rode past Narbonne. Legate may already be north — Corbières anyway.” |
| Corbières → Act I road | always | Back to the Aude | “Downhill toward ferry-mud and whatever Narbonne still wants from us.” |
| Any → Act III river | Serena resolved \|\| `talked_hugues` | Names and wood | “Act III. Lord or empty house, then the splinter’s end.” |
| Act III open | `lord_name` set | Rope on paper | “Raimon of Quéribus. Hide him, hang him, or walk past.” |
| Act III open | `lord_name` empty | Cold ash | “No name. Hill house may already be empty.” |

## Toast on zone enter (once)

| Enter | Toast |
|---|---|
| Corbières first time | Catalana: “Real stone. False altar. Watch the loft.” |
| Return Act I with `priory_path` set | Guillem: “Priory’s behind us. Keep the bag dry.” |
| Act III river | Arnau: “Wood or politics next. Don’t rush the wax.” |
| Act III after `rest_leper` | Elias: “Bleeds quiet. Don’t open them for sport.” |

## Save-safe storyBeat refresh (if beat looks stale)

On load, if zone is `corbieres` and `act2_beat` empty → `Corbières priory. Splinter on a false altar — northern captain wants the ruin as a warrant.`
If zone is Act III and `!act3_done` → use `07` open beat.
If `act3_done` → keep closing splinter storyBeat; don’t reset.

## Continuity one-liners NPCs can reuse

- Guiraut after Act II return: “Hill dust on you. The chest still wrong?”
- Mairia if trust≥2 and Act III not done: “We still eat. Don’t bring captains to our fire.”
- Mairia if trust0: “Keep walking. The column remembers the porch.”
- Narbonne agent if spoken again before Act III close: “Letter’s filed. Wood’s your problem now.”

No new flags — read existing ones only.
