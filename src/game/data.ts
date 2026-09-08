import type { DialogueNode, Item, MapZone, NpcDef, PartyMember } from './types';

export const PLAYER_START = { x: -1.0, z: 30.5 }; // Fontfroide yard (~−1.2 m, +36.6 m)
export const CORBIERES_START = { x: 0, z: 2 };
export const ACT3_START = { x: 0, z: 2 };

export const JOB_PORTRAIT_COLOR: Record<string, string> = {
  guide: '#6a5038',
  sergeant: '#4a4858',
  convers: '#5a5040',
  clerk: '#6a5a48',
  surgeon: '#4a5848',
};

/** Default formation L→R facing: guide · sergeant · convers · clerk · surgeon */
export function createDefaultParty(): PartyMember[] {
  return [
    {
      id: 'guide',
      name: 'Catalana',
      role: 'Guide',
      stats: { hp: 18, maxHp: 18, atk: 6, def: 2 },
      recruited: true,
    },
    {
      id: 'sergeant',
      name: 'Sergeant Guillem',
      role: 'Sergeant',
      stats: { hp: 28, maxHp: 28, atk: 8, def: 5 },
      recruited: true,
    },
    {
      id: 'convers',
      name: 'Brother Peire',
      role: 'Convers',
      stats: { hp: 22, maxHp: 22, atk: 5, def: 3 },
      recruited: true,
    },
    {
      id: 'clerk',
      name: 'Arnau the Clerk',
      role: 'Clerk',
      stats: { hp: 16, maxHp: 16, atk: 3, def: 2 },
      recruited: true,
    },
    {
      id: 'surgeon',
      name: 'Master Elias',
      role: 'Surgeon',
      stats: { hp: 14, maxHp: 14, atk: 2, def: 2 },
      recruited: true,
    },
  ];
}

export function createDefaultInventory(): Item[] {
  return [
    {
      id: 'true_letter',
      name: 'True Sealed Letter',
      description: 'For the Narbonne agent. Break the seal to peek and you become the next forger.',
      qty: 1,
    },
    {
      id: 'splinter',
      name: 'Relic Splinter',
      description: 'Sold as a saint’s staff — likely pine or stolen timber.',
      qty: 1,
    },
    {
      id: 'false_seal',
      name: 'Near-True Lead Seal',
      description: 'Almost a living pope’s die — wrong month / rim name. Fools a crowd.',
      qty: 1,
    },
    {
      id: 'bandages',
      name: 'Boiled Linen',
      description: 'Between-scene wrap. Surgeon prefers Stabilize in a fight.',
      qty: 2,
    },
  ];
}

export const DEFAULT_FLAGS: Record<string, boolean | string | number> = {
  chest_carrier: '',
  seal_intact: true,
  pilgrim_trust: 2,
  mold_fate: '',
  party_is_forger: false,
  act1_beat: 'start',
  ambush_done: false,
  ferry_done: false,
  talked_cellarer: false,
  talked_mairia: false,
  has_loft_ambush: false,
  warn_seal_break: false,
  child_burial: '',
  narbonne_outcome: '',
  talked_parish: false,
  talked_narbonne: false,
  act1_complete: false,
  map_zone: 'act1_road',
  combat_mode: 'rtwp',
  act2_beat: '',
  priory_path: '',
  splinter_status: '',
  captain_deal: 'none',
  smoke_loft: false,
  talked_berna: false,
  talked_hugues: false,
  talked_serena: false,
  lord_name: '',
  lord_name_known: false,
  act3_beat: '',
  lord_fate: '',
  splinter_end: '',
  act3_done: false,
  talked_leper: false,
  hint_lord_road: false,
  hold_door_done: false,
  priory_fight_done: false,
  /** Engineering: Rest once-per-beat key (mapZone:beat). */
  rested_beat_key: '',
  road_help_cart: false,
  talked_wayside_monk: false,
  talked_cart_widow: false,
  talked_ferry_idler: false,
  talked_vine_boy: false,
  talked_leper_bell: false,
  talked_market_crier: false,
};

export const DIALOGUES: Record<string, DialogueNode[]> = {
  cellarer: [
    {
      id: 'start',
      speaker: 'Brother Guiraut',
      text: 'Chest came after Compline. Lead seal, splinter sold as a saint’s staff, and a letter calling poor apostles to a ruined priory in the Corbières. The seal is wrong — not loudly. Wrong by a month and a name that should not sit on the rim.',
      choices: [
        { text: 'Show me the fault in the seal.', next: 'seal_fault' },
        { text: 'Who paid for the wood and the lead?', next: 'who_paid' },
        { text: 'We ride. Who carries the bag?', next: 'carrier' },
      ],
    },
    {
      id: 'seal_fault',
      speaker: 'Brother Guiraut',
      text: 'Die-cut is a hair soft on the keys. Rim name belongs to a dead chamberlain. A crowd will kneel. A careful clerk will spit.',
      choices: [
        { text: 'Then we do not break the true letter to peek.', next: 'carrier' },
        { text: 'If I must verify the wax, I will own the sin.', next: 'carrier', effect: 'warn_seal_break' },
      ],
    },
    {
      id: 'who_paid',
      speaker: 'Brother Guiraut',
      text: 'Goldsmith in the river towns. Mold may still be under his floor. Viscount’s riders will want it. So will whoever hired the hand.',
      choices: [{ text: 'Names later. Who carries the bag?', next: 'carrier' }],
    },
    {
      id: 'carrier',
      speaker: 'Brother Guiraut',
      text: 'True sealed letter for Narbonne rides with you. Break that seal to read it and you become the next forger on this road. Pick who keeps the bag dry.',
      choices: [
        { text: 'Clerk takes it. Hands that know wax.', effect: 'carrier_clerk' },
        { text: 'Sergeant. If they take the bag, they take a fight.', effect: 'carrier_sergeant' },
        { text: 'Convers. He already carries the house keys.', effect: 'carrier_convers' },
      ],
    },
    {
      id: 'after',
      speaker: 'Brother Guiraut',
      text: 'The bag is spoken for. Walk the pilgrim road. Do not break the true seal.',
      choices: [
        { text: 'Peek the true letter anyway.', effect: 'break_true_seal' },
        { text: '(Leave)', effect: 'end' },
      ],
    },
  ],
  pilgrim_mairia: [
    {
      id: 'start',
      speaker: 'Mairia of Quillan',
      text: 'West to Galicia if the ferries hold. We have bread for three days if nobody steals the mule. You smell of abbey wax. Are you road-guard or tithe-men?',
      choices: [
        { text: 'Neither. We walk you as far as Narbonne.', next: 'walk_with', effect: 'pilgrim_trust_up' },
        { text: 'Ask fewer questions. Keep the column tight.', next: 'tight', effect: 'pilgrim_trust_flat' },
        { text: 'Move aside. Our letter does not wait on mules.', next: 'cold', effect: 'pilgrim_trust_down' },
      ],
    },
    {
      id: 'walk_with',
      speaker: 'Mairia of Quillan',
      text: 'Then share the mud. Men in borrowed badges have been cutting the draille paths. They wear crosses that do not match their horses.',
      choices: [{ text: 'Show me where they cut.', effect: 'end_hook_bandits' }],
    },
    {
      id: 'tight',
      speaker: 'Mairia of Quillan',
      text: 'Tight we can do. Still — if you hear iron in the scrub before the mile marker, it is not pilgrims.',
      choices: [{ text: 'Understood.', effect: 'end_hook_bandits' }],
    },
    {
      id: 'cold',
      speaker: 'Mairia of Quillan',
      text: 'Then ride past. When the badges come, do not look back for our smoke.',
      choices: [{ text: '(Leave the column)', effect: 'end_column_cold' }],
    },
    {
      id: 'after',
      speaker: 'Mairia of Quillan',
      text: 'The mile marker still smells of iron. Clear the badges, or the ferry will feel it.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  bandit_captain: [
    {
      id: 'start',
      speaker: 'Badge-Sergeant',
      text: 'Hospital work. Toll for the poor on the road. Open the chest and we count the charity.',
      choices: [
        { text: '[Clerk] Your badge is last year’s stamp. Wrong die.', next: 'call_bluff' },
        { text: '[Sergeant] Formation. Spears up. No one opens that chest.', effect: 'start_ambush' },
        { text: '[Guide] Take the side path. Leave them the empty road.', effect: 'slip_draille' },
      ],
    },
    {
      id: 'call_bluff',
      speaker: 'Badge-Sergeant',
      text: '…Mud on the road makes stamps soft. Or you are clever. Clever men bleed the same.',
      choices: [
        { text: 'Walk away. We keep the chest.', effect: 'bandits_withdraw' },
        { text: 'Then come take it.', effect: 'start_ambush' },
      ],
    },
  ],
  mold_choice: [
    {
      id: 'start',
      speaker: 'Viscount’s Rider',
      text: 'Goldsmith’s already fish-food. The mold is the crime that walks. Hand it up and the viscount names you friends of order. Drown it and nobody names anybody.',
      choices: [
        { text: 'Give him the mold.', effect: 'mold_given_viscount' },
        { text: 'We drown it. No more seals from this die.', effect: 'mold_drowned' },
        { text: '[Clerk] We keep it as proof for Narbonne.', effect: 'mold_kept' },
      ],
    },
    {
      id: 'after',
      speaker: 'Viscount’s Rider',
      text: 'The mold is settled. The ferry waits.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  priest_ramon: [
    {
      id: 'start',
      speaker: 'Father Ramon',
      text: 'Bells stay down. Burial ground locked until a legate says the word. The child is in the porch. Do not ask me for a mass I cannot say.',
      choices: [
        { text: '[Clerk] Record a lay burial. Ink is not a sacrament.', next: 'lay_burial' },
        { text: '[Surgeon] Dig outside the wall before the street sours.', next: 'outside' },
        { text: '[Convers] I have a shovel. Say where.', next: 'lay_burial' },
        { text: 'We cannot linger.', next: 'refuse' },
      ],
    },
    {
      id: 'lay_burial',
      speaker: 'Father Ramon',
      text: 'Write it under my name if you must. Peire — dusk, quiet, no bell. The column is watching from the road.',
      choices: [
        { text: 'We dig at dusk.', effect: 'child_burial_helped' },
        { text: 'Mark it deferred — we return after the ferry.', effect: 'child_burial_deferred' },
      ],
    },
    {
      id: 'outside',
      speaker: 'Father Ramon',
      text: 'Outside the wall is still earth. Elias, keep the linen boiled. If the pilgrims sing, stop them.',
      choices: [{ text: 'Quiet burial. Then the river.', effect: 'child_burial_helped' }],
    },
    {
      id: 'refuse',
      speaker: 'Father Ramon',
      text: 'Then keep your sealed letters. Roads remember who passed a porch like this with dry hands.',
      choices: [
        { text: '(Leave)', effect: 'child_burial_refused' },
        { text: 'Wait — we dig. No mass.', next: 'lay_burial' },
      ],
    },
    {
      id: 'after',
      speaker: 'Father Ramon',
      text: 'The porch is empty. Go. The Aude does not wait on clerks.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  ferry_rope: [
    {
      id: 'start',
      speaker: 'Ferryman Peire',
      text: 'Rope’s taut and watched. Far latch is theirs. You want the column across, Sergeant holds the planks while the Convers cuts — not the other way round.',
      choices: [
        { text: 'Form up — Hold, then Cut.', effect: 'start_ferry' },
        { text: '[Guide] There’s a sheep-gate downriver if trust buys silence.', next: 'alt', effect: 'ferry_alt_check' },
      ],
    },
    {
      id: 'alt',
      speaker: 'Ferryman Peire',
      text: 'Sheep-gate floods after rain. With friends in the column, maybe. Without them, you swim with the letter.',
      choices: [
        { text: 'We take the rope fight.', effect: 'start_ferry' },
        { text: 'Try the sheep-gate.', effect: 'start_ferry_sheepgate' },
      ],
    },
  ],
  narbonne_agent: [
    {
      id: 'clean',
      speaker: 'Agent (Narbonne)',
      text: 'Wax unbroken. Good. Names first — goldsmith’s already river-meat. Who paid the die, and who copied the chancery hand?',
      choices: [
        { text: 'Mold drowned. Trail ends in the Aude.', next: 'ask_mold_drowned' },
        { text: 'Mold to the viscount. He rides soft.', next: 'ask_mold_given' },
        { text: 'We kept the mold. Proof for your table.', next: 'ask_mold_kept' },
      ],
    },
    {
      id: 'forger',
      speaker: 'Agent (Narbonne)',
      text: 'That seal has been open. You smell like every clerk who thought peeking was clever. Speak carefully — or the gate keeps the letter and not you.',
      choices: [
        { text: 'We broke it to verify the hand. Here is what we read.', next: 'forger_confess' },
        { text: 'The bag was forced on the road. The words are still true.', next: 'forger_lie' },
        { text: '[Clerk] Refuse the hand-off. We ride past if the legate has gone north.', effect: 'narbonne_deferred_gate' },
      ],
    },
    {
      id: 'ask_mold_drowned',
      speaker: 'Agent (Narbonne)',
      text: 'Then nobody mints from that die again. Pilgrims?',
      choices: [{ text: 'Report the column.', next: 'pilgrims' }],
    },
    {
      id: 'ask_mold_given',
      speaker: 'Agent (Narbonne)',
      text: 'Viscount has a leash. He will use it. You bought a friend who collects.',
      choices: [{ text: 'Report the column.', next: 'pilgrims' }],
    },
    {
      id: 'ask_mold_kept',
      speaker: 'Agent (Narbonne)',
      text: 'Put it on the table. If the die matches the false rim, Arnau, you just bought us a hanging — theirs or yours.',
      choices: [{ text: 'Hand over the mold and the letter.', next: 'pilgrims', effect: 'mold_to_agent' }],
    },
    {
      id: 'forger_confess',
      speaker: 'Agent (Narbonne)',
      text: 'Honesty keeps you breathing. The letter is stained. I can still ride the names north if the pilgrims are off the killing ground.',
      choices: [{ text: 'Report the column.', next: 'pilgrims', effect: 'narbonne_letter_damaged' }],
    },
    {
      id: 'forger_lie',
      speaker: 'Agent (Narbonne)',
      text: 'Bandits who open papal wax and leave the courier standing? Try again.',
      choices: [
        { text: 'Fine — we peeked.', next: 'forger_confess' },
        { text: 'Then keep your gate. We move the column anyway.', effect: 'narbonne_refused_forger' },
      ],
    },
    {
      id: 'pilgrims',
      speaker: 'Agent (Narbonne)',
      text: 'The west road is a magazine if a box leads them. Where is Mairia’s column?',
      choices: [
        { text: 'With us — off the killing ground.', next: 'close_good', effect: 'narbonne_delivered' },
        { text: 'Scattered. We chose the bag over the mule.', next: 'close_cold', effect: 'narbonne_delivered' },
      ],
    },
    {
      id: 'close_good',
      speaker: 'Agent (Narbonne)',
      text: 'Act I ends here: letter in, pilgrims breathing, priory still waiting in the Corbières. Do not open another seal for sport.',
      choices: [{ text: '(End Act I frame)', effect: 'end_act1' }],
    },
    {
      id: 'close_cold',
      speaker: 'Agent (Narbonne)',
      text: 'Letter in. Road hostile. You will feel that in the hills. Priory next — if you still have five walking.',
      choices: [{ text: '(End Act I frame)', effect: 'end_act1' }],
    },
    {
      id: 'after',
      speaker: 'Agent (Narbonne)',
      text: 'Gate business is done. The Corbières wait.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  corbieres_road: [
    {
      id: 'start',
      speaker: 'Hill Road',
      text: 'Mud thins to scrub. The ruined priory sits east in the Corbières — Act II ground. Walk the stub road, or stay in Narbonne’s dust.',
      choices: [
        { text: 'Take the Corbières road.', effect: 'enter_corbieres' },
        { text: '(Stay)', effect: 'end' },
      ],
    },
  ],
  priory_stub: [
    {
      id: 'start',
      speaker: 'Priory Gate',
      text: 'Weathered boards on real stone. False altar inside. Berna holds the yard — Hugues’s pickets already count vine rows.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  berna: [
    {
      id: 'start',
      speaker: 'Berna',
      text: 'Rome’s wax is soft. This wood walked from a saint’s hand. Kneel and the vines keep their water. Stand aside and the northern host calls you a magazine.',
      choices: [
        { text: '[Clerk] That seal’s rim name is dead. Your bull is a month wrong.', next: 'call_seal' },
        { text: '[Guide] Half these faces are hired. The other half are hungry.', next: 'crowd_read' },
        { text: 'We only came to see the box.', next: 'see_box' },
      ],
    },
    {
      id: 'call_seal',
      speaker: 'Berna',
      text: 'A clerk’s tongue. The square hears wood, not Latin. Prove it without a riot or step back.',
      choices: [
        { text: 'Talk them apart — no blades in the yard.', next: 'fork', effect: 'priory_path_talk' },
        { text: 'We take the chest when your backs turn.', next: 'fork', effect: 'priory_path_steal' },
      ],
    },
    {
      id: 'crowd_read',
      speaker: 'Berna',
      text: 'Hungry men still kneel. Hungry men also run if the loft catches fire.',
      choices: [
        { text: 'Hold the nave door. Get people out the sheep-gate.', next: 'fork', effect: 'priory_path_hold' },
        { text: 'Talk first. Steel second.', next: 'fork', effect: 'priory_path_talk' },
      ],
    },
    {
      id: 'see_box',
      speaker: 'Berna',
      text: 'Look. Don’t touch. Touching is for the apostles.',
      choices: [
        { text: '[Convers] Latch is soft. We can lift it in the smoke.', next: 'fork', effect: 'priory_path_steal' },
        { text: 'Enough looking.', next: 'fork', effect: 'priory_path_talk' },
      ],
    },
    {
      id: 'fork',
      speaker: 'Berna',
      text: 'Choose, then. The captain’s pickets are already counting vine rows.',
      choices: [{ text: '(Commit the path)', effect: 'end_priory_fork' }],
    },
    {
      id: 'after',
      speaker: 'Berna',
      text: 'Path is set. The loft or the captain next — not both at once if you can help it.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  hugues: [
    {
      id: 'start',
      speaker: 'Captain Hugues',
      text: 'This ruin is a warrant. Heretics in the nave, vines unpaid, my men fed. Hand me a reason not to burn the sheep-gate behind you.',
      choices: [
        { text: '[Clerk] The bull is forged. Hang the goldsmith’s die, not the village.', next: 'forge_proof' },
        { text: '[Sergeant] You want a clean excuse. A massacre makes a dirty one.', next: 'clean_excuse' },
        { text: 'Take the stones. Leave the people the path.', effect: 'captain_vines_seized' },
      ],
    },
    {
      id: 'forge_proof',
      speaker: 'Captain Hugues',
      text: 'Show me lead that matches, or a mold, or a name. Paper without teeth is weather.',
      choices: [
        { text: 'We kept the mold. Match it.', next: 'mold_show', effect: 'need_mold_kept' },
        { text: 'Mold’s in the Aude. You’ll have to trust a clerk’s eye.', next: 'no_mold' },
        { text: 'Viscount has the mold. Ride his leash.', next: 'viscount_leash' },
      ],
    },
    {
      id: 'mold_show',
      speaker: 'Captain Hugues',
      text: '…Die fits the false rim. Fine. I spare the yard. I still take the priory stones for the host.',
      choices: [{ text: 'Stones, not blood.', effect: 'captain_vines_spared' }],
    },
    {
      id: 'no_mold',
      speaker: 'Captain Hugues',
      text: 'Trust is expensive. Coin or a hostage night, or I count vines my way.',
      choices: [
        { text: 'Pay him off. Column stays fed.', effect: 'captain_bribed_off' },
        { text: 'No deal. We hold what we hold.', effect: 'captain_vines_seized' },
      ],
    },
    {
      id: 'viscount_leash',
      speaker: 'Captain Hugues',
      text: 'Then the viscount and I will speak. You bought a soft rider a louder friend.',
      choices: [{ text: '(Leave him to it)', effect: 'captain_vines_spared' }],
    },
    {
      id: 'clean_excuse',
      speaker: 'Captain Hugues',
      text: 'Guillem talks like a man who has starved a castle. Very well — door held, people gone, I claim empty stone.',
      choices: [{ text: 'Empty stone. We’re done here.', effect: 'captain_vines_spared' }],
    },
    {
      id: 'after',
      speaker: 'Captain Hugues',
      text: 'The warrant is settled enough. Serena still knows which lord paid the die.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  serena: [
    {
      id: 'start',
      speaker: 'Na Serena',
      text: 'My husband sold wine to whoever paid for that lead die. The lord who signed the purse sits warm in a hill house. Name him in Narbonne and he hangs. Stay quiet and he hides you once.',
      choices: [
        { text: 'Give the name. Act III will need it.', effect: 'learn_lord_name' },
        { text: 'Keep it. We may need a roof more than a hanging.', effect: 'lord_name_withheld' },
      ],
    },
    {
      id: 'after',
      speaker: 'Na Serena',
      text: 'I’ve said what I’ll say. The hill house waits or it doesn’t.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  hold_door: [
    {
      id: 'start',
      speaker: 'Nave Door',
      text: 'Sergeant Holds the nave — Convers opens the sheep-gate. Same muscle as the ferry rope, different wood.',
      choices: [
        { text: 'Form up — Hold the door.', effect: 'start_hold_door' },
        { text: '(Not yet)', effect: 'end' },
      ],
    },
  ],
  road_back_narbonne: [
    {
      id: 'start',
      speaker: 'Road West',
      text: 'Back toward Narbonne and the Aude road. River watch opens after Serena, a settled Hugues deal, or the priory fight’s end.',
      choices: [
        { text: 'Return to the Act I road (Fontfroide–Narbonne).', effect: 'enter_act1_road' },
        { text: 'Take the river watch — Act III close.', effect: 'enter_act3' },
        { text: '(Stay)', effect: 'end' },
      ],
    },
    {
      id: 'gate_act3',
      speaker: 'Road West',
      text: 'Not yet — speak Serena, settle Hugues, or finish the priory fight. Then the river.',
      choices: [{ text: '(Understood)', effect: 'end' }],
    },
  ],
  river_watch: [
    {
      id: 'start',
      speaker: 'Catalana',
      text: 'Willows again. Same watch eyes as the infirmarian will name at dawn — if we sleep there. Captains don’t like leper doors.',
      choices: [
        { text: 'Take the infirmary roof.', next: 'to_leper', effect: 'act3_to_leper' },
        { text: '[Sergeant] Push for the hill house tonight.', next: 'to_lord', effect: 'act3_to_lord' },
        { text: 'Skip roofs. Straight to the wood’s end.', effect: 'act3_to_splinter' },
      ],
    },
    {
      id: 'to_leper',
      speaker: 'Sergeant Guillem',
      text: 'Quiet approach. Elias works; the rest don’t sing.',
      choices: [{ text: '(Go)', effect: 'end' }],
    },
    {
      id: 'to_lord',
      speaker: 'Arnau the Clerk',
      text: 'If we have Raimon’s name, the rope is already on the table. If we don’t, the house may be empty.',
      choices: [{ text: '(Go)', effect: 'end' }],
    },
  ],
  leper_house: [
    {
      id: 'start',
      speaker: 'Infirmarian',
      text: 'Bells don’t ring here either. You can sleep if you don’t bring captains to the door. The Surgeon works; the rest keep quiet.',
      choices: [
        { text: '[Surgeon] Boil linen. We stay till dawn.', next: 'work' },
        { text: '[Clerk] Any courier hide here since the ferry fights?', next: 'courier' },
        { text: 'We move before dawn.', effect: 'skip_leper' },
      ],
    },
    {
      id: 'courier',
      speaker: 'Infirmarian',
      text: 'One hooded man left wax scrap in the ash. Not papal — household. Hill-road grit on the boot mud.',
      choices: [
        { text: 'That tracks to Quéribus.', next: 'work', effect: 'hint_lord_road' },
        { text: 'Burn the scrap. We sleep.', next: 'work' },
      ],
    },
    {
      id: 'work',
      speaker: 'Master Elias',
      text: 'Hold still who can. Time and linen — not miracles. Anyone still bleeding loses the next spear stand.',
      choices: [{ text: 'Dawn, then.', next: 'dawn', effect: 'rest_leper' }],
    },
    {
      id: 'dawn',
      speaker: 'Infirmarian',
      text: 'Road’s wet. Someone watched the gate from the willows. Not pilgrims. If you owe a hill lord silence, spend it carefully.',
      choices: [
        { text: 'Hill house next.', effect: 'end_leper_to_lord' },
        { text: 'We’ve had enough roofs. The splinter.', effect: 'end_leper_to_splinter' },
      ],
    },
    {
      id: 'after',
      speaker: 'Infirmarian',
      text: 'Door stays shut. Don’t bring iron back.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  lord_raimon: [
    {
      id: 'start',
      speaker: 'Raimon of Quéribus',
      text: 'You have my name. That is already a rope. I hid a courier once. I can hide five — if the splinter does not walk through my market.',
      choices: [
        { text: 'Hide us. We never write your name into any letter.', next: 'hide' },
        { text: 'We already sent your name toward Narbonne.', next: 'named' },
        { text: '[Clerk] Walk away. No hide, no hanging from our hand.', next: 'walk' },
        { text: '[Sergeant] Pay in grain for the column. Silence costs food.', next: 'grain' },
      ],
    },
    {
      id: 'hide',
      speaker: 'Raimon of Quéribus',
      text: 'Cellar until the host’s dust settles. If Berna’s wood appears in my square, the deal burns with it.',
      choices: [
        { text: 'Splinter will not walk your market.', effect: 'lord_hidden' },
        { text: 'We can’t promise the wood’s end yet.', next: 'hide_risk' },
      ],
    },
    {
      id: 'hide_risk',
      speaker: 'Raimon of Quéribus',
      text: 'Then you get one night, not a season. Leave before Compline tomorrow.',
      choices: [{ text: 'One night.', effect: 'lord_hidden' }],
    },
    {
      id: 'named',
      speaker: 'Raimon of Quéribus',
      text: 'Then I am already dead on paper. Get out before my men decide you are the rope.',
      choices: [
        { text: 'We go.', effect: 'lord_named_hanged' },
        { text: '[Guide] Sheep-path out. Now.', effect: 'lord_named_hanged' },
      ],
    },
    {
      id: 'walk',
      speaker: 'Raimon of Quéribus',
      text: 'Clever cowardice. I ride north before someone less polite arrives.',
      choices: [{ text: '(Leave him to the road)', effect: 'lord_unnamed_fled' }],
    },
    {
      id: 'grain',
      speaker: 'Raimon of Quéribus',
      text: 'Grain for silence. Take it. If Narbonne already has my name, you’ve robbed a corpse.',
      choices: [
        { text: 'Silence and grain. We never wrote you.', effect: 'lord_hidden_grain' },
        { text: 'Name’s already gone. Keep your grain.', effect: 'lord_named_hanged' },
      ],
    },
    {
      id: 'after',
      speaker: 'Raimon of Quéribus',
      text: 'Door’s done with you. Mind the wood.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  lord_rumor: [
    {
      id: 'start',
      speaker: 'Empty Hill House',
      text: 'Shutters out. Ash cold. Someone rode north before you — or never meant to be found.',
      choices: [
        { text: '[Guide] Tracks toward the willows, then gone.', effect: 'lord_unnamed_fled' },
        { text: 'Nothing here. The splinter waits.', effect: 'lord_unnamed_fled' },
      ],
    },
    {
      id: 'hinted',
      speaker: 'Empty Hill House',
      text: 'Boot grit matches the infirmary ash. He’s ahead of you on the north track — not waiting.',
      choices: [
        { text: '[Guide] He’s ahead. We don’t chase.', effect: 'lord_unnamed_fled' },
        { text: 'Then the splinter.', effect: 'lord_unnamed_fled' },
      ],
    },
    {
      id: 'after',
      speaker: 'Empty Hill House',
      text: 'Dust and an open gate. The square still waits on the wood.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  splinter_judgment: [
    {
      id: 'start',
      speaker: 'Arnau the Clerk',
      text: 'Wood or politics. Put it back on an altar and someone else will kneel. Break it in the square as pine and the crowd learns what wax was worth. Keep it and you become the next chest.',
      choices: [
        { text: 'Return it to a quiet altar. No market walk.', next: 'altar' },
        { text: 'Break it public. Call it pine.', next: 'break' },
        { text: 'Keep it in the bag. We are not done with roads.', next: 'keep' },
        { text: '[Convers] Let Peire snap it here — no crowd, no altar.', next: 'break_quiet' },
      ],
    },
    {
      id: 'altar',
      speaker: 'Brother Peire',
      text: 'Quiet stone. I’ll set it where no market sees. Don’t ask which house.',
      choices: [{ text: 'Set it.', next: 'close', effect: 'splinter_altar' }],
    },
    {
      id: 'break',
      speaker: 'Catalana',
      text: 'Square’s wet enough. They’ll hear pine. Some will hate us. Some will stop kneeling at boxes.',
      choices: [{ text: 'Break it.', next: 'close', effect: 'splinter_broken_public' }],
    },
    {
      id: 'break_quiet',
      speaker: 'Brother Peire',
      text: 'No sermon. Just wood. Same truth, fewer ears.',
      choices: [{ text: 'Snap it.', next: 'close', effect: 'splinter_broken_quiet' }],
    },
    {
      id: 'keep',
      speaker: 'Sergeant Guillem',
      text: 'Then we stay the next chest. Formation stays up. I’m not dying for a secret pine.',
      choices: [{ text: 'Bag stays. We walk.', next: 'close', effect: 'splinter_kept_bag' }],
    },
    {
      id: 'close',
      speaker: 'Sergeant Guillem',
      text: 'War’s still south and north. We named what we could. Formation — we walk.',
      choices: [{ text: '(End campaign frame)', effect: 'end_act3' }],
    },
    {
      id: 'after',
      speaker: 'Sergeant Guillem',
      text: 'Frame’s closed. Keep your boots dry.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  act3_gate: [
    {
      id: 'start',
      speaker: 'River Watch Path',
      text: 'Act III close: willows, leper roof, hill lord, then the splinter — altar, pine, or bag.',
      choices: [
        { text: 'Walk the closing pass.', effect: 'enter_act3' },
        { text: '(Not yet)', effect: 'end' },
      ],
    },
  ],
  road_to_corbieres_from_act3: [
    {
      id: 'start',
      speaker: 'Hill Road East',
      text: 'Back toward the Corbières priory stub.',
      choices: [
        { text: 'Return to Corbières.', effect: 'enter_corbieres' },
        { text: '(Stay)', effect: 'end' },
      ],
    },
  ],
  road_to_narbonne_from_act3: [
    {
      id: 'start',
      speaker: 'Road to Narbonne',
      text: 'Dust toward the gate and the Fontfroide road.',
      choices: [
        { text: 'Return to the Act I road.', effect: 'enter_act1_road' },
        { text: '(Stay)', effect: 'end' },
      ],
    },
  ],
  // --- Interactive cast (13): party RMB + road NPCs ---
  party_guide: [
    {
      id: 'start',
      speaker: 'Catalana',
      text: 'Draille’s soft after rain. Badges like borrowed stamps, houses that still take strangers, loft angles — ask before you charge the nave.',
      choices: [
        { text: 'Any cut off the road?', next: 'cut' },
        { text: 'What do you make of the column?', next: 'column' },
        { text: '(Leave her to scout)', effect: 'end' },
      ],
    },
    {
      id: 'cut',
      speaker: 'Catalana',
      text: 'Sheep-paths behind the mile marker, and a willow ditch before the ferry. Both beat dying on the crown of the road.',
      choices: [{ text: 'Show me when it matters.', effect: 'end' }],
    },
    {
      id: 'column',
      speaker: 'Catalana',
      text: 'Hungry mouths are witnesses. Lose them and every village hears we chose a bag over a mule.',
      choices: [{ text: 'Understood.', effect: 'end' }],
    },
  ],
  party_sergeant: [
    {
      id: 'start',
      speaker: 'Sergeant Guillem',
      text: 'Formation first. I Hold doors and ropes; you don’t sprint Cut. Watch rotations — if someone’s bleeding, Elias works before I shove another spear.',
      choices: [
        { text: 'How do you want us lined?', next: 'line' },
        { text: 'The bag.', next: 'bag' },
        { text: '(Back to the road)', effect: 'end' },
      ],
    },
    {
      id: 'line',
      speaker: 'Sergeant Guillem',
      text: 'Me front. Convers on latches. Guide loft if there’s a loft. Clerk behind my shoulder. Surgeon last — he’s not a blade.',
      choices: [{ text: 'Locked.', effect: 'end' }],
    },
    {
      id: 'bag',
      speaker: 'Sergeant Guillem',
      text: 'Whoever carries it doesn’t drop it for cleverness. Broken wax makes us the next forgers on this road.',
      choices: [{ text: 'Bag stays dry.', effect: 'end' }],
    },
  ],
  party_convers: [
    {
      id: 'start',
      speaker: 'Brother Peire',
      text: 'Keys, grain, soft latches. I cut rope under Hold — not before. If you need a quiet snap of pine later, my hands are already dirty from barn work.',
      choices: [
        { text: 'Abbey life miss you?', next: 'abbey' },
        { text: 'Any lock ahead worry you?', next: 'lock' },
        { text: '(Leave him)', effect: 'end' },
      ],
    },
    {
      id: 'abbey',
      speaker: 'Brother Peire',
      text: 'Fontfroide still has oats. This road has captains. I know which one starves you slower.',
      choices: [{ text: 'Fair.', effect: 'end' }],
    },
    {
      id: 'lock',
      speaker: 'Brother Peire',
      text: 'Goldsmith floorboards, nave bars, sheep-gates — all softer than they look if nobody’s watching the hinge.',
      choices: [{ text: 'I’ll call you to the hinge.', effect: 'end' }],
    },
  ],
  party_clerk: [
    {
      id: 'start',
      speaker: 'Arnau the Clerk',
      text: 'Seals, rim names, chancery hands. I Call out lies on badges and I do not peek the true letter unless you order a sin we both own.',
      choices: [
        { text: 'Remind me what was wrong with their bull.', next: 'bull' },
        { text: 'Narbonne.', next: 'narb' },
        { text: '(Leave the ink alone)', effect: 'end' },
      ],
    },
    {
      id: 'bull',
      speaker: 'Arnau the Clerk',
      text: 'Die soft on the keys. Rim name belongs to a dead chamberlain. Crowd kneels; careful clerks spit.',
      choices: [{ text: 'Keep spitting.', effect: 'end' }],
    },
    {
      id: 'narb',
      speaker: 'Arnau the Clerk',
      text: 'Agent wants names and unbroken wax. Mold kept, drowned, or given — each writes a different rope.',
      choices: [{ text: 'We’ll choose cleanly.', effect: 'end' }],
    },
  ],
  party_surgeon: [
    {
      id: 'start',
      speaker: 'Master Elias',
      text: 'I’m not a blade. Stabilize in the press; Rest between roofs — linen and time, once a beat. Prayer is weather, not a button.',
      choices: [
        { text: 'Who’s worst right now?', next: 'triage' },
        { text: 'What poisons should we fear?', next: 'poison' },
        { text: '(Let him pack linen)', effect: 'end' },
      ],
    },
    {
      id: 'triage',
      speaker: 'Master Elias',
      text: 'Whoever’s marked bleeding drops next if I don’t touch them. Out-for-act means they walk the mule, not the spear line.',
      choices: [{ text: 'I’ll call Rest at the next roof.', effect: 'end' }],
    },
    {
      id: 'poison',
      speaker: 'Master Elias',
      text: 'Well water after a host camps, and anything a goldsmith leaves in a cup. Boil what you can. Don’t kiss relics.',
      choices: [{ text: 'Noted.', effect: 'end' }],
    },
  ],
  wayside_monk: [
    {
      id: 'start',
      speaker: 'Wayside Monk',
      text: 'Cross is older than this war. I don’t bless captains. I count who still buries their dead.',
      choices: [
        { text: 'Seen borrowed badges?', next: 'badges' },
        { text: 'Any word of Fontfroide’s chest?', next: 'chest' },
        { text: '(Pass on)', effect: 'end' },
      ],
    },
    {
      id: 'badges',
      speaker: 'Wayside Monk',
      text: 'Men with Hospital marks and farmer horses. Catalana would smell them before I finished the Ave.',
      choices: [{ text: 'Obliged.', effect: 'end' }],
    },
    {
      id: 'chest',
      speaker: 'Wayside Monk',
      text: 'Abbey wax on the road is never holy for long. Keep your seal bag closed.',
      choices: [{ text: 'We intend to.', effect: 'end' }],
    },
    {
      id: 'after',
      speaker: 'Wayside Monk',
      text: 'Still counting graves. The road doesn’t get shorter.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  cart_widow: [
    {
      id: 'start',
      speaker: 'Cart Widow',
      text: 'Axle’s cracked and the host eats axles. Don’t ask me for the pilgrim road’s kindness — ask if you’ve got a Convers who can brace wood.',
      choices: [
        { text: '[Convers] I can brace it. No coin.', next: 'brace', effect: 'road_help_cart' },
        { text: 'We can’t linger.', effect: 'end' },
      ],
    },
    {
      id: 'brace',
      speaker: 'Cart Widow',
      text: 'Then the next village owes you bread, not me. Go before the badges smell a stopped cart.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
    {
      id: 'after',
      speaker: 'Cart Widow',
      text: 'Axle holds. Don’t stand in the ruts.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  ferry_idler: [
    {
      id: 'start',
      speaker: 'Idle Boatman',
      text: 'Rope fight’s for men with sergeants. I just know the Aude takes whatever you drop — mold, bodies, bad seals.',
      choices: [
        { text: 'Any watch on the far latch?', next: 'watch' },
        { text: '(Leave)', effect: 'end' },
      ],
    },
    {
      id: 'watch',
      speaker: 'Idle Boatman',
      text: 'Always. Cut under Hold or swim with your letter.',
      choices: [{ text: 'We’ll Hold.', effect: 'end' }],
    },
    {
      id: 'after',
      speaker: 'Idle Boatman',
      text: 'River’s still hungry. Keep your bag dry.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  vine_boy: [
    {
      id: 'start',
      speaker: 'Vine Boy',
      text: 'Northern men count rows like they’re already paid. Berna’s box makes old women kneel. I just want the sheep-gate left open.',
      choices: [
        { text: 'Where’s the loft?', next: 'loft' },
        { text: 'Who paid for the show?', next: 'pay' },
        { text: '(Move on)', effect: 'end' },
      ],
    },
    {
      id: 'loft',
      speaker: 'Vine Boy',
      text: 'Above the false altar. Crossbow likes that cough of smoke.',
      choices: [{ text: 'Catalana’s problem.', effect: 'end' }],
    },
    {
      id: 'pay',
      speaker: 'Vine Boy',
      text: 'Ask Na Serena. She sold wine to the purse. I only carry baskets.',
      choices: [{ text: 'We will.', effect: 'end' }],
    },
    {
      id: 'after',
      speaker: 'Vine Boy',
      text: 'Gate still stuck. Rows still counted.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],
  leper_bell: [
    {
      id: 'start',
      speaker: 'Gate Ringer',
      text: 'No parish bells. We ring wood so captains don’t pretend they didn’t see the door. Sleep if Elias is with you. Don’t bring iron inside.',
      choices: [{ text: 'Understood.', effect: 'end' }],
    },
  ],
  market_crier: [
    {
      id: 'start',
      speaker: 'Market Crier',
      text: 'Interdict weather — thin market, locked ground, rumors thicker than bread. Hooded clerks buy silence with unbroken wax.',
      choices: [
        { text: 'Seen a legate ride?', next: 'legate' },
        { text: '(Pass)', effect: 'end' },
      ],
    },
    {
      id: 'legate',
      speaker: 'Market Crier',
      text: 'North, or so the ferrymen swear. Your agent will know if the letter still matters.',
      choices: [{ text: 'We’ll ask him.', effect: 'end' }],
    },
    {
      id: 'after',
      speaker: 'Market Crier',
      text: 'Still thin. Still talking.',
      choices: [{ text: '(Leave)', effect: 'end' }],
    },
  ],

};

export const NPCS = [
  // Tile coords = world meters / TILE(1.2). Hubs per docs/open-map-extents-act1.md
  {
    id: 'cellarer',
    name: 'Brother Guiraut',
    color: 0x6a6a58,
    x: -5.0,
    z: 31.7,
    dialogueId: 'cellarer',
    hint: 'Talk to the cellarer',
  },
  {
    id: 'mairia',
    name: 'Mairia of Quillan',
    color: 0x6a5038,
    x: 1.8,
    z: 18.5,
    dialogueId: 'pilgrim_mairia',
    hint: 'Talk to Mairia',
  },
  {
    id: 'wayside_monk',
    name: 'Wayside Monk',
    color: 0x5a5848,
    x: -1.83,
    z: 20.0,
    dialogueId: 'wayside_monk',
    hint: 'Talk to wayside monk',
  },
  {
    id: 'cart_widow',
    name: 'Cart Widow',
    color: 0x6a5040,
    x: 2.0,
    z: 16.67,
    dialogueId: 'cart_widow',
    hint: 'Talk to cart widow',
  },
  {
    id: 'bandits',
    name: 'Badge Bandits',
    color: 0x3a3028,
    x: 0.9,
    z: 6.7,
    dialogueId: 'bandit_captain',
    hint: 'Confront badge bandits',
    combat: true,
  },
  {
    id: 'parish',
    name: 'Father Ramon',
    color: 0x5a5848,
    x: 5.8,
    z: -1.7,
    dialogueId: 'priest_ramon',
    hint: 'Parish porch',
  },
  {
    id: 'mold',
    name: 'Viscount’s Rider',
    color: 0x4a4858,
    x: -5.8,
    z: -11.7,
    dialogueId: 'mold_choice',
    hint: 'Mold choice',
  },
  {
    id: 'ferry',
    name: 'Ferry Rope',
    color: 0x4a4030,
    x: 0.0,
    z: -26.7,
    dialogueId: 'ferry_rope',
    hint: 'Ferry crossing',
    combat: true,
  },
  {
    id: 'ferry_idler',
    name: 'Idle Boatman',
    color: 0x4a5048,
    x: -2.08,
    z: -25.0,
    dialogueId: 'ferry_idler',
    hint: 'Talk to boatman',
  },
  {
    id: 'narbonne',
    name: 'Narbonne Agent',
    color: 0x3a4858,
    x: 4.2,
    z: -36.7,
    dialogueId: 'narbonne_agent',
    hint: 'Deliver the letter',
  },
  {
    id: 'market_crier',
    name: 'Market Crier',
    color: 0x5a4840,
    x: 2.92,
    z: -35.0,
    dialogueId: 'market_crier',
    hint: 'Market crier',
  },
  {
    id: 'vine_boy',
    name: 'Vine Boy',
    color: 0x5a5038,
    x: -2.67,
    z: -21.67,
    dialogueId: 'vine_boy',
    hint: 'Vine boy at Corbières turnoff',
  },
  {
    id: 'corbieres_road',
    name: 'Road to Corbières',
    color: 0x4a4030,
    x: -3.3,
    z: -23.3,
    dialogueId: 'corbieres_road',
    hint: 'Hill road to Corbières (Act II stub)',
  },
] as const satisfies readonly NpcDef[];
export const CORBIERES_NPCS = [
  {
    id: 'priory_door',
    name: 'Priory Gate',
    color: 0x5a5848,
    x: -2.2,
    z: -3.5,
    dialogueId: 'priory_stub',
    hint: 'Priory gate',
  },
  {
    id: 'berna',
    name: 'Berna',
    color: 0x6a5038,
    x: 0.2,
    z: -2.0,
    dialogueId: 'berna',
    hint: 'Yard preacher — hard fork',
  },
  {
    id: 'hold_door',
    name: 'Nave Door',
    color: 0x4a4030,
    x: 2.0,
    z: -3.2,
    dialogueId: 'hold_door',
    hint: 'Hold door / sheep-gate (ferry pattern)',
    combat: true,
  },
  {
    id: 'hugues',
    name: 'Captain Hugues',
    color: 0x4a4858,
    x: -1.5,
    z: 0.5,
    dialogueId: 'hugues',
    hint: 'Northern captain',
  },
  {
    id: 'serena',
    name: 'Na Serena',
    color: 0x5a5040,
    x: 2.2,
    z: 1.0,
    dialogueId: 'serena',
    hint: 'Vine widow — name seed',
  },
  {
    id: 'vine_boy',
    name: 'Vine Boy',
    color: 0x5a5038,
    x: 2.4,
    z: 2.2,
    dialogueId: 'vine_boy',
    hint: 'Vine boy on the approach',
  },
  {
    id: 'road_back',
    name: 'Road to Narbonne',
    color: 0x4a4030,
    x: 0.0,
    z: 3.5,
    dialogueId: 'road_back_narbonne',
    hint: 'Return toward Narbonne / Act III',
  },
  {
    id: 'act3_road',
    name: 'River Watch / Act III',
    color: 0x3a4858,
    x: -2.5,
    z: 3.2,
    dialogueId: 'act3_gate',
    hint: 'Act III close (after Serena)',
  },
] as const satisfies readonly NpcDef[];

export const ACT3_NPCS = [
  {
    id: 'river_watch',
    name: 'Willow Watch',
    color: 0x5a5040,
    x: 0.0,
    z: 1.2,
    dialogueId: 'river_watch',
    hint: 'Willow watch / river path',
  },
  {
    id: 'leper',
    name: 'Leper House',
    color: 0x4a5848,
    x: -2.0,
    z: -1.5,
    dialogueId: 'leper_house',
    hint: 'Infirmary roof',
  },
  {
    id: 'leper_bell',
    name: 'Gate Ringer',
    color: 0x4a5840,
    x: -2.8,
    z: -0.6,
    dialogueId: 'leper_bell',
    hint: 'Gate ringer — ambient',
  },
  {
    id: 'lord',
    name: 'Hill House',
    color: 0x4a4858,
    x: 1.8,
    z: -2.2,
    dialogueId: 'lord_raimon',
    hint: 'Lord Raimon — hide or hang',
  },
  {
    id: 'lord_empty',
    name: 'Empty Hill House',
    color: 0x3a3830,
    x: 2.8,
    z: -1.0,
    dialogueId: 'lord_rumor',
    hint: 'Empty hill house if no name',
  },
  {
    id: 'splinter',
    name: 'Splinter Judgment',
    color: 0x6a5a48,
    x: 0.2,
    z: -3.8,
    dialogueId: 'splinter_judgment',
    hint: 'Altar / break / keep / quiet snap',
  },
  {
    id: 'road_corbieres',
    name: 'Road to Corbières',
    color: 0x4a4030,
    x: 2.5,
    z: 3.2,
    dialogueId: 'road_to_corbieres_from_act3',
    hint: 'Back to Corbières',
  },
  {
    id: 'road_narbonne',
    name: 'Road to Narbonne',
    color: 0x4a4030,
    x: -2.5,
    z: 3.2,
    dialogueId: 'road_to_narbonne_from_act3',
    hint: 'Back to Fontfroide–Narbonne road',
  },
] as const satisfies readonly NpcDef[];

/** Act III entry on the Act I road (near Narbonne) — not a dead end after Serena. */
export const ACT1_ACT3_GATE: NpcDef = {
  id: 'act3_gate',
  name: 'River Watch / Act III',
  color: 0x3a4858,
  x: 2.5,
  z: -40.0,
  dialogueId: 'act3_gate',
  hint: 'Act III close (after Serena)',
};

export function npcsForZone(zone: MapZone): NpcDef[] {
  if (zone === 'corbieres') return [...CORBIERES_NPCS];
  if (zone === 'act3_close') return [...ACT3_NPCS];
  return [...NPCS, ACT1_ACT3_GATE];
}

