import * as THREE from 'three';
import { npcsForZone } from './data';
import { fitToHeight, loadModel, tintMeshes } from './assets';
import type { JobId, MapZone, NpcDef } from './types';
import { SELECT_ORDER } from './types';

const TILE = 1.2;
const GRID = 11; // -5..5
const PLAYER_RADIUS = 0.32;
/** Formation trail center-to-center (~0.9 m). Soft-slide uses a leaner radius so doorways stay clear. */
const FOLLOW_SPACING = 0.9;
const FOLLOWER_RADIUS = 0.22;
const ORBIT_DIST = 18;
const ORBIT_PITCH_MIN = 0.35;
const ORBIT_PITCH_MAX = 1.25;

/** Prefer muted medieval props; avoid ghost/crypt fantasy kits. */
const PATH = {
  player: './models/characters/clerk.glb',
  cellarer: './models/characters/odon.glb',
  mairia: './models/characters/marta.glb',
  wallDoor: './models/fantasy/wall-door.glb',
  wallWindow: './models/fantasy/wall-window-shutters.glb',
  wallBlock: './models/fantasy/wall-block.glb',
  wallCorner: './models/fantasy/wall-corner.glb',
  wallArch: './models/fantasy/wall-arch.glb',
  wallArchTop: './models/fantasy/wall-arch-top.glb',
  roofGable: './models/fantasy/roof-gable.glb',
  roofHigh: './models/fantasy/roof-high-gable.glb',
  lantern: './models/fantasy/lantern.glb',
  cart: './models/fantasy/cart.glb',
  lightpost: './models/graveyard/lightpost-single.glb',
  bench: './models/graveyard/bench.glb',
  fence: './models/graveyard/iron-fence.glb',
  pine: './models/graveyard/pine-fall.glb',
  pillar: './models/graveyard/pillar-square.glb',
  barrel: './models/pirate/barrel.glb',
  crate: './models/pirate/crate.glb',
  badgeBandit: './models/characters/badge_bandit.glb',
  badgeBanditB: './models/characters/badge_bandit_b.glb',
  ferryRope: './models/props/ferry_rope.glb',
  // Optional Act I parish art — load when present; placeholders otherwise
  parishPorch: './models/props/parish_porch.glb',
  burialGate: './models/props/burial_gate.glb',
  // Optional party / priory art — load when present; placeholders otherwise
  sergeant: './models/characters/sergeant.glb',
  convers: './models/characters/convers.glb',
  guide: './models/characters/guide.glb',
  surgeon: './models/characters/surgeon.glb',
  clerkParty: './models/characters/clerk.glb',
  // Optional Corbières / priory kit (Art drops) — null-ok loadModel
  falseAltar: './models/props/false_altar.glb',
  yardRope: './models/props/yard_rope.glb',
  collapsingLoft: './models/props/collapsing_loft.glb',
  sheepGate: './models/props/sheep_gate.glb',
  huguesPavilion: './models/props/hugues_pavilion.glb',
  bernaNpc: './models/characters/brin.glb',
  huguesNpc: './models/characters/rowan.glb',
  serenaNpc: './models/characters/mirelle.glb',
};

/** Axis-aligned collider on XZ plane (y ignored for walk). */
export type Collider = { minX: number; maxX: number; minZ: number; maxZ: number };

export class World {
  readonly scene = new THREE.Scene();
  readonly camera: THREE.OrthographicCamera;
  readonly renderer: THREE.WebGLRenderer;
  readonly raycaster = new THREE.Raycaster();
  readonly pointer = new THREE.Vector2();
  readonly ready: Promise<void>;

  private ground!: THREE.Mesh;
  private playerMesh!: THREE.Group;
  private npcMeshes = new Map<string, THREE.Group>();
  private followerMeshes = new Map<JobId, THREE.Group>();
  private pathTarget: THREE.Vector3 | null = null;
  private zone: MapZone = 'act1_road';
  private activeNpcs: NpcDef[] = [];
  private controlledId: JobId = 'clerk';
  private followerTrail: JobId[] = [];
  private readonly moveSpeed = 4.5;
  private marker!: THREE.Mesh;
  private clock = new THREE.Clock();
  private lanternFlickers: Array<{ light: THREE.PointLight; base: number }> = [];
  private colliders: Collider[] = [];
  private camYaw = Math.PI / 4;
  private camPitch = 0.72;
  private camDist = ORBIT_DIST;
  private frustumSize = 9;
  playerX = 0;
  playerZ = 2;
  onArrive: (() => void) | null = null;

  constructor(canvas: HTMLCanvasElement, zone: MapZone = 'act1_road') {
    this.zone = zone;
    this.activeNpcs = npcsForZone(zone);
    // Winter day — cold, muted, no gothic magic glow
    const bg = zone === 'corbieres' ? 0x5a6068 : zone === 'act3_close' ? 0x586068 : 0x6a7078;
    const fog = zone === 'corbieres' ? 0x7a8088 : zone === 'act3_close' ? 0x788088 : 0x8a9098;
    this.scene.background = new THREE.Color(bg);
    this.scene.fog = new THREE.FogExp2(fog, zone === 'act1_road' ? 0.028 : 0.032);

    const aspect = window.innerWidth / window.innerHeight;
    const frustum = this.frustumSize;
    this.camera = new THREE.OrthographicCamera(
      -frustum * aspect,
      frustum * aspect,
      frustum,
      -frustum,
      0.1,
      120
    );

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 0.95;

    this.setupLights();
    if (zone === 'corbieres') this.buildCorbieresHub();
    else if (zone === 'act3_close') this.buildAct3Hub();
    else this.buildBaseHub();

    this.playerMesh = this.makeCharacter(0x6a5a48, 0.55);
    this.scene.add(this.playerMesh);
    this.setPlayerPos(this.playerX, this.playerZ);

    for (const n of this.activeNpcs) {
      let g: THREE.Group;
      if (n.id === 'ferry') {
        g = this.makeFerryPlaceholder();
      } else if (n.id === 'bandits') {
        g = this.makeBanditPlaceholder(n.color);
      } else if (
        n.id === 'priory_door' ||
        n.id === 'corbieres_road' ||
        n.id === 'hold_door' ||
        n.id === 'act3_road' ||
        n.id === 'act3_gate' ||
        n.id === 'road_corbieres' ||
        n.id === 'road_narbonne' ||
        n.id === 'river_watch' ||
        n.id === 'leper' ||
        n.id === 'lord' ||
        n.id === 'lord_empty' ||
        n.id === 'splinter'
      ) {
        g = this.makeDoorPlaceholder(n.color);
      } else if (n.id === 'mold') {
        g = this.makeCharacter(n.color, 0.52);
      } else {
        g = this.makeCharacter(n.color, 0.5);
      }
      g.position.set(n.x * TILE, 0, n.z * TILE);
      g.userData.npcId = n.id;
      this.scene.add(g);
      this.npcMeshes.set(n.id, g);
      this.addCircleCollider(n.x * TILE, n.z * TILE, n.id === 'ferry' || n.id === 'priory_door' ? 0.55 : 0.4);
    }

    // Follower capsules (Art owns final meshes — placeholders only)
    const followerColors: Record<JobId, number> = {
      guide: 0x6a5038,
      sergeant: 0x4a4858,
      convers: 0x5a5040,
      clerk: 0x6a5a48,
      surgeon: 0x4a5848,
    };
    for (const id of SELECT_ORDER) {
      const f = this.makeCharacter(followerColors[id], 0.45);
      f.visible = false;
      this.scene.add(f);
      this.followerMeshes.set(id, f);
    }

    const mGeo = new THREE.RingGeometry(0.15, 0.28, 24);
    mGeo.rotateX(-Math.PI / 2);
    this.marker = new THREE.Mesh(
      mGeo,
      new THREE.MeshBasicMaterial({ color: 0xa09070, transparent: true, opacity: 0.65 })
    );
    this.marker.visible = false;
    this.scene.add(this.marker);

    window.addEventListener('resize', () => this.onResize());
    this.updateCamera();
    this.ready = this.polishWithModels();
  }

  orbit(dYaw: number, dPitch = 0): void {
    this.camYaw += dYaw;
    this.camPitch = Math.max(ORBIT_PITCH_MIN, Math.min(ORBIT_PITCH_MAX, this.camPitch + dPitch));
    this.updateCamera();
  }

  private updateCamera(): void {
    const tx = this.playerMesh?.position.x ?? this.playerX * TILE;
    const tz = this.playerMesh?.position.z ?? this.playerZ * TILE;
    const cp = Math.cos(this.camPitch);
    const sp = Math.sin(this.camPitch);
    const cy = Math.cos(this.camYaw);
    const sy = Math.sin(this.camYaw);
    const ox = this.camDist * cp * sy;
    const oy = this.camDist * sp;
    const oz = this.camDist * cp * cy;
    this.camera.position.set(tx + ox, oy, tz + oz);
    this.camera.lookAt(tx, 0.6, tz);
    this.camera.updateProjectionMatrix();
  }

  private setupLights(): void {
    const ambient = new THREE.AmbientLight(0x9aa0a8, 0.42);
    this.scene.add(ambient);

    const hemi = new THREE.HemisphereLight(0xc8d0d8, 0x4a4038, 0.65);
    this.scene.add(hemi);

    const sun = new THREE.DirectionalLight(0xe8e4d8, 0.7);
    sun.position.set(6, 18, 4);
    sun.castShadow = true;
    sun.shadow.mapSize.set(1024, 1024);
    sun.shadow.camera.near = 1;
    sun.shadow.camera.far = 40;
    const s = 12;
    sun.shadow.camera.left = -s;
    sun.shadow.camera.right = s;
    sun.shadow.camera.top = s;
    sun.shadow.camera.bottom = -s;
    sun.shadow.bias = -0.0008;
    sun.shadow.normalBias = 0.02;
    this.scene.add(sun);

    const cool = new THREE.DirectionalLight(0xb0c0d0, 0.25);
    cool.position.set(-5, 6, -6);
    this.scene.add(cool);
  }

  private addLanternLight(x: number, y: number, z: number, intensity = 0.55): void {
    const light = new THREE.PointLight(0xffc080, intensity, 6, 2);
    light.position.set(x, y, z);
    light.castShadow = false;
    this.scene.add(light);
    this.lanternFlickers.push({ light, base: intensity });
  }

  private addAABB(minX: number, maxX: number, minZ: number, maxZ: number): void {
    this.colliders.push({ minX, maxX, minZ, maxZ });
  }

  private addBoxCollider(cx: number, cz: number, halfW: number, halfD: number): void {
    this.addAABB(cx - halfW, cx + halfW, cz - halfD, cz + halfD);
  }

  private addCircleCollider(cx: number, cz: number, r: number): void {
    this.addBoxCollider(cx, cz, r * 0.85, r * 0.85);
  }

  private resolveCollision(
    fromX: number,
    fromZ: number,
    toX: number,
    toZ: number,
    radius = PLAYER_RADIUS
  ): { x: number; z: number } {
    let x = toX;
    let z = toZ;
    const r = radius;

    const hits = (px: number, pz: number) => {
      for (const c of this.colliders) {
        if (px + r > c.minX && px - r < c.maxX && pz + r > c.minZ && pz - r < c.maxZ) return c;
      }
      return null;
    };

    if (!hits(x, z)) return { x, z };
    // Axis slide — keep doorways traversable (followers + player soft-slide)
    if (!hits(x, fromZ)) return { x, z: fromZ };
    if (!hits(fromX, z)) return { x: fromX, z };
    return { x: fromX, z: fromZ };
  }

  /** Prefer ideal offset; if blocked, nudge sideways so trail doesn't plug doorways. */
  private softSlideFollower(
    fromX: number,
    fromZ: number,
    idealX: number,
    idealZ: number,
    sideX: number,
    sideZ: number
  ): { x: number; z: number } {
    const primary = this.resolveCollision(fromX, fromZ, idealX, idealZ, FOLLOWER_RADIUS);
    const dx = idealX - primary.x;
    const dz = idealZ - primary.z;
    if (dx * dx + dz * dz < 0.04) return primary;
    // Try soft lateral offsets (±) toward clear space
    for (const sign of [1, -1, 1.6, -1.6]) {
      const tx = idealX + sideX * 0.35 * sign;
      const tz = idealZ + sideZ * 0.35 * sign;
      const slid = this.resolveCollision(fromX, fromZ, tx, tz, FOLLOWER_RADIUS);
      const sx = idealX - slid.x;
      const sz = idealZ - slid.z;
      if (sx * sx + sz * sz < dx * dx + dz * dz) return slid;
    }
    return primary;
  }

  /** Fontfroide road: dirt track, ditch, abbey wall stubs, alley posts. */
  private buildBaseHub(): void {
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x5a5044,
      roughness: 0.95,
      metalness: 0.02,
    });
    const geo = new THREE.PlaneGeometry(GRID * TILE, GRID * TILE);
    geo.rotateX(-Math.PI / 2);
    this.ground = new THREE.Mesh(geo, groundMat);
    this.ground.receiveShadow = true;
    this.ground.name = 'ground';
    this.scene.add(this.ground);

    // Muddy road strip (walkable)
    const road = new THREE.Mesh(
      new THREE.BoxGeometry(2.4, 0.04, GRID * TILE),
      new THREE.MeshStandardMaterial({ color: 0x4a4034, roughness: 0.98 })
    );
    road.position.set(0.2, 0.02, 0);
    road.receiveShadow = true;
    road.name = 'road';
    this.scene.add(road);

    // Ditch (soft barrier — drown-evidence flavor)
    const ditch = new THREE.Mesh(
      new THREE.BoxGeometry(1.1, 0.08, GRID * TILE * 0.85),
      new THREE.MeshStandardMaterial({
        color: 0x3a4238,
        roughness: 0.9,
        metalness: 0.05,
      })
    );
    ditch.position.set(-3.6, -0.02, 0);
    ditch.receiveShadow = true;
    ditch.name = 'ditch';
    this.scene.add(ditch);
    this.addAABB(-4.2, -3.0, -GRID * TILE * 0.45, -0.9);
    this.addAABB(-4.2, -3.0, 0.9, GRID * TILE * 0.45);

    // Abbey wall stubs (west) — stone, muted
    const places: Array<[number, number, number, number, number]> = [
      [-5.0, -3.5, 1.8, 2.4, 0x6a6860],
      [-5.0, 0.5, 1.6, 2.6, 0x5e5c54],
      [-5.0, 4.0, 1.7, 2.2, 0x626058],
      [5.0, -2.5, 1.5, 1.8, 0x5a5048],
      [5.0, 2.5, 1.4, 1.6, 0x4a443c],
      [1.5, 5.2, 2.0, 1.4, 0x585048],
    ];
    for (const [gx, gz, w, h, col] of places) {
      const b = new THREE.Mesh(
        new THREE.BoxGeometry(w, h, w * 0.75),
        new THREE.MeshStandardMaterial({ color: col, roughness: 0.9 })
      );
      const px = gx * TILE * 0.85;
      const pz = gz * TILE * 0.85;
      b.position.set(px, h / 2, pz);
      b.castShadow = true;
      b.receiveShadow = true;
      b.name = 'temp-building';
      this.scene.add(b);
      this.addBoxCollider(px, pz, w * 0.5, w * 0.75 * 0.5);
    }

    // Alley stone posts (east) — formation fight framing
    const postMat = new THREE.MeshStandardMaterial({ color: 0x686860, roughness: 0.88 });
    const postL = new THREE.Mesh(new THREE.BoxGeometry(0.4, 2.0, 0.4), postMat);
    const postR = postL.clone();
    postL.position.set(2.4 * TILE, 1.0, -4 * TILE);
    postR.position.set(4.0 * TILE, 1.0, -4 * TILE);
    for (const a of [postL, postR]) {
      a.castShadow = true;
      a.name = 'temp-arch';
      this.scene.add(a);
    }
    this.addBoxCollider(2.4 * TILE, -4 * TILE, 0.28, 0.28);
    this.addBoxCollider(4.0 * TILE, -4 * TILE, 0.28, 0.28);

    // Label: coordinate / art placeholder
    const labelCanvas = document.createElement('canvas');
    labelCanvas.width = 512;
    labelCanvas.height = 64;
    const ctx = labelCanvas.getContext('2d')!;
    ctx.fillStyle = 'rgba(40,36,30,0.55)';
    ctx.fillRect(0, 0, 512, 64);
    ctx.fillStyle = '#c8c0b0';
    ctx.font = '28px Georgia, serif';
    ctx.fillText('Fontfroide → Narbonne road  [ART PLACEHOLDER]', 16, 42);
    const tex = new THREE.CanvasTexture(labelCanvas);
    const label = new THREE.Mesh(
      new THREE.PlaneGeometry(6.5, 0.8),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false })
    );
    label.position.set(0, 0.05, 5.8);
    label.rotation.x = -Math.PI / 2;
    label.name = 'art-label';
    this.scene.add(label);

    const grid = new THREE.GridHelper(GRID * TILE, GRID, 0x4a4438, 0x4a4438);
    grid.position.y = 0.01;
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.18;
    this.scene.add(grid);
  }

  /** Act II scaffold — Corbières priory road (placeholder geometry). */
  private buildCorbieresHub(): void {
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x4a4840,
      roughness: 0.96,
      metalness: 0.02,
    });
    const geo = new THREE.PlaneGeometry(GRID * TILE, GRID * TILE);
    geo.rotateX(-Math.PI / 2);
    this.ground = new THREE.Mesh(geo, groundMat);
    this.ground.receiveShadow = true;
    this.ground.name = 'ground';
    this.scene.add(this.ground);

    const road = new THREE.Mesh(
      new THREE.BoxGeometry(1.8, 0.04, GRID * TILE),
      new THREE.MeshStandardMaterial({ color: 0x3a3830, roughness: 0.98 })
    );
    road.position.set(0, 0.02, 0);
    road.receiveShadow = true;
    this.scene.add(road);

    // Scrub hills / rock stubs
    const rocks: Array<[number, number, number, number]> = [
      [-4.2, -2.0, 1.6, 1.4],
      [4.0, -1.5, 1.8, 1.6],
      [-3.5, 3.0, 1.4, 1.2],
      [3.8, 2.8, 1.5, 1.3],
      [-1.8, -4.2, 2.2, 1.8],
      [1.8, -4.0, 2.0, 1.7],
    ];
    for (const [gx, gz, w, h] of rocks) {
      const b = new THREE.Mesh(
        new THREE.BoxGeometry(w, h, w * 0.8),
        new THREE.MeshStandardMaterial({ color: 0x5a5850, roughness: 0.92 })
      );
      const px = gx * TILE * 0.85;
      const pz = gz * TILE * 0.85;
      b.position.set(px, h / 2, pz);
      b.castShadow = true;
      b.receiveShadow = true;
      b.name = 'temp-building';
      this.scene.add(b);
      this.addBoxCollider(px, pz, w * 0.45, w * 0.8 * 0.45);
    }

    const labelCanvas = document.createElement('canvas');
    labelCanvas.width = 560;
    labelCanvas.height = 64;
    const ctx = labelCanvas.getContext('2d')!;
    ctx.fillStyle = 'rgba(40,36,30,0.55)';
    ctx.fillRect(0, 0, 560, 64);
    ctx.fillStyle = '#c8c0b0';
    ctx.font = '26px Georgia, serif';
    ctx.fillText('Corbières priory road  [ACT II STUB — ART PLACEHOLDER]', 12, 42);
    const tex = new THREE.CanvasTexture(labelCanvas);
    const label = new THREE.Mesh(
      new THREE.PlaneGeometry(7.2, 0.8),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false })
    );
    label.position.set(0, 0.05, 5.5);
    label.rotation.x = -Math.PI / 2;
    label.name = 'art-label';
    this.scene.add(label);

    const grid = new THREE.GridHelper(GRID * TILE, GRID, 0x3a3830, 0x3a3830);
    grid.position.y = 0.01;
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.16;
    this.scene.add(grid);
  }

  private buildAct3Hub(): void {
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x5a5850,
      roughness: 0.95,
      metalness: 0.02,
    });
    this.ground = new THREE.Mesh(new THREE.PlaneGeometry(GRID * TILE * 1.4, GRID * TILE * 1.4), groundMat);
    this.ground.rotation.x = -Math.PI / 2;
    this.ground.receiveShadow = true;
    this.scene.add(this.ground);

    // Soft bounds
    this.addAABB(-GRID * TILE * 0.55, GRID * TILE * 0.55, -GRID * TILE * 0.55, -GRID * TILE * 0.48);
    this.addAABB(-GRID * TILE * 0.55, GRID * TILE * 0.55, GRID * TILE * 0.48, GRID * TILE * 0.55);
    this.addAABB(-GRID * TILE * 0.55, -GRID * TILE * 0.48, -GRID * TILE * 0.55, GRID * TILE * 0.55);
    this.addAABB(GRID * TILE * 0.48, GRID * TILE * 0.55, -GRID * TILE * 0.55, GRID * TILE * 0.55);

    // Leper house / hill house / square placeholders
    const hut = new THREE.Mesh(
      new THREE.BoxGeometry(2.2, 1.6, 1.8),
      new THREE.MeshStandardMaterial({ color: 0x4a4840, roughness: 0.92 })
    );
    hut.position.set(-2.0 * TILE, 0.8, -1.5 * TILE);
    hut.castShadow = true;
    hut.receiveShadow = true;
    hut.name = 'act3-leper-hut';
    this.scene.add(hut);
    this.addBoxCollider(-2.0 * TILE, -1.5 * TILE, 1.0, 0.85);

    const hall = new THREE.Mesh(
      new THREE.BoxGeometry(2.6, 2.0, 2.0),
      new THREE.MeshStandardMaterial({ color: 0x4a4650, roughness: 0.9 })
    );
    hall.position.set(1.8 * TILE, 1.0, -2.2 * TILE);
    hall.castShadow = true;
    hall.name = 'act3-hill-hall';
    this.scene.add(hall);
    this.addBoxCollider(1.8 * TILE, -2.2 * TILE, 1.2, 0.95);

    const altar = new THREE.Mesh(
      new THREE.BoxGeometry(1.0, 0.7, 0.8),
      new THREE.MeshStandardMaterial({ color: 0x5a5448, roughness: 0.88 })
    );
    altar.position.set(0.2 * TILE, 0.35, -3.8 * TILE);
    altar.castShadow = true;
    altar.name = 'act3-splinter-altar';
    this.scene.add(altar);
    this.addBoxCollider(0.2 * TILE, -3.8 * TILE, 0.55, 0.45);

    const labelCanvas = document.createElement('canvas');
    labelCanvas.width = 520;
    labelCanvas.height = 64;
    const ctx = labelCanvas.getContext('2d')!;
    ctx.fillStyle = 'rgba(40,36,30,0.55)';
    ctx.fillRect(0, 0, 520, 64);
    ctx.fillStyle = '#c8c0b0';
    ctx.font = '26px Georgia, serif';
    ctx.fillText('Act III close — leper · lord · splinter', 12, 42);
    const tex = new THREE.CanvasTexture(labelCanvas);
    const label = new THREE.Mesh(
      new THREE.PlaneGeometry(6.8, 0.8),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false })
    );
    label.position.set(0, 0.05, 5.2);
    label.rotation.x = -Math.PI / 2;
    label.name = 'art-label';
    this.scene.add(label);

    const grid = new THREE.GridHelper(GRID * TILE, GRID, 0x3a3830, 0x3a3830);
    grid.position.y = 0.01;
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.16;
    this.scene.add(grid);
  }

  private makeDoorPlaceholder(color: number): THREE.Group {
    const g = new THREE.Group();
    const frame = new THREE.Mesh(
      new THREE.BoxGeometry(1.1, 2.2, 0.35),
      new THREE.MeshStandardMaterial({ color, roughness: 0.9 })
    );
    frame.position.y = 1.1;
    frame.castShadow = true;
    const plank = new THREE.Mesh(
      new THREE.BoxGeometry(0.7, 1.6, 0.12),
      new THREE.MeshStandardMaterial({ color: 0x3a3020, roughness: 0.95 })
    );
    plank.position.set(0, 0.95, 0.2);
    plank.castShadow = true;
    g.add(frame, plank);
    g.name = 'door-placeholder';
    return g;
  }

    private makeChestPlaceholder(): THREE.Group {
    const g = new THREE.Group();
    const box = new THREE.Mesh(
      new THREE.BoxGeometry(0.7, 0.4, 0.45),
      new THREE.MeshStandardMaterial({ color: 0x4a3424, roughness: 0.85 })
    );
    box.position.y = 0.2;
    box.castShadow = true;
    const lid = new THREE.Mesh(
      new THREE.BoxGeometry(0.72, 0.08, 0.48),
      new THREE.MeshStandardMaterial({ color: 0x3a2818, roughness: 0.8 })
    );
    lid.position.set(0, 0.42, -0.05);
    lid.rotation.x = -0.45;
    lid.castShadow = true;
    g.add(box, lid);
    g.name = 'chest-placeholder';
    return g;
  }

  private makeFerryPlaceholder(): THREE.Group {
    const g = new THREE.Group();
    const post = new THREE.Mesh(
      new THREE.CylinderGeometry(0.08, 0.1, 1.4, 8),
      new THREE.MeshStandardMaterial({ color: 0x4a4030, roughness: 0.9 })
    );
    post.position.y = 0.7;
    post.castShadow = true;
    const rope = new THREE.Mesh(
      new THREE.CylinderGeometry(0.03, 0.03, 2.2, 6),
      new THREE.MeshStandardMaterial({ color: 0x8a7a58, roughness: 0.85 })
    );
    rope.rotation.z = Math.PI / 2;
    rope.position.set(0.9, 1.1, 0);
    g.add(post, rope);
    g.name = 'ferry-placeholder';
    return g;
  }

  private makeBanditPlaceholder(color: number): THREE.Group {
    const g = this.makeCharacter(color, 0.52);
    const badge = new THREE.Mesh(
      new THREE.CircleGeometry(0.08, 10),
      new THREE.MeshStandardMaterial({ color: 0xa0a090, metalness: 0.6, roughness: 0.4 })
    );
    badge.position.set(0.12, 1.0, 0.22);
    g.add(badge);
    // second figure offset for "group"
    const g2 = this.makeCharacter(0x4a4038, 0.48);
    g2.position.set(0.55, 0, 0.2);
    g.add(g2);
    return g;
  }

  private removeNamed(prefix: string): void {
    const doomed: THREE.Object3D[] = [];
    this.scene.traverse((o) => {
      if (o.name.startsWith(prefix)) doomed.push(o);
    });
    for (const o of doomed) {
      o.parent?.remove(o);
    }
  }

  private async polishWithModels(): Promise<void> {
    // Optional party GLBs (non-blocking) — upgrade followers / player when files exist
    await this.tryHookPartyMeshes();
    if (this.zone === 'corbieres' || this.zone === 'act3_close') {
      // Stub maps — keep box geometry; optional priory kit / NPC GLBs when Art ships them.
      await this.tryHookPrioryKit();
      this.updateCamera();
      return;
    }
    const urls = [
      PATH.player,
      PATH.cellarer,
      PATH.mairia,
      PATH.wallDoor,
      PATH.wallWindow,
      PATH.wallBlock,
      PATH.wallCorner,
      PATH.wallArch,
      PATH.wallArchTop,
      PATH.roofGable,
      PATH.roofHigh,
      PATH.lantern,
      PATH.cart,
      PATH.lightpost,
      PATH.bench,
      PATH.fence,
      PATH.pine,
      PATH.pillar,
      PATH.barrel,
      PATH.crate,
    ];
    const loaded = await Promise.all(urls.map((u) => loadModel(u)));
    const byUrl = new Map<string, THREE.Group | null>();
    urls.forEach((u, i) => byUrl.set(u, loaded[i]));

    const take = (key: keyof typeof PATH) => byUrl.get(PATH[key])?.clone(true) ?? null;

    await this.upgradeCharacter('player', take('player'), 1.75, 0x6a5a48);
    await this.upgradeNpc('cellarer', take('cellarer'), 1.5, 0x6a6a58);
    await this.upgradeNpc('mairia', take('mairia'), 1.5, 0x6a5038);
    // Art hooks — use GLBs when present; keep placeholders if missing
    const banditA = await loadModel(PATH.badgeBandit);
    const banditB = await loadModel(PATH.badgeBanditB);
    if (banditA) {
      await this.upgradeNpc('bandits', banditA, 1.7, 0x3a3028, 0.1);
      // optional second figure already baked or skip
      if (banditB) {
        /* second mesh reserved — Art may dual-body later */
      }
    }
    const ferryArt = await loadModel(PATH.ferryRope);
    if (ferryArt) {
      await this.upgradeNpc('ferry', ferryArt, 1.4, 0x4a4030, 0.15);
    }

    this.colliders = [];
    this.addAABB(-4.2, -3.0, -GRID * TILE * 0.45, -0.9);
    this.addAABB(-4.2, -3.0, 0.9, GRID * TILE * 0.45);
    for (const n of this.activeNpcs) {
      this.addCircleCollider(
        n.x * TILE,
        n.z * TILE,
        n.id === 'ferry' || n.id === 'priory_door' ? 0.55 : 0.4
      );
    }

    // Parish porch + burial gate (Art drops) — after collider reset
    await this.tryHookParishProps();

    this.removeNamed('temp-building');
    this.removeNamed('temp-arch');

    // Abbey / roadside stone structures (Kenney walls recolored toward dirt-and-mail)
    this.placeBuilding(-5.0 * TILE * 0.85, -3.5 * TILE * 0.85, take, 'stone');
    this.placeBuilding(-5.0 * TILE * 0.85, 0.5 * TILE * 0.85, take, 'stone');
    this.placeBuilding(-5.0 * TILE * 0.85, 4.0 * TILE * 0.85, take, 'wood');
    this.placeBuilding(5.0 * TILE * 0.85, -2.5 * TILE * 0.85, take, 'wood');
    this.placeBuilding(5.0 * TILE * 0.85, 2.5 * TILE * 0.85, take, 'wood');
    this.placeBuilding(1.5 * TILE * 0.85, 5.2 * TILE * 0.85, take, 'wood');

    const pillarL = take('pillar');
    const pillarR = take('pillar');
    if (pillarL && pillarR) {
      fitToHeight(pillarL, 2.0);
      fitToHeight(pillarR, 2.0);
      tintMeshes(pillarL, 0x6a6860, 0.25);
      tintMeshes(pillarR, 0x6a6860, 0.25);
      pillarL.position.set(2.4 * TILE, 0, -4 * TILE);
      pillarR.position.set(4.0 * TILE, 0, -4 * TILE);
      this.scene.add(pillarL, pillarR);
      this.addBoxCollider(2.4 * TILE, -4 * TILE, 0.3, 0.3);
      this.addBoxCollider(4.0 * TILE, -4 * TILE, 0.3, 0.3);
    } else {
      const postMat = new THREE.MeshStandardMaterial({ color: 0x686860, roughness: 0.88 });
      const aL = new THREE.Mesh(new THREE.BoxGeometry(0.4, 2.0, 0.4), postMat);
      const aR = aL.clone();
      aL.position.set(2.4 * TILE, 1.0, -4 * TILE);
      aR.position.set(4.0 * TILE, 1.0, -4 * TILE);
      this.scene.add(aL, aR);
      this.addBoxCollider(2.4 * TILE, -4 * TILE, 0.28, 0.28);
      this.addBoxCollider(4.0 * TILE, -4 * TILE, 0.28, 0.28);
    }

    for (const [x, z] of [
      [-2.2, 2.0],
      [-2.5, 2.4],
      [3.8, 1.8],
    ] as const) {
      const barrel = take('barrel');
      if (!barrel) break;
      fitToHeight(barrel, 0.45);
      tintMeshes(barrel, 0x5a4838, 0.2);
      barrel.position.set(x, 0, z);
      this.scene.add(barrel);
      this.addCircleCollider(x, z, 0.28);
    }

    const crate = take('crate');
    if (crate) {
      fitToHeight(crate, 0.4);
      tintMeshes(crate, 0x5a4838, 0.15);
      crate.position.set(3.2, 0, 2.2);
      this.scene.add(crate);
      this.addBoxCollider(3.2, 2.2, 0.3, 0.3);
    }

    const cart = take('cart');
    if (cart) {
      fitToHeight(cart, 0.85);
      tintMeshes(cart, 0x4a4034, 0.2);
      cart.position.set(2.2, 0, 1.0);
      cart.rotation.y = -0.4;
      this.scene.add(cart);
      this.addBoxCollider(2.2, 1.0, 0.7, 0.4);
    }

    const bench = take('bench');
    if (bench) {
      fitToHeight(bench, 0.45);
      bench.position.set(-1.5, 0, -1.8);
      bench.rotation.y = 0.2;
      this.scene.add(bench);
      this.addBoxCollider(-1.5, -1.8, 0.55, 0.25);
    }

    for (const [x, z] of [
      [-2.8, -0.5],
      [1.8, -3.2],
      [-4.0, 3.0],
    ] as const) {
      const post = take('lightpost') ?? take('lantern');
      if (!post) continue;
      fitToHeight(post, 2.0);
      tintMeshes(post, 0x4a4838, 0.2);
      post.position.set(x, 0, z);
      this.scene.add(post);
      this.addCircleCollider(x, z, 0.18);
      this.addLanternLight(x, 1.6, z, 0.5);
    }

    const fence = take('fence');
    if (fence) {
      fitToHeight(fence, 1.0);
      tintMeshes(fence, 0x3a3830, 0.3);
      fence.position.set(1.6 * TILE, 0, -4.5 * TILE);
      this.scene.add(fence);
      this.addBoxCollider(1.6 * TILE, -4.5 * TILE, 0.7, 0.12);
      const fence2 = fence.clone(true);
      fence2.position.set(4.6 * TILE, 0, -4.5 * TILE);
      this.scene.add(fence2);
      this.addBoxCollider(4.6 * TILE, -4.5 * TILE, 0.7, 0.12);
    }

    const pine = take('pine');
    if (pine) {
      fitToHeight(pine, 2.4);
      pine.position.set(-5.5, 0, -4.5);
      this.scene.add(pine);
      this.addCircleCollider(-5.5, -4.5, 0.35);
      const pine2 = pine.clone(true);
      pine2.position.set(5.5, 0, 4.8);
      fitToHeight(pine2, 2.1);
      this.scene.add(pine2);
      this.addCircleCollider(5.5, 4.8, 0.35);
    }

    this.updateCamera();
  }

  private placeBuilding(
    x: number,
    z: number,
    take: (k: keyof typeof PATH) => THREE.Group | null,
    kind: 'stone' | 'wood'
  ): void {
    const wallA = kind === 'wood' ? take('wallBlock') : take('wallDoor') ?? take('wallBlock');
    const wallB = take('wallWindow') ?? take('wallBlock');
    const roof = take('roofHigh') ?? take('roofGable');
    if (!wallA || !wallB) {
      const h = 1.8;
      const b = new THREE.Mesh(
        new THREE.BoxGeometry(1.6, h, 1.4),
        new THREE.MeshStandardMaterial({
          color: kind === 'wood' ? 0x4a4438 : 0x5e5c54,
          roughness: 0.9,
        })
      );
      b.position.set(x, h / 2, z);
      b.castShadow = true;
      this.scene.add(b);
      this.addBoxCollider(x, z, 0.8, 0.7);
      return;
    }

    const g = new THREE.Group();
    fitToHeight(wallA, 1.35);
    fitToHeight(wallB, 1.35);
    tintMeshes(wallA, kind === 'stone' ? 0x6a6860 : 0x5a4a38, 0.35);
    tintMeshes(wallB, kind === 'stone' ? 0x6a6860 : 0x5a4a38, 0.35);
    wallA.position.set(0, 0, 0.55);
    wallB.position.set(0, 0, -0.55);
    wallB.rotation.y = Math.PI;
    g.add(wallA, wallB);
    const wallC = take('wallBlock');
    const wallD = take('wallCorner') ?? take('wallBlock');
    if (wallC && wallD) {
      fitToHeight(wallC, 1.35);
      fitToHeight(wallD, 1.35);
      tintMeshes(wallC, kind === 'stone' ? 0x6a6860 : 0x5a4a38, 0.35);
      tintMeshes(wallD, kind === 'stone' ? 0x6a6860 : 0x5a4a38, 0.35);
      wallC.position.set(0.55, 0, 0);
      wallC.rotation.y = Math.PI / 2;
      wallD.position.set(-0.55, 0, 0);
      wallD.rotation.y = -Math.PI / 2;
      g.add(wallC, wallD);
    }
    if (roof) {
      fitToHeight(roof, 0.7);
      tintMeshes(roof, 0x4a4034, 0.4);
      roof.position.set(0, 1.35, 0);
      g.add(roof);
    }
    g.position.set(x, 0, z);
    g.rotation.y = (x + z) % 2 === 0 ? Math.PI / 2 : 0;
    this.scene.add(g);
    this.addBoxCollider(x, z, 0.85, 0.75);
  }

  private async upgradeCharacter(
    _which: 'player',
    model: THREE.Group | null,
    height: number,
    tint: number
  ): Promise<void> {
    if (!model) return;
    fitToHeight(model, height);
    tintMeshes(model, tint, 0.15);
    const pos = this.playerMesh.position.clone();
    const rotY = this.playerMesh.rotation.y;
    this.scene.remove(this.playerMesh);
    this.playerMesh = model;
    this.playerMesh.position.copy(pos);
    this.playerMesh.rotation.y = rotY;
    this.scene.add(this.playerMesh);
  }


  /** Non-blocking: parish porch / burial gate props when Art ships them. */
  private async tryHookParishProps(): Promise<void> {
    if (this.zone !== 'act1_road') return;
    const parish = this.activeNpcs.find((n) => n.id === 'parish');
    const px = (parish?.x ?? 0.8) * TILE;
    const pz = (parish?.z ?? -2.6) * TILE;

    const porch = await loadModel(PATH.parishPorch);
    if (porch) {
      fitToHeight(porch, 2.35);
      tintMeshes(porch, 0x6a6860, 0.12);
      // Sit slightly behind/ beside the priest interact point
      porch.position.set(px - 0.15, 0, pz - 0.85);
      porch.rotation.y = Math.PI * 0.08;
      porch.name = 'parish-porch-art';
      this.scene.add(porch);
      this.addBoxCollider(px - 0.15, pz - 0.85, 1.1, 0.7);
    }

    const gate = await loadModel(PATH.burialGate);
    if (gate) {
      fitToHeight(gate, 1.85);
      tintMeshes(gate, 0x4a4840, 0.15);
      gate.position.set(px + 1.6, 0, pz - 0.4);
      gate.rotation.y = -Math.PI * 0.35;
      gate.name = 'burial-gate-art';
      this.scene.add(gate);
      this.addBoxCollider(px + 1.6, pz - 0.4, 0.7, 0.35);
    }
  }

  /** Non-blocking: if party/priory GLBs exist under public/models, upgrade meshes. */
  private async tryHookPartyMeshes(): Promise<void> {
    const jobs: Array<{ id: JobId; path: string; h: number; tint: number }> = [
      { id: 'clerk', path: PATH.clerkParty, h: 1.75, tint: 0x6a5a48 },
      { id: 'sergeant', path: PATH.sergeant, h: 1.78, tint: 0x4a4858 },
      { id: 'convers', path: PATH.convers, h: 1.72, tint: 0x5a5040 },
      { id: 'guide', path: PATH.guide, h: 1.7, tint: 0x6a5038 },
      { id: 'surgeon', path: PATH.surgeon, h: 1.68, tint: 0x4a5848 },
    ];
    for (const j of jobs) {
      const art = await loadModel(j.path);
      if (!art) continue;
      if (j.id === this.controlledId) {
        await this.upgradeCharacter('player', art.clone(true), j.h, j.tint);
      }
      const follower = this.followerMeshes.get(j.id);
      if (follower) {
        // Replace follower capsule with GLB clone when present
        const mesh = art.clone(true);
        fitToHeight(mesh, j.h * 0.92);
        tintMeshes(mesh, j.tint, 0.12);
        mesh.visible = follower.visible;
        mesh.position.copy(follower.position);
        this.scene.remove(follower);
        this.scene.add(mesh);
        this.followerMeshes.set(j.id, mesh);
      }
    }
  }


  /** Non-blocking: priory props (false altar, yard rope, loft, sheep-gate, pavilion) + NPC stand-ins. */
  private async tryHookPrioryKit(): Promise<void> {
    if (this.zone !== 'corbieres' && this.zone !== 'act3_close') return;

    if (this.zone === 'corbieres') {
      const door = this.activeNpcs.find((n) => n.id === 'priory_door');
      const dx = (door?.x ?? -2.2) * TILE;
      const dz = (door?.z ?? -3.5) * TILE;
      const hold = this.activeNpcs.find((n) => n.id === 'hold_door');
      const hx = (hold?.x ?? 2.0) * TILE;
      const hz = (hold?.z ?? -3.2) * TILE;
      const hug = this.activeNpcs.find((n) => n.id === 'hugues');
      const px = (hug?.x ?? -1.5) * TILE;
      const pz = (hug?.z ?? 0.5) * TILE;

      const sheep = await loadModel(PATH.sheepGate);
      if (sheep) {
        fitToHeight(sheep, 2.2);
        tintMeshes(sheep, 0x5a5848, 0.12);
        sheep.position.set(dx, 0, dz);
        sheep.name = 'sheep-gate-art';
        this.scene.add(sheep);
        this.addBoxCollider(dx, dz, 0.9, 0.4);
      }

      const rope = await loadModel(PATH.yardRope);
      if (rope) {
        fitToHeight(rope, 1.4);
        tintMeshes(rope, 0x4a4030, 0.12);
        rope.position.set(hx - 0.35, 0, hz + 0.2);
        rope.name = 'yard-rope-art';
        this.scene.add(rope);
      }

      const loft = await loadModel(PATH.collapsingLoft);
      if (loft) {
        fitToHeight(loft, 2.3);
        tintMeshes(loft, 0x5a5040, 0.1);
        loft.position.set(dx + 2.2, 0, dz - 1.2);
        loft.name = 'collapsing-loft-art';
        this.scene.add(loft);
        this.addBoxCollider(dx + 2.2, dz - 1.2, 1.2, 0.9);
      }

      const pavilion = await loadModel(PATH.huguesPavilion);
      if (pavilion) {
        fitToHeight(pavilion, 2.6);
        tintMeshes(pavilion, 0x4a4858, 0.1);
        pavilion.position.set(px - 0.4, 0, pz - 0.6);
        pavilion.name = 'hugues-pavilion-art';
        this.scene.add(pavilion);
        this.addBoxCollider(px - 0.4, pz - 0.6, 1.1, 0.8);
      }

      const altar = await loadModel(PATH.falseAltar);
      if (altar) {
        fitToHeight(altar, 1.1);
        tintMeshes(altar, 0x5a5448, 0.12);
        altar.position.set(0.2 * TILE, 0, -4.2 * TILE);
        altar.name = 'false-altar-art';
        this.scene.add(altar);
        this.addBoxCollider(0.2 * TILE, -4.2 * TILE, 0.7, 0.45);
      }

      const npcHooks: Array<{ id: string; path: string; h: number; tint: number }> = [
        { id: 'berna', path: PATH.bernaNpc, h: 1.65, tint: 0x4a5848 },
        { id: 'hugues', path: PATH.huguesNpc, h: 1.78, tint: 0x4a4858 },
        { id: 'serena', path: PATH.serenaNpc, h: 1.68, tint: 0x5a4058 },
      ];
      for (const h of npcHooks) {
        const art = await loadModel(h.path);
        if (art) await this.upgradeNpc(h.id, art, h.h, h.tint, 0.12);
      }
    }

    if (this.zone === 'act3_close') {
      const altarNpc = this.activeNpcs.find((n) => n.id === 'splinter');
      const ax = (altarNpc?.x ?? 0.2) * TILE;
      const az = (altarNpc?.z ?? -3.8) * TILE;
      const altar = await loadModel(PATH.falseAltar);
      if (altar) {
        fitToHeight(altar, 1.1);
        tintMeshes(altar, 0x5a5448, 0.15);
        altar.position.set(ax, 0, az);
        altar.name = 'false-altar-art';
        this.scene.add(altar);
      }
    }
  }

  private async upgradeNpc(
    id: string,
    model: THREE.Group | null,
    height: number,
    tint: number,
    tintStrength = 0.2
  ): Promise<void> {
    if (!model) return;
    const old = this.npcMeshes.get(id);
    if (!old) return;
    fitToHeight(model, height);
    tintMeshes(model, tint, tintStrength);
    model.position.copy(old.position);
    model.userData.npcId = id;
    model.visible = old.visible;
    this.scene.remove(old);
    this.scene.add(model);
    this.npcMeshes.set(id, model);
  }

  private makeCharacter(color: number, scale: number): THREE.Group {
    const g = new THREE.Group();
    const body = new THREE.Mesh(
      new THREE.CapsuleGeometry((0.28 * scale) / 0.5, (0.55 * scale) / 0.5, 6, 10),
      new THREE.MeshStandardMaterial({ color, roughness: 0.75 })
    );
    body.position.y = ((0.7 * scale) / 0.5) * 0.55;
    body.castShadow = true;
    const head = new THREE.Mesh(
      new THREE.SphereGeometry((0.22 * scale) / 0.5, 14, 14),
      new THREE.MeshStandardMaterial({ color: 0xd4c4a8 })
    );
    head.position.y = ((1.15 * scale) / 0.5) * 0.55;
    head.castShadow = true;
    g.add(body, head);
    return g;
  }

  setControlled(id: JobId, trail: JobId[]): void {
    this.controlledId = id;
    this.followerTrail = trail;
    this.layoutFollowers(true);
  }

  private layoutFollowers(snap: boolean, dt = 1 / 60): void {
    // trail already excludes controlledId + outForAct / downed (Game.followerTrail)
    for (const id of SELECT_ORDER) {
      const mesh = this.followerMeshes.get(id);
      if (!mesh) continue;
      if (id === this.controlledId || !this.followerTrail.includes(id)) {
        mesh.visible = false;
      }
    }

    const facing = this.playerMesh.rotation.y;
    const backX = -Math.sin(facing);
    const backZ = -Math.cos(facing);
    const sideX = Math.cos(facing);
    const sideZ = Math.sin(facing);
    // Frame-rate independent soft chase
    const lerp = snap ? 1 : 1 - Math.exp(-9 * Math.max(0.001, dt));

    let anchorX = this.playerMesh.position.x;
    let anchorZ = this.playerMesh.position.z;

    for (let slot = 0; slot < this.followerTrail.length; slot++) {
      const id = this.followerTrail[slot];
      const mesh = this.followerMeshes.get(id);
      if (!mesh) continue;
      mesh.visible = true;
      const side = slot % 2 === 0 ? -0.22 : 0.22;
      const idealX = anchorX + backX * FOLLOW_SPACING + sideX * side;
      const idealZ = anchorZ + backZ * FOLLOW_SPACING + sideZ * side;
      // Snap from ideal (avoid flying in from origin); chase uses current mesh pos
      const fromX = snap ? idealX : mesh.position.x;
      const fromZ = snap ? idealZ : mesh.position.z;
      const slid = this.softSlideFollower(fromX, fromZ, idealX, idealZ, sideX, sideZ);
      if (snap) {
        mesh.position.set(slid.x, 0, slid.z);
      } else {
        mesh.position.x += (slid.x - mesh.position.x) * lerp;
        mesh.position.z += (slid.z - mesh.position.z) * lerp;
        mesh.position.y = 0;
      }
      mesh.rotation.y = facing;
      // Offset chain: next slot trails this follower's settled target (not a blob on the leader)
      anchorX = slid.x;
      anchorZ = slid.z;
    }
  }

  setPlayerPos(x: number, z: number): void {
    this.playerX = x;
    this.playerZ = z;
    this.playerMesh.position.set(x * TILE, 0, z * TILE);
    this.updateCamera();
  }

  hideNpc(id: string, hide: boolean): void {
    const m = this.npcMeshes.get(id);
    if (m) m.visible = !hide;
  }

  private onResize(): void {
    const aspect = window.innerWidth / window.innerHeight;
    const frustum = this.frustumSize;
    this.camera.left = -frustum * aspect;
    this.camera.right = frustum * aspect;
    this.camera.top = frustum;
    this.camera.bottom = -frustum;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(window.innerWidth, window.innerHeight);
  }

  screenToGround(clientX: number, clientY: number): THREE.Vector3 | null {
    this.pointer.x = (clientX / window.innerWidth) * 2 - 1;
    this.pointer.y = -(clientY / window.innerHeight) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const hits = this.raycaster.intersectObject(this.ground);
    if (!hits.length) return null;
    return hits[0].point.clone();
  }

  pickNpc(clientX: number, clientY: number): NpcDef | null {
    this.pointer.x = (clientX / window.innerWidth) * 2 - 1;
    this.pointer.y = -(clientY / window.innerHeight) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const meshes: THREE.Object3D[] = [];
    for (const [, m] of this.npcMeshes) {
      if (m.visible) meshes.push(m);
    }
    const hits = this.raycaster.intersectObjects(meshes, true);
    if (!hits.length) return null;
    let obj: THREE.Object3D | null = hits[0].object;
    while (obj) {
      if (obj.userData?.npcId) {
        const id = obj.userData.npcId as string;
        return this.activeNpcs.find((n) => n.id === id) ?? null;
      }
      obj = obj.parent;
    }
    return null;
  }

  moveToWorld(point: THREE.Vector3): void {
    const half = (GRID * TILE) / 2 - 0.4;
    point.x = Math.max(-half, Math.min(half, point.x));
    point.z = Math.max(-half, Math.min(half, point.z));
    this.pathTarget = point;
    this.marker.position.set(point.x, 0.05, point.z);
    this.marker.visible = true;
  }

  nearestNpc(maxDist = 1.6): NpcDef | null {
    let best: NpcDef | null = null;
    let bestD = maxDist;
    const px = this.playerX * TILE;
    const pz = this.playerZ * TILE;
    for (const n of this.activeNpcs) {
      const m = this.npcMeshes.get(n.id);
      if (m && !m.visible) continue;
      const dx = n.x * TILE - px;
      const dz = n.z * TILE - pz;
      const d = Math.hypot(dx, dz);
      if (d < bestD) {
        bestD = d;
        best = n;
      }
    }
    return best;
  }

  update(dt: number): void {
    const t = this.clock.getElapsedTime();
    for (let i = 0; i < this.lanternFlickers.length; i++) {
      const f = this.lanternFlickers[i];
      f.light.intensity = f.base * (0.9 + 0.1 * Math.sin(t * 4 + i * 1.7));
    }

    if (!this.pathTarget) {
      this.layoutFollowers(false, dt);
      this.updateCamera();
      return;
    }
    const pos = this.playerMesh.position;
    const dx = this.pathTarget.x - pos.x;
    const dz = this.pathTarget.z - pos.z;
    const dist = Math.hypot(dx, dz);
    if (dist < 0.08) {
      this.pathTarget = null;
      this.marker.visible = false;
      this.playerX = pos.x / TILE;
      this.playerZ = pos.z / TILE;
      this.onArrive?.();
      this.updateCamera();
      return;
    }
    const step = Math.min(dist, this.moveSpeed * dt);
    const wantX = pos.x + (dx / dist) * step;
    const wantZ = pos.z + (dz / dist) * step;
    const resolved = this.resolveCollision(pos.x, pos.z, wantX, wantZ);
    const moved = Math.hypot(resolved.x - pos.x, resolved.z - pos.z);
    if (moved < 1e-4 && dist > 0.15) {
      this.pathTarget = null;
      this.marker.visible = false;
    } else {
      pos.x = resolved.x;
      pos.z = resolved.z;
      this.playerMesh.rotation.y = Math.atan2(dx, dz);
    }
    this.playerX = pos.x / TILE;
    this.playerZ = pos.z / TILE;
    this.layoutFollowers(false, dt);
    this.updateCamera();
  }

  render(): void {
    this.renderer.render(this.scene, this.camera);
  }

  dispose(): void {
    this.renderer.dispose();
  }
}
