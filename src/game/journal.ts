import type { JournalEntry, PartyMember } from './types';

type FlagMap = Record<string, boolean | string | number>;

function trustLabel(trust: number): string {
  if (trust <= 0) return 'scattered';
  if (trust === 1) return 'uneasy';
  if (trust === 2) return 'steady';
  return 'loyal';
}

function burialNote(fate: string): string {
  if (fate === 'helped') return 'You dug a quiet lay burial. The column noticed.';
  if (fate === 'refused') return 'You left the porch. Roads remember dry hands.';
  if (fate === 'deferred') return 'Burial marked deferred — a debt for the hills.';
  return '';
}

function moldNote(fate: string): string {
  if (fate === 'given_viscount') return 'Mold handed to the viscount’s rider. A soft road, a hard leash later.';
  if (fate === 'drowned') return 'Mold drowned in the Aude. No die walks from that goldsmith again.';
  if (fate === 'kept') return 'Mold kept as proof. Heavy in the bag, heavier at every gate.';
  return '';
}

function narbonneNote(outcome: string): string {
  if (outcome === 'delivered') return 'Letter delivered. Names ride north.';
  if (outcome === 'letter_damaged') return 'Letter stained but accepted. You are known as a peeker.';
  if (outcome === 'refused_forger') return 'Gate kept you out. The column moved without a clean hand-off.';
  if (outcome === 'deferred_gate') return 'You rode past Narbonne. The legate may already be north.';
  return '';
}

/** Quest-log entries derived from story flags — never dump raw keys. */
export function buildJournal(flags: FlagMap, _party?: PartyMember[]): JournalEntry[] {
  const entries: JournalEntry[] = [];
  const carrier = String(flags.chest_carrier || '');
  const sealIntact = !!flags.seal_intact;
  const forger = !!flags.party_is_forger || !sealIntact;
  const trust = Number(flags.pilgrim_trust) || 0;
  const ambushDone = !!flags.ambush_done;
  const moldFate = String(flags.mold_fate || '');
  const burial = String(flags.child_burial || '');
  const ferryDone = !!flags.ferry_done;
  const narbonne = String(flags.narbonne_outcome || '');
  const talkedCellarer = !!flags.talked_cellarer;
  const talkedMairia = !!flags.talked_mairia;
  const parishTouched = !!flags.talked_parish || burial !== '';
  const act1Complete =
    !!flags.act1_complete || narbonne !== '' || String(flags.act1_beat) === 'narbonne_gate';

  // q_chest — always visible
  {
    let status: JournalEntry['status'] = 'active';
    let body =
      'Brother Guiraut holds a near-true chest at Fontfroide — false rim on the show seal, true letter for Narbonne. Choose who carries the bag. Do not break the true wax.';
    if (talkedCellarer && carrier) {
      body = forger
        ? `The chest rides with the ${carrier}. True seal broken — you peeked. Gates will smell wax on your hands.`
        : `The chest rides with the ${carrier}. Seal intact. Keep the bag dry on the pilgrim road.`;
    }
    if (narbonne || act1Complete) {
      status = 'done';
      body = `Fontfroide bag settled at Narbonne’s door. Carrier was the ${carrier || 'unset'}. Seal ended ${sealIntact ? 'intact' : 'broken'}.`;
    }
    entries.push({ id: 'q_chest', title: 'The Fontfroide chest', body, status, sort: 10 });
  }

  // q_pilgrims
  if (carrier) {
    let status: JournalEntry['status'] = 'active';
    let body = `Mairia’s column: trust ${trustLabel(trust)} (${trust}/3). Feed them, walk them, or leave them to the badges.`;
    if (trust <= 0 && ambushDone) {
      status = 'failed';
      body = 'Column scattered after the ambush window. Ferry will feel the empty road.';
    }
    if (narbonne || act1Complete) {
      status = trust <= 0 ? 'failed' : 'done';
      body =
        trust <= 0
          ? 'Column lost or scattered before Narbonne. The hills will be harder for it.'
          : `Column reported at Narbonne — trust ended ${trustLabel(trust)}.`;
    }
    entries.push({ id: 'q_pilgrims', title: 'The westbound column', body, status, sort: 20 });
  }

  // q_ambush
  if (talkedMairia || carrier) {
    let status: JournalEntry['status'] = ambushDone ? 'done' : 'active';
    let body = ambushDone
      ? 'Ambush cleared or slipped. Torn badges in the mud.'
      : 'Borrowed badges on the wet road. Guide can Point the false stamps; Clerk can Call them out — or take the spears.';
    entries.push({ id: 'q_ambush', title: 'Borrowed badges', body, status, sort: 30 });
  }

  // q_parish
  if (ambushDone) {
    const status: JournalEntry['status'] = burial ? 'done' : 'active';
    const body = burial
      ? burialNote(burial)
      : 'Father Ramon’s bells stay down. Lay burial, dig outside the wall, or walk past — the column is watching.';
    entries.push({ id: 'q_parish', title: 'The locked burial', body, status, sort: 40 });
  }

  // q_mold — after parish resolved, or after ambush if parish already touched / mold taken
  if (ambushDone && (parishTouched || moldFate)) {
    const status: JournalEntry['status'] = moldFate ? 'done' : 'active';
    const body = moldFate
      ? moldNote(moldFate)
      : 'Viscount’s rider wants the mold: give it, drown it, or keep it as proof for Narbonne.';
    entries.push({ id: 'q_mold', title: 'The goldsmith’s mold', body, status, sort: 50 });
  }

  // q_ferry
  if (moldFate) {
    const status: JournalEntry['status'] = ferryDone ? 'done' : 'active';
    const body = ferryDone
      ? 'Ferry rope cut. Crossing open toward Narbonne.'
      : trust >= 2
        ? 'Sergeant Holds; Convers Cuts. Sheep-gate possible if the column vouches.'
        : 'Sergeant Holds; Convers must Cut the rope. Sheep-gate won’t open without trust.';
    entries.push({ id: 'q_ferry', title: 'The ferry rope', body, status, sort: 60 });
  }

  // q_letter
  if (talkedCellarer) {
    let status: JournalEntry['status'] = narbonne ? 'done' : 'active';
    let body = narbonne
      ? narbonneNote(narbonne)
      : sealIntact
        ? 'Deliver the letter with wax unbroken. Peeking makes you the next forger on this road.'
        : 'Wax already cracked. Speak carefully at the gate — or ride past.';
    entries.push({ id: 'q_letter', title: 'Letter for Narbonne', body, status, sort: 70 });
  }

  // q_corbieres — Act II
  if (act1Complete || !!flags.act1_complete) {
    const inHills = String(flags.map_zone) === 'corbieres';
    const path = String(flags.priory_path || '');
    const deal = String(flags.captain_deal || 'none');
    let body = inHills
      ? 'Hill road to the ruined priory. Berna holds the yard — steal, talk, or hold the nave door.'
      : 'Act I closed. Take the hill road from Narbonne toward the ruined priory in the Corbières.';
    let status: JournalEntry['status'] = 'active';
    if (path) {
      body = `Priory path: ${path.replace('_', ' ')}. Hugues wants the ruin as a warrant.`;
    }
    if (deal !== 'none') {
      status = 'done';
      body = `Hugues deal: ${deal.split('_').join(' ')}. Serena may still name the hill lord.`;
    }
    entries.push({ id: 'q_corbieres', title: 'Corbières priory', body, status, sort: 80 });
  }

  if (String(flags.captain_deal || 'none') !== 'none' || !!flags.talked_serena) {
    const name = String(flags.lord_name || '');
    const known = !!flags.lord_name_known;
    entries.push({
      id: 'q_name_seed',
      title: 'The hill lord’s name',
      body: known
        ? `Na Serena named ${name}. Act III seed.`
        : flags.talked_serena
          ? 'Name withheld — a roof may matter more than a hanging.'
          : 'Speak Na Serena after Hugues for the purse that paid the die.',
      status: flags.talked_serena ? 'done' : 'active',
      sort: 90,
    });
  }

  // Act III journal map (07-act-iii-thick)
  if (!!flags.talked_serena || !!flags.act3_beat || !!flags.act3_done) {
    entries.push({
      id: 'act3_open',
      title: 'Act III — names and wood',
      body: 'Willows, optional leper roof, hill lord or empty house, then the splinter.',
      status: flags.act3_done ? 'done' : 'active',
      sort: 100,
    });
  }
  if (flags.talked_leper || flags.bark_rest_leper) {
    entries.push({
      id: 'rest_leper',
      title: 'Night under unringing bells',
      body: flags.bark_rest_leper
        ? 'Linen boiled. Willow watch named at dawn. Bleeds cleared for now.'
        : 'Infirmary roof touched — no captains at the door.',
      status: flags.talked_leper ? 'done' : 'active',
      sort: 110,
    });
  }
  {
    const lord = String(flags.lord_fate || '');
    if (lord || String(flags.act3_beat) === 'lord') {
      const body =
        lord === 'hidden'
          ? 'Raimon hid you. Silence owed — splinter must not walk his market.'
          : lord === 'named_hanged'
            ? 'Name sent toward Narbonne. Hill house empties.'
            : lord === 'unnamed_fled'
              ? 'No hanging from your hand — or the house was already empty.'
              : 'Hill house ahead — hide, name, walk, or grain for silence.';
      entries.push({
        id: lord ? `lord_${lord}` : 'lord_pending',
        title: lord ? `Lord fate — ${lord.split('_').join(' ')}` : 'The hill house',
        body,
        status: lord ? 'done' : 'active',
        sort: 120,
      });
    }
  }
  {
    const sp = String(flags.splinter_end || '');
    if (sp || String(flags.act3_beat) === 'splinter' || String(flags.act3_beat) === 'close') {
      const body =
        sp === 'altar'
          ? 'Splinter quiet on stone. No market walk.'
          : sp === 'broken_public'
            ? 'Pine — public or quiet snap. Crowds or fewer ears.'
            : sp === 'kept_bag'
              ? 'Wood kept in the bag. You stay the next chest.'
              : 'Altar, public break, quiet snap, or keep — last magazine in the bag.';
      entries.push({
        id: sp ? `splinter_${sp}` : 'splinter_pending',
        title: sp ? `Splinter — ${sp.split('_').join(' ')}` : 'The wood’s end',
        body,
        status: sp ? 'done' : 'active',
        sort: 130,
      });
    }
  }
  if (flags.act3_done) {
    entries.push({
      id: 'end_act3',
      title: 'Frame closed — war continues',
      body: 'Campaign frame closed. Your five still walk. The war goes on.',
      status: 'done',
      sort: 140,
    });
  }

  return entries.sort((a, b) => a.sort - b.sort);
}
