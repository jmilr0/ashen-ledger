# Per-character stats + equip sheet

**Owner:** Game Design · **For:** Engineering / Narrative flavor later  
**Canon:** No magic hotbar. Jobs stay jobs. Dirt gear.

## Open
- `C` / `P` party panel → click member **or** `I` inventory with selected companion.
- Strip portrait click (hub) selects sheet target; bag pip still ≠ face.

## Stats (per `PartyMember`)
Keep existing combat stats; show plainly:

| Field | Source |
|---|---|
| Name / Role (job) | existing |
| HP / maxHP | existing |
| ATK / DEF | existing |
| Status | bleeding, outForAct, downed |
| Notes | one-liner role blurb (optional static string per job) |

No MP. No spell slots.

## Equip slots (per character)
| Slot | Examples |
|---|---|
| `hand` | Inkknife, spear, staff, club, crossbow (Guide) |
| `body` | Mail, habit, cloak |
| `pack` | Personal small item (salve stack stays party shared **or** move salves to pack — prefer **party shared consumables** + unique hand/body per char) |

### Inventory model
```ts
interface EquipSlot { hand?: ItemId; body?: ItemId }
// PartyMember += equip: EquipSlot
// Party inventory = shared pool; equipped items removed from pool or flagged equippedBy
```

### Rules
1. Only **one** character can equip a unique item.
2. Job soft gates (toast if wrong): Guide prefers crossbow in hand; Sergeant mail; Clerk staff; Convers club; Surgeon no weapon required.
3. ATK/DEF derive: `base job stats + hand/body bonuses` (tiny: spear +2 atk, mail +2 def, staff +0 atk +1 def, etc.).
4. Unequip → back to shared inventory.
5. Combat uses equipped ATK/DEF (already on member.stats — refresh on equip change).

### First-cut item bonuses (tune later)
| Item | Slot | Bonus |
|---|---|---|
| Spear / household arms | hand | +2 ATK |
| Club | hand | +1 ATK |
| Staff | hand | +1 DEF |
| Crossbow | hand | +2 ATK (ranged flavor only in Bolt) |
| Inkknife | hand | +1 ATK |
| Mail | body | +2 DEF |
| Cloak / habit | body | +1 DEF |
| Canal salve / boiled linen | consumable | shared; Use from inventory as now |

## UI (minimum)
- Left: party list. Right: selected stats + 2 equip slots + “Unequip”.
- Shared inventory list below with **Equip to [Name]** when slot-compatible.
- No drag-drop required first cut — buttons OK.

## RMB inspect (follow-up, same pass if cheap)
- People: talk (existing).
- Objects: `inspect` / `loot` / `use` via prop `userData.interact` — chest, rope, mold cavity, mile marker, bell. Short Narrative lines later; Engineering stub “Worn wood. Nothing loose.” until copy lands.

## Acceptance
- Open C, select Guillem, equip mail → DEF up on card and in next fight.
- Equip spear on Convers → Guillem’s spear slot empty.
- Guide Bolt still works; ATK reflects crossbow if equipped.
