import type { Combatant, CombatEncounter, JobId, PartyMember } from './types';

export type CombatActionId =
  | 'hold'
  | 'thrust'
  | 'shove'
  | 'club'
  | 'cut_rope'
  | 'kick_latch'
  | 'brace_wagon'
  | 'bolt'
  | 'slip'
  | 'point'
  | 'call_out'
  | 'staff'
  | 'show_seal'
  | 'stabilize'
  | 'drag';

const ALLY_ORDER: JobId[] = ['sergeant', 'convers', 'guide', 'clerk', 'surgeon'];

export interface CombatOptions {
  encounter: CombatEncounter;
  sealIntact: boolean;
  hasLoft?: boolean;
  shoveWater?: boolean;
  pilgrimTrust?: number;
}

/** Formation lane combat — jobs, not fantasy spells. */
export class CombatSession {
  allies: Combatant[];
  enemies: Combatant[];
  log: string[] = [];
  turn: 'player' | 'enemy' = 'player';
  over = false;
  victory = false;
  encounter: CombatEncounter;
  activeAllyId: JobId | null = null;
  badgesExposed = false;
  sealShownThisFight = false;
  sealIntact: boolean;
  hasLoft: boolean;
  shoveWater: boolean;
  ropeCut = false;
  /** Ferry win when Convers cuts rope while Sergeant held this round or last. */
  sergeantHeldThisRound = false;
  round = 1;

  constructor(party: PartyMember[], opts: CombatOptions) {
    this.encounter = opts.encounter;
    this.sealIntact = opts.sealIntact;
    this.hasLoft = !!opts.hasLoft;
    this.shoveWater = !!opts.shoveWater;

    const available = party.filter((p) => p.recruited && !p.outForAct);
    this.allies = ALLY_ORDER.map((id) => available.find((p) => p.id === id))
      .filter((p): p is PartyMember => !!p)
      .map((p) => this.makeAlly(p));

    if (opts.encounter === 'ambush') {
      this.enemies = [
        {
          id: 'bandit_a',
          name: 'Badge Captain',
          hp: 18,
          maxHp: 18,
          atk: 7,
          def: 3,
          isPlayer: false,
          slot: 'frontL',
        },
        {
          id: 'bandit_b',
          name: 'Borrowed-Badge Thug',
          hp: 14,
          maxHp: 14,
          atk: 6,
          def: 2,
          isPlayer: false,
          slot: 'frontR',
        },
      ];
      this.log.push('Borrowed-badge ambush on the wet road. Formation — Point then Call out if you can.');
    } else {
      this.enemies = [
        {
          id: 'ferry_guard',
          name: 'River Watch',
          hp: 16,
          maxHp: 16,
          atk: 6,
          def: 3,
          isPlayer: false,
          slot: 'frontL',
        },
        {
          id: 'ferry_thug',
          name: 'Toll Blade',
          hp: 12,
          maxHp: 12,
          atk: 5,
          def: 2,
          isPlayer: false,
          slot: 'frontR',
        },
      ];
      const stress =
        (opts.pilgrimTrust ?? 2) <= 0
          ? ' Column is scattered — ferry starts stressed.'
          : '';
      this.log.push(
        'Ferry rope under pressure. Sergeant Holds; Convers must Cut rope to free the crossing.' + stress
      );
    }

    this.activeAllyId = this.nextAllyId(null);
  }

  private makeAlly(p: PartyMember): Combatant {
    const slot = this.defaultSlot(p.id);
    return {
      id: `ally-${p.id}`,
      name: p.name,
      hp: p.stats.hp,
      maxHp: p.stats.maxHp,
      atk: p.stats.atk,
      def: p.stats.def,
      isPlayer: true,
      memberId: p.id,
      slot,
      bleeding: !!p.bleeding,
      bleedTicks: p.bleedTicks ?? 0,
      downed: p.stats.hp <= 0,
      holding: false,
    };
  }

  private defaultSlot(id: JobId): Combatant['slot'] {
    switch (id) {
      case 'sergeant':
        return 'frontL';
      case 'convers':
        return 'frontR';
      case 'clerk':
        return 'rearL';
      case 'surgeon':
        return 'rearR';
      case 'guide':
        return this.hasLoft ? 'loft' : 'rearL';
    }
  }

  living(side: 'allies' | 'enemies'): Combatant[] {
    return this[side].filter((c) => c.hp > 0 && !c.downed);
  }

  private orderedLivingAllies(): Combatant[] {
    return ALLY_ORDER.map((id) => this.allies.find((a) => a.memberId === id && a.hp > 0 && !a.downed)).filter(
      (a): a is Combatant => !!a
    );
  }

  private nextAllyId(after: JobId | null): JobId | null {
    const living = this.orderedLivingAllies();
    if (!living.length) return null;
    if (!after) return living[0].memberId ?? null;
    const idx = living.findIndex((a) => a.memberId === after);
    if (idx < 0 || idx >= living.length - 1) return null;
    return living[idx + 1].memberId ?? null;
  }

  activeAlly(): Combatant | null {
    if (!this.activeAllyId) return null;
    return this.allies.find((a) => a.memberId === this.activeAllyId && a.hp > 0 && !a.downed) ?? null;
  }

  actionsFor(job: JobId): { id: CombatActionId; label: string; enabled: boolean }[] {
    const a = this.activeAlly();
    if (!a || a.memberId !== job) return [];
    const inLoft = a.slot === 'loft';
    const flankOk = this.hasLoft || inLoft;
    switch (job) {
      case 'sergeant':
        return [
          { id: 'hold', label: 'Hold line', enabled: true },
          { id: 'thrust', label: 'Thrust', enabled: this.living('enemies').length > 0 },
          {
            id: 'shove',
            label: this.shoveWater ? 'Shove (into water)' : 'Shove',
            enabled: this.living('enemies').length > 0,
          },
        ];
      case 'convers':
        return [
          { id: 'club', label: 'Club', enabled: this.living('enemies').length > 0 },
          {
            id: 'cut_rope',
            label: 'Cut rope',
            enabled: this.encounter === 'ferry' && !this.ropeCut,
          },
          {
            id: 'kick_latch',
            label: 'Kick latch',
            enabled: this.encounter === 'ambush',
          },
          { id: 'brace_wagon', label: 'Brace wagon', enabled: true },
        ];
      case 'guide':
        return [
          { id: 'bolt', label: 'Bolt', enabled: flankOk && this.living('enemies').length > 0 },
          { id: 'slip', label: 'Slip → loft', enabled: this.hasLoft && !inLoft },
          { id: 'point', label: 'Point (expose badges)', enabled: this.encounter === 'ambush' && !this.badgesExposed },
        ];
      case 'clerk':
        return [
          {
            id: 'call_out',
            label: 'Call out',
            enabled: this.badgesExposed && this.living('enemies').some((e) => !e.wavering),
          },
          { id: 'staff', label: 'Staff', enabled: this.living('enemies').length > 0 },
          {
            id: 'show_seal',
            label: 'Show seal',
            enabled: this.sealIntact && !this.sealShownThisFight,
          },
        ];
      case 'surgeon':
        return [
          {
            id: 'stabilize',
            label: 'Stabilize',
            enabled: this.allies.some((x) => x.bleeding && !x.downed),
          },
          {
            id: 'drag',
            label: 'Drag',
            enabled: this.allies.some((x) => x.downed || x.hp <= 0),
          },
        ];
    }
  }

  private dmg(atk: number, def: number): number {
    return Math.max(1, atk - def + Math.floor(Math.random() * 3));
  }

  private frontDefBonus(): number {
    const sarge = this.allies.find((a) => a.memberId === 'sergeant');
    return sarge?.holding ? 2 : 0;
  }

  private afterPlayerAction(): void {
    this.checkEnd();
    if (this.over) return;
    const next = this.nextAllyId(this.activeAllyId);
    if (next) {
      this.activeAllyId = next;
      this.turn = 'player';
      return;
    }
    this.turn = 'enemy';
    this.enemyPhase();
    if (!this.over) {
      this.bleedTicks();
      this.checkEnd();
    }
    if (!this.over) {
      // clear hold at end of full round after enemy+bleed
      for (const a of this.allies) a.holding = false;
      this.sergeantHeldThisRound = false;
      this.round += 1;
      this.turn = 'player';
      this.activeAllyId = this.nextAllyId(null);
    }
  }

  act(action: CombatActionId, targetId?: string): void {
    if (this.over || this.turn !== 'player') return;
    const actor = this.activeAlly();
    if (!actor || !actor.memberId) return;
    const job = actor.memberId;
    const allowed = this.actionsFor(job).find((x) => x.id === action && x.enabled);
    if (!allowed) {
      this.log.push(`${actor.name} cannot ${action} now.`);
      return;
    }

    const foe =
      this.enemies.find((e) => e.id === targetId && e.hp > 0) ?? this.living('enemies')[0];

    switch (action) {
      case 'hold': {
        actor.holding = true;
        this.sergeantHeldThisRound = true;
        this.log.push(`${actor.name} Holds the front line.`);
        break;
      }
      case 'thrust': {
        if (!foe) return;
        const d = this.dmg(actor.atk, foe.def);
        foe.hp = Math.max(0, foe.hp - d);
        this.log.push(`${actor.name} Thrusts for ${d}. ${foe.name}: ${foe.hp}/${foe.maxHp}`);
        if (foe.hp <= 0) foe.downed = true;
        break;
      }
      case 'shove': {
        if (!foe) return;
        if (this.shoveWater && Math.random() < 0.45) {
          foe.hp = 0;
          foe.downed = true;
          this.log.push(`${actor.name} Shoves ${foe.name} into the water.`);
        } else {
          const d = this.dmg(Math.max(2, actor.atk - 2), foe.def);
          foe.hp = Math.max(0, foe.hp - d);
          this.log.push(`${actor.name} Shoves ${foe.name} for ${d}.`);
          if (foe.hp <= 0) foe.downed = true;
        }
        break;
      }
      case 'club': {
        if (!foe) return;
        const d = this.dmg(actor.atk, foe.def);
        foe.hp = Math.max(0, foe.hp - d);
        this.log.push(`${actor.name} Clubs for ${d}. ${foe.name}: ${foe.hp}/${foe.maxHp}`);
        if (foe.hp <= 0) foe.downed = true;
        break;
      }
      case 'cut_rope': {
        if (!this.sergeantHeldThisRound) {
          this.log.push('Rope frays — need Sergeant Hold before Cut rope lands clean.');
          // still spend the action; partial progress
          break;
        }
        this.ropeCut = true;
        this.log.push(`${actor.name} Cuts the ferry rope under Sergeant Hold — crossing frees.`);
        this.victory = true;
        this.over = true;
        return;
      }
      case 'kick_latch': {
        this.log.push(`${actor.name} Kicks a scrub latch — one flank opens.`);
        this.hasLoft = true;
        break;
      }
      case 'brace_wagon': {
        for (const a of this.allies) {
          if (a.slot === 'frontL' || a.slot === 'frontR') a.def += 1;
        }
        this.log.push(`${actor.name} Braces the wagon — front hardens.`);
        break;
      }
      case 'bolt': {
        if (!foe) return;
        const d = this.dmg(actor.atk + 1, foe.def);
        foe.hp = Math.max(0, foe.hp - d);
        this.log.push(`${actor.name} looses a Bolt for ${d}. ${foe.name}: ${foe.hp}/${foe.maxHp}`);
        if (foe.hp <= 0) foe.downed = true;
        break;
      }
      case 'slip': {
        actor.slot = 'loft';
        this.log.push(`${actor.name} Slips to the loft.`);
        break;
      }
      case 'point': {
        this.badgesExposed = true;
        for (const e of this.enemies) e.badgesExposed = true;
        this.log.push(`${actor.name} Points — borrowed badges flash wrong. Clerk can Call out.`);
        break;
      }
      case 'call_out': {
        const target = this.living('enemies').find((e) => e.badgesExposed) ?? this.living('enemies')[0];
        if (!target) break;
        target.wavering = true;
        this.log.push(`${actor.name} Calls out the false badge — ${target.name} wavers (skips next attack).`);
        break;
      }
      case 'staff': {
        if (!foe) return;
        const d = this.dmg(Math.max(2, actor.atk - 2), foe.def);
        foe.hp = Math.max(0, foe.hp - d);
        this.log.push(`${actor.name} pokes with Staff for ${d}.`);
        if (foe.hp <= 0) foe.downed = true;
        break;
      }
      case 'show_seal': {
        this.sealShownThisFight = true;
        for (const e of this.living('enemies')) e.wavering = true;
        this.log.push(`${actor.name} Shows the intact seal — foes hesitate this round.`);
        break;
      }
      case 'stabilize': {
        const bleed = this.allies.find((x) => x.bleeding && !x.downed);
        if (!bleed) break;
        bleed.bleeding = false;
        bleed.bleedTicks = 0;
        this.log.push(`${actor.name} Stabilizes ${bleed.name} — bleeding stopped.`);
        break;
      }
      case 'drag': {
        const down = this.allies.find((x) => x.downed || x.hp <= 0);
        if (!down) break;
        down.slot = 'rearR';
        down.downed = true;
        this.log.push(`${actor.name} Drags ${down.name} to the rear.`);
        break;
      }
    }

    this.afterPlayerAction();
  }

  private enemyPhase(): void {
    for (const foe of [...this.living('enemies')]) {
      if (foe.wavering) {
        this.log.push(`${foe.name} wavers and skips the swing.`);
        foe.wavering = false;
        continue;
      }
      const targets = this.living('allies');
      if (!targets.length) break;
      // prefer front rank
      const front = targets.filter((t) => t.slot === 'frontL' || t.slot === 'frontR');
      const pool = front.length ? front : targets;
      const ally = pool[Math.floor(Math.random() * pool.length)];
      let def = ally.def;
      if (ally.slot === 'frontL' || ally.slot === 'frontR') def += this.frontDefBonus();
      const d = this.dmg(foe.atk, def);
      ally.hp = Math.max(0, ally.hp - d);
      this.log.push(`${foe.name} cuts for ${d}. ${ally.name}: ${ally.hp}/${ally.maxHp}`);
      if (ally.hp <= 0) {
        ally.downed = true;
        this.log.push(`${ally.name} is downed.`);
      } else if (Math.random() < 0.35) {
        ally.bleeding = true;
        ally.bleedTicks = ally.bleedTicks ?? 0;
        this.log.push(`${ally.name} is bleeding.`);
      }
    }
  }

  private bleedTicks(): void {
    for (const a of this.allies) {
      if (!a.bleeding || a.downed) continue;
      a.bleedTicks = (a.bleedTicks ?? 0) + 1;
      this.log.push(`${a.name} bleeds (tick ${a.bleedTicks}/2).`);
      if (a.bleedTicks >= 2) {
        a.downed = true;
        a.hp = 0;
        this.log.push(`${a.name} is out for the Act — bleeding went untreated.`);
      }
    }
  }

  private checkEnd(): void {
    if (this.encounter === 'ferry' && this.ropeCut) {
      this.over = true;
      this.victory = true;
      return;
    }
    if (!this.living('enemies').length) {
      this.over = true;
      this.victory = true;
      this.log.push(
        this.encounter === 'ambush'
          ? 'Ambush broken. Borrowed badges lie in the mud.'
          : 'River watch cleared — but the rope still mattered.'
      );
    } else if (!this.living('allies').length) {
      this.over = true;
      this.victory = false;
      this.log.push('Formation collapses in the mud.');
    }
  }

  applyToParty(party: PartyMember[]): void {
    for (const a of this.allies) {
      const m = party.find((p) => p.id === a.memberId);
      if (!m) continue;
      m.stats.hp = Math.max(0, a.hp);
      m.bleeding = !!a.bleeding;
      m.bleedTicks = a.bleedTicks ?? 0;
      if ((a.bleedTicks ?? 0) >= 2 || (a.downed && (a.bleedTicks ?? 0) >= 2)) {
        m.outForAct = true;
        m.bleeding = false;
      }
      if (a.downed && m.stats.hp <= 0 && !m.outForAct) {
        // downed but not out — limp at 1 hp after fight if surgeon present
        const surg = party.find((p) => p.id === 'surgeon' && !p.outForAct);
        if (surg) m.stats.hp = Math.max(1, Math.floor(m.stats.maxHp * 0.25));
        else m.stats.hp = 1;
      }
    }
  }
}
