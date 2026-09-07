/** Ending scroll from content/narrative/11-epilogue.md — dirt and consequence, no magic. */

export type EpilogueCard = { title: string; body: string };

export function buildEpilogueCards(
  flags: Record<string, boolean | string | number>,
  party: Array<{ outForAct?: boolean }>
): EpilogueCard[] {
  const cards: EpilogueCard[] = [];

  // 1 — Splinter
  const splinter = String(flags.splinter_end || 'altar');
  if (splinter === 'broken_public') {
    let body =
      'They heard it snap. Some cursed you. Some stopped trusting boxes for a week. That is as much truth as a road gets.';
    if (flags.bark_break_quiet || flags.splinter_quiet) {
      body += ' Peire broke it without a sermon.';
    }
    cards.push({ title: 'Pine in the square', body });
  } else if (splinter === 'kept_bag') {
    cards.push({
      title: 'Still in the bag',
      body: 'The splinter travels with you. So does every captain who can smell wax. You chose to remain a chest.',
    });
  } else {
    cards.push({
      title: 'Quiet stone',
      body: 'The wood sits where no market sees it. Someone may still kneel — but not because your bag walked the square.',
    });
  }

  // 2 — Names (first matching)
  const lord = String(flags.lord_fate || '');
  const mold = String(flags.mold_fate || '');
  const narbonne = String(flags.narbonne_outcome || '');
  const forger = !!flags.party_is_forger || flags.seal_intact === false;
  let names: EpilogueCard | null = null;
  if (lord === 'hidden') {
    names = {
      title: 'A silence owed',
      body: 'Raimon of Quéribus keeps his hill — and you keep your mouths shut. Hide is a debt; debts walk both ways.',
    };
  } else if (lord === 'named_hanged') {
    names = {
      title: 'Rope on paper',
      body: 'The name reached ears that hang. The hill house empties. You sleep colder and call it justice or necessity.',
    };
  } else if (lord === 'unnamed_fled') {
    names = {
      title: 'Cold ash',
      body: 'No name held. Tracks north, then nothing. The die’s payer dissolves into weather.',
    };
  } else if (mold === 'kept' && (narbonne === 'delivered' || narbonne === 'letter_damaged')) {
    names = {
      title: 'Die on the table',
      body: 'The mold matched enough. Narbonne has teeth; whose neck it closes on is no longer only yours.',
    };
  } else if (mold === 'drowned') {
    names = {
      title: 'Lead in the Aude',
      body: 'The die is cold river-metal. Cleaner conscience. Fewer proofs.',
    };
  } else if (mold === 'given_viscount') {
    names = {
      title: 'Soft rider',
      body: 'The viscount holds the mold. You bought a friend who collects.',
    };
  } else if (forger) {
    names = {
      title: 'Broken wax',
      body: 'Gates remember peekers. Your letter arrived stained, or not at all — either way, clerks will sniff you twice.',
    };
  }
  if (names) cards.push(names);

  // 3 — Road
  const trust = Number(flags.pilgrim_trust) || 0;
  const bits: string[] = [];
  if (trust >= 2) bits.push('Mairia’s column ate your mud and lived.');
  else if (trust === 1) bits.push('The column thinned but still walked west.');
  else bits.push('You chose the bag over the mule. The road behind you is hostile mouths.');

  const burial = String(flags.child_burial || '');
  if (burial === 'helped') bits.push('A child went into quiet earth without bells.');
  else if (burial === 'refused') bits.push('A porch still talks about dry hands.');
  else if (burial === 'deferred') bits.push('A shovel was promised and not finished.');

  const deal = String(flags.captain_deal || 'none');
  if (deal === 'vines_spared') bits.push('Hugues took empty stone, not a massacre warrant.');
  else if (deal === 'vines_seized') bits.push('Vines will feed northern horses. You bought time, not mercy.');
  else if (deal === 'bribed_off') bits.push('Coin bought a quieter captain for a while.');

  cards.push({ title: 'The road', body: bits.join(' ') });

  // 4 — Party (optional)
  const partyLines: string[] = [];
  if (party.some((p) => p.outForAct)) {
    partyLines.push('Not all five walk out whole. Elias’s linen has limits.');
  }
  if (forger) partyLines.push('Arnau’s fingers still smell of broken wax.');
  if (String(flags.chest_carrier || '') === 'convers' && flags.act3_done) {
    partyLines.push('Peire carried keys and a bag and did not drop either.');
  }
  if (partyLines.length) {
    cards.push({ title: 'Five jobs', body: partyLines.join(' ') });
  }

  // 5 — Close
  cards.push({
    title: 'Winter holds',
    body: 'Winter does not end because five people named a forgery. Northern banners still move. Local counts still play for time. You move pilgrims off one killing ground, put a die out of easy reach, and decide what a stick of wood was worth.\n\nThe war goes on. Your boots are still wet.',
  });

  return cards;
}
