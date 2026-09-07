import {
  ACT3_START,
  CORBIERES_START,
  createDefaultInventory,
  createDefaultParty,
  DEFAULT_FLAGS,
  DIALOGUES,
  PLAYER_START,
} from './data';
import { CombatSession, type CombatActionId } from './combat';
import { buildJournal } from './journal';
import { buildEpilogueCards } from './epilogue';
import { hasSave, loadGame, saveGame } from './save';
import type {
  CombatEncounter,
  DialogueNode,
  Item,
  JobId,
  MapZone,
  NpcDef,
  PartyMember,
  SaveData,
  Screen,
} from './types';
import { SELECT_ORDER } from './types';
import { World } from './world';
import { JOB_PORTRAIT_COLOR } from './data';

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
  private controlledId: JobId = 'clerk';
  private mapZone: MapZone = 'act1_road';
  private journalToastIds = new Set<string>();

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
      if (e.key === 'j' || e.key === 'J') {
        if (this.screen === 'journal') this.closeOverlay();
        else if (this.screen === 'hub') this.showJournal();
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
        if (
          this.screen === 'party' ||
          this.screen === 'inventory' ||
          this.screen === 'journal' ||
          this.screen === 'help' ||
          this.screen === 'epilogue'
        ) {
          this.closeOverlay();
        }
      }
      if (e.key === 'h' || e.key === 'H' || e.key === '?') {
        if (this.screen === 'help') this.closeOverlay();
        else if (this.screen === 'hub') this.showHelp();
      }
      if ((e.key === 's' || e.key === 'S') && (e.ctrlKey || e.metaKey)) {
        e.preventDefault();
        if (this.screen === 'hub') this.persist('Saved.');
      }
      // Party switch 1–5 / Tab
      if (this.screen === 'hub') {
        const digit = e.key >= '1' && e.key <= '5' ? Number(e.key) - 1 : -1;
        if (digit >= 0 && digit < SELECT_ORDER.length) {
          this.selectCompanion(SELECT_ORDER[digit]);
        }
        if (e.key === 'Tab') {
          e.preventDefault();
          this.cycleCompanion(e.shiftKey ? -1 : 1);
        }
      }
      // Combat Space pause
      if (this.screen === 'combat' && e.code === 'Space') {
        e.preventDefault();
        this.combat?.togglePause();
        this.drawCombat();
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
      <p class="hint">LMB move · RMB talk / drag orbit · Q/R rotate · E/F interact · I inv · C party · J journal · H/? help · 1–5/Tab switch · Ctrl+S save</p>
    `;
    this.ui.appendChild(el);
    el.querySelector('#btn-new')!.addEventListener('click', () => this.newGame());
    el.querySelector('#btn-continue')!.addEventListener('click', () => this.continueGame());
  }

  private newGame(): void {
    this.party = createDefaultParty();
    this.inventory = createDefaultInventory();
    this.flags = { ...DEFAULT_FLAGS };
    this.controlledId = 'clerk';
    this.mapZone = 'act1_road';
    this.journalToastIds = new Set();
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
    this.mapZone = (data.mapZone || (this.flags.map_zone as MapZone) || 'act1_road') as MapZone;
    this.flags.map_zone = this.mapZone;
    this.controlledId = this.resolveControlled(data.controlledId);
    this.refreshStoryBeatOnLoad();
    this.enterHub(data.playerX, data.playerZ);
  }

  private persist(msg = 'Progress noted.'): void {
    if (!this.world) return;
    this.flags.map_zone = this.mapZone;
    const data: SaveData = {
      version: 1,
      party: this.party,
      inventory: this.inventory,
      flags: this.flags,
      playerX: this.world.playerX,
      playerZ: this.world.playerZ,
      storyBeat: this.storyBeat,
      controlledId: this.controlledId,
      mapZone: this.mapZone,
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
      this.world.orbit(-dx * 0.0084, dy * 0.006); // ~1.2× prior RMB latches
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

  private resolveControlled(preferred?: JobId): JobId {
    const order: JobId[] = preferred
      ? [preferred, 'clerk', 'sergeant', 'convers', 'guide', 'surgeon']
      : ['clerk', 'sergeant', 'convers', 'guide', 'surgeon'];
    for (const id of order) {
      const m = this.party.find((p) => p.id === id);
      if (m && m.recruited && !m.outForAct && m.stats.hp > 0) return id;
    }
    return 'clerk';
  }

  private followerTrail(): JobId[] {
    return SELECT_ORDER.filter(
      (id) =>
        id !== this.controlledId &&
        this.party.some((p) => p.id === id && p.recruited && !p.outForAct && p.stats.hp > 0)
    );
  }

  /** Explicit Rest (10-rest-action): Surgeon required, once per beat — not auto-magic. */
  private surgeonPresent(): boolean {
    return this.party.some((p) => p.id === 'surgeon' && p.recruited && !p.outForAct && p.stats.hp > 0);
  }

  private currentRestBeatKey(): string {
    const beat =
      this.mapZone === 'act3_close'
        ? String(this.flags.act3_beat || 'river')
        : this.mapZone === 'corbieres'
          ? String(this.flags.act2_beat || 'road')
          : String(this.flags.act1_beat || 'road');
    return `${this.mapZone}:${beat}`;
  }

  private restUsedThisBeat(): boolean {
    return String(this.flags.rested_beat_key || '') === this.currentRestBeatKey();
  }

  private markRestUsedThisBeat(): void {
    this.flags.rested_beat_key = this.currentRestBeatKey();
  }

  /** Clear bleeds + partial HP. Caller enforces Surgeon / beat lock. */
  private applyPartyRestHeal(): void {
    for (const m of this.party) {
      if (!m.recruited || m.outForAct || m.stats.hp <= 0) continue;
      m.bleeding = false;
      m.bleedTicks = 0;
      if (m.stats.hp < m.stats.maxHp) {
        const gain = Math.max(3, Math.floor(m.stats.maxHp * 0.25));
        m.stats.hp = Math.min(m.stats.maxHp, m.stats.hp + gain);
      }
    }
    this.markRestUsedThisBeat();
    this.refreshPartyStrip();
  }

  /** Party-panel Rest — Elias works. Time and linen. */
  private tryExplicitRest(): void {
    if (this.combat) {
      this.toast('Not while iron’s up.');
      return;
    }
    if (!this.surgeonPresent()) {
      this.toast('No steady hands. Keep walking.');
      return;
    }
    if (this.restUsedThisBeat()) {
      this.toast('Linen’s spent. Wait for the next roof.');
      return;
    }
    this.applyPartyRestHeal();
    this.barkOnce('party_rest', 'Elias: Hold still who can. Time and linen — not miracles.');
    this.toast('Elias works. Time and linen.');
    this.persist();
  }

  /** 09: Act III river unlock — Serena OR Hugues deal OR priory aftermath (no new flags). */
  private act3RiverUnlocked(): boolean {
    if (this.flags.act3_done) return false;
    if (this.flags.talked_serena) return true;
    const deal = String(this.flags.captain_deal || 'none');
    if (this.flags.talked_hugues && deal !== 'none') return true;
    const path = String(this.flags.priory_path || '');
    const fightDone =
      !!this.flags.hold_door_done ||
      !!this.flags.priory_fight_done ||
      String(this.flags.act2_beat || '') === 'fight';
    if (path && fightDone) return true;
    return false;
  }

  selectCompanion(id: JobId): void {
    const m = this.party.find((p) => p.id === id);
    if (!m || !m.recruited || m.outForAct || m.stats.hp <= 0) {
      this.toast(`${id} unavailable.`);
      return;
    }
    this.controlledId = id;
    this.world?.setControlled(id, this.followerTrail());
    this.refreshPartyStrip();
    this.toast(`Controlling ${m.name}.`);
  }

  private cycleCompanion(dir: number): void {
    const living = SELECT_ORDER.filter((id) =>
      this.party.some((p) => p.id === id && p.recruited && !p.outForAct && p.stats.hp > 0)
    );
    if (!living.length) return;
    let idx = living.indexOf(this.controlledId);
    if (idx < 0) idx = 0;
    idx = (idx + dir + living.length) % living.length;
    this.selectCompanion(living[idx]);
  }

  private async enterHub(x: number, z: number): Promise<void> {
    this.screen = 'hub';
    this.clearUi();
    const canvas = document.getElementById('game-canvas') as HTMLCanvasElement;
    this.world?.dispose();
    this.controlledId = this.resolveControlled(this.controlledId);
    this.world = new World(canvas, this.mapZone);
    this.world.setPlayerPos(x, z);
    this.world.setControlled(this.controlledId, this.followerTrail());
    this.applyNpcVisibility();
    this.bindCanvasInput(canvas);
    this.renderHud();
    this.running = true;
    this.last = performance.now();
    requestAnimationFrame((t) => this.loop(t));
    await this.world.ready;
    this.applyNpcVisibility();
    this.world.setControlled(this.controlledId, this.followerTrail());
  }

  private applyNpcVisibility(): void {
    if (!this.world) return;
    if (this.mapZone === 'act1_road') {
      if (this.flags.ambush_done) this.world.hideNpc('bandits', true);
      if (this.flags.ferry_done) this.world.hideNpc('ferry', true);
      const act1Done = !!this.flags.act1_complete || !!this.flags.narbonne_outcome;
      this.world.hideNpc('corbieres_road', !act1Done);
      const act3Open = this.act3RiverUnlocked();
      this.world.hideNpc('act3_gate', !act3Open);
      return;
    }
    if (this.mapZone === 'corbieres') {
      if (this.flags.hold_door_done) this.world.hideNpc('hold_door', true);
      const act3Open = this.act3RiverUnlocked();
      this.world.hideNpc('act3_road', !act3Open);
      return;
    }
    if (this.mapZone === 'act3_close') {
      const beat = String(this.flags.act3_beat || 'river');
      const named = !!this.flags.lord_name_known && !!this.flags.lord_name;
      const showLeper = beat === 'leper' || !!this.flags.talked_leper || beat === 'lord' || beat === 'splinter' || beat === 'close';
      const showLordPath = beat === 'lord' || beat === 'splinter' || beat === 'close' || !!this.flags.lord_fate;
      const showSplinter =
        beat === 'splinter' || beat === 'close' || !!this.flags.lord_fate || beat === 'splinter';
      this.world.hideNpc('leper', beat === 'river');
      this.world.hideNpc('lord', !(showLordPath && named));
      this.world.hideNpc('lord_empty', !(showLordPath && !named));
      this.world.hideNpc('splinter', !(beat === 'splinter' || beat === 'close' || !!this.flags.lord_fate));
      // river_watch always available until act3_done
      this.world.hideNpc('river_watch', !!this.flags.act3_done);
    }
  }

  private renderHud(): void {
    const hud = document.createElement('div');
    hud.id = 'hud';
    const carrier = this.flags.chest_carrier || '—';
    const trust = this.flags.pilgrim_trust;
    const zoneLabel =
      this.mapZone === 'corbieres'
        ? 'Corbières priory'
        : this.mapZone === 'act3_close'
          ? 'Act III close'
          : 'Fontfroide–Narbonne road';
    hud.innerHTML = `
      <div class="topbar">
        <button class="btn" id="hud-party">Party (C)</button>
        <button class="btn" id="hud-inv">Inventory (I)</button>
        <button class="btn" id="hud-journal">Journal (J)</button>
        <button class="btn" id="hud-save">Save</button>
        <button class="btn" id="hud-title">Title</button>
      </div>
      <div class="objective panel">${this.storyBeat}<br/><span class="stats">carrier: ${carrier} · seal ${this.flags.seal_intact ? 'intact' : 'broken'} · pilgrim trust ${trust} · ${zoneLabel}</span></div>
      <div class="party-strip" id="party-strip"></div>
      <div class="minimap-hint panel">LMB walk · RMB NPC / orbit · Q/R · E/F · 1–5/Tab · J journal · H help</div>
    `;
    this.ui.appendChild(hud);
    hud.querySelector('#hud-party')!.addEventListener('click', () => this.showParty());
    hud.querySelector('#hud-inv')!.addEventListener('click', () => this.showInventory());
    hud.querySelector('#hud-journal')!.addEventListener('click', () => this.showJournal());
    hud.querySelector('#hud-save')!.addEventListener('click', () => this.persist());
    hud.querySelector('#hud-title')!.addEventListener('click', () => {
      this.persist('Autosaved on exit.');
      this.showTitle();
    });
    this.refreshPartyStrip();
  }

  private refreshPartyStrip(): void {
    const strip = document.getElementById('party-strip');
    if (!strip) return;
    const carrier = String(this.flags.chest_carrier || '');
    strip.innerHTML = SELECT_ORDER.map((id, i) => {
      const p = this.party.find((m) => m.id === id)!;
      const hpPct = Math.round((Math.max(0, p.stats.hp) / p.stats.maxHp) * 100);
      const dead = p.outForAct || p.stats.hp <= 0;
      const active = id === this.controlledId;
      const bag = carrier === id ? '<span class="bag-pip" title="carries bag">bag</span>' : '';
      const status = [
        p.outForAct ? 'out' : '',
        p.bleeding ? 'bleed' : '',
        p.stats.hp <= 0 && !p.outForAct ? 'down' : '',
      ]
        .filter(Boolean)
        .join(' ');
      return `<button class="portrait${active ? ' active' : ''}${dead ? ' dead' : ''}" data-job="${id}" ${dead ? 'disabled' : ''} title="${p.name} (${i + 1})">
        <span class="portrait-swatch" style="background:${JOB_PORTRAIT_COLOR[id]}"></span>
        <span class="portrait-meta"><strong>${i + 1} ${p.role}</strong>${bag}
        <span class="stats">HP ${p.stats.hp}/${p.stats.maxHp}${status ? ' · ' + status : ''}</span>
        <span class="bar"><span style="width:${hpPct}%"></span></span></span>
      </button>`;
    }).join('');
    strip.querySelectorAll('[data-job]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = (btn as HTMLElement).dataset.job as JobId;
        if (this.screen === 'hub') this.selectCompanion(id);
      });
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

  private openNpc(n: NpcDef): void {
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
    if (n.id === 'corbieres_road') {
      if (!this.flags.act1_complete && !this.flags.narbonne_outcome) {
        this.toast('Finish the Narbonne letter first.');
        return;
      }
      this.startDialogue('corbieres_road');
      return;
    }
    if (n.id === 'priory_door') {
      this.startDialogue('priory_stub');
      return;
    }
    if (n.id === 'berna') {
      this.startDialogue('berna');
      return;
    }
    if (n.id === 'hugues') {
      if (!this.flags.priory_path && !this.flags.hold_door_done && !this.flags.priory_fight_done) {
        this.toast('Settle Berna’s yard fork first.');
        return;
      }
      this.startDialogue('hugues');
      return;
    }
    if (n.id === 'serena') {
      if (String(this.flags.captain_deal || 'none') === 'none' && !this.flags.talked_hugues) {
        this.toast('Speak Captain Hugues before Serena’s name.');
        return;
      }
      this.startDialogue('serena');
      return;
    }
    if (n.id === 'hold_door') {
      if (this.flags.hold_door_done) {
        this.toast('Sheep-gate already open.');
        return;
      }
      if (this.flags.priory_path !== 'hold_door' && this.flags.priory_path !== 'steal') {
        this.toast('Commit Berna’s hold-door or steal path first — or talk Hugues after talk path.');
        return;
      }
      this.startDialogue('hold_door');
      return;
    }
    if (n.id === 'road_back') {
      this.startDialogue('road_back_narbonne');
      return;
    }
    if (n.id === 'act3_road' || n.id === 'act3_gate') {
      if (this.flags.act3_done) {
        this.toast('Campaign frame already closed.');
        return;
      }
      if (!this.act3RiverUnlocked()) {
        this.toast('Speak Serena, settle Hugues’s deal, or finish the priory fight — then the river.');
        return;
      }
      this.startDialogue('act3_gate');
      return;
    }
    if (n.id === 'river_watch') {
      this.startDialogue('river_watch');
      return;
    }
    if (n.id === 'leper') {
      const beat = String(this.flags.act3_beat || '');
      if (beat === 'river') {
        this.toast('Speak the willow watch first — or take the infirmary from there.');
        return;
      }
      this.startDialogue('leper_house');
      return;
    }
    if (n.id === 'lord' || n.id === 'lord_empty') {
      const beat = String(this.flags.act3_beat || '');
      const allow =
        beat === 'lord' ||
        beat === 'splinter' ||
        beat === 'close' ||
        !!this.flags.lord_fate;
      if (!allow) {
        this.toast('River watch / leper first — or push for the hill house from the willows.');
        return;
      }
      const named = !!this.flags.lord_name_known && !!this.flags.lord_name;
      if (n.id === 'lord' && !named) {
        this.toast('No name — try the empty hill house.');
        return;
      }
      if (n.id === 'lord_empty' && named && !this.flags.lord_fate) {
        this.startDialogue('lord_raimon');
        return;
      }
      if (named) this.startDialogue('lord_raimon');
      else this.startDialogue('lord_rumor');
      return;
    }
    if (n.id === 'splinter') {
      const beat = String(this.flags.act3_beat || '');
      if (!this.flags.lord_fate && beat !== 'splinter') {
        this.toast('Settle the hill house (or empty rumor) before the wood — or skip roofs at the willows.');
        return;
      }
      this.startDialogue('splinter_judgment');
      return;
    }
    if (n.id === 'road_corbieres') {
      this.startDialogue('road_to_corbieres_from_act3');
      return;
    }
    if (n.id === 'road_narbonne') {
      this.startDialogue('road_to_narbonne_from_act3');
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
    if (id === 'berna' && this.flags.talked_berna) startId = 'after';
    if (id === 'hugues' && this.flags.talked_hugues) startId = 'after';
    if (id === 'serena' && this.flags.talked_serena) startId = 'after';
    if (id === 'leper_house' && this.flags.talked_leper) startId = 'after';
    if ((id === 'lord_raimon' || id === 'lord_rumor') && this.flags.lord_fate) startId = 'after';
    else if (id === 'lord_rumor' && this.flags.hint_lord_road && !this.flags.lord_fate) startId = 'hinted';
    if (id === 'splinter_judgment' && this.flags.act3_done) startId = 'after';
    else if (id === 'splinter_judgment' && this.flags.splinter_end) startId = 'close';
    this.dialogueNode = tree.find((n) => n.id === startId) ?? tree[0];
    this.dialogueNode = this.maybeAutoPilgrimClose(this.dialogueNode);
    this.dialogueNode = this.maybeAct3Variants(this.dialogueNode, id);
    this.dialogueNode = this.maybeContinuityLines(this.dialogueNode, id);
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
      this.dialogueNode = this.maybeAutoPilgrimClose(this.dialogueNode);
      if (this.dialogueNode) this.drawDialogue();
      return;
    }
    if (!effect || effect === 'end') this.closeDialogue();
  }

  private maybeAct3Variants(node: DialogueNode | null, id: string): DialogueNode | null {
    if (!node) return node;
    if (id === 'leper_house' && node.id === 'start') {
      let text = node.text;
      if (this.flags.party_is_forger || !this.flags.seal_intact) {
        text =
          'You smell of broken wax. Sleep anyway — sickness doesn’t read seals. Bells don’t ring here either. The Surgeon works; the rest keep quiet.';
      }
      const choices = [...(node.choices ?? [])];
      if (this.flags.child_burial === 'helped' && !choices.some((c) => c.next === 'work' && c.text.includes('buried'))) {
        choices.splice(1, 0, {
          text: 'We buried a child without bells already.',
          next: 'work',
        });
      }
      return { ...node, text, choices };
    }
    if (id === 'splinter_judgment' && node.id === 'start') {
      const deal = String(this.flags.captain_deal || 'none');
      const trust = Number(this.flags.pilgrim_trust) || 0;
      let text = node.text;
      if (deal === 'vines_seized') {
        text =
          'Hugues already counts vines. The wood’s the last magazine left in our bag. Altar, pine in the square, quiet snap, or keep it.';
      } else if (trust <= 0) {
        text =
          'No column left to shock. Break it for the empty road, or don’t. Altar, pine, quiet snap, or bag.';
      } else if (this.flags.party_is_forger || !this.flags.seal_intact) {
        text =
          'We’re already peekers. Keeping the wood makes us the next chest. Altar, public break, quiet snap, or keep walking with it.';
      }
      return { ...node, text };
    }
    return node;
  }

  private maybeAutoPilgrimClose(node: DialogueNode | null): DialogueNode | null {
    if (!node || this.dialogueNpc !== 'narbonne_agent' || node.id !== 'pilgrims') return node;
    const trust = Number(this.flags.pilgrim_trust) || 0;
    if (trust >= 2) {
      this.applyEffect('narbonne_delivered');
      return this.dialogueTree.find((n) => n.id === 'close_good') ?? node;
    }
    if (trust <= 0) {
      this.applyEffect('narbonne_delivered');
      return this.dialogueTree.find((n) => n.id === 'close_cold') ?? node;
    }
    return node;
  }

  private barkOnce(key: string, line: string): void {
    const flagKey = `bark_${key}`;
    if (this.flags[flagKey]) return;
    this.flags[flagKey] = true;
    this.toast(line);
  }

  /** 08-zone-transitions: restore objective if save landed mid-zone with a stale beat. */
  private refreshStoryBeatOnLoad(): void {
    if (this.flags.act3_done) return; // keep closing splinter beat
    const zone = this.mapZone;
    const beat = (this.storyBeat || '').trim();
    const stale =
      !beat ||
      beat.includes('(Act II stub)') ||
      beat === 'Back on the Fontfroide–Narbonne road.' ||
      beat === 'Fontfroide. Take the chest. Do not break the true seal.';
    if (zone === 'corbieres' && !this.flags.act2_beat) {
      this.storyBeat =
        'Corbières priory. Splinter on a false altar — northern captain wants the ruin as a warrant.';
      return;
    }
    if (zone === 'corbieres' && stale) {
      const path = String(this.flags.priory_path || '');
      const deal = String(this.flags.captain_deal || 'none');
      if (deal !== 'none') {
        this.storyBeat =
          'Priory settled with Hugues. Speak Na Serena for the lord’s name — Act III seed.';
      } else if (path === 'hold_door') {
        this.storyBeat = 'Nave door held. Column / locals through the sheep-gate — then the loft.';
      } else if (path === 'steal') {
        this.storyBeat = 'Chest taken quiet. Get out the sheep-gate before the loft notices.';
      } else if (path === 'talk') {
        this.storyBeat = 'Crowd thinning. Hold the yard or let Hugues claim the stones.';
      } else {
        this.storyBeat =
          'Corbières priory. Splinter on a false altar — northern captain wants the ruin as a warrant.';
      }
      return;
    }
    if (zone === 'act3_close' && !this.flags.act3_done) {
      const ab = String(this.flags.act3_beat || 'river');
      if (ab === 'leper') this.storyBeat = 'Infirmary roof. Boil linen — or move before dawn.';
      else if (ab === 'lord') this.storyBeat = 'Hill house next — hide, hang, or empty rumor.';
      else if (ab === 'splinter' || ab === 'close')
        this.storyBeat = 'Decide the wood — altar, pine, quiet snap, or bag.';
      else this.storyBeat = 'Act III. Names, then the splinter — altar or pine in the square.';
    }
  }

  /** 08 continuity one-liners when revisiting Act I NPCs (no new flags). */
  private maybeContinuityLines(node: DialogueNode | null, id: string): DialogueNode | null {
    if (!node || node.id !== 'after') return node;
    const act2 = !!this.flags.act2_beat || !!this.flags.priory_path;
    const act3Open = this.act3RiverUnlocked() || !!this.flags.act3_beat;
    if (id === 'cellarer' && act2) {
      return {
        ...node,
        text: 'Hill dust on you. The chest still wrong?',
        choices: [{ text: '(Leave)', effect: 'end' }],
      };
    }
    if (id === 'pilgrim_mairia' && (act2 || act3Open)) {
      const trust = Number(this.flags.pilgrim_trust) || 0;
      const text =
        trust >= 2 && !this.flags.act3_done
          ? 'We still eat. Don’t bring captains to our fire.'
          : trust <= 0
            ? 'Keep walking. The column remembers the porch.'
            : node.text;
      return { ...node, text, choices: [{ text: '(Leave)', effect: 'end' }] };
    }
    if (id === 'narbonne_agent' && this.flags.talked_narbonne && !this.flags.act3_done) {
      return {
        ...node,
        text: 'Letter’s filed. Wood’s your problem now.',
        choices: [{ text: '(Leave)', effect: 'end' }],
      };
    }
    return node;
  }

  private adjustTrust(delta: number): void {
    const cur = Number(this.flags.pilgrim_trust) || 0;
    const next = Math.max(0, Math.min(3, cur + delta));
    this.flags.pilgrim_trust = next;
    if (next >= 3 && cur < 3) this.barkOnce('pilgrim_trust_3', "Catalana: Column's eating our mud like friends.");
    if (next <= 0 && cur > 0) this.barkOnce('pilgrim_trust_0', "Don't look back for our smoke.");
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
      if (who === 'clerk') this.barkOnce('carrier_clerk', 'Guillem: Arnau has the bag. If they want it, they go through mail.');
      if (who === 'sergeant') this.barkOnce('carrier_sergeant', 'Arnau: Heavy hands, dry wax. Don’t flex the seal.');
      if (who === 'convers') this.barkOnce('carrier_convers', 'Catalana: Peire already carries keys. One more latch won’t kill him.');
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
      this.barkOnce('break_true_seal', 'Guillem: We’re the next forgers on this road. Formation stays tight.');
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
      this.flags.act1_complete = true;
      this.storyBeat =
        'Gate kept you out. Hill road to Corbières is open.';
      this.applyNpcVisibility();
      this.refreshObjective();
      this.persist();
      return 'close';
    }
    if (effect === 'narbonne_deferred_gate') {
      this.flags.narbonne_outcome = 'deferred_gate';
      this.flags.talked_narbonne = true;
      this.flags.act1_beat = 'narbonne_gate';
      this.flags.act1_complete = true;
      this.storyBeat =
        'You rode past Narbonne. Take the Corbières hill road.';
      this.applyNpcVisibility();
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (effect === 'end_act1') {
      this.flags.talked_narbonne = true;
      this.flags.act1_beat = 'narbonne_gate';
      this.flags.act1_complete = true;
      const outcome = String(this.flags.narbonne_outcome || '');
      const trust = Number(this.flags.pilgrim_trust) || 0;
      if (outcome === 'delivered') {
        this.storyBeat =
          trust >= 2
            ? 'Letter delivered. Take the hill road to Corbières (Act II stub).'
            : 'Letter delivered. Road hostile — hill road to Corbières is open.';
      } else if (outcome === 'letter_damaged') {
        this.storyBeat =
          'Letter stained but names ride. Hill road to Corbières is open.';
      } else if (outcome === 'refused_forger') {
        this.storyBeat =
          'Gate kept you out. Hill road to Corbières is the only clean exit.';
      } else if (outcome === 'deferred_gate') {
        this.storyBeat =
          'You rode past Narbonne. Take the Corbières hill road.';
      } else {
        this.storyBeat = 'Act I closed. Take the hill road to Corbières (Act II stub).';
      }
      this.toast('Act I frame complete — Corbières road unlocked.');
      this.applyNpcVisibility();
      this.maybeJournalDoneToast();
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (
      effect === 'priory_path_steal' ||
      effect === 'priory_path_talk' ||
      effect === 'priory_path_hold'
    ) {
      const path =
        effect === 'priory_path_steal' ? 'steal' : effect === 'priory_path_talk' ? 'talk' : 'hold_door';
      this.flags.priory_path = path;
      this.flags.talked_berna = true;
      this.flags.act2_beat = 'fork';
      if (path === 'steal') this.barkOnce('priory_path_steal', 'Peire: Latch is soft. Smoke helps.');
      if (path === 'talk') this.barkOnce('priory_path_talk', 'Arnau: If they hear the rim name, some will leave without blood.');
      if (path === 'hold_door') this.barkOnce('priory_path_hold', 'Guillem: Door’s mine. Sheep-gate’s yours.');
      return 'continue';
    }

    if (effect === 'end_priory_fork') {
      this.flags.talked_berna = true;
      const path = String(this.flags.priory_path || 'talk');
      if (path === 'steal') {
        this.storyBeat = 'Chest taken quiet. Get out the sheep-gate before the loft notices.';
        this.flags.smoke_loft = true;
        this.barkOnce('smoke_loft', "Catalana: Loft's coughing. Bolt's mine if you clear the angle.");
      } else if (path === 'hold_door') {
        this.storyBeat = 'Nave door held. Column / locals through the sheep-gate — then the loft.';
      } else {
        this.storyBeat = 'Crowd thinning. Hold the yard or let Hugues claim the stones.';
      }
      this.flags.act2_beat = 'fork';
      this.refreshObjective();
      this.persist();
      // talk + high trust can skip fight → go speak Hugues
      if (path === 'talk' && (Number(this.flags.pilgrim_trust) || 0) >= 2) {
        this.toast('Crowd parts without steel — speak Hugues.');
        return 'close';
      }
      if (path === 'talk') {
        this.startCombat('priory_yard');
        return 'combat';
      }
      if (path === 'steal' || path === 'hold_door') {
        this.toast(path === 'steal' ? 'Sheep-gate exit — expect pickets.' : 'Form at the nave door.');
        return 'close';
      }
      return 'close';
    }

    if (effect === 'start_hold_door') {
      if (this.flags.priory_path === 'steal') {
        this.startCombat('priory_yard');
      } else {
        this.startCombat('hold_door');
      }
      return 'combat';
    }

    if (effect === 'need_mold_kept') {
      if (this.flags.mold_fate !== 'kept') {
        this.dialogueNode = this.dialogueTree.find((n) => n.id === 'no_mold') ?? this.dialogueNode;
        this.drawDialogue();
        return 'stay';
      }
      return 'continue';
    }

    if (
      effect === 'captain_vines_spared' ||
      effect === 'captain_vines_seized' ||
      effect === 'captain_bribed_off'
    ) {
      const deal =
        effect === 'captain_vines_spared'
          ? 'vines_spared'
          : effect === 'captain_vines_seized'
            ? 'vines_seized'
            : 'bribed_off';
      this.flags.captain_deal = deal;
      this.flags.talked_hugues = true;
      this.flags.act2_beat = 'aftermath';
      if (deal === 'vines_spared') this.barkOnce('captain_vines_spared', 'Guillem: Empty stone. People walk.');
      if (deal === 'vines_seized') this.barkOnce('captain_vines_seized', 'Catalana: He’ll count vines either way. We bought time, not mercy.');
      if (deal === 'bribed_off') this.barkOnce('captain_bribed_off', 'Peire: Coin gone. Column still eats.');
      this.storyBeat =
        'Priory settled with Hugues. Speak Na Serena for the lord’s name — Act III seed.';
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (effect === 'learn_lord_name') {
      this.flags.lord_name = 'Raimon of Quéribus';
      this.flags.lord_name_known = true;
      this.flags.talked_serena = true;
      this.addItemOnce({
        id: 'hill_lord_name',
        name: 'Name: Raimon of Quéribus',
        description: 'Write it once. Burn the scrap. Act III seed.',
        qty: 1,
      });
      this.barkOnce('learn_lord_name', 'Arnau: Raimon of Quéribus. Write it once. Burn the scrap.');
      if (!this.flags.act3_beat) this.flags.act3_beat = 'river';
      this.storyBeat =
        'Act III. Names, then the splinter — altar or pine in the square.';
      this.applyNpcVisibility();
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (effect === 'lord_name_withheld') {
      this.flags.lord_name_known = false;
      this.flags.talked_serena = true;
      this.barkOnce('lord_name_withheld', 'Elias: A roof later may cost more than a name now.');
      if (!this.flags.act3_beat) this.flags.act3_beat = 'river';
      this.storyBeat =
        'Act III. Names, then the splinter — altar or pine in the square.';
      this.applyNpcVisibility();
      this.refreshObjective();
      this.persist();
      return 'close';
    }

    if (effect === 'enter_act3') {
      if (!this.act3RiverUnlocked()) {
        this.toast('Speak Serena, settle Hugues’s deal, or finish the priory fight first.');
        if (this.dialogueNpc === 'road_back_narbonne') {
          this.dialogueNode = this.dialogueTree.find((n) => n.id === 'gate_act3') ?? this.dialogueNode;
          this.drawDialogue();
          return 'stay';
        }
        return 'close';
      }
      this.mapZone = 'act3_close';
      this.flags.map_zone = 'act3_close';
      if (!this.flags.act3_beat) this.flags.act3_beat = 'river';
      this.storyBeat = this.flags.talked_serena
        ? 'Act III. Names, then the splinter — altar or pine in the square.'
        : 'Act III. No widow’s name yet — hill may be ash; wood still waits.';
      // Once-toasts if Serena skipped (09): prefer Hugues-path bark, else fight-path
      if (!this.flags.talked_serena) {
        const deal = String(this.flags.captain_deal || 'none');
        const viaHugues = !!this.flags.talked_hugues && deal !== 'none';
        if (viaHugues) {
          this.barkOnce(
            'act3_skip_serena_hugues',
            'Catalana: No widow’s name. Hill house may be ash. Wood still waits.'
          );
        } else {
          this.barkOnce(
            'act3_skip_serena_fight',
            'Guillem: Captain’s still talking or he’s not. We don’t need her to end the wood.'
          );
        }
      }
      this.barkOnce('enter_act3_river', 'Arnau: Wood or politics next. Don’t rush the wax.');
      if (this.flags.talked_leper || this.flags.bark_rest_leper) {
        this.barkOnce('enter_act3_after_leper', 'Elias: Bleeds quiet. Don’t open them for sport.');
      }
      this.maybeJournalDoneToast();
      this.applyNpcVisibility();
      this.persist();
      this.closeDialogue();
      void this.enterHub(ACT3_START.x, ACT3_START.z);
      return 'stay';
    }

    if (effect === 'act3_to_leper') {
      this.flags.act3_beat = 'leper';
      this.storyBeat = 'Infirmary roof. Boil linen — or move before dawn.';
      this.refreshObjective();
      this.applyNpcVisibility();
      return 'continue';
    }
    if (effect === 'act3_to_lord') {
      this.flags.act3_beat = 'lord';
      this.storyBeat = 'Hill house next — hide, hang, or empty rumor.';
      this.refreshObjective();
      this.applyNpcVisibility();
      return 'continue';
    }
    if (effect === 'act3_to_splinter') {
      this.flags.act3_beat = 'splinter';
      this.flags.lord_fate = this.flags.lord_fate || 'unnamed_fled';
      this.storyBeat = 'Straight to the wood’s end. Altar, pine, or bag.';
      this.refreshObjective();
      this.applyNpcVisibility();
      this.persist();
      return 'close';
    }

    if (effect === 'hint_lord_road') {
      this.flags.hint_lord_road = true;
      this.barkOnce('hint_lord_road', 'Catalana: Hill grit. He’s ahead, not waiting.');
      return 'continue';
    }

    if (effect === 'rest_leper') {
      this.flags.talked_leper = true;
      // Same Rest as party panel — no double-heal if linen already spent this beat
      if (!this.restUsedThisBeat() && this.surgeonPresent()) {
        this.applyPartyRestHeal();
        this.barkOnce('rest_leper', 'Elias: Dawn linen. No captains at the door.');
        this.toast('Elias works. Time and linen.');
      } else if (this.restUsedThisBeat()) {
        this.barkOnce('rest_leper', 'Elias: Dawn linen. No captains at the door.');
        this.toast('Linen’s spent. Wait for the next roof.');
      } else {
        this.barkOnce('rest_leper', 'Elias: Dawn linen. No captains at the door.');
      }
      return 'continue';
    }

    if (effect === 'skip_leper') {
      this.flags.talked_leper = true;
      this.flags.act3_beat = 'lord';
      this.barkOnce('skip_leper', 'Elias: Then the bleeds stay. Don’t ask me for miracles on the march.');
      this.storyBeat = 'Leper roof skipped. Hill house — or the wood.';
      this.refreshObjective();
      this.applyNpcVisibility();
      this.persist();
      return 'close';
    }

    if (effect === 'end_leper_to_lord') {
      this.flags.talked_leper = true;
      this.flags.act3_beat = 'lord';
      this.storyBeat = 'Lord settled next — then decide the wood.';
      this.refreshObjective();
      this.applyNpcVisibility();
      this.persist();
      return 'close';
    }

    if (effect === 'end_leper_to_splinter') {
      this.flags.talked_leper = true;
      this.flags.act3_beat = 'splinter';
      this.flags.lord_fate = this.flags.lord_fate || 'unnamed_fled';
      this.storyBeat = 'Enough roofs. Decide the wood before the road closes.';
      this.refreshObjective();
      this.applyNpcVisibility();
      this.persist();
      return 'close';
    }

    if (
      effect === 'lord_hidden' ||
      effect === 'lord_hidden_grain' ||
      effect === 'lord_named_hanged' ||
      effect === 'lord_unnamed_fled'
    ) {
      const fate =
        effect === 'lord_named_hanged'
          ? 'named_hanged'
          : effect === 'lord_unnamed_fled'
            ? 'unnamed_fled'
            : 'hidden';
      this.flags.lord_fate = fate;
      this.flags.act3_beat = 'splinter';
      if (effect === 'lord_hidden_grain') {
        this.addItemOnce({
          id: 'hill_grain',
          name: 'Hill grain',
          description: 'Silence bought in sacks. Column eats; Raimon stays unnamed by you.',
          qty: 1,
        });
      }
      if (fate === 'hidden') this.barkOnce('lord_hidden', 'Guillem: We owe a silence. Keep it.');
      if (fate === 'named_hanged')
        this.barkOnce('lord_named_hanged', 'Catalana: Hill house will empty. Don’t sleep there.');
      if (fate === 'unnamed_fled') this.toast('Hill house empty — or left alone. Splinter next.');
      this.storyBeat = 'Lord settled. Decide the wood before the road closes.';
      this.refreshObjective();
      this.applyNpcVisibility();
      this.persist();
      return 'close';
    }

    if (
      effect === 'splinter_altar' ||
      effect === 'splinter_broken_public' ||
      effect === 'splinter_broken_quiet' ||
      effect === 'splinter_kept_bag'
    ) {
      const end =
        effect === 'splinter_altar'
          ? 'altar'
          : effect === 'splinter_kept_bag'
            ? 'kept_bag'
            : 'broken_public';
      this.flags.splinter_end = end;
      this.flags.act3_beat = 'close';
      if (end === 'altar') {
        this.barkOnce('splinter_altar', 'Arnau: Quiet stone. Someone else can kneel without our bag.');
        this.inventory = this.inventory.filter((i) => i.id !== 'splinter');
      } else if (effect === 'splinter_broken_quiet') {
        this.barkOnce('break_quiet', 'Peire: No crowd. Just pine.');
        this.inventory = this.inventory.filter((i) => i.id !== 'splinter');
      } else if (end === 'broken_public') {
        this.barkOnce('splinter_broken_public', 'Peire: Pine sounds like pine. Good.');
        this.inventory = this.inventory.filter((i) => i.id !== 'splinter');
      } else {
        this.barkOnce('splinter_kept_bag', 'Guillem: Then we stay the next chest. Formation.');
      }
      // lord + splinter toast pairs
      if (this.flags.lord_fate === 'hidden' && end === 'broken_public') {
        this.toast('Raimon still safe — market never saw the show.');
      }
      if (this.flags.lord_fate === 'hidden' && end === 'kept_bag') {
        this.toast('Hill silence and a bagged relic. Someone will notice.');
      }
      return 'continue';
    }

    if (effect === 'end_act3') {
      this.flags.act3_done = true;
      this.flags.act3_beat = 'close';
      const end = String(this.flags.splinter_end || 'altar');
      if (end === 'broken_public') {
        this.storyBeat = 'Pine in the square. Crowds will remember the sound. The war goes on.';
      } else if (end === 'kept_bag') {
        this.storyBeat = 'Wood still in the bag. So does the risk. The war goes on.';
      } else {
        this.storyBeat = 'Splinter quiet on stone. Forgery named where it would take. The war goes on.';
      }
      this.barkOnce('end_act3', "Guillem: War's still moving. We walk.");
      this.toast('Campaign frame closed — war continues.');
      this.refreshObjective();
      this.persist();
      this.closeDialogue();
      this.showEpilogue();
      return 'stay';
    }

    if (effect === 'enter_corbieres') {
      this.mapZone = 'corbieres';
      this.flags.map_zone = 'corbieres';
      this.flags.act1_complete = true;
      if (!this.flags.act2_beat) this.flags.act2_beat = 'road';
      if (!this.flags.priory_path && String(this.flags.captain_deal || 'none') === 'none') {
        this.storyBeat =
          'Corbières priory. Splinter on a false altar — northern captain wants the ruin as a warrant.';
      }
      this.barkOnce('enter_priory', 'Catalana: Real stone. False altar. Watch the loft.');
      this.maybeJournalDoneToast();
      this.persist();
      this.closeDialogue();
      void this.enterHub(CORBIERES_START.x, CORBIERES_START.z);
      return 'stay';
    }

    if (effect === 'enter_act1_road') {
      this.mapZone = 'act1_road';
      this.flags.map_zone = 'act1_road';
      this.storyBeat = this.flags.priory_path
        ? 'Downhill toward ferry-mud. Priory’s behind — keep the bag dry.'
        : 'Back on the Fontfroide–Narbonne road.';
      if (this.flags.priory_path) {
        this.barkOnce('return_aude', 'Guillem: Priory’s behind us. Keep the bag dry.');
      } else {
        this.toast('Returning to Act I road.');
      }
      this.maybeJournalDoneToast();
      this.persist();
      this.closeDialogue();
      void this.enterHub(-1.2, -4.2);
      return 'stay';
    }

    return 'close';
  }

  private maybeJournalDoneToast(): void {
    const entries = buildJournal(this.flags, this.party);
    for (const e of entries) {
      if (e.status === 'done' && !this.journalToastIds.has(e.id)) {
        this.journalToastIds.add(e.id);
        this.toast(`Journal updated: ${e.title}`);
        break;
      }
    }
  }

  private refreshObjective(): void {
    const obj = document.querySelector('#hud .objective');
    if (!obj) return;
    const carrier = this.flags.chest_carrier || '—';
    const trust = this.flags.pilgrim_trust;
    const zoneLabel =
      this.mapZone === 'corbieres'
        ? 'Corbières priory'
        : this.mapZone === 'act3_close'
          ? 'Act III close'
          : 'Fontfroide–Narbonne road';
    obj.innerHTML = `${this.storyBeat}<br/><span class="stats">carrier: ${carrier} · seal ${this.flags.seal_intact ? 'intact' : 'broken'} · pilgrim trust ${trust} · ${zoneLabel}</span>`;
  }

  private startCombat(
    encounter: CombatEncounter,
    opts?: { shoveWater?: boolean }
  ): void {
    const shoveWater =
      opts?.shoveWater !== undefined ? opts.shoveWater : encounter === 'ferry';
    const mode = this.flags.combat_mode === 'rounds' ? 'rounds' : 'rtwp';
    this.combat = new CombatSession(this.party, {
      encounter,
      sealIntact: !!this.flags.seal_intact,
      hasLoft: encounter === 'ambush' ? !!this.flags.has_loft_ambush : true,
      shoveWater,
      pilgrimTrust: Number(this.flags.pilgrim_trust) || 0,
      mode,
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
    const rtwp = c.mode === 'rtwp';
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
    const orderLabel = (id: string): string => {
      const map: Record<string, string> = {
        hold: 'Hold line',
        cut_rope: c.encounter === 'hold_door' ? 'Open sheep-gate' : 'Cut rope',
        thrust: 'Thrust',
        point: 'Point',
        call_out: 'Call out',
        bolt: 'Bolt',
        brace: 'Brace',
        brace_wagon: 'Brace wagon',
        stabilize: 'Stabilize',
        tend: 'Tend',
        wait: 'Wait',
        shove: 'Shove',
        show_seal: 'Show seal',
      };
      return map[id] ?? id;
    };
    const allies = c.allies
      .map((a) => {
        const selected = a.memberId === (c.selectedAllyId ?? c.activeAllyId);
        const holdPip =
          a.holding && c.holdSeconds > 0 ? `Hold ${c.holdSeconds.toFixed(1)}s` : a.holding ? 'Hold' : '';
        const tags = [
          a.slot ?? '',
          holdPip,
          a.order ? orderLabel(a.order) : '',
          a.bleeding ? `bleed ${a.bleedTicks ?? 0}/2` : '',
          a.downed ? 'downed' : '',
          selected ? (rtwp ? 'selected' : 'your move') : '',
        ]
          .filter(Boolean)
          .join(' · ');
        const job = a.memberId ?? '';
        return `<button class="enemy-chip${selected ? ' active-ally' : ''}" data-select="${job}" ${a.downed || a.hp <= 0 ? 'disabled' : ''}>${a.name} HP ${a.hp}/${a.maxHp}${tags ? ' · ' + tags : ''}</button>`;
      })
      .join('');
    const log = c.log.slice(-5).join('<br/>');
    const actorId = c.selectedAllyId ?? c.activeAllyId;
    const actions =
      actorId && !c.over && (rtwp || c.turn === 'player') ? c.actionsFor(actorId) : [];
    const btns = actions
      .map(
        (a) =>
          `<button class="btn${a.id === 'hold' || a.id === 'cut_rope' || a.id === 'call_out' ? ' primary' : ''}" data-act="${a.id}" ${a.enabled ? '' : 'disabled'}>${a.label}</button>`
      )
      .join('');
    const banner = rtwp
      ? c.paused
        ? 'PAUSED — Space to resume · click portrait · queue orders'
        : 'LIVE — Space to pause'
      : `Round ${c.round} · sergeant→convers→guide→clerk→surgeon`;
    const encLabel =
      c.encounter === 'ambush'
        ? 'Borrowed-badge ambush'
        : c.encounter === 'ferry'
          ? 'Ferry rope'
          : c.encounter === 'hold_door'
            ? 'Nave door / sheep-gate'
            : 'Priory yard';
    panel.innerHTML = `
      <div class="combat-meta stats">${banner} · ${encLabel}${rtwp ? '' : ' · rounds fallback'}</div>
      <div class="enemy-row">${enemies}</div>
      <div class="enemy-row combat-portraits">${allies}</div>
      <div class="combat-log">${log}</div>
      <div class="actions">${btns}${
        rtwp && !c.over
          ? `<button class="btn" id="combat-pause">${c.paused ? 'Resume (Space)' : 'Pause (Space)'}</button>`
          : ''
      }${c.over ? '<button class="btn primary" id="finish">Continue</button>' : ''}</div>
    `;
    panel.querySelectorAll('[data-select]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = (btn as HTMLElement).dataset.select as JobId;
        if (!id) return;
        if (rtwp) {
          c.selectAlly(id);
          if (!c.paused) {
            c.paused = true;
            c.log.push('PAUSED — issuing orders.');
          }
        } else {
          c.activeAllyId = id;
        }
        this.drawCombat();
      });
    });
    panel.querySelectorAll('[data-act]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = (btn as HTMLElement).dataset.act as CombatActionId;
        c.act(id);
        this.drawCombat();
      });
    });
    panel.querySelector('#combat-pause')?.addEventListener('click', () => {
      c.togglePause();
      this.drawCombat();
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
      } else if (c.encounter === 'ferry') {
        this.flags.ferry_done = true;
        this.world?.hideNpc('ferry', true);
        this.flags.act1_beat = 'ferry';
        this.storyBeat = 'Ferry rope cut. Deliver the letter to the Narbonne agent.';
        this.barkOnce('ferry_cut', 'Peire: Rope’s cut. Move the column.');
        this.toast('Crossing freed.');
      } else if (c.encounter === 'hold_door') {
        this.flags.hold_door_done = true;
        this.flags.priory_fight_done = true;
        this.flags.act2_beat = 'fight';
        this.world?.hideNpc('hold_door', true);
        this.storyBeat =
          'Priory settled. Speak Hugues or ride — Act III still needs names and the splinter’s end.';
        this.toast('Sheep-gate open — nave held.');
      } else if (c.encounter === 'priory_yard') {
        this.flags.priory_fight_done = true;
        this.flags.act2_beat = 'fight';
        this.storyBeat =
          'Yard cleared. Speak Hugues — Act III still needs names and the splinter’s end.';
        this.toast('Yard scuffle over.');
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
    document.getElementById('party-panel')?.remove();
    const panel = document.createElement('div');
    panel.id = 'party-panel';
    panel.className = 'panel';
    const members = SELECT_ORDER.map((id) => this.party.find((p) => p.id === id)!)
      .map((p) => {
        const hpPct = Math.round((Math.max(0, p.stats.hp) / p.stats.maxHp) * 100);
        const flags = [
          p.id === this.controlledId ? 'active speaker' : '',
          p.outForAct ? 'out for Act' : '',
          p.bleeding ? 'bleeding' : '',
          p.stats.hp <= 0 && !p.outForAct ? 'downed' : '',
          this.flags.chest_carrier === p.id ? 'carries bag' : '',
        ]
          .filter(Boolean)
          .join(' · ');
        const canSelect = p.recruited && !p.outForAct && p.stats.hp > 0;
        return `<div class="member-card${p.id === this.controlledId ? ' controlled' : ''}">
          <div>
            <strong>${p.name}</strong>
            <div class="stats">${p.role} · ATK ${p.stats.atk} DEF ${p.stats.def}${flags ? ' · ' + flags : ''}</div>
            <div class="bar"><span style="width:${hpPct}%"></span></div>
          </div>
          <div class="stats">HP ${p.stats.hp}/${p.stats.maxHp}<br/>
          ${canSelect ? `<button class="btn" data-face="${p.id}">Set face</button>` : '<span class="stub-note">unavailable</span>'}
          </div>
        </div>`;
      })
      .join('');
    const canRest = !this.combat;
    panel.innerHTML = `<h2>Party — The Broken Seal</h2>
      <p class="stats" style="margin-top:0.35rem;opacity:0.75">Formation L→R: Guide · Sergeant · Convers · Clerk · Surgeon. Face = hub controlled (1–5 / Tab). Bag ≠ face.</p>
      <div class="members">${members}</div>
      <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.6rem">
        ${canRest ? `<button class="btn" id="party-rest" title="Elias works. Time and linen.">Rest — Elias works. Time and linen.</button>` : ''}
        <button class="btn" id="close-party">Close</button>
      </div>`;
    this.ui.appendChild(panel);
    panel.querySelector('#close-party')!.addEventListener('click', () => this.closeOverlay());
    panel.querySelector('#party-rest')?.addEventListener('click', () => {
      this.tryExplicitRest();
      panel.remove();
      this.showParty();
    });
    panel.querySelectorAll('[data-face]').forEach((btn) => {
      btn.addEventListener('click', () => {
        this.selectCompanion((btn as HTMLElement).dataset.face as JobId);
        panel.remove();
        this.showParty();
      });
    });
  }

  private showJournal(): void {
    this.screen = 'journal';
    document.getElementById('journal-panel')?.remove();
    const panel = document.createElement('div');
    panel.id = 'journal-panel';
    panel.className = 'panel';
    const entries = buildJournal(this.flags, this.party);
    const rows = entries
      .map(
        (e) => `<div class="journal-entry status-${e.status}">
          <div class="journal-head"><strong>${e.title}</strong><span class="journal-status">${e.status}</span></div>
          <p>${e.body}</p>
        </div>`
      )
      .join('');
    panel.innerHTML = `<h2>Journal</h2>
      <p class="stats" style="margin-top:0.35rem;opacity:0.75">Quest log from the road — not a flag dump.</p>
      <div class="journal-list">${rows || '<em>Nothing recorded yet.</em>'}</div>
      <button class="btn" id="close-journal">Close</button>`;
    this.ui.appendChild(panel);
    panel.querySelector('#close-journal')!.addEventListener('click', () => this.closeOverlay());
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
        ${
          i.id === 'bandages' || (i.id === 'true_letter' && this.flags.seal_intact)
            ? `<button class="btn" data-use="${i.id}">${i.id === 'true_letter' ? 'Peek seal' : 'Use'}</button>`
            : ''
        }</div>`
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
      return;
    }
    if (id === 'true_letter') {
      this.applyEffect('break_true_seal');
    }
  }

  private closeOverlay(): void {
    document.getElementById('party-panel')?.remove();
    document.getElementById('inventory-panel')?.remove();
    document.getElementById('journal-panel')?.remove();
    document.getElementById('help-panel')?.remove();
    document.getElementById('epilogue-panel')?.remove();
    this.screen = 'hub';
    this.refreshPartyStrip();
  }

  /** Controls help — content/narrative/12-controls-help.md as-is. */
  private showHelp(): void {
    this.screen = 'help';
    document.getElementById('help-panel')?.remove();
    const panel = document.createElement('div');
    panel.id = 'help-panel';
    panel.className = 'panel';
    panel.innerHTML = `<h2>The Broken Seal — five jobs. No miracles.</h2>
      <ul class="help-list">
        <li><strong>1–5 / Tab</strong> — who’s in front. Bag pip isn’t the face.</li>
        <li><strong>LMB</strong> move · <strong>RMB</strong> talk / orbit · <strong>Q/R</strong> turn the view</li>
        <li><strong>J</strong> journal (flags don’t lie politely)</li>
        <li><strong>Space</strong> — LIVE / PAUSED. Queue orders while paused; Hold, then Cut.</li>
        <li><strong>Rest</strong> — Elias and linen, once per beat. Not a spell.</li>
      </ul>
      <p class="help-tips">Seals, pilgrims, wet boots. Return closes the panel.</p>
      <button class="btn" id="close-help">Return</button>`;
    this.ui.appendChild(panel);
    panel.querySelector('#close-help')!.addEventListener('click', () => this.closeOverlay());
  }

  /** Act III ending overlay — content/narrative/11-epilogue.md */
  private showEpilogue(): void {
    this.screen = 'epilogue';
    document.getElementById('epilogue-panel')?.remove();
    const panel = document.createElement('div');
    panel.id = 'epilogue-panel';
    panel.className = 'panel';
    const cards = buildEpilogueCards(this.flags, this.party);
    const body = cards
      .map((c) => {
        const paras = c.body
          .split(/\n\n/)
          .map((p) => `<p>${p}</p>`)
          .join('');
        const head = c.title ? `<h3>${c.title}</h3>` : '';
        return `<div class="epilogue-card">${head}${paras}</div>`;
      })
      .join('');
    panel.innerHTML = `<h2>Frame closed — war continues</h2>
      <p class="stats" style="margin-top:0.35rem;opacity:0.75">Dirt and consequence. You do not win the war.</p>
      <div class="epilogue-scroll">${body}</div>
      <div style="display:flex;gap:0.5rem;flex-wrap:wrap;margin-top:0.75rem">
        <button class="btn primary" id="epilogue-title">Return to title</button>
        <button class="btn" id="epilogue-continue">Continue exploring</button>
      </div>`;
    this.ui.appendChild(panel);
    panel.querySelector('#epilogue-title')!.addEventListener('click', () => {
      document.getElementById('epilogue-panel')?.remove();
      this.showTitle();
    });
    panel.querySelector('#epilogue-continue')!.addEventListener('click', () => {
      this.closeOverlay();
      this.refreshObjective();
    });
  }

  private loop(t: number): void {
    if (!this.running || !this.world) return;
    const dt = Math.min(0.05, (t - this.last) / 1000);
    this.last = t;
    if (this.screen === 'hub') this.world.update(dt);
    if (this.screen === 'combat' && this.combat && !this.combat.over) {
      const before = this.combat.log.length;
      const wasPaused = this.combat.paused;
      this.combat.update(dt);
      if (this.combat.log.length !== before || this.combat.paused !== wasPaused || this.combat.over) {
        this.drawCombat();
      }
    }
    this.world.render();
    requestAnimationFrame((nt) => this.loop(nt));
  }
}
