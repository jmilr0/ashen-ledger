# Companion barks (toast / one-line UI)

Trigger once per flag unless noted. Speaker id = party member id.

## Act I

| Trigger | Speaker | Line |
|---|---|---|
| `carrier_clerk` | sergeant | “Arnau has the bag. If they want it, they go through mail.” |
| `carrier_sergeant` | clerk | “Heavy hands, dry wax. Don’t flex the seal.” |
| `carrier_convers` | guide | “Peire already carries keys. One more latch won’t kill him.” |
| `warn_seal_break` | clerk | “Peek and every careful gate smells us.” |
| `break_true_seal` | sergeant | “We’re the next forgers on this road. Formation stays tight.” |
| `pilgrim_trust` hit 3 | guide | “Column’s eating our mud like friends.” |
| `pilgrim_trust` hit 0 | toast | “Don’t look back for our smoke.” |
| `child_burial_helped` | surgeon | “Quiet earth. Boiled linen after.” |
| `child_burial_helped` | toast | “Mairia: They saw. The column eats quieter tonight.” |
| `child_burial_refused` | guide | “That porch will talk in every village to Narbonne.” |
| `mold_given_viscount` | clerk | “He rides soft. Someone else still paid for the first seal.” |
| `mold_drowned` | convers | “Lead goes cold in the Aude. Letter’s still warm.” |
| `mold_kept` | sergeant | “Proof that hangs them — or us. Bag stays dry.” |
| ambush Point success | guide | “Badges don’t match the horses.” |
| ambush Call out success | clerk | “Wrong die. Step back or bleed for a lie.” |
| ferry ropeCut | convers | “Rope’s cut. Move the column.” |
| ferry win + trust>=2 | sergeant | “Hold held. Nobody in the water.” |
| ferry win + trust0 | guide | “We cross. They scatter. Road’ll remember.” |
| `narbonne_delivered` + trust>=2 | clerk | “Wax unbroken. Names next.” |
| member `out_for_act` | surgeon | “They’re done for this road. Don’t ask them to stand a spear.” |
| Stabilize success | surgeon | “Hold still. Time and linen — not miracles.” |
| Surgeon Wait | surgeon | “I’m not a blade. Say when someone drops.” |

## Act II

| Trigger | Speaker | Line |
|---|---|---|
| enter priory | guide | “Real stone. False altar. Watch the loft.” |
| `priory_path_steal` | convers | “Latch is soft. Smoke helps.” |
| `priory_path_talk` | clerk | “If they hear the rim name, some will leave without blood.” |
| `priory_path_hold` | sergeant | “Door’s mine. Sheep-gate’s yours.” |
| `smoke_loft` | guide | “Loft’s coughing. Bolt’s mine if you clear the angle.” |
| `captain_vines_spared` | sergeant | “Empty stone. People walk.” |
| `captain_vines_seized` | guide | “He’ll count vines either way. We bought time, not mercy.” |
| `captain_bribed_off` | convers | “Coin gone. Column still eats.” |
| `learn_lord_name` | clerk | “Raimon of Quéribus. Write it once. Burn the scrap.” |
| `lord_name_withheld` | surgeon | “A roof later may cost more than a name now.” |

## Act III

| Trigger | Speaker | Line |
|---|---|---|
| `rest_leper` | surgeon | “Dawn linen. No captains at the door.” |
| `lord_hidden` | sergeant | “We owe a silence. Keep it.” |
| `lord_named_hanged` | guide | “Hill house will empty. Don’t sleep there.” |
| `splinter_altar` | clerk | “Quiet stone. Someone else can kneel without our bag.” |
| `splinter_broken_public` | convers | “Pine sounds like pine. Good.” |
| `splinter_kept_bag` | sergeant | “Then we stay the next chest. Formation.” |
| `end_act3` | sergeant | “War’s still moving. We walk.” |

## Job combat callouts (reuse)

| Action | Speaker | Line |
|---|---|---|
| Hold line | sergeant | “Front rank — hold!” |
| Cut rope | convers | “Cutting!” |
| Point | guide | “There — wrong stamp.” |
| Call out | clerk | “That badge is last year’s lie!” |
| Stabilize | surgeon | “Stay down. I’ve got the bleed.” |
| Bolt | guide | “From the loft!” |
| Show seal (if intact) | clerk | “Look at the wax — then decide.” |
| Show seal (if broken) | clerk | “Don’t. They’ll smell the break.” |
