# Act I leftovers (still stubbed on Eng’s last ping)

## Pilgrim close auto-pick (narbonne `pilgrims` node)
If you want zero player choice at report:
- `pilgrim_trust >= 2` → jump to `close_good`
- `pilgrim_trust == 0` → jump to `close_cold`
- else keep both choices

## `peek_letter` (inventory / camp)
See `03-parish-narbonne.md`. Effect `break_true_seal` → `seal_intact=false`, `party_is_forger=true`.
