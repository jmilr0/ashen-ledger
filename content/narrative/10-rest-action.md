# Explicit Rest (BG feel — not auto-magic)

Aligns with Design: one Rest action at camp / leper when Surgeon is present and not `out_for_act`. Clears bleeds + partial HP. No hotbar miracle.

## UI label
`Rest` — subtitle: `Elias works. Time and linen.`

## Locked reasons (toast)
| Reason | Toast |
|---|---|
| Surgeon out / missing | “No steady hands. Keep walking.” |
| In combat | “Not while iron’s up.” |
| Already rested this beat | “Linen’s spent. Wait for the next roof.” |

## Success bark
Master Elias: “Hold still who can. Time and linen — not miracles.”

## Leper overlap
`leper_house` `[Surgeon] Boil linen…` / `rest_leper` **is** the Rest action at that roof — don’t double-heal if they also hit strip Rest in the same beat. Camp Rest elsewhere uses the same effect id `party_rest` (or reuse `rest_leper` clearing rules).

## Journal (optional once)
Title: `Linen and quiet` — Body: “Bleeds bound. No saints required.”
