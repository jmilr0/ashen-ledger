import type { Combatant, PartyMember } from './types';

export class CombatSession {
  allies: Combatant[];
  enemies: Combatant[];
  log: string[] = [];
  turn: 'player' | 'enemy' = 'player';
  over = false;
  victory = false;

  constructor(party: PartyMember[]) {
    this.allies = party
      .filter((p) => p.recruited)
      .map((p) => ({
        id: `ally-${p.id}`,
        name: p.name,
        hp: p.stats.hp,
        maxHp: p.stats.maxHp,
        atk: p.stats.atk,
        def: p.stats.def,
        isPlayer: true,
        memberId: p.id,
      }));
    this.enemies = [
      {
        id: 'wraith',
        name: 'Blot-Wraith',
        hp: 34,
        maxHp: 34,
        atk: 8,
        def: 2,
        isPlayer: false,
      },
    ];
    this.log.push('A Blot-Wraith uncoils from unpaid ink near the east arch.');
  }

  living(side: 'allies' | 'enemies'): Combatant[] {
    return this[side].filter((c) => c.hp > 0);
  }

  private dmg(atk: number, def: number): number {
    return Math.max(1, atk - def + Math.floor(Math.random() * 3));
  }

  playerAttack(targetId: string): void {
    if (this.over || this.turn !== 'player') return;
    const attacker = this.living('allies')[0];
    const target = this.enemies.find((e) => e.id === targetId && e.hp > 0);
    if (!attacker || !target) return;
    const d = this.dmg(attacker.atk, target.def);
    target.hp = Math.max(0, target.hp - d);
    this.log.push(`${attacker.name} strikes for ${d}. ${target.name}: ${target.hp}/${target.maxHp}`);
    this.checkEnd();
    if (!this.over) {
      this.turn = 'enemy';
      this.enemyTurn();
    }
  }

  playerSkill(): void {
    if (this.over || this.turn !== 'player') return;
    const caster = this.living('allies').find((a) => a.memberId === 'mirelle') ?? this.living('allies')[0];
    const target = this.living('enemies')[0];
    if (!caster || !target) return;
    const d = this.dmg(caster.atk + 3, target.def);
    target.hp = Math.max(0, target.hp - d);
    this.log.push(`${caster.name} unmakes a ledger-line — ${d} damage to ${target.name}.`);
    this.checkEnd();
    if (!this.over) {
      this.turn = 'enemy';
      this.enemyTurn();
    }
  }

  playerDefend(): void {
    if (this.over || this.turn !== 'player') return;
    const a = this.living('allies')[0];
    if (!a) return;
    a.def += 2;
    this.log.push(`${a.name} braces (temporary defense).`);
    this.turn = 'enemy';
    this.enemyTurn();
    a.def -= 2;
  }

  private enemyTurn(): void {
    if (this.over) return;
    const foe = this.living('enemies')[0];
    const ally = this.living('allies')[0];
    if (!foe || !ally) {
      this.checkEnd();
      return;
    }
    const d = this.dmg(foe.atk, ally.def);
    ally.hp = Math.max(0, ally.hp - d);
    this.log.push(`${foe.name} lashes with wet ink for ${d}. ${ally.name}: ${ally.hp}/${ally.maxHp}`);
    this.checkEnd();
    if (!this.over) this.turn = 'player';
  }

  private checkEnd(): void {
    if (!this.living('enemies').length) {
      this.over = true;
      this.victory = true;
      this.log.push('The Blot-Wraith collapses into ash and unpaid interest.');
    } else if (!this.living('allies').length) {
      this.over = true;
      this.victory = false;
      this.log.push('You fall. The Ledger writes another name.');
    }
  }

  applyHpToParty(party: PartyMember[]): void {
    for (const a of this.allies) {
      const m = party.find((p) => p.id === a.memberId);
      if (m) m.stats.hp = Math.max(1, a.hp);
    }
  }
}
