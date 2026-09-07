import {
  createDefaultInventory,
  createDefaultParty,
  DEFAULT_FLAGS,
  DIALOGUES,
  NPCS,
  PLAYER_START,
} from './data';
import { CombatSession, type CombatActionId } from './combat';
import { hasSave, loadGame, saveGame } from './save';
import type { CombatEncounter, DialogueNode, Item, JobId, PartyMember, SaveData, Screen } from './types';
import { World } from './world';

export class Game {
  private world: World | null = null;
  private ui: HTMLElement;
  private screen: Screen = 'title';
  private party: PartyMember[] = createDefaultParty();
  private inventory: Item[] = createDefaultInventory();
  private flags: Record<string, boolean | string | number> = { ...DEFAULT_FLAGS };
  private storyBeat = 'Fontfroide. Take the chest. Do not break the true seal.';
  private dialogueTree: DialogueNode[] = [];
  private dialogueNpc = '';
  private dialogueNode: DialogueNode | null = null;
  private combat: CombatSession | null = null;
  private last = 0;
  private running = false;
  private orbitDragging = false;
  private lastPointerX = 0;
  private lastPointerY = 0;
  private canvasHandlersBound = false;

  constructor() {
    this.ui = document.getElementById('ui-root')!;
    this.bindGlobalKeys();
    this.showTitle();
  }

  private bindGlobalKeys(): void {
    window.addEventListener('keydown', (e) => {
      if (this.screen === 'title') return;
      if (e.key === 'i' || e.key === 'I') {
        if (this.screen === 'inventory') this.closeOverlay();
        else if (this.screen === 'hub') this.showInventory();
      }
      if (e.key === 'c' || e.key === 'C' || e.key === 'p' || e.key === 'P') {
        if (this.screen === 'party') this.closeOverlay();
        else if (this.screen === 'hub') this.showParty();
      }
      if (e.key === 'e' || e.key === 'E' || e.key === 'f' || e.key === 'F') {
        if (this.screen === 'hub') this.tryInteract();
      }
      if (e.key === 'q' || e.key === 'Q') {
        if (this.screen === 'hub') this.world?.orbit(-0.18);
      }
      if (e.key === 'r' || e.key === 'R') {
        if (this.screen === 'hub') this.world?.orbit(0.18);
      }
      if (e.key === 'Escape') {
        if (this.screen === 'party' || this.screen === 'inventory') this.closeOverlay();
      }
      if ((e.key === 's' || e.key === 'S') && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        if (this.screen === 'hub') this.persist('Saved.');
      }
    });
  }

  private toast(msg: string): void {
    let t = document.getElementById('toast');
    if (!t) {
      t = document.createElement('div');
      t.id = 'toast';
      t.className = 'panel';
      this.ui.appendChild(t);
    }
    t.textContent = msg;
    t.classList.add('show');
    setTimeout(() => t?.classList.remove('show'), 2000);
  }

  private clearUi(): void {
    this.ui.innerHTML = '';
  }

  private showTitle(): void {
    this.screen = 'title';
    this.running = false;
    this.world?.dispose();
    this.world = null;
    this.clearUi();
    const el = document.createElement('div');
    el.id = 'title-screen';
    el.innerHTML = `
      <h1>The Broken Seal</h1>
      <p class="tagline">Winter 1208, Occitania. Fontfroide to Narbonne — dirt, wax, mail, bad roads.
      Five jobs. No magic. A near-true seal and a letter that must stay closed.</p>
      <div class="menu">
        <button class="btn primary" id="btn-new">New Journey</button>
        <button class="btn" id="btn-continue" ${hasSave() ? '' : 'disabled'}>Continue</button>
      </div>
      <p class="hint">LMB move · RMB talk / drag orbit · Q/R rotate · E/F interact · I inv · C party · Ctrl+S save</p>
    `;
    this.ui.appendChild(el);
    el.querySelector('#btn-new')!.addEventListener('click', () => this.newGame());
    el.querySelector('#btn-continue')!.addEventListener('click', () => this.continueGame());
  }

  private newGame(): void {
    this.party = createDefaultParty();
    this.inventory = createDefaultInventory();
    this.flags = { ...DEFAULT_FLAGS };
    this.storyBeat = 'Fontfroide. Take the chest. Do not break the true seal.';
    this.enterHub(PLAYER_START.x, PLAYER_START.z);
  }

  private continueGame(): void {
    const data = loadGame();
    if (!data) {
      this.toast('No save found.');
      return;
    }
    this.party = data.party;
    this.inventory = data.inventory;
    this.flags = { ...DEFAULT_FLAGS, ...data.flags };
    this.storyBeat = data.storyBeat;
    this.enterHub(data.playerX, data.playerZ);
  }

  private persist(msg = 'Progress noted.'): void {
    if (!this.world) return;
    const data: SaveData = {
      version: 1,
      party: this.party,
      inventory: this.inventory,
      flags: this.flags,
      playerX: this.world.playerX,
      playerZ: this.world.playerZ,
      storyBeat: this.storyBeat,
    };
    saveGame(data);
    this.toast(msg);
  }

  private bindCanvasInput(canvas: HTMLCanvasElement): void {
    if (this.canvasHandlersBound) return;
    this.canvasHandlersBound = true;
    canvas.addEventListener('contextmenu', (ev) => ev.preventDefault());
    canvas.addEventListener('pointerdown', (ev) => {
      if (this.screen !== 'hub' || !this.world) return;
      if (ev.button === 2) {
        const npc = this.world.pickNpc(ev.clientX, ev.clientY);
        if (npc) {
          this.openNpc(npc);
          return;
        }
        this.orbitDragging = true;
        this.lastPointerX = ev.clientX;
        this.lastPointerY = ev.clientY;
        canvas.setPointerCapture(ev.pointerId);
        return;
      }
      if (ev.button === 0) {
        const pt = this.world.screenToGround(ev.clientX, ev.clientY);
        if (pt) this.world.moveToWorld(pt);
      }
    });
    canvas.addEventListener('pointermove', (ev) => {
      if (!this.orbitDragging || !this.world || this.screen !== 'hub') return;
      const dx = ev.clientX - this.lastPointerX;
      const dy = ev.clientY - this.lastPointerY;
      this.lastPointerX = ev.clientX;
      this.lastPointerY = ev.clientY;
      this.world.orbit(-dx * 0.007, dy * 0.005);
    });
    const endOrbit = (ev: PointerEvent) => {
      if (ev.button === 2 || this.orbitDragging) {
        this.orbitDragging = false;
        try {
          canvas.releasePointerCapture(ev.pointerId);
        } catch {
          /* ignore */
        }
      }
    };
    canvas.addEventListener('pointerup', endOrbit);
    canvas.addEventListener('pointercancel', endOrbit);
  }

  private async enterHub(x: number, z: number): Promise<void> {
    this.screen = 'hub';
    this.clearUi();
    const canvas = document.getElementById('game-canvas') as HTMLCanvasElement;
    this.world?.dispose();
    this.world = new World(canvas);
    this.world.setPlayerPos(x, z);
    if (this.flags.ambush_done) this.world.hideNpc('bandits', true);
    if (this.flags.ferry_done) this.world.hideNpc('ferry', true);
    this.bindCanvasInput(canvas);
    this.renderHud();
    this.running = true;
    this.last = performance.now();
    requestAnimationFrame((t) => this.loop(t));
    await this.world.ready;
    if (this.flags.ambush_done) this.world.hideNpc('bandits', true);
    if (this.flags.ferry_done) this.world.hideNpc('ferry', true);
  }

  private renderHud(): void {
    const hud = document.createElement('div');
    hud.id = 'hud';
    const carrier = this.flags.chest_carrier || '—';
    const trust = this.flags.pilgrim_trust;
    hud.innerHTML = `
      <div class="topbar">
        <button class="btn" id="hud-party">Party (C)</button>
        <button class="btn" id="hud-inv">Inventory (I)</button>
        <button class="btn" id="hud-save">Save</button>
        <button class="btn" id="hud-title">Title</button>
      </div>
      <div class="objective panel">${this.storyBeat}<br/><span class="stats">carrier: ${carrier} · seal ${this.flags.seal_intact ? 'intact' : 'broken'} · pilgrim trust ${trust}</span></div>
      <div class="minimap-hint panel">LMB walk · RMB NPC / orbit · Q/R rotate · E/F interact</div>
    `;
    this.ui.appendChild(hud);
    hud.querySelector('#hud-party')!.addEventListener('click', () => this.showParty());
    hud.querySelector('#hud-inv')!.addEventListener('click', () => this.showInventory());
    hud.querySelector('#hud-save')!.addEventListener('click', () => this.persist());
    hud.querySelector('#hud-title')!.addEventListener('click', () => {
      this.persist('Autosaved on exit.');
      this.showTitle();
    });
  }

  private tryInteract(): void {
    if (!this.world || this.screen !== 'hub') return;
    const n = this.world.nearestNpc();
    if (!n) {
      this.toast('Nothing nearby.');
      return;
    }
    this.openNpc(n);
  }

  private openNpc(n: (typeof NPCS)[number]): void {
    if (n.id === 'bandits') {
      if (this.flags.ambush_done) {
        this.toast('Only mud and torn badges remain.');
        return;
      }
      if (!this.flags.chest_carrier) {
        this.toast('Speak to Brother Guiraut — choose who carries the bag first.');
        return;
      }
      this.startDialogue('bandit_captain');
      return;
    }
    if (n.id === 'parish') {
      if (!this.flags.ambush_done) {
        this.toast('Clear or slip the badge ambush first.');
        return;
      }
      this.startDialogue('priest_ramon');
      return;
    }
    if (n.id === 'ferry') {
      if (this.flags.ferry_done) {
        this.toast('Rope cut. Crossing open.');
        return;
      }
      if (!this.flags.mold_fate) {
        this.toast('Settle the mold with the viscount’s rider first.');
        return;
      }
      this.startDialogue('ferry_rope');
      return;
    }
    if (n.id === 'mold') {
      if (!this.flags.ambush_done) {
        this.toast('Clear or slip the badge ambush first.');
        return;
      }
      if (!this.flags.talked_parish && !this.flags.child_burial) {
        this.toast('Father Ramon’s porch is still waiting — then the mold.');
        return;
      }
      if (this.flags.mold_fate) {
        this.startDialogue('mold_choice');
        // will open 'after'
        return;
      }
      this.startDialogue('mold_choice');
      return;
    }
    if (n.id === 'narbonne') {
      if (!this.flags.ferry_done) {
        this.toast('Cut the ferry rope first — then deliver the letter.');
        return;
      }
      this.startDialogue('narbonne_agent');
      return;
    }
    if (n.id === 'mairia' && !this.flags.chest_carrier) {
      this.toast('Take the chest from the cellarer first.');
      return;
    }
    this.startDialogue(n.dialogueId);
  }

  private startDialogue(id: string): void {
    const tree = DIALOGUES[id];
    if (!tree) return;
    this.dialogueNpc = id;
    this.dialogueTree = tree;
    let startId = 'start';
    if (id === 'cellarer' && this.flags.talked_cellarer) startId = 'after';
    if (id === 'pilgrim_mairia' && this.flags.talked_mairia) startId = 'after';
    if (id === 'mold_choice' && this.flags.mold_fate) startId = 'after';
    if (id === 'priest_ramon' && this.flags.talked_parish) startId = 'after';
    if (id === 'narbonne_agent') {
      if (this.flags.talked_narbonne) startId = 'after';
      else if (this.flags.party_is_forger || !this.flags.seal_intact) startId = 'forger';
      else startId = 'clean';
    }
    this.dialogueNode = tree.find((n) => n.id === startId) ?? tree[0];
    this.screen = 'dialogue';
    this.drawDialogue();
  }

  private drawDialogue(): void {
    let box = document.getElementById('dialogue-box');
    if (!box) {
      box = document.createElement('div');
      box.id = 'dialogue-box';
      box.className = 'panel';
      this.ui.appendChild(box);
    }
    const node = this.dialogueNode!;
    const choices = node.choices ?? [{ text: '(Continue)', effect: 'end' }];
    box.innerHTML = `
      <div class="speaker">${node.speaker}</div>
      <div class="text">${node.text}</div>
      <div class="choices"></div>
    `;
    const wrap = box.querySelector('.choices')!;
    for (const c of choices) {
      const b = document.createElement('button');
      b.className = 'btn';
      b.textContent = c.text;
      b.onclick = () => this.pickChoice(c.next, c.effect);
      wrap.appendChild(b);
    }
  }

  private closeDialogue(): void {
    document.getElementById('dialogue-box')?.remove();
    this.screen = 'hub';
  }

  private pickChoice(next?: string, effect?: string): void {
    if (effect) {
      const result = this.applyEffect(effect);
      if (result === 'close') {
        this.closeDialogue();
        return;
      }
      if (result === 'combat') {
        this.closeDialogue();
        return;
      }
      if (result === 'stay') return;
    }
    if (next) {
      this.dialogueNode = this.dialogueTree.find((n) => n.id === next) ?? null;
      if (this.dialogueNode) this.drawDialogue();
      return;
    }
    if (!effect || effect === 'end') this.closeDialogue();
  }

  private adjustTrust(delta: number): void {
    const cur = Number(this.flags.pilgrim_trust) || 0;
    this.flags.pilgrim_trust = Math.max(0, Math.min(3, cur + delta));
  }

  private addItemOnce(item: Item): void {
    if (this.inventory.some((i) => i.id === item.id)) return;
    this.inventory.push(item);
  }

  /** close | stay | combat | continue */
  private applyEffect(effect: string): 'close' | 'stay' | 'combat' | 'continue' {
    if (effect === 'end') return 'close';

    if (effect === 'warn_seal_break') {
      this.flags.warn_seal_break = true;
      return 'continue';
    }

    if (effect === 'carrier_clerk' || effect === 'carrier_sergeant' || effect === 'carrier_convers') {
      const who = effect.replace('carrier_', '') as JobId;
      this.flags.chest_carrier = who;
      this.flags.talked_cellarer = true;
      this.flags.act1_beat = 'road';
      this.storyBeat =
        'Walk the pilgrim road toward Narbonne. Keep the column fed and the bag dry.';
      this.toast(`Chest carrier: ${who}`);
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (effect === 'break_true_seal') {
      if (!this.flags.seal_intact) {
        this.toast('Seal already broken.');
        return 'stay';
      }
      this.flags.seal_intact = false;
      this.flags.party_is_forger = true;
      this.addItemOnce({
        id: 'true_letter_open',
        name: 'Opened True Letter',
        description: 'Wax cracked. You know the contents — and so will every gate clerk.',
        qty: 1,
      });
      this.toast('True seal broken. Party is marked as forger.');
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (effect === 'pilgrim_trust_up') {
      this.adjustTrust(1);
      return 'continue';
    }
    if (effect === 'pilgrim_trust_flat') return 'continue';
    if (effect === 'pilgrim_trust_down') {
      this.adjustTrust(-1);
      return 'continue';
    }

    if (effect === 'end_hook_bandits') {
      this.flags.talked_mairia = true;
      this.storyBeat = 'Borrowed badges on the draille. Confront them east of the mile marker.';
      this.refreshObjective();
      this.persist();
      return 'close';
    }
    if (effect === 'end_column_cold') {
      this.flags.talked_mairia = true;
      this.adjustTrust(-2);
      this.storyBeat = 'Column cold. Ambush still waits — ferry will start stressed if trust hits 0.';
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (effect === 'start_ambush') {
      this.startCombat('ambush');
      return 'combat';
    }
    if (effect === 'bandits_withdraw' || effect === 'slip_draille') {
      this.flags.ambush_done = true;
      this.world?.hideNpc('bandits', true);
      if (effect === 'slip_draille') this.adjustTrust(0);
      else this.adjustTrust(1);
      this.flags.act1_beat = 'after_bandits';
      this.storyBeat = 'Bandits cleared or slipped. Next: Father Ramon’s porch, then the mold.';
      this.toast(effect === 'slip_draille' ? 'Slipped the draille.' : 'Bandits withdraw.');
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (effect === 'mold_given_viscount' || effect === 'mold_drowned' || effect === 'mold_kept') {
      const fate =
        effect === 'mold_given_viscount'
          ? 'given_viscount'
          : effect === 'mold_drowned'
            ? 'drowned'
            : 'kept';
      this.flags.mold_fate = fate;
      this.flags.act1_beat = 'after_mold';
      if (fate === 'kept') {
        this.addItemOnce({
          id: 'seal_mold',
          name: 'Seal Mold',
          description: 'Proof that can hang you. Keep the bag dry.',
          qty: 1,
        });
      }
      this.storyBeat = 'Mold settled. Reach the ferry before the roads tighten.';
      this.toast(
        fate === 'given_viscount'
          ? 'Mold given to the viscount.'
          : fate === 'drowned'
            ? 'Mold drowned in the Aude.'
            : 'Mold kept as proof.'
      );
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (
      effect === 'child_burial_helped' ||
      effect === 'child_burial_refused' ||
      effect === 'child_burial_deferred'
    ) {
      const fate =
        effect === 'child_burial_helped'
          ? 'helped'
          : effect === 'child_burial_refused'
            ? 'refused'
            : 'deferred';
      this.flags.child_burial = fate;
      this.flags.talked_parish = true;
      this.flags.act1_beat = 'parish';
      if (fate === 'helped') {
        this.adjustTrust(1);
        this.toast('Mairia: They saw. The column eats quieter tonight.');
      } else if (fate === 'refused') {
        this.adjustTrust(-1);
        this.toast('Catalana: That porch will talk in every village to Narbonne.');
      } else {
        this.toast('Burial marked deferred — Act II debt.');
      }
      this.storyBeat = 'Parish porch settled. Next: settle the mold with the viscount’s rider.';
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (effect === 'ferry_alt_check') {
      return 'continue';
    }

    if (effect === 'start_ferry') {
      this.startCombat('ferry');
      return 'combat';
    }

    if (effect === 'start_ferry_sheepgate') {
      const trust = Number(this.flags.pilgrim_trust) || 0;
      if (trust >= 2) {
        this.startCombat('ferry', { shoveWater: true });
        return 'combat';
      }
      this.toast('The sheep-gate won’t open — the column won’t vouch for you.');
      this.startCombat('ferry');
      return 'combat';
    }

    if (effect === 'mold_to_agent') {
      this.inventory = this.inventory.filter((i) => i.id !== 'seal_mold');
      return 'continue';
    }

    if (effect === 'narbonne_delivered') {
      // Keep letter_damaged if forger path already stained the wax.
      if (this.flags.narbonne_outcome !== 'letter_damaged') {
        this.flags.narbonne_outcome = 'delivered';
      }
      this.flags.talked_narbonne = true;
      return 'continue';
    }
    if (effect === 'narbonne_letter_damaged') {
      this.flags.narbonne_outcome = 'letter_damaged';
      this.flags.talked_narbonne = true;
      return 'continue';
    }
    if (effect === 'narbonne_refused_forger') {
      this.flags.narbonne_outcome = 'refused_forger';
      this.flags.talked_narbonne = true;
      this.flags.act1_beat = 'narbonne_gate';
      this.storyBeat =
        'Gate kept you out. Column moved anyway. Act I ends ugly — priory still ahead.';
      this.refreshObjective();
      this.persist();
      return 'close';
    }
    if (effect === 'narbonne_deferred_gate') {
      this.flags.narbonne_outcome = 'deferred_gate';
      this.flags.talked_narbonne = true;
      this.flags.act1_beat = 'narbonne_gate';
      this.storyBeat =
        'You rode past Narbonne. The legate may already be north. Priory is the only road left.';
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (effect === 'end_act1') {
      this.flags.talked_narbonne = true;
      this.flags.act1_beat = 'narbonne_gate';
      const outcome = String(this.flags.narbonne_outcome || '');
      const trust = Number(this.flags.pilgrim_trust) || 0;
      if (outcome === 'delivered') {
        this.storyBeat =
          trust >= 2
            ? 'Letter delivered. Pilgrims clear of the magazine road. Corbières priory waits (Act II).'
            : 'Letter delivered. Road behind you is hostile. Corbières priory waits.';
      } else if (outcome === 'letter_damaged') {
        this.storyBeat =
          'Letter stained but names ride. You are known as a peeker. Priory waits.';
      } else if (outcome === 'refused_forger') {
        this.storyBeat =
          'Gate kept you out. Column moved anyway. Act I ends ugly — priory still ahead.';
      } else if (outcome === 'deferred_gate') {
        this.storyBeat =
          'You rode past Narbonne. The legate may already be north. Priory is the only road left.';
      } else {
        this.storyBeat = 'Act I frame closed at Narbonne. Corbières priory waits (Act II).';
      }
      this.toast('Act I frame complete.');
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    return 'close';
  }

  private refreshObjective(): void {
    const obj = document.querySelector('#hud .objective');
    if (!obj) return;
    const carrier = this.flags.chest_carrier || '—';
    const trust = this.flags.pilgrim_trust;
    obj.innerHTML = `${this.storyBeat}<br/><span class="stats">carrier: ${carrier} · seal ${this.flags.seal_intact ? 'intact' : 'broken'} · pilgrim trust ${trust}</span>`;
  }

  private startCombat(
    encounter: CombatEncounter,
    opts?: { shoveWater?: boolean }
  ): void {
    const shoveWater =
      opts?.shoveWater !== undefined ? opts.shoveWater : encounter === 'ferry';
    this.combat = new CombatSession(this.party, {
      encounter,
      sealIntact: !!this.flags.seal_intact,
      hasLoft: encounter === 'ambush' ? !!this.flags.has_loft_ambush : true,
      shoveWater,
      pilgrimTrust: Number(this.flags.pilgrim_trust) || 0,
    });
    this.screen = 'combat';
    this.drawCombat();
  }

  private drawCombat(): void {
    let panel = document.getElementById('combat-panel');
    if (!panel) {
      panel = document.createElement('div');
      panel.id = 'combat-panel';
      panel.className = 'panel';
      this.ui.appendChild(panel);
    }
    const c = this.combat!;
    const enemies = c.enemies
      .map((e) => {
        const tags = [
          e.wavering ? 'waver' : '',
          e.badgesExposed ? 'exposed' : '',
          e.hp <= 0 ? 'down' : '',
        ]
          .filter(Boolean)
          .join(' · ');
        return `<div class="enemy-chip">${e.name} HP ${e.hp}/${e.maxHp}${tags ? ' · ' + tags : ''}</div>`;
      })
      .join('');
    const allies = c.allies
      .map((a) => {
        const active = a.memberId === c.activeAllyId && c.turn === 'player' && !c.over;
        const tags = [
          a.slot ?? '',
          a.holding ? 'Hold' : '',
          a.bleeding ? `bleed ${a.bleedTicks ?? 0}/2` : '',
          a.downed ? 'downed' : '',
          active ? 'your move' : '',
        ]
          .filter(Boolean)
          .join(' · ');
        return `<div class="enemy-chip${active ? ' active-ally' : ''}">${a.name} HP ${a.hp}/${a.maxHp}${tags ? ' · ' + tags : ''}</div>`;
      })
      .join('');
    const log = c.log.slice(-5).join('<br/>');
    const actor = c.activeAlly();
    const actions =
      actor?.memberId && c.turn === 'player' && !c.over
        ? c.actionsFor(actor.memberId)
        : [];
    const btns = actions
      .map(
        (a) =>
          `<button class="btn${a.id === 'hold' || a.id === 'cut_rope' || a.id === 'call_out' ? ' primary' : ''}" data-act="${a.id}" ${a.enabled ? '' : 'disabled'}>${a.label}</button>`
      )
      .join('');
    panel.innerHTML = `
      <div class="combat-meta stats">Round ${c.round} · ${c.encounter === 'ambush' ? 'Borrowed-badge ambush' : 'Ferry rope'} · order sergeant→convers→guide→clerk→surgeon</div>
      <div class="enemy-row">${enemies}</div>
      <div class="enemy-row">${allies}</div>
      <div class="combat-log">${log}</div>
      <div class="actions">${btns}${c.over ? '<button class="btn primary" id="finish">Continue</button>' : ''}</div>
    `;
    panel.querySelectorAll('[data-act]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = (btn as HTMLElement).dataset.act as CombatActionId;
        c.act(id);
        this.drawCombat();
      });
    });
    panel.querySelector('#finish')?.addEventListener('click', () => this.endCombat());
  }

  private endCombat(): void {
    const c = this.combat!;
    c.applyToParty(this.party);
    document.getElementById('combat-panel')?.remove();
    this.combat = null;
    this.screen = 'hub';
    if (c.victory) {
      if (c.encounter === 'ambush') {
        this.flags.ambush_done = true;
        this.world?.hideNpc('bandits', true);
        this.adjustTrust(1);
        this.addItemOnce({
          id: 'borrowed_badge',
          name: 'Borrowed Badge',
          description: 'Wrong die, cut straps. Proof of stolen colors.',
          qty: 1,
        });
        this.flags.act1_beat = 'after_bandits';
        this.storyBeat = 'Bandits cleared. Next: Father Ramon’s porch, then the mold.';
        this.toast('Ambush broken.');
      } else {
        this.flags.ferry_done = true;
        this.world?.hideNpc('ferry', true);
        this.flags.act1_beat = 'ferry';
        this.storyBeat =
          'Ferry rope cut. Deliver the letter to the Narbonne agent.';
        this.toast('Crossing freed.');
      }
      this.refreshObjective();
      this.persist();
    } else {
      this.toast('Formation broken. Stabilize and try again.');
      const clerk = this.party.find((p) => p.id === 'clerk');
      if (clerk && clerk.stats.hp <= 0) clerk.stats.hp = Math.max(4, Math.floor(clerk.stats.maxHp * 0.3));
    }
  }

  private showParty(): void {
    this.screen = 'party';
    const panel = document.createElement('div');
    panel.id = 'party-panel';
    panel.className = 'panel';
    const order: JobId[] = ['guide', 'sergeant', 'convers', 'clerk', 'surgeon'];
    const members = order
      .map((id) => this.party.find((p) => p.id === id)!)
      .map((p) => {
        const hpPct = Math.round((Math.max(0, p.stats.hp) / p.stats.maxHp) * 100);
        const flags = [
          p.outForAct ? 'out for Act' : '',
          p.bleeding ? 'bleeding' : '',
          this.flags.chest_carrier === p.id ? 'carries bag' : '',
        ]
          .filter(Boolean)
          .join(' · ');
        return `<div class="member-card">
          <div>
            <strong>${p.name}</strong>
            <div class="stats">${p.role} · ATK ${p.stats.atk} DEF ${p.stats.def}${flags ? ' · ' + flags : ''}</div>
            <div class="bar"><span style="width:${hpPct}%"></span></div>
          </div>
          <div class="stats">HP ${p.stats.hp}/${p.stats.maxHp}<br/><span class="stub-note">job (no spells)</span></div>
        </div>`;
      })
      .join('');
    panel.innerHTML = `<h2>Party — The Broken Seal</h2>
      <p class="stats" style="margin-top:0.35rem;opacity:0.75">Formation L→R: Guide · Sergeant · Convers · Clerk · Surgeon. Front = Sergeant+Convers.</p>
      <div class="members">${members}</div>
      <button class="btn" id="close-party">Close</button>`;
    this.ui.appendChild(panel);
    panel.querySelector('#close-party')!.addEventListener('click', () => this.closeOverlay());
  }

  private showInventory(): void {
    this.screen = 'inventory';
    const panel = document.createElement('div');
    panel.id = 'inventory-panel';
    panel.className = 'panel';
    const items = this.inventory
      .map(
        (i) => `<div class="item-row"><div><strong>${i.name}</strong> ×${i.qty}<br/>
        <span class="stats">${i.description}</span></div>
        ${i.id === 'bandages' ? `<button class="btn" data-use="${i.id}">Use</button>` : ''}</div>`
      )
      .join('');
    panel.innerHTML = `<h2>Inventory</h2><div class="items">${items || '<em>Empty</em>'}</div>
      <button class="btn" id="close-inv">Close</button>`;
    this.ui.appendChild(panel);
    panel.querySelector('#close-inv')!.addEventListener('click', () => this.closeOverlay());
    panel.querySelectorAll('[data-use]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.useItem((btn as HTMLElement).dataset.use!);
        panel.remove();
        this.showInventory();
      });
    });
  }

  private useItem(id: string): void {
    const item = this.inventory.find((i) => i.id === id);
    if (!item || item.qty < 1) return;
    if (id === 'bandages') {
      const lead = this.party.find((p) => p.id === 'clerk' && !p.outForAct) ?? this.party.find((p) => !p.outForAct)!;
      lead.stats.hp = Math.min(lead.stats.maxHp, lead.stats.hp + 8);
      lead.bleeding = false;
      lead.bleedTicks = 0;
      item.qty -= 1;
      if (item.qty <= 0) this.inventory = this.inventory.filter((i) => i.qty > 0);
      this.toast(`Boiled linen on ${lead.name}.`);
    }
  }

  private closeOverlay(): void {
    document.getElementById('party-panel')?.remove();
    document.getElementById('inventory-panel')?.remove();
    this.screen = 'hub';
  }

  private loop(t: number): void {
    if (!this.running || !this.world) return;
    const dt = Math.min(0.05, (t - this.last) / 1000);
    this.last = t;
    if (this.screen === 'hub') this.world.update(dt);
    this.world.render();
    requestAnimationFrame((nt) => this.loop(nt));
  }
}
