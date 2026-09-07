import {
  createDefaultInventory,
  createDefaultParty,
  DIALOGUES,
  NPCS,
  PLAYER_START,
} from './data';
import { CombatSession } from './combat';
import { hasSave, loadGame, saveGame } from './save';
import type { DialogueNode, Item, PartyMember, SaveData, Screen } from './types';
import { World } from './world';

export class Game {
  private world: World | null = null;
  private ui: HTMLElement;
  private screen: Screen = 'title';
  private party: PartyMember[] = createDefaultParty();
  private inventory: Item[] = createDefaultInventory();
  private flags: Record<string, boolean | string | number> = {
    debtStance: '',
    wraithDead: false,
    talkedMirelle: false,
  };
  private storyBeat = 'Arrive in Merrowgate. Seek Quill about the drowned list.';
  private dialogueTree: DialogueNode[] = [];
  private dialogueNpc = '';
  private dialogueNode: DialogueNode | null = null;
  private combat: CombatSession | null = null;
  private last = 0;
  private running = false;
  private pendingInteract: (typeof NPCS)[number] | null = null;
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
      if (e.key === 'e' || e.key === 'E') {
        // E is interact backup (also used historically); Q/E reserved for camera — use F for interact
        if (this.screen === 'hub') this.tryInteract();
      }
      if (e.key === 'f' || e.key === 'F') {
        if (this.screen === 'hub') this.tryInteract();
      }
      if (e.key === 'q' || e.key === 'Q') {
        if (this.screen === 'hub') this.world?.orbit(-0.18);
      }
      if (e.key === 'r' || e.key === 'R') {
        // R rotates the other way (E kept as interact backup)
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
    setTimeout(() => t?.classList.remove('show'), 1800);
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
      <h1>Ashen Ledger</h1>
      <p class="tagline">In canal-city Merrowgate, unpaid debts curdle into living curses.
      A drowned creditor washed ashore clutching your names as collateral.</p>
      <div class="menu">
        <button class="btn primary" id="btn-new">New Investigation</button>
        <button class="btn" id="btn-continue" ${hasSave() ? '' : 'disabled'}>Continue</button>
      </div>
      <p class="hint">LMB move · RMB talk / drag orbit · Q/R rotate camera · E/F interact · I inv · C party · Ctrl+S save</p>
    `;
    this.ui.appendChild(el);
    el.querySelector('#btn-new')!.addEventListener('click', () => this.newGame());
    el.querySelector('#btn-continue')!.addEventListener('click', () => this.continueGame());
  }

  private newGame(): void {
    this.party = createDefaultParty();
    this.inventory = createDefaultInventory();
    this.flags = { debtStance: '', wraithDead: false, talkedMirelle: false };
    this.storyBeat = 'Arrive in Merrowgate. Seek Quill about the drowned list.';
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
    this.flags = data.flags;
    this.storyBeat = data.storyBeat;
    this.enterHub(data.playerX, data.playerZ);
  }

  private persist(msg = 'Progress inscribed.'): void {
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
        // Right-click: interact with NPC under cursor, else start orbit drag
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
    if (this.flags.wraithDead) this.world.hideNpc('wraith', true);
    this.world.onArrive = () => {
      if (this.pendingInteract) {
        const n = this.pendingInteract;
        this.pendingInteract = null;
        this.openNpc(n);
      }
    };

    this.bindCanvasInput(canvas);

    this.renderHud();
    this.running = true;
    this.last = performance.now();
    requestAnimationFrame((t) => this.loop(t));
    await this.world.ready;
    if (this.flags.wraithDead) this.world.hideNpc('wraith', true);
  }

  private renderHud(): void {
    const hud = document.createElement('div');
    hud.id = 'hud';
    hud.innerHTML = `
      <div class="topbar">
        <button class="btn" id="hud-party">Party (C)</button>
        <button class="btn" id="hud-inv">Inventory (I)</button>
        <button class="btn" id="hud-save">Save</button>
        <button class="btn" id="hud-title">Title</button>
      </div>
      <div class="objective panel">${this.storyBeat}</div>
      <div class="minimap-hint panel">LMB walk · RMB NPC talk / drag orbit · Q/R rotate · E/F interact</div>
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
    if ('combat' in n && n.combat) {
      if (this.flags.wraithDead) {
        this.toast('Only ash remains.');
        return;
      }
      if (!this.party.find((p) => p.id === 'mirelle')?.recruited) {
        this.toast('The wraith ignores you — recruit Quill first.');
        return;
      }
      this.startCombat();
      return;
    }
    this.startDialogue(n.dialogueId);
  }

  private startDialogue(id: string): void {
    const tree = DIALOGUES[id];
    if (!tree) return;
    this.dialogueNpc = id;
    this.dialogueTree = tree;
    const startId =
      id === 'mirelle' && this.party.find((p) => p.id === 'mirelle')?.recruited ? 'after' : 'start';
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

  private pickChoice(next?: string, effect?: string): void {
    if (effect) this.applyEffect(effect);
    if (effect === 'end' || effect === 'end_recruit') {
      document.getElementById('dialogue-box')?.remove();
      this.screen = 'hub';
      return;
    }
    if (next) {
      this.dialogueNode = this.dialogueTree.find((n) => n.id === next) ?? null;
      if (this.dialogueNode) this.drawDialogue();
    }
  }

  private applyEffect(effect: string): void {
    if (effect === 'recruit_forge') {
      this.flags.debtStance = 'forge';
      this.flags.talkedMirelle = true;
    }
    if (effect === 'recruit_confess') {
      this.flags.debtStance = 'confess';
      this.flags.talkedMirelle = true;
    }
    if (effect === 'end_recruit') {
      const m = this.party.find((p) => p.id === 'mirelle');
      if (m) m.recruited = true;
      const stance = this.flags.debtStance === 'forge' ? 'forged names' : 'true debt';
      this.storyBeat = `Mirelle joins you (debt stance: ${stance}). Defeat the Blot-Wraith at the east arch.`;
      this.toast('Mirelle Quill joins the party.');
      this.refreshObjective();
      this.persist();
    }
  }

  private refreshObjective(): void {
    const obj = document.querySelector('#hud .objective');
    if (obj) obj.textContent = this.storyBeat;
  }

  private startCombat(): void {
    this.combat = new CombatSession(this.party);
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
      .map(
        (e) =>
          `<div class="enemy-chip">${e.name} HP ${e.hp}/${e.maxHp}</div>`
      )
      .join('');
    const log = c.log.slice(-3).join('<br/>');
    const canAct = !c.over && c.turn === 'player';
    panel.innerHTML = `
      <div class="enemy-row">${enemies}</div>
      <div class="combat-log">${log}</div>
      <div class="actions">
        <button class="btn primary" id="atk" ${canAct ? '' : 'disabled'}>Attack</button>
        <button class="btn" id="skill" ${canAct ? '' : 'disabled'}>Unmake Line</button>
        <button class="btn" id="def" ${canAct ? '' : 'disabled'}>Defend</button>
        ${c.over ? '<button class="btn primary" id="finish">Continue</button>' : ''}
      </div>
    `;
    panel.querySelector('#atk')?.addEventListener('click', () => {
      c.playerAttack('wraith');
      this.drawCombat();
    });
    panel.querySelector('#skill')?.addEventListener('click', () => {
      c.playerSkill();
      this.drawCombat();
    });
    panel.querySelector('#def')?.addEventListener('click', () => {
      c.playerDefend();
      this.drawCombat();
    });
    panel.querySelector('#finish')?.addEventListener('click', () => this.endCombat());
  }

  private endCombat(): void {
    const c = this.combat!;
    c.applyHpToParty(this.party);
    document.getElementById('combat-panel')?.remove();
    this.combat = null;
    this.screen = 'hub';
    if (c.victory) {
      this.flags.wraithDead = true;
      this.world?.hideNpc('wraith', true);
      const stance = this.flags.debtStance;
      if (stance === 'forge') {
        this.storyBeat =
          'Wraith slain. With proof of forgery, you may seize or rewrite the Ashen Ledger.';
        this.inventory.push({
          id: 'vault_key',
          name: 'Vault Blot-Key',
          description: 'Warm iron. Opens the quay vault toward the Ledger.',
          qty: 1,
        });
      } else {
        this.storyBeat =
          'Wraith slain. Having confessed the debt, burn or rewrite the Ledger — both will scar.';
        this.inventory.push({
          id: 'ash_quill',
          name: 'Ash Quill',
          description: 'Writes corrections the Ledger cannot easily refuse.',
          qty: 1,
        });
      }
      this.toast('Victory. Spoils depend on your debt stance.');
      this.refreshObjective();
      this.persist();
    } else {
      this.toast('Defeat. Rest and try again.');
      const lead = this.party.find((p) => p.id === 'rowan');
      if (lead) lead.stats.hp = Math.max(8, Math.floor(lead.stats.maxHp * 0.4));
    }
  }

  private showParty(): void {
    this.screen = 'party';
    const panel = document.createElement('div');
    panel.id = 'party-panel';
    panel.className = 'panel';
    const members = this.party
      .filter((p) => p.recruited)
      .map((p) => {
        const hpPct = Math.round((p.stats.hp / p.stats.maxHp) * 100);
        const mpPct = Math.round((p.stats.mp / p.stats.maxMp) * 100);
        return `<div class="member-card">
          <div>
            <strong>${p.name}</strong>
            <div class="stats">${p.role} · ATK ${p.stats.atk} DEF ${p.stats.def}</div>
            <div class="bar"><span style="width:${hpPct}%"></span></div>
            <div class="bar mp"><span style="width:${mpPct}%"></span></div>
          </div>
          <div class="stats">HP ${p.stats.hp}/${p.stats.maxHp}<br/>MP ${p.stats.mp}/${p.stats.maxMp}</div>
        </div>`;
      })
      .join('');
    panel.innerHTML = `<h2>Party</h2><div class="members">${members}</div>
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
        ${i.id === 'salve' ? `<button class="btn" data-use="${i.id}">Use</button>` : ''}</div>`
      )
      .join('');
    panel.innerHTML = `<h2>Inventory</h2><div class="items">${items || '<em>Empty</em>'}</div>
      <button class="btn" id="close-inv">Close</button>`;
    this.ui.appendChild(panel);
    panel.querySelector('#close-inv')!.addEventListener('click', () => this.closeOverlay());
    panel.querySelectorAll('[data-use]').forEach((btn) => {
      btn.addEventListener('click', () => {
        const id = (btn as HTMLElement).dataset.use!;
        this.useItem(id);
        panel.remove();
        this.showInventory();
      });
    });
  }

  private useItem(id: string): void {
    const item = this.inventory.find((i) => i.id === id);
    if (!item || item.qty < 1) return;
    if (id === 'salve') {
      const lead = this.party.find((p) => p.id === 'rowan')!;
      lead.stats.hp = Math.min(lead.stats.maxHp, lead.stats.hp + 12);
      item.qty -= 1;
      if (item.qty <= 0) this.inventory = this.inventory.filter((i) => i.qty > 0);
      this.toast('Canal salve restores Rowan.');
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
