import * as THREE from 'three';
import { npcsForZone } from './data';
import { fitToHeight, loadModel, tintMeshes } from './assets';
import type { JobId, MapZone, NpcDef, WorldInteractable } from './types';
import { SELECT_ORDER } from './types';

const TILE = 1.2;
/** Act I outdoor half-extents in meters (docs/open-map-extents-act1.md): ~32×100 m. */
const HALF_X = 16;
const HALF_Z = 50;
/** Legacy square stub maps (Corbières / Act III) until their outdoor docs land. */
const GRID = 18; // ~21.6 m
const PLAYER_RADIUS = 0.32;
/** Soft-slide leaner radius so ≥1.2 m doorways stay clear. */
const FOLLOWER_RADIUS = 0.22;
/** m/s — below this, keep last yaw (no arrive / wall jitter). */
const FACE_MOVE_EPS = 0.15;
/** Exp yaw damp: yaw += shortestArc * (1 - exp(-TURN_RATE * dt)). */
const TURN_RATE = 12;
/** Hard turn cap while walking (~540°/s). */
const TURN_CAP_RAD = (540 * Math.PI) / 180;
/** In-place stop-turn before stepping (~360°/s). */
const STOP_TURN_RATE = (360 * Math.PI) / 180;
/** Follower position chase toward own slot (docs/locomotion-formation-v2.md). */
const FOLLOW_CHASE = 5.5;
/** Follower yaw lag vs leader when nearly stopped (slight lag, not instant-copy). */
const FOLLOW_YAW_LAG = 9;
/** Seconds of nearly-perp slide before facing velocity instead of click intent. */
const WALL_SLIDE_OVERRIDE_S = 0.25;
/**
 * Loose formation soft slots in leader space: (forward, right) meters.
 * Kill 0.9 m conga — ~2–3 wide, 2 ranks (docs/locomotion-formation-v2.md).
 */
const FORMATION_SLOTS: Record<JobId, { fwd: number; right: number }> = {
  sergeant: { fwd: -1.4, right: -0.7 },
  convers: { fwd: -1.4, right: 0.7 },
  guide: { fwd: -2.6, right: -1.1 },
  clerk: { fwd: -2.6, right: 1.1 },
  surgeon: { fwd: -2.8, right: 0.0 },
};
const ORBIT_DIST = 24;
const ORBIT_PITCH_MIN = 0.35;
const ORBIT_PITCH_MAX = 1.25;

/** Prefer muted medieval props; avoid ghost/crypt fantasy kits. */
const PATH = {
  player: './models/characters/clerk.glb',
  cellarer: './models/characters/guiraut.glb',
  mairia: './models/characters/mairia.glb',
  ramon: './models/characters/ramon.glb',
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
  mileMarker: './models/props/mile_marker.glb',
  moldCavity: './models/props/mold_cavity.glb',
  cloisterArcade: './models/props/cloister_arcade.glb',
  cloisterWell: './models/props/cloister_well.glb',
  leperRest: './models/props/leper_rest.glb',
  narbonneAgent: './models/characters/narbonne_agent.glb',
  // Upcoming Art aliases (non-blocking) — prefer agent, then courier names
  narbonneCourier: './models/characters/narbonne_courier.glb',
  hoodedCourier: './models/characters/hooded_courier.glb',
  // Interim NPC stand-ins (brin/rowan/mirelle) — not final hero art
  bernaNpc: './models/characters/brin.glb',
  huguesNpc: './models/characters/rowan.glb',
  serenaNpc: './models/characters/mirelle.glb',
  // Optional named NPC Art (prefer when present)
  bernaArt: './models/characters/berna.glb',
  huguesArt: './models/characters/hugues.glb',
  serenaArt: './models/characters/serena.glb',
  // Upcoming Art road dressing (exact names) — non-blocking loadModel
  roadCart: './models/props/road_cart.glb',
  roadFenceRun: './models/props/road_fence_run.glb',
  mudRutPatch: './models/props/mud_rut_patch.glb',
  pilgrimBundle: './models/props/pilgrim_bundle.glb',
  waysideCross: './models/props/wayside_cross.glb',
  ferryBoat: './models/props/ferry_boat.glb',
  // Building shells (Art exact names) — null-ok; replace Kenney/box when present
  fontfroideDormer: './models/props/fontfroide_dormer.glb',
  parishNaveShell: './models/props/parish_nave_shell.glb',
  prioryRuinWall: './models/props/priory_ruin_wall.glb',
  prioryNaveShell: './models/props/priory_nave_shell.glb',
  roadHouseShell: './models/props/road_house_shell.glb',
  goldsmithShopShell: './models/props/goldsmith_shop_shell.glb',
  // Open-map stockpile (Art) — |x|≥4 bands + hub pockets; null-ok
  cloisterArcadeB: './models/props/cloister_arcade_b.glb',
  ruinDebrisPile: './models/props/ruin_debris_pile.glb',
  villageShed: './models/props/village_shed.glb',
  oliveOrCypress: './models/props/olive_or_cypress.glb',
  marketStall: './models/props/market_stall.glb',
  leperBellPost: './models/props/leper_bell_post.glb',
  lootChest: './models/props/loot_chest.glb',
  inspectCrate: './models/props/inspect_crate.glb',
  herbPouch: './models/props/herb_pouch.glb',
  letterPacket: './models/props/letter_packet.glb',
  weaponRack: './models/props/weapon_rack.glb',
  // Kenney extras for zone densify (already licensed in repo)
  borderPillar: './models/graveyard/border-pillar.glb',
  lanternCandle: './models/graveyard/lantern-candle.glb',
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
  /** Prop RMB targets (inspect / loot / use). */
  private interactables = new Map<string, { mesh: THREE.Object3D; def: WorldInteractable }>();
  private pathTarget: THREE.Vector3 | null = null;
  /** Click-intent yaw (atan2 to destination). Blend while moving. */
  private intentYaw: number | null = null;
  /** Accumulated time velocity is nearly perpendicular to intent (wall-slide). */
  private wallSlideTimer = 0;
  /** Brief in-place yaw before stepping when stopped click needs >90°. */
  private stopTurnUntil = 0;
  private zone: MapZone = 'act1_road';
  private activeNpcs: NpcDef[] = [];
  private controlledId: JobId = 'clerk';
  private followerTrail: JobId[] = [];
  /** Compress offsets when doorways block (scale toward trail, then expand). */
  private formationCompress = 1;
  private formationBlockStreak = 0;
  private readonly moveSpeed = 4.5;
  private marker!: THREE.Mesh;
  private clock = new THREE.Clock();
  private lanternFlickers: Array<{ light: THREE.PointLight; base: number }> = [];
  private colliders: Collider[] = [];
  private camYaw = Math.PI / 4;
  private camPitch = 0.72;
  private camDist = ORBIT_DIST;
  private frustumSize = 14;
  playerX = 0;
  playerZ = 2;
  onArrive: (() => void) | null = null;

  constructor(canvas: HTMLCanvasElement, zone: MapZone = 'act1_road') {
    this.zone = zone;
    this.activeNpcs = npcsForZone(zone);
    // Winter dirt — overcast cold, muted haze (readable for orbit cam)
    const bg = zone === 'corbieres' ? 0x4e545c : zone === 'act3_close' ? 0x4c525a : 0x585e66;
    const fog = zone === 'corbieres' ? 0x6e747c : zone === 'act3_close' ? 0x6c727a : 0x7a8088;
    this.scene.background = new THREE.Color(bg);
    this.scene.fog = new THREE.FogExp2(fog, zone === 'act1_road' ? 0.014 : 0.036);

    const aspect = window.innerWidth / window.innerHeight;
    const frustum = this.frustumSize;
    this.camera = new THREE.OrthographicCamera(
      -frustum * aspect,
      frustum * aspect,
      frustum,
      -frustum,
      0.1,
      220
    );

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 0.82;

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
      this.addCircleCollider(
        n.x * TILE,
        n.z * TILE,
        n.id === 'ferry' || n.id === 'priory_door' ? 0.55 : 0.3
      );
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
      f.userData.jobId = id;
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
    // Cool overcast fill — less default Three.js bright, still orbit-readable
    const ambient = new THREE.AmbientLight(0x8a929a, 0.38);
    this.scene.add(ambient);

    const hemi = new THREE.HemisphereLight(0xb8c4d0, 0x3a342c, 0.72);
    this.scene.add(hemi);

    const sun = new THREE.DirectionalLight(0xd0d4d8, 0.48);
    sun.position.set(4, 22, 3);
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

    const cool = new THREE.DirectionalLight(0x9eb0c4, 0.32);
    cool.position.set(-6, 8, -5);
    this.scene.add(cool);

    const rim = new THREE.DirectionalLight(0xa8b0b8, 0.12);
    rim.position.set(2, 4, 8);
    this.scene.add(rim);
  }

  private addLanternLight(x: number, y: number, z: number, intensity = 0.55): void {
    const light = new THREE.PointLight(0xe8c090, intensity * 0.85, 5.5, 2);
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

  /** Fontfroide → Narbonne contiguous outdoor (~100 m N–S × ~32 m E–W). */
  private buildBaseHub(): void {
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x4a443a,
      roughness: 0.98,
      metalness: 0.01,
    });
    const geo = new THREE.PlaneGeometry(HALF_X * 2, HALF_Z * 2);
    geo.rotateX(-Math.PI / 2);
    this.ground = new THREE.Mesh(geo, groundMat);
    this.ground.receiveShadow = true;
    this.ground.name = 'ground';
    this.scene.add(this.ground);

    // Road crown x ∈ [-1.2, 1.2] full Z — keep clear of heavy colliders
    const road = new THREE.Mesh(
      new THREE.BoxGeometry(2.4, 0.04, HALF_Z * 2),
      new THREE.MeshStandardMaterial({ color: 0x3a342c, roughness: 0.99 })
    );
    road.position.set(0, 0.02, 0);
    road.receiveShadow = true;
    road.name = 'road';
    this.scene.add(road);

    // Soft ditch west of road (shoulders / dressing band) — gaps so hubs stay walkable
    const ditchMat = new THREE.MeshStandardMaterial({
      color: 0x3a4238,
      roughness: 0.9,
      metalness: 0.05,
    });
    for (const [z0, z1] of [
      [-48, -38],
      [-30, -18],
      [-10, 2],
      [10, 28],
      [34, 46],
    ] as Array<[number, number]>) {
      const len = z1 - z0;
      const ditch = new THREE.Mesh(new THREE.BoxGeometry(1.0, 0.08, len), ditchMat);
      ditch.position.set(-3.4, -0.02, (z0 + z1) / 2);
      ditch.receiveShadow = true;
      ditch.name = 'ditch';
      this.scene.add(ditch);
      this.addAABB(-4.0, -2.8, z0 + 0.2, z1 - 0.2);
    }

    // Hub shells |x| ≥ 4 (world meters) — Fontfroide / parish / goldsmith / Narbonne pockets
    const places: Array<[number, number, number, number, number, string]> = [
      // Fontfroide cloister west (−6, +38)
      [-8.5, 40, 3.2, 2.8, 0x6a6860, 'temp-building-fontfroide'],
      [-9.2, 36, 2.6, 2.4, 0x5e5c54, 'temp-building-fontfroide'],
      [-7.0, 42, 2.2, 2.0, 0x626058, 'temp-building-fontfroide'],
      // Mile marker shoulders
      [5.5, 24, 1.6, 1.4, 0x5a5048, 'temp-building'],
      [-5.8, 20, 1.5, 1.3, 0x4a443c, 'temp-building'],
      // Ambush scrub
      [5.2, 10, 1.4, 1.2, 0x585048, 'temp-building'],
      [-5.5, 6, 1.5, 1.1, 0x4a4438, 'temp-building'],
      // Parish east (+7, −2)
      [9.5, -1.5, 3.0, 2.6, 0x5a5048, 'temp-building-parish'],
      [10.2, -4.0, 2.2, 2.0, 0x4a443c, 'temp-building-parish'],
      // Goldsmith west (−7, −14)
      [-9.0, -13, 2.8, 2.4, 0x5a5848, 'temp-building-goldsmith'],
      [-9.5, -16, 2.0, 1.8, 0x4a4840, 'temp-building-goldsmith'],
      // Ferry approach scrub
      [5.0, -28, 1.6, 1.2, 0x4a4438, 'temp-building'],
      [-5.2, -30, 1.5, 1.1, 0x585048, 'temp-building'],
      // Narbonne pocket (+5, −44)
      [9.0, -44, 3.0, 2.5, 0x4a4850, 'temp-building-narbonne'],
      [8.2, -41, 2.2, 2.0, 0x3a3838, 'temp-building-narbonne'],
      [10.0, -47, 2.0, 1.8, 0x454038, 'temp-building-narbonne'],
      // Corbières turnoff spur west
      [-7.5, -28, 1.8, 1.4, 0x4a4030, 'temp-building'],
    ];
    for (const [wx, wz, w, h, col, name] of places) {
      const b = new THREE.Mesh(
        new THREE.BoxGeometry(w, h, w * 0.75),
        new THREE.MeshStandardMaterial({ color: col, roughness: 0.9 })
      );
      b.position.set(wx, h / 2, wz);
      b.castShadow = true;
      b.receiveShadow = true;
      b.name = name;
      this.scene.add(b);
      this.addBoxCollider(wx, wz, w * 0.45, w * 0.75 * 0.45);
    }

    // Soft playable bounds (thin walls)
    this.addAABB(-HALF_X - 0.4, HALF_X + 0.4, -HALF_Z - 0.6, -HALF_Z + 0.35);
    this.addAABB(-HALF_X - 0.4, HALF_X + 0.4, HALF_Z - 0.35, HALF_Z + 0.6);
    this.addAABB(-HALF_X - 0.6, -HALF_X + 0.35, -HALF_Z, HALF_Z);
    this.addAABB(HALF_X - 0.35, HALF_X + 0.6, -HALF_Z, HALF_Z);

    this.scatterSimpleRocks([
      [-4.5, 35, 0.55, 0.35],
      [4.2, 30, 0.5, 0.3],
      [-4.8, 12, 0.45, 0.28],
      [4.6, 4, 0.5, 0.3],
      [-4.4, -8, 0.48, 0.28],
      [4.8, -20, 0.52, 0.32],
      [-5.0, -36, 0.55, 0.34],
      [4.4, -42, 0.5, 0.3],
      [3.8, 22, 0.4, 0.22],
      [-3.9, -14, 0.42, 0.24],
    ]);

    const labelCanvas = document.createElement('canvas');
    labelCanvas.width = 640;
    labelCanvas.height = 64;
    const ctx = labelCanvas.getContext('2d')!;
    ctx.fillStyle = 'rgba(40,36,30,0.55)';
    ctx.fillRect(0, 0, 640, 64);
    ctx.fillStyle = '#c8c0b0';
    ctx.font = '26px Georgia, serif';
    ctx.fillText('Fontfroide → Narbonne  ·  contiguous outdoor  [ACT I]', 16, 42);
    const tex = new THREE.CanvasTexture(labelCanvas);
    const label = new THREE.Mesh(
      new THREE.PlaneGeometry(10, 0.9),
      new THREE.MeshBasicMaterial({ map: tex, transparent: true, depthWrite: false })
    );
    label.position.set(0, 0.05, 48);
    label.rotation.x = -Math.PI / 2;
    label.name = 'art-label';
    this.scene.add(label);

    const grid = new THREE.GridHelper(HALF_Z * 2, 40, 0x4a4438, 0x4a4438);
    grid.position.y = 0.01;
    grid.scale.set(HALF_X / HALF_Z, 1, 1);
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.12;
    this.scene.add(grid);
  }

  /** Act II scaffold — Corbières priory road (placeholder geometry). */
  private buildCorbieresHub(): void {
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x3e4038,
      roughness: 0.98,
      metalness: 0.01,
    });
    const geo = new THREE.PlaneGeometry(GRID * TILE, GRID * TILE);
    geo.rotateX(-Math.PI / 2);
    this.ground = new THREE.Mesh(geo, groundMat);
    this.ground.receiveShadow = true;
    this.ground.name = 'ground';
    this.scene.add(this.ground);

    const road = new THREE.Mesh(
      new THREE.BoxGeometry(1.8, 0.04, GRID * TILE),
      new THREE.MeshStandardMaterial({ color: 0x322e28, roughness: 0.99 })
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
      [-4.6, 0.6, 1.1, 0.9],
      [4.5, 0.8, 1.2, 1.0],
      [-2.8, 4.4, 1.0, 0.8],
      [2.6, 4.2, 1.1, 0.85],
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
      // South facade stubs near priory_door — stripped when Art priory shell ships
      b.name = gz <= -4.0 ? 'temp-building-priory' : 'temp-building';
      this.scene.add(b);
      this.addBoxCollider(px, pz, w * 0.45, w * 0.8 * 0.45);
    }

    this.scatterSimpleRocks([
      [-5.62, -3.89, 0.45, 0.25],
      [5.4, -3.67, 0.5, 0.28],
      [-5.4, 2.38, 0.4, 0.22],
      [5.51, 3.24, 0.48, 0.26],
      [-4.75, -0.43, 0.42, 0.24],
      [4.97, -0.22, 0.46, 0.26],
      [-1.73, 5.18, 0.38, 0.2],
      [1.51, 4.97, 0.4, 0.22],
      [-5.83, -5.18, 0.5, 0.28],
      [5.72, 1.94, 0.44, 0.24],
    ]);

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
      color: 0x484640,
      roughness: 0.98,
      metalness: 0.01,
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

    // Edge clutter — leave center square + approaches clear
    this.scatterSimpleRocks([
      [-4.32, 3.02, 0.55, 0.3],
      [4.54, 2.59, 0.6, 0.32],
      [-4.75, -3.46, 0.5, 0.28],
      [4.32, -3.89, 0.55, 0.3],
      [-3.46, 4.54, 0.7, 0.35],
      [3.67, 4.32, 0.65, 0.34],
      [-5.18, 0.22, 0.48, 0.26],
      [4.97, -0.65, 0.5, 0.28],
      [-1.94, 4.97, 0.42, 0.24],
      [1.73, 4.86, 0.44, 0.25],
    ]);
    const stump = new THREE.Mesh(
      new THREE.CylinderGeometry(0.28, 0.35, 0.35, 8),
      new THREE.MeshStandardMaterial({ color: 0x3a342c, roughness: 0.95 })
    );
    stump.position.set(-3.6 * TILE, 0.18, 0.8 * TILE);
    stump.castShadow = true;
    stump.name = 'env-stump';
    this.scene.add(stump);
    this.addCircleCollider(-3.6 * TILE, 0.8 * TILE, 0.3);
    const fencePost = new THREE.Mesh(
      new THREE.BoxGeometry(0.12, 1.1, 0.12),
      new THREE.MeshStandardMaterial({ color: 0x3a3830, roughness: 0.92 })
    );
    for (const [gx, gz] of [
      [3.8, -0.4],
      [3.8, 0.4],
      [3.8, 1.2],
    ] as const) {
      const p = fencePost.clone();
      p.position.set(gx * TILE, 0.55, gz * TILE);
      p.castShadow = true;
      p.name = 'env-fence-post';
      this.scene.add(p);
      this.addCircleCollider(gx * TILE, gz * TILE, 0.14);
    }

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

  /** After polish collider wipe — restore env rock/stump/post blockers. */
  private rebindEnvPropColliders(): void {
    this.scene.traverse((o) => {
      if (o.name === 'env-rock') {
        this.addCircleCollider(o.position.x, o.position.z, 0.28);
      } else if (o.name === 'env-stump') {
        this.addCircleCollider(o.position.x, o.position.z, 0.3);
      } else if (o.name === 'env-fence-post') {
        this.addCircleCollider(o.position.x, o.position.z, 0.14);
      }
    });
  }

  /** Low rocks / mud clumps at map edges — colliders small, road kept clear. */
  private scatterSimpleRocks(spots: Array<[number, number, number, number]>): void {
    for (const [gx, gz, w, h] of spots) {
      const mat = new THREE.MeshStandardMaterial({
        color: 0x4a4640,
        roughness: 0.96,
        metalness: 0.02,
      });
      const rock = new THREE.Mesh(new THREE.DodecahedronGeometry(w * 0.55, 0), mat);
      // Spots are world meters (Act I outdoor + stub hubs)
      const px = gx;
      const pz = gz;
      rock.position.set(px, h * 0.35, pz);
      rock.scale.set(1, 0.55 + h * 0.35, 0.85);
      rock.rotation.set(0.2, gx + gz, 0.15);
      rock.castShadow = true;
      rock.receiveShadow = true;
      rock.name = 'env-rock';
      this.scene.add(rock);
      this.addCircleCollider(px, pz, Math.max(0.22, w * 0.35));
    }
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
      await this.tryHookBuildingShells();
      await this.tryScatterZoneDressing();
      this.updateCamera();
      return;
    }
    const urls = [
      PATH.player,
      PATH.cellarer,
      PATH.mairia,
      PATH.ramon,
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
    await this.upgradeNpc('parish', take('ramon'), 1.72, 0x5a5848);
    // Art hooks — use GLBs when present; keep placeholders if missing
    const banditA = await loadModel(PATH.badgeBandit);
    const banditB = await loadModel(PATH.badgeBanditB);
    if (banditA) {
      await this.upgradeNpc('bandits', banditA, 1.7, 0x3a3028, 0.1);
      // Second ambush figure when Art ships badge_bandit_b
      if (banditB) {
        const side = banditB;
        fitToHeight(side, 1.68);
        tintMeshes(side, 0x3a3028, 0.1);
        const bandits = this.activeNpcs.find((n) => n.id === 'bandits');
        const bx = (bandits?.x ?? 3.2) * TILE;
        const bz = (bandits?.z ?? -3.8) * TILE;
        side.position.set(bx + 0.55, 0, bz - 0.45);
        side.rotation.y = Math.PI * 0.35;
        side.name = 'badge-bandit-b-art';
        this.scene.add(side);
      }
    }
    const ferryArt = await loadModel(PATH.ferryRope);
    if (ferryArt) {
      await this.upgradeNpc('ferry', ferryArt, 1.4, 0x4a4030, 0.15);
    }
    // Prefer shipped agent; fall back to upcoming courier Art names
    const narbonneArt =
      (await loadModel(PATH.narbonneAgent)) ??
      (await loadModel(PATH.narbonneCourier)) ??
      (await loadModel(PATH.hoodedCourier));
    if (narbonneArt) {
      await this.upgradeNpc('narbonne', narbonneArt, 1.72, 0x3a4858, 0.12);
    }

    this.colliders = [];
    // Re-seed ditch gaps + soft bounds (Act I contiguous)
    if (this.zone === 'act1_road') {
      for (const [z0, z1] of [
        [-48, -38],
        [-30, -18],
        [-10, 2],
        [10, 28],
        [34, 46],
      ] as Array<[number, number]>) {
        this.addAABB(-4.0, -2.8, z0 + 0.2, z1 - 0.2);
      }
      this.addAABB(-HALF_X - 0.4, HALF_X + 0.4, -HALF_Z - 0.6, -HALF_Z + 0.35);
      this.addAABB(-HALF_X - 0.4, HALF_X + 0.4, HALF_Z - 0.35, HALF_Z + 0.6);
      this.addAABB(-HALF_X - 0.6, -HALF_X + 0.35, -HALF_Z, HALF_Z);
      this.addAABB(HALF_X - 0.35, HALF_X + 0.6, -HALF_Z, HALF_Z);
    } else {
      this.addAABB(-4.2, -3.0, -GRID * TILE * 0.45, -0.9);
      this.addAABB(-4.2, -3.0, 0.9, GRID * TILE * 0.45);
    }
    for (const n of this.activeNpcs) {
      this.addCircleCollider(
        n.x * TILE,
        n.z * TILE,
        n.id === 'ferry' || n.id === 'priory_door' ? 0.55 : 0.3
      );
    }

    // Parish porch + burial gate (Art drops) — after collider reset
    await this.tryHookParishProps();
    this.rebindEnvPropColliders();

    this.removeNamed('temp-building');
    this.removeNamed('temp-building-fontfroide');
    this.removeNamed('temp-building-parish');
    this.removeNamed('temp-building-goldsmith');
    this.removeNamed('temp-building-narbonne');
    this.removeNamed('temp-arch');

    // Hub shells along contiguous Act I (world meters; |x|≥4)
    this.placeBuilding(-8.5, 40, take, 'stone', 'kenney-building-west');
    this.placeBuilding(-9.0, 36, take, 'stone', 'kenney-building-west');
    this.placeBuilding(-7.5, 42, take, 'wood', 'kenney-building-west');
    this.placeBuilding(9.5, -1.5, take, 'wood', 'kenney-building-parish');
    this.placeBuilding(-9.0, -13, take, 'wood', 'kenney-building-goldsmith');
    this.placeBuilding(9.0, -44, take, 'wood', 'kenney-building-narbonne');
    this.placeBuilding(5.5, 24, take, 'wood');
    this.placeBuilding(-5.8, 20, take, 'wood');

    const pillarL = take('pillar');
    const pillarR = take('pillar');
    if (pillarL && pillarR) {
      fitToHeight(pillarL, 2.0);
      fitToHeight(pillarR, 2.0);
      tintMeshes(pillarL, 0x6a6860, 0.25);
      tintMeshes(pillarR, 0x6a6860, 0.25);
      // Parish approach posts (east of road, near Ramon)
      pillarL.position.set(5.2, 0, -0.5);
      pillarR.position.set(6.8, 0, -0.5);
      this.scene.add(pillarL, pillarR);
      this.addBoxCollider(5.2, -0.5, 0.3, 0.3);
      this.addBoxCollider(6.8, -0.5, 0.3, 0.3);
    } else {
      const postMat = new THREE.MeshStandardMaterial({ color: 0x686860, roughness: 0.88 });
      const aL = new THREE.Mesh(new THREE.BoxGeometry(0.4, 2.0, 0.4), postMat);
      const aR = aL.clone();
      aL.position.set(5.2, 1.0, -0.5);
      aR.position.set(6.8, 1.0, -0.5);
      this.scene.add(aL, aR);
      this.addBoxCollider(5.2, -0.5, 0.28, 0.28);
      this.addBoxCollider(6.8, -0.5, 0.28, 0.28);
    }

    for (const [x, z] of [
      [-2.4, 36],
      [3.6, 20],
      [-2.6, 6],
      [3.5, -14],
      [-2.5, -30],
      [3.4, -42],
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
      // Extra barren trees at corners — densify without blocking road
      for (const [x, z, h] of [
        [-5.2, 5.0, 2.0],
        [5.4, -4.6, 1.9],
        [-4.8, -1.2, 1.7],
      ] as const) {
        const t = pine.clone(true);
        fitToHeight(t, h);
        t.position.set(x, 0, z);
        this.scene.add(t);
        this.addCircleCollider(x, z, 0.32);
      }
    }

    // Extra fence runs along east scrub (leave alley between pillars open)
    if (fence) {
      const fence3 = fence.clone(true);
      fence3.position.set(5.2 * TILE, 0, -2.2 * TILE);
      fence3.rotation.y = Math.PI / 2;
      this.scene.add(fence3);
      this.addBoxCollider(5.2 * TILE, -2.2 * TILE, 0.12, 0.7);
      const fence4 = fence.clone(true);
      fence4.position.set(5.2 * TILE, 0, 0.6 * TILE);
      fence4.rotation.y = Math.PI / 2;
      this.scene.add(fence4);
      this.addBoxCollider(5.2 * TILE, 0.6 * TILE, 0.12, 0.7);
    }

    // Building shells after Kenney composites so Art can strip tagged interim boxes
    await this.tryHookBuildingShells();
    this.rebindEnvPropColliders();

    this.updateCamera();
  }

  private placeBuilding(
    x: number,
    z: number,
    take: (k: keyof typeof PATH) => THREE.Group | null,
    kind: 'stone' | 'wood',
    tag = 'kenney-building'
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
      b.name = tag;
      this.scene.add(b);
      this.addBoxCollider(x, z, 0.8, 0.7);
      return;
    }

    const g = new THREE.Group();
    g.name = tag;
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


  /** Non-blocking: densify Corbières / Act III with Kenney + Art road dressing. */
  private async tryScatterZoneDressing(): Promise<void> {
    const pine = await loadModel(PATH.pine);
    // Prefer Art fence run; fall back to Kenney iron fence
    const fenceArt = await loadModel(PATH.roadFenceRun);
    const fence = fenceArt ?? (await loadModel(PATH.fence));
    const mile = await loadModel(PATH.mileMarker);
    const cartArt = await loadModel(PATH.roadCart);
    const cart = cartArt ?? (await loadModel(PATH.cart));
    const mud = await loadModel(PATH.mudRutPatch);
    const bundle = await loadModel(PATH.pilgrimBundle);
    const cross = await loadModel(PATH.waysideCross);
    const barrel = await loadModel(PATH.barrel);
    const crate = await loadModel(PATH.crate);
    const bench = await loadModel(PATH.bench);
    const pillar = await loadModel(PATH.borderPillar);
    const light = await loadModel(PATH.lightpost);

    const placeFence = (
      proto: THREE.Group,
      x: number,
      z: number,
      rot: number,
      withCollider: boolean
    ) => {
      const f = proto.clone(true);
      f.position.set(x, 0, z);
      f.rotation.y = rot;
      f.name = 'env-fence';
      this.scene.add(f);
      // GD: cart/fence colliders stay OFF the walk lane (protect ~0.9m follower trail)
      if (withCollider) {
        this.addBoxCollider(x, z, rot === 0 ? 0.7 : 0.12, rot === 0 ? 0.12 : 0.7);
      }
    };

    if (this.zone === 'corbieres') {
      if (pine) {
        for (const [x, z, h] of [
          [-5.4, -4.6, 2.2],
          [5.3, -4.4, 2.0],
          [-5.5, 4.6, 1.9],
          [5.4, 4.5, 2.1],
          [-5.6, 1.0, 1.7],
          [5.5, 2.2, 1.8],
          [-5.3, -1.8, 1.85],
        ] as const) {
          const t = pine.clone(true);
          fitToHeight(t, h);
          tintMeshes(t, 0x3a4038, 0.2);
          t.position.set(x, 0, z);
          t.name = 'env-pine';
          this.scene.add(t);
          this.addCircleCollider(x, z, 0.32);
        }
      }
      if (fence) {
        fitToHeight(fence, fenceArt ? 1.15 : 1.0);
        tintMeshes(fence, 0x3a3830, 0.3);
        // Edge runs only — leave center road (±~1.0) + approaches clear
        for (const [x, z, rot] of [
          [-4.8, 5.0, 0],
          [-2.6, 5.0, 0],
          [2.8, 5.0, 0],
          [4.6, 5.0, 0],
          [5.0, -1.0, Math.PI / 2],
          [5.0, 1.4, Math.PI / 2],
          [-5.1, -2.4, Math.PI / 2],
          [-5.1, 2.8, Math.PI / 2],
        ] as const) {
          placeFence(fence, x, z, rot, true);
        }
      }
      // Repeated mile markers / wayside crosses — roadside, not in lane
      if (mile) {
        fitToHeight(mile, 1.15);
        tintMeshes(mile, 0x6a6860, 0.12);
        for (const [x, z] of [
          [-1.55, -4.2],
          [1.6, -1.2],
          [-1.6, 1.8],
          [1.55, 4.0],
        ] as const) {
          const m = mile.clone(true);
          m.position.set(x, 0, z);
          m.name = 'mile-marker-art';
          this.scene.add(m);
          this.addCircleCollider(x, z, 0.22);
        }
      }
      if (cross) {
        fitToHeight(cross, 1.6);
        tintMeshes(cross, 0x5a5848, 0.12);
        cross.position.set(1.7, 0, -3.6);
        cross.name = 'wayside-cross-art';
        this.scene.add(cross);
        this.addCircleCollider(1.7, -3.6, 0.22);
      }
      // Cart OFF walk lane (east scrub)
      if (cart) {
        fitToHeight(cart, 0.9);
        tintMeshes(cart, 0x4a4034, 0.2);
        cart.position.set(3.6, 0, 2.4);
        cart.rotation.y = -0.55;
        cart.name = 'road-cart-art';
        this.scene.add(cart);
        this.addBoxCollider(3.6, 2.4, 0.65, 0.4);
      }
      // Visual-only Art dressing (no colliders per GD)
      if (mud) {
        fitToHeight(mud, 0.08);
        tintMeshes(mud, 0x3a342c, 0.15);
        for (const [x, z, rot] of [
          [0.15, -2.8, 0.1],
          [-0.1, 0.6, -0.2],
          [0.2, 2.4, 0.05],
        ] as const) {
          const p = mud.clone(true);
          p.position.set(x, 0.01, z);
          p.rotation.y = rot;
          p.name = 'mud-rut-art';
          this.scene.add(p);
        }
      }
      if (bundle) {
        fitToHeight(bundle, 0.55);
        tintMeshes(bundle, 0x5a4838, 0.12);
        for (const [x, z] of [
          [-3.4, -0.8],
          [3.2, -2.6],
          [-3.6, 3.0],
        ] as const) {
          const b = bundle.clone(true);
          b.position.set(x, 0, z);
          b.name = 'pilgrim-bundle-art';
          this.scene.add(b);
        }
      }
      if (barrel) {
        for (const [x, z] of [
          [-3.8, 1.6],
          [3.4, 0.2],
          [3.8, -3.0],
        ] as const) {
          const b = barrel.clone(true);
          fitToHeight(b, 0.45);
          tintMeshes(b, 0x5a4838, 0.2);
          b.position.set(x, 0, z);
          b.name = 'env-barrel';
          this.scene.add(b);
          this.addCircleCollider(x, z, 0.26);
        }
      }
      if (crate) {
        fitToHeight(crate, 0.4);
        tintMeshes(crate, 0x5a4838, 0.15);
        crate.position.set(3.9, 0, 1.6);
        crate.name = 'env-crate';
        this.scene.add(crate);
        this.addBoxCollider(3.9, 1.6, 0.28, 0.28);
      }
      if (bench) {
        fitToHeight(bench, 0.45);
        tintMeshes(bench, 0x4a4034, 0.15);
        bench.position.set(-3.2, 0, 2.2);
        bench.rotation.y = 0.35;
        bench.name = 'env-bench';
        this.scene.add(bench);
        this.addBoxCollider(-3.2, 2.2, 0.5, 0.22);
      }
      if (pillar) {
        fitToHeight(pillar, 1.5);
        tintMeshes(pillar, 0x5a5848, 0.2);
        for (const [x, z] of [
          [-4.2, -4.0],
          [4.2, -3.8],
        ] as const) {
          const p = pillar.clone(true);
          p.position.set(x, 0, z);
          p.name = 'env-border-pillar';
          this.scene.add(p);
          this.addCircleCollider(x, z, 0.28);
        }
      }
      if (light) {
        fitToHeight(light, 2.0);
        tintMeshes(light, 0x4a4838, 0.2);
        for (const [x, z] of [
          [-3.0, -4.4],
          [3.2, 3.6],
        ] as const) {
          const p = light.clone(true);
          p.position.set(x, 0, z);
          p.name = 'env-lightpost';
          this.scene.add(p);
          this.addCircleCollider(x, z, 0.18);
          this.addLanternLight(x, 1.6, z, 0.45);
        }
      }
    }

    if (this.zone === 'act3_close') {
      if (pine) {
        for (const [x, z, h] of [
          [-5.2, -4.2, 2.0],
          [5.1, -4.0, 1.85],
          [-5.0, 4.6, 1.9],
          [5.2, 4.4, 2.05],
          [-5.3, 1.2, 1.75],
          [5.3, -1.2, 1.8],
        ] as const) {
          const t = pine.clone(true);
          fitToHeight(t, h);
          tintMeshes(t, 0x3a4038, 0.22);
          t.position.set(x, 0, z);
          t.name = 'env-pine';
          this.scene.add(t);
          this.addCircleCollider(x, z, 0.32);
        }
      }
      if (fence) {
        fitToHeight(fence, fenceArt ? 1.15 : 1.0);
        tintMeshes(fence, 0x3a3830, 0.3);
        for (const [x, z, rot] of [
          [-4.6, -4.8, 0],
          [-2.4, -4.8, 0],
          [2.6, -4.8, 0],
          [4.8, 1.6, Math.PI / 2],
          [4.8, 3.2, Math.PI / 2],
          [-4.8, 2.0, Math.PI / 2],
        ] as const) {
          placeFence(fence, x, z, rot, true);
        }
      }
      if (mile) {
        fitToHeight(mile, 1.1);
        tintMeshes(mile, 0x6a6860, 0.12);
        for (const [x, z] of [
          [-1.7, 2.8],
          [1.8, 2.6],
          [-3.6, 3.4],
        ] as const) {
          const m = mile.clone(true);
          m.position.set(x, 0, z);
          m.name = 'mile-marker-art';
          this.scene.add(m);
          this.addCircleCollider(x, z, 0.22);
        }
      }
      if (cross) {
        fitToHeight(cross, 1.55);
        tintMeshes(cross, 0x5a5848, 0.12);
        cross.position.set(3.4, 0, 2.8);
        cross.name = 'wayside-cross-art';
        this.scene.add(cross);
        this.addCircleCollider(3.4, 2.8, 0.22);
      }
      if (cart) {
        fitToHeight(cart, 0.88);
        tintMeshes(cart, 0x4a4034, 0.2);
        cart.position.set(-3.8, 0, 2.6);
        cart.rotation.y = 0.7;
        cart.name = 'road-cart-art';
        this.scene.add(cart);
        this.addBoxCollider(-3.8, 2.6, 0.65, 0.4);
      }
      if (mud) {
        fitToHeight(mud, 0.08);
        tintMeshes(mud, 0x3a342c, 0.15);
        for (const [x, z, rot] of [
          [0.0, 0.4, 0.12],
          [0.3, -0.8, -0.15],
        ] as const) {
          const p = mud.clone(true);
          p.position.set(x, 0.01, z);
          p.rotation.y = rot;
          p.name = 'mud-rut-art';
          this.scene.add(p);
        }
      }
      if (bundle) {
        fitToHeight(bundle, 0.55);
        tintMeshes(bundle, 0x5a4838, 0.12);
        for (const [x, z] of [
          [-3.4, -3.0],
          [3.6, 0.6],
        ] as const) {
          const b = bundle.clone(true);
          b.position.set(x, 0, z);
          b.name = 'pilgrim-bundle-art';
          this.scene.add(b);
        }
      }
      if (barrel) {
        for (const [x, z] of [
          [-3.8, -0.4],
          [3.6, -3.2],
        ] as const) {
          const b = barrel.clone(true);
          fitToHeight(b, 0.45);
          tintMeshes(b, 0x5a4838, 0.2);
          b.position.set(x, 0, z);
          b.name = 'env-barrel';
          this.scene.add(b);
          this.addCircleCollider(x, z, 0.26);
        }
      }
      if (bench) {
        fitToHeight(bench, 0.45);
        tintMeshes(bench, 0x4a4034, 0.15);
        bench.position.set(3.2, 0, -0.8);
        bench.rotation.y = -0.4;
        bench.name = 'env-bench';
        this.scene.add(bench);
        this.addBoxCollider(3.2, -0.8, 0.5, 0.22);
      }
      if (light) {
        fitToHeight(light, 2.0);
        tintMeshes(light, 0x4a4838, 0.2);
        const p = light.clone(true);
        p.position.set(-3.4, 0, 3.2);
        p.name = 'env-lightpost';
        this.scene.add(p);
        this.addCircleCollider(-3.4, 3.2, 0.18);
        this.addLanternLight(-3.4, 1.6, 3.2, 0.45);
      }
    }
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

    // Mile marker — Fontfroide–Narbonne road set dressing (near ambush scrub)
    const bandits = this.activeNpcs.find((n) => n.id === 'bandits');
    const bx = (bandits?.x ?? 3.2) * TILE;
    const bz = (bandits?.z ?? -3.8) * TILE;
    const mile = await loadModel(PATH.mileMarker);
    if (mile) {
      fitToHeight(mile, 1.2);
      tintMeshes(mile, 0x6a6860, 0.12);
      mile.position.set(bx - 1.1, 0, bz + 0.8);
      mile.name = 'mile-marker-art';
      this.scene.add(mile);
      this.addBoxCollider(bx - 1.1, bz + 0.8, 0.35, 0.35);
    }

    // Goldsmith mold cavity — beside viscount’s rider / mold beat
    const moldNpc = this.activeNpcs.find((n) => n.id === 'mold');
    const mx = (moldNpc?.x ?? -2.0) * TILE;
    const mz = (moldNpc?.z ?? -3.5) * TILE;
    const cavity = await loadModel(PATH.moldCavity);
    if (cavity) {
      fitToHeight(cavity, 0.85);
      tintMeshes(cavity, 0x4a4030, 0.12);
      cavity.position.set(mx + 0.55, 0, mz - 0.35);
      cavity.name = 'mold-cavity-art';
      this.scene.add(cavity);
      this.addBoxCollider(mx + 0.55, mz - 0.35, 0.55, 0.45);
    }

    // Fontfroide cloister bay + yard well (Art drops) — west abbey near cellarer
    const cellarer = this.activeNpcs.find((n) => n.id === 'cellarer');
    const cx = (cellarer?.x ?? -3.2) * TILE;
    const cz = (cellarer?.z ?? -1.2) * TILE;
    const arcade = await loadModel(PATH.cloisterArcade);
    if (arcade) {
      fitToHeight(arcade, 3.2);
      tintMeshes(arcade, 0x6a6860, 0.1);
      // Backdrop along west abbey wall; keep ditch gap clear
      arcade.position.set(cx - 0.95, 0, cz - 1.35);
      arcade.rotation.y = Math.PI * 0.08;
      arcade.name = 'cloister-arcade-art';
      this.scene.add(arcade);
      this.addBoxCollider(cx - 0.95, cz - 1.35, 1.35, 0.85);
    }
    const arcadeB = await loadModel(PATH.cloisterArcadeB);
    if (arcadeB) {
      fitToHeight(arcadeB, 3.0);
      tintMeshes(arcadeB, 0x626058, 0.1);
      arcadeB.position.set(cx - 1.1, 0, cz + 2.4);
      arcadeB.rotation.y = Math.PI * 0.1;
      arcadeB.name = 'cloister-arcade-b-art';
      this.scene.add(arcadeB);
      this.addBoxCollider(cx - 1.1, cz + 2.4, 1.2, 0.8);
    }
    const well = await loadModel(PATH.cloisterWell);
    if (well) {
      fitToHeight(well, 1.5);
      tintMeshes(well, 0x5a5848, 0.12);
      well.position.set(cx + 1.05, 0, cz + 0.95);
      well.name = 'cloister-well-art';
      this.scene.add(well);
      this.addBoxCollider(cx + 1.05, cz + 0.95, 0.7, 0.7);
    }

    // Art road dressing pre-hooks (Act I) — cart/fence OFF walk lane; mud/bundle visual-only
    await this.tryHookRoadDressingArt();
  }

  /**
   * Non-blocking building shells — Art exact names under props/.
   * GD: doorways ≥1.2 m clear; wall colliders tight (no fat AABB into walk lane);
   * replace Kenney/box when present. Rest/combat untouched.
   */
  private async tryHookBuildingShells(): Promise<void> {
    const placeVisual = (
      model: THREE.Group,
      name: string,
      x: number,
      z: number,
      h: number,
      rot: number
    ) => {
      fitToHeight(model, h);
      tintMeshes(model, 0x5a5848, 0.1);
      model.position.set(x, 0, z);
      model.rotation.y = rot;
      model.name = name;
      this.scene.add(model);
    };

    /** Wall strips only — leave ≥1.2 m doorway gap on the open face (local -Z). */
    const placeWallColliders = (
      x: number,
      z: number,
      halfW: number,
      halfD: number,
      wall = 0.28,
      doorGap = 1.25
    ) => {
      const pier = Math.max(0.35, (halfW * 2 - doorGap) * 0.5);
      // Front piers (doorway between)
      this.addBoxCollider(x - (halfW - pier * 0.5), z - halfD + wall * 0.5, pier * 0.5, wall * 0.5);
      this.addBoxCollider(x + (halfW - pier * 0.5), z - halfD + wall * 0.5, pier * 0.5, wall * 0.5);
      // Back wall
      this.addBoxCollider(x, z + halfD - wall * 0.5, halfW, wall * 0.5);
      // Side walls
      this.addBoxCollider(x - halfW + wall * 0.5, z, wall * 0.5, halfD - wall);
      this.addBoxCollider(x + halfW - wall * 0.5, z, wall * 0.5, halfD - wall);
    };

    if (this.zone === 'act1_road') {
      const cellarer = this.activeNpcs.find((n) => n.id === 'cellarer');
      const cx = (cellarer?.x ?? -3.2) * TILE;
      const cz = (cellarer?.z ?? -1.2) * TILE;
      // West of ditch / walk lane — Fontfroide dormer bay
      const dormer = await loadModel(PATH.fontfroideDormer);
      if (dormer) {
        this.removeNamed('kenney-building-west');
        const x = cx - 1.55;
        const z = cz - 0.35;
        placeVisual(dormer, 'fontfroide-dormer-art', x, z, 3.5, Math.PI * 0.06);
        placeWallColliders(x, z, 1.35, 1.05);
      }

      const parish = this.activeNpcs.find((n) => n.id === 'parish');
      const px = (parish?.x ?? 0.8) * TILE;
      const pz = (parish?.z ?? -2.6) * TILE;
      const nave = await loadModel(PATH.parishNaveShell);
      if (nave) {
        this.removeNamed('kenney-building-parish');
        // Behind porch; road strip stays clear for two-abreast + followers
        const x = px + 0.2;
        const z = pz - 1.85;
        placeVisual(nave, 'parish-nave-shell-art', x, z, 4.0, Math.PI * 0.08);
        placeWallColliders(x, z, 1.7, 1.15, 0.3, 1.3);
      }

      const mold = this.activeNpcs.find((n) => n.id === 'mold');
      const mx = (mold?.x ?? 3.5) * TILE;
      const mz = (mold?.z ?? 0.8) * TILE;
      const shop = await loadModel(PATH.goldsmithShopShell);
      if (shop) {
        const x = mx + 0.9;
        const z = mz + 0.2;
        placeVisual(shop, 'goldsmith-shop-shell-art', x, z, 2.8, -0.2);
        placeWallColliders(x, z, 1.1, 0.95, 0.26, 1.2);
      }

      // East roadside house — off walk lane
      const house = await loadModel(PATH.roadHouseShell);
      if (house) {
        const x = 5.8;
        const z = 8.0;
        placeVisual(house, 'road-house-shell-art', x, z, 2.9, -Math.PI * 0.5);
        placeWallColliders(x, z, 1.05, 0.95, 0.26, 1.2);
      }
    }

    if (this.zone === 'corbieres') {
      const door = this.activeNpcs.find((n) => n.id === 'priory_door');
      const dx = (door?.x ?? -2.2) * TILE;
      const dz = (door?.z ?? -3.5) * TILE;

      const nave = await loadModel(PATH.prioryNaveShell);
      if (nave) {
        this.removeNamed('temp-building-priory');
        const x = dx - 0.15;
        const z = dz - 1.25;
        placeVisual(nave, 'priory-nave-shell-art', x, z, 3.6, Math.PI * 0.04);
        placeWallColliders(x, z, 1.55, 1.2, 0.28, 1.3);
      }

      const ruin = await loadModel(PATH.prioryRuinWall);
      if (ruin) {
        // Flank wall — tight strip, leave approach to door ≥1.2 m
        const x = dx + 2.4;
        const z = dz - 0.6;
        placeVisual(ruin, 'priory-ruin-wall-art', x, z, 2.8, Math.PI * 0.5);
        this.addBoxCollider(x, z, 0.22, 1.1);
      }
    }
  }

  /** Non-blocking Art road props — exact names under props/; GD collision rules. */
  private async tryHookRoadDressingArt(): Promise<void> {
  
    if (this.zone !== 'act1_road') return;

    const cart = (await loadModel(PATH.roadCart)) ?? (await loadModel(PATH.cart));
    if (cart) {
      fitToHeight(cart, 0.9);
      tintMeshes(cart, 0x4a4034, 0.2);
      // Shoulders only — |x| 1.2–4; keep crown clear for follower trail
      for (const [x, z, rot] of [
        [3.2, 19.5, -0.35],
        [3.4, -8.0, 0.2],
        [-3.3, -24.0, 0.4],
      ] as const) {
        const c = cart.clone(true);
        c.position.set(x, 0, z);
        c.rotation.y = rot;
        c.name = 'road-cart-art';
        this.scene.add(c);
        this.addBoxCollider(x, z, 0.65, 0.4);
      }
    }

    const fenceRun = (await loadModel(PATH.roadFenceRun)) ?? (await loadModel(PATH.fence));
    if (fenceRun) {
      fitToHeight(fenceRun, 1.1);
      tintMeshes(fenceRun, 0x3a3830, 0.28);
      for (const [x, z, rot] of [
        [-3.6, 34, 0],
        [3.6, 12, 0],
        [-3.6, -6, 0],
        [3.6, -22, Math.PI / 2],
        [-3.8, -40, 0],
      ] as const) {
        const f = fenceRun.clone(true);
        f.position.set(x, 0, z);
        f.rotation.y = rot;
        f.name = 'road-fence-run-art';
        this.scene.add(f);
        this.addBoxCollider(x, z, rot === 0 ? 0.7 : 0.12, rot === 0 ? 0.12 : 0.7);
      }
    }

    const mud = await loadModel(PATH.mudRutPatch);
    if (mud) {
      fitToHeight(mud, 0.08);
      tintMeshes(mud, 0x3a342c, 0.15);
      for (const [x, z, rot] of [
        [0.2, 30, 0.08],
        [0.1, 18, -0.1],
        [0.25, 6, 0.04],
        [0.15, -12, -0.08],
        [0.2, -28, 0.06],
        [0.1, -40, -0.05],
      ] as const) {
        const p = mud.clone(true);
        p.position.set(x, 0.01, z);
        p.rotation.y = rot;
        p.name = 'mud-rut-art';
        this.scene.add(p);
      }
    }

    const bundle = await loadModel(PATH.pilgrimBundle);
    if (bundle) {
      fitToHeight(bundle, 0.55);
      tintMeshes(bundle, 0x5a4838, 0.12);
      for (const [x, z] of [
        [-2.4, 22],
        [3.2, 17],
        [-2.6, -2],
      ] as const) {
        const b = bundle.clone(true);
        b.position.set(x, 0, z);
        b.name = 'pilgrim-bundle-art';
        this.scene.add(b);
      }
    }

    const cross = await loadModel(PATH.waysideCross);
    if (cross) {
      fitToHeight(cross, 1.6);
      tintMeshes(cross, 0x5a5848, 0.12);
      for (const [x, z] of [
        [-2.6, 21],
        [2.8, -15],
        [-2.4, -36],
      ] as const) {
        const c = cross.clone(true);
        c.position.set(x, 0, z);
        c.name = 'wayside-cross-art';
        this.scene.add(c);
        this.addCircleCollider(x, z, 0.22);
      }
    }

    // Mile markers along Fontfroide–Narbonne road
    const mile = await loadModel(PATH.mileMarker);
    if (mile) {
      fitToHeight(mile, 1.15);
      tintMeshes(mile, 0x6a6860, 0.12);
      for (const [x, z] of [
        [-1.55, 38],
        [1.6, 22],
        [-1.55, 8],
        [1.55, -2],
        [-1.55, -14],
        [1.6, -32],
        [-1.5, -44],
      ] as const) {
        const m = mile.clone(true);
        m.position.set(x, 0, z);
        m.name = 'mile-marker-art';
        this.scene.add(m);
        this.addCircleCollider(x, z, 0.22);
      }
    }

    const boat = await loadModel(PATH.ferryBoat);
    if (boat) {
      const ferry = this.activeNpcs.find((n) => n.id === 'ferry');
      const fx = (ferry?.x ?? 0.5) * TILE;
      const fz = (ferry?.z ?? -5.0) * TILE;
      fitToHeight(boat, 1.1);
      tintMeshes(boat, 0x4a4030, 0.12);
      boat.position.set(fx + 1.4, 0, fz - 0.2);
      boat.rotation.y = Math.PI * 0.15;
      boat.name = 'ferry-boat-art';
      this.scene.add(boat);
      this.addBoxCollider(fx + 1.4, fz - 0.2, 0.9, 0.45);
    }

    await this.tryHookOpenMapStockpile();
  }

  /** Non-blocking: ruin debris, sheds, trees, market stall — |x|≥4 / hubs; crown clear. */
  private async tryHookOpenMapStockpile(): Promise<void> {
    if (this.zone !== 'act1_road') return;

    const debris = await loadModel(PATH.ruinDebrisPile);
    if (debris) {
      fitToHeight(debris, 0.85);
      tintMeshes(debris, 0x5a5848, 0.15);
      for (const [x, z, rot] of [
        [-5.2, 36, 0.2],
        [5.4, 10, -0.3],
        [-5.5, -16, 0.4],
        [5.6, -40, 0.1],
      ] as const) {
        const d = debris.clone(true);
        d.position.set(x, 0, z);
        d.rotation.y = rot;
        d.name = 'ruin-debris-art';
        this.scene.add(d);
        this.addCircleCollider(x, z, 0.45);
      }
    }

    const shed = await loadModel(PATH.villageShed);
    if (shed) {
      fitToHeight(shed, 2.2);
      tintMeshes(shed, 0x4a4438, 0.12);
      for (const [x, z, rot] of [
        [5.8, 22, 0.15],
        [-6.2, -8, -0.2],
        [6.0, -28, 0.1],
      ] as const) {
        const s = shed.clone(true);
        s.position.set(x, 0, z);
        s.rotation.y = rot;
        s.name = 'village-shed-art';
        this.scene.add(s);
        this.addBoxCollider(x, z, 1.0, 0.85);
      }
    }

    const tree = await loadModel(PATH.oliveOrCypress);
    if (tree) {
      fitToHeight(tree, 3.4);
      tintMeshes(tree, 0x3a4038, 0.18);
      for (const [x, z] of [
        [-5.0, 42],
        [5.2, 28],
        [-5.4, 4],
        [5.5, -10],
        [-5.2, -26],
        [5.3, -46],
      ] as const) {
        const t = tree.clone(true);
        t.position.set(x, 0, z);
        t.name = 'olive-cypress-art';
        this.scene.add(t);
        this.addCircleCollider(x, z, 0.35);
      }
    }

    const stall = await loadModel(PATH.marketStall);
    if (stall) {
      fitToHeight(stall, 2.0);
      tintMeshes(stall, 0x5a4840, 0.12);
      stall.position.set(7.2, 0, -43);
      stall.rotation.y = -0.35;
      stall.name = 'market-stall-art';
      this.scene.add(stall);
      this.addBoxCollider(7.2, -43, 1.1, 0.7);
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
        mesh.rotation.y = follower.rotation.y;
        mesh.userData.jobId = j.id;
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

      // Interim remaps (not final Art): dedicated GLB → stand-in → party mesh (scale/tint)
      const npcHooks: Array<{
        id: string;
        paths: string[];
        h: number;
        tint: number;
      }> = [
        {
          id: 'berna',
          paths: [PATH.bernaArt, PATH.bernaNpc, PATH.guide],
          h: 1.65,
          tint: 0x4a5848,
        },
        {
          id: 'hugues',
          paths: [PATH.huguesArt, PATH.huguesNpc, PATH.sergeant],
          h: 1.82,
          tint: 0x3a3a48,
        },
        {
          id: 'serena',
          paths: [PATH.serenaArt, PATH.serenaNpc, PATH.convers],
          h: 1.68,
          tint: 0x5a4058,
        },
      ];
      for (const h of npcHooks) {
        let art: THREE.Group | null = null;
        for (const p of h.paths) {
          art = await loadModel(p);
          if (art) break;
        }
        if (art) await this.upgradeNpc(h.id, art, h.h, h.tint, 0.18);
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

      // Leper-house Rest cot — upgrades interact mesh; pick latch already ~1.2×
      const rest = await loadModel(PATH.leperRest);
      if (rest) {
        await this.upgradeNpc('leper', rest, 0.95, 0x5a5848, 0.1);
        const bellPost = await loadModel(PATH.leperBellPost);
        if (bellPost) {
          const bellNpc = this.activeNpcs.find((n) => n.id === 'leper_bell') ?? this.activeNpcs.find((n) => n.id === 'leper');
          const bx = (bellNpc?.x ?? -2.8) * TILE;
          const bz = (bellNpc?.z ?? -0.6) * TILE;
          fitToHeight(bellPost, 2.4);
          tintMeshes(bellPost, 0x4a4840, 0.12);
          bellPost.position.set(bx - 0.7, 0, bz + 0.5);
          bellPost.name = 'leper-bell-post-art';
          this.scene.add(bellPost);
          this.addCircleCollider(bx - 0.7, bz + 0.5, 0.28);
        }
        const leper = this.activeNpcs.find((n) => n.id === 'leper');
        const lx = (leper?.x ?? -2.0) * TILE;
        const lz = (leper?.z ?? -1.5) * TILE;
        this.addBoxCollider(lx, lz, 0.85, 0.65);
      }
    }

    await this.seedWorldInteractables();
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

  /** Shortest signed yaw delta in (-π, π]. */
  private shortestYawDelta(from: number, to: number): number {
    let d = to - from;
    while (d > Math.PI) d -= Math.PI * 2;
    while (d < -Math.PI) d += Math.PI * 2;
    return d;
  }

  /**
   * Smooth yaw: shortest-arc * (1 - exp(-rate·dt)), capped at TURN_CAP_RAD °/s feel.
   * Callers skip when stopped so last facing holds (no spin-on-arrive).
   */
  private smoothYaw(current: number, target: number, dt: number, rate = TURN_RATE): number {
    const dtClamped = Math.max(0.001, dt);
    const delta = this.shortestYawDelta(current, target);
    const expStep = delta * (1 - Math.exp(-rate * dtClamped));
    const maxStep = TURN_CAP_RAD * dtClamped;
    const step =
      Math.abs(expStep) <= maxStep ? expStep : Math.sign(expStep) * maxStep;
    return current + step;
  }

  /**
   * Face toward a yaw target with v1 damper (TURN_RATE + cap).
   * speed < FACE_MOVE_EPS (~0.15 m/s) → hold yaw (no snap / arrive twitch).
   */
  private faceTowardYaw(
    mesh: THREE.Object3D,
    targetYaw: number,
    speed: number,
    dt: number,
    rate = TURN_RATE
  ): void {
    if (speed < FACE_MOVE_EPS) return;
    mesh.rotation.y = this.smoothYaw(mesh.rotation.y, targetYaw, dt, rate);
  }

  /** Face horizontal move velocity from resolved delta (followers / slide fallback). */
  private faceMoveVelocity(
    mesh: THREE.Object3D,
    dx: number,
    dz: number,
    dt: number,
    rate = TURN_RATE
  ): void {
    const speed = Math.hypot(dx, dz) / Math.max(0.001, dt);
    if (speed < FACE_MOVE_EPS) return;
    this.faceTowardYaw(mesh, Math.atan2(dx, dz), speed, dt, rate);
  }

  /**
   * Controlled yaw: prefer click intent; wall-slide override if stuck >0.25s;
   * hold under FACE_MOVE_EPS (docs/locomotion-formation-v2.md).
   */
  private updateControlledYaw(
    movedX: number,
    movedZ: number,
    dt: number,
    intentDx: number,
    intentDz: number
  ): void {
    const speed = Math.hypot(movedX, movedZ) / Math.max(0.001, dt);
    if (speed < FACE_MOVE_EPS) {
      this.wallSlideTimer = 0;
      return;
    }
    const velYaw = Math.atan2(movedX, movedZ);
    let target = velYaw;
    if (this.intentYaw != null) {
      const intentLen = Math.hypot(intentDx, intentDz);
      const intentYaw =
        intentLen > 1e-4 ? Math.atan2(intentDx, intentDz) : this.intentYaw;
      this.intentYaw = intentYaw;
      const arc = Math.abs(this.shortestYawDelta(intentYaw, velYaw));
      // Nearly perpendicular to intent → accumulate wall-slide timer
      if (arc > Math.PI * 0.45) {
        this.wallSlideTimer += dt;
      } else {
        this.wallSlideTimer = 0;
      }
      if (this.wallSlideTimer < WALL_SLIDE_OVERRIDE_S && arc < Math.PI * 0.5) {
        target = intentYaw;
      } else if (this.wallSlideTimer >= WALL_SLIDE_OVERRIDE_S) {
        target = velYaw; // face along wall so we don't moonwalk
      } else {
        target = intentYaw;
      }
    } else {
      this.wallSlideTimer = 0;
    }
    this.faceTowardYaw(this.playerMesh, target, speed, dt);
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
    const fwdX = Math.sin(facing);
    const fwdZ = Math.cos(facing);
    const sideX = Math.cos(facing);
    const sideZ = -Math.sin(facing);
    const dtClamped = Math.max(0.001, dt);
    const chase = snap ? 1 : 1 - Math.exp(-FOLLOW_CHASE * dtClamped);
    const leadX = this.playerMesh.position.x;
    const leadZ = this.playerMesh.position.z;

    // Doorway compress: scale offsets toward trail when softSlide fails repeatedly
    if (!snap) {
      if (this.formationBlockStreak >= 2) {
        this.formationCompress = Math.max(0.55, this.formationCompress - dtClamped * 1.2);
      } else {
        this.formationCompress = Math.min(1, this.formationCompress + dtClamped * 0.8);
      }
    } else {
      this.formationCompress = 1;
      this.formationBlockStreak = 0;
    }

    let blockedThisFrame = 0;
    const scale = this.formationCompress;

    for (const id of this.followerTrail) {
      const mesh = this.followerMeshes.get(id);
      if (!mesh) continue;
      mesh.visible = true;
      const slot = FORMATION_SLOTS[id] ?? { fwd: -1.8, right: 0 };
      const idealX = leadX + fwdX * slot.fwd * scale + sideX * slot.right * scale;
      const idealZ = leadZ + fwdZ * slot.fwd * scale + sideZ * slot.right * scale;

      if (snap) {
        const slid = this.softSlideFollower(idealX, idealZ, idealX, idealZ, sideX, sideZ);
        mesh.position.set(slid.x, 0, slid.z);
        continue;
      }

      const fromX = mesh.position.x;
      const fromZ = mesh.position.z;
      const slid = this.softSlideFollower(fromX, fromZ, idealX, idealZ, sideX, sideZ);
      const missIdeal = Math.hypot(idealX - slid.x, idealZ - slid.z);
      const canStep = Math.hypot(slid.x - fromX, slid.z - fromZ);
      // softSlide failed: freeze slot (no wall rubber-band)
      if (missIdeal > 0.25 && canStep < 1e-4) {
        blockedThisFrame += 1;
        mesh.rotation.y = this.smoothYaw(mesh.rotation.y, facing, dtClamped, FOLLOW_YAW_LAG);
        continue;
      }

      const prevX = mesh.position.x;
      const prevZ = mesh.position.z;
      mesh.position.x += (slid.x - mesh.position.x) * chase;
      mesh.position.z += (slid.z - mesh.position.z) * chase;
      mesh.position.y = 0;
      const movedX = mesh.position.x - prevX;
      const movedZ = mesh.position.z - prevZ;
      const moveSpeed = Math.hypot(movedX, movedZ) / dtClamped;
      if (moveSpeed >= FACE_MOVE_EPS) {
        this.faceMoveVelocity(mesh, movedX, movedZ, dtClamped);
      } else {
        mesh.rotation.y = this.smoothYaw(mesh.rotation.y, facing, dtClamped, FOLLOW_YAW_LAG);
      }
    }

    if (blockedThisFrame > 0) this.formationBlockStreak += 1;
    else this.formationBlockStreak = 0;
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

  /** Tag a mesh for RMB inspect/loot/use. */
  private registerInteractable(
    mesh: THREE.Object3D,
    def: WorldInteractable,
    x?: number,
    z?: number
  ): void {
    if (x != null && z != null) mesh.position.set(x, mesh.position.y, z);
    mesh.userData.interactId = def.id;
    this.interactables.set(def.id, { mesh, def });
    if (!mesh.parent) this.scene.add(mesh);
  }

  /**
   * Hub props for RMB context (docs/stats-equip-sheet.md).
   * NPCs stay talk via pickNpc; these cover chests, cavity, markers, loot piles.
   */
  private async seedWorldInteractables(): Promise<void> {
    this.interactables.clear();
    // Clear prior interact-tagged meshes we own
    const doomed: THREE.Object3D[] = [];
    this.scene.traverse((o) => {
      if (o.name.startsWith('interact-')) doomed.push(o);
    });
    for (const o of doomed) o.parent?.remove(o);

    const tagNamed = (
      name: string,
      def: WorldInteractable,
      fallback: () => { x: number; z: number; mesh?: THREE.Object3D }
    ) => {
      let found: THREE.Object3D | null = null;
      this.scene.traverse((o) => {
        if (!found && o.name === name) found = o;
      });
      if (found) {
        this.registerInteractable(found, def);
        return;
      }
      const fb = fallback();
      if (fb.mesh) {
        this.registerInteractable(fb.mesh, def, fb.x, fb.z);
      }
    };

    if (this.zone === 'act1_road') {
      const cellarer = this.activeNpcs.find((n) => n.id === 'cellarer');
      const cx = (cellarer?.x ?? -3.2) * TILE;
      const cz = (cellarer?.z ?? -1.2) * TILE;
      const chestArt = await loadModel(PATH.lootChest);
      const chest = chestArt ?? this.makeChestPlaceholder();
      if (chestArt) {
        fitToHeight(chest, 0.55);
        tintMeshes(chest, 0x4a3424, 0.12);
      }
      chest.name = 'interact-fontfroide-chest';
      this.registerInteractable(
        chest,
        {
          id: 'fontfroide_chest',
          kind: 'inspect',
          label: 'Relic Chest',
          hint: 'Oak, waxed linen, lead seal on the false bull inside.',
          dialogueId: 'obj_fontfroide_chest',
        },
        cx + 0.85,
        cz + 0.35
      );

      tagNamed(
        'mold-cavity-art',
        {
          id: 'mold_cavity',
          kind: 'inspect',
          label: 'Mold cavity',
          hint: 'Goldsmith’s under-board hollow. River-slick.',
          dialogueId: 'obj_mold_cavity',
        },
        () => {
          const mold = this.activeNpcs.find((n) => n.id === 'mold');
          const mx = ((mold?.x ?? -2.0) * TILE) + 0.55;
          const mz = ((mold?.z ?? -3.5) * TILE) - 0.35;
          const stub = new THREE.Mesh(
            new THREE.BoxGeometry(0.55, 0.35, 0.45),
            new THREE.MeshStandardMaterial({ color: 0x3a3020, roughness: 0.9 })
          );
          stub.position.y = 0.18;
          const g = new THREE.Group();
          g.add(stub);
          g.name = 'interact-mold-cavity';
          return { x: mx, z: mz, mesh: g };
        }
      );

      tagNamed(
        'mile-marker-art',
        {
          id: 'mile_marker',
          kind: 'inspect',
          label: 'Mile marker',
          hint: 'Wet limestone. Scrapes where badges leaned.',
          dialogueId: 'obj_mile_marker',
        },
        () => {
          const bandits = this.activeNpcs.find((n) => n.id === 'bandits');
          const bx = ((bandits?.x ?? 3.2) * TILE) - 1.1;
          const bz = ((bandits?.z ?? -3.8) * TILE) + 0.8;
          const post = new THREE.Mesh(
            new THREE.CylinderGeometry(0.08, 0.1, 1.1, 8),
            new THREE.MeshStandardMaterial({ color: 0x6a6860, roughness: 0.95 })
          );
          post.position.y = 0.55;
          const g = new THREE.Group();
          g.add(post);
          g.name = 'interact-mile-marker';
          return { x: bx, z: bz, mesh: g };
        }
      );

      // Ambush loot pile
      const bandits = this.activeNpcs.find((n) => n.id === 'bandits');
      const lx = ((bandits?.x ?? 3.2) * TILE) + 1.1;
      const lz = ((bandits?.z ?? -3.8) * TILE) + 0.6;
      let lootMesh: THREE.Object3D | null = null;
      this.scene.traverse((o) => {
        if (!lootMesh && (o.name === 'ruin-debris-art' || o.name === 'pilgrim-bundle-art')) {
          const dx = o.position.x - lx;
          const dz = o.position.z - lz;
          if (Math.hypot(dx, dz) < 8) lootMesh = o;
        }
      });
      if (!lootMesh) {
        const pile = new THREE.Group();
        const a = new THREE.Mesh(
          new THREE.BoxGeometry(0.55, 0.2, 0.4),
          new THREE.MeshStandardMaterial({ color: 0x3a3428, roughness: 0.95 })
        );
        a.position.y = 0.1;
        const b = new THREE.Mesh(
          new THREE.SphereGeometry(0.18, 8, 6),
          new THREE.MeshStandardMaterial({ color: 0x4a4030, roughness: 0.9 })
        );
        b.position.set(0.15, 0.22, 0.05);
        pile.add(a, b);
        pile.name = 'interact-ambush-loot';
        lootMesh = pile;
        lootMesh.position.set(lx, 0, lz);
        this.scene.add(lootMesh);
      }
      this.registerInteractable(lootMesh, {
        id: 'ambush_loot',
        kind: 'loot',
        label: 'Loot pile',
        hint: 'Torn badges and a wet purse.',
        dialogueId: 'obj_ambush_loot',
        lootItemId: 'canal_salve',
      });

      tagNamed(
        'burial-gate-art',
        {
          id: 'burial_gate',
          kind: 'inspect',
          label: 'Burial gate',
          hint: 'Locked under interdict weather.',
          dialogueId: 'obj_burial_gate',
        },
        () => {
          const parish = this.activeNpcs.find((n) => n.id === 'parish');
          const px = ((parish?.x ?? 2.5) * TILE) + 1.6;
          const pz = ((parish?.z ?? 8) * TILE) - 0.4;
          const door = this.makeDoorPlaceholder(0x4a4840);
          door.name = 'interact-burial-gate';
          return { x: px, z: pz, mesh: door };
        }
      );

      const ferry = this.npcMeshes.get('ferry');
      if (ferry) {
        this.registerInteractable(ferry, {
          id: 'ferry_rope',
          kind: 'inspect',
          label: 'Ferry rope',
          hint: 'Taut hemp. Far latch watched.',
          dialogueId: 'obj_ferry_rope',
        });
      }

      // Art densifiers — road crate + herb pouch + wayside chest (off crown)
      const crateArt = await loadModel(PATH.inspectCrate);
      if (crateArt) {
        fitToHeight(crateArt, 0.7);
        tintMeshes(crateArt, 0x4a4030, 0.1);
        crateArt.name = 'interact-road-crate';
        this.registerInteractable(
          crateArt,
          {
            id: 'road_crate',
            kind: 'loot',
            label: 'Road crate',
            hint: 'Wet oak. Rope handles.',
            dialogueId: 'obj_crate',
            lootItemId: 'travel_rations',
          },
          3.4,
          6.0
        );
      }

      const herbArt = await loadModel(PATH.herbPouch);
      if (herbArt) {
        fitToHeight(herbArt, 0.35);
        tintMeshes(herbArt, 0x4a5840, 0.12);
        herbArt.name = 'interact-herb-pouch';
        this.registerInteractable(
          herbArt,
          {
            id: 'herb_pouch',
            kind: 'loot',
            label: 'Herb pouch',
            hint: 'Bitter greens Elias trusts.',
            dialogueId: 'obj_herb_pouch',
            lootItemId: 'bitter_herbs',
          },
          -3.2,
          12.5
        );
      }

      const waysideArt = await loadModel(PATH.lootChest);
      if (waysideArt) {
        const w = waysideArt.clone(true);
        fitToHeight(w, 0.48);
        tintMeshes(w, 0x3a3020, 0.1);
        w.name = 'interact-wayside-chest';
        this.registerInteractable(
          w,
          {
            id: 'wayside_chest',
            kind: 'loot',
            label: 'Wayside chest',
            hint: 'Cheap lock. Emergency coin.',
            dialogueId: 'obj_wayside_chest',
          },
          3.6,
          -12.0
        );
      }

      tagNamed(
        'wayside-cross-art',
        {
          id: 'wayside_cross',
          kind: 'inspect',
          label: 'Wayside cross',
          hint: 'Wood gone grey. Pilgrims touch it; clerks count the cracks.',
        },
        () => ({ x: 0, z: 0 })
      );
    }

    if (this.zone === 'act3_close' || this.zone === 'corbieres') {
      tagNamed(
        'leper-bell-post-art',
        {
          id: 'leper_bell',
          kind: 'inspect',
          label: 'Leper bell',
          hint: 'Iron tongue for the house of outcasts. Ring only if you mean the road to hear.',
        },
        () => ({ x: 0, z: 0 })
      );
      // Splinter / altar inspect stubs when meshes exist
      this.scene.traverse((o) => {
        if (o.name === 'splinter-plinth-art' || o.name.includes('false-altar') || o.name === 'false-altar-art') {
          if (!this.interactables.has('splinter_plinth')) {
            this.registerInteractable(o, {
              id: 'splinter_plinth',
              kind: 'inspect',
              label: 'Splinter plinth',
              hint: 'A saint’s staff sold by the inch. Pine under gilt dust.',
            });
          }
        }
      });
    }
  }

  pickInteractable(clientX: number, clientY: number): WorldInteractable | null {
    this.pointer.x = (clientX / window.innerWidth) * 2 - 1;
    this.pointer.y = -(clientY / window.innerHeight) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const meshes: THREE.Object3D[] = [];
    for (const { mesh } of this.interactables.values()) {
      if (mesh.visible !== false) meshes.push(mesh);
    }
    if (meshes.length) {
      const hits = this.raycaster.intersectObjects(meshes, true);
      if (hits.length) {
        let obj: THREE.Object3D | null = hits[0].object;
        while (obj) {
          if (obj.userData?.interactId) {
            const id = obj.userData.interactId as string;
            return this.interactables.get(id)?.def ?? null;
          }
          obj = obj.parent;
        }
      }
    }
    const pt = this.screenToGround(clientX, clientY);
    if (!pt) return null;
    const maxD = 1.6 * 1.2;
    let best: WorldInteractable | null = null;
    let bestD = maxD;
    for (const { mesh, def } of this.interactables.values()) {
      if (mesh.visible === false) continue;
      const d = Math.hypot(mesh.position.x - pt.x, mesh.position.z - pt.z);
      if (d < bestD) {
        bestD = d;
        best = def;
      }
    }
    return best;
  }

  nearestInteractable(maxDist = 1.6 * 1.2): WorldInteractable | null {
    let best: WorldInteractable | null = null;
    let bestD = maxDist;
    const px = this.playerMesh.position.x;
    const pz = this.playerMesh.position.z;
    for (const { mesh, def } of this.interactables.values()) {
      if (mesh.visible === false) continue;
      const d = Math.hypot(mesh.position.x - px, mesh.position.z - pz);
      if (d < bestD) {
        bestD = d;
        best = def;
      }
    }
    return best;
  }

  markInteractableLooted(id: string): void {
    const entry = this.interactables.get(id);
    if (!entry) return;
    entry.def.lootItemId = undefined;
    entry.def.kind = 'inspect';
    entry.def.hint = entry.def.hint + ' (already searched)';
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
    if (hits.length) {
      let obj: THREE.Object3D | null = hits[0].object;
      while (obj) {
        if (obj.userData?.npcId) {
          const id = obj.userData.npcId as string;
          return this.activeNpcs.find((n) => n.id === id) ?? null;
        }
        obj = obj.parent;
      }
    }
    // ~1.2× RMB latch: if mesh miss, latch nearest NPC to ground under cursor
    const pt = this.screenToGround(clientX, clientY);
    if (!pt) return null;
    const maxD = 1.6 * 1.2;
    let best: NpcDef | null = null;
    let bestD = maxD;
    for (const n of this.activeNpcs) {
      const m = this.npcMeshes.get(n.id);
      if (m && !m.visible) continue;
      const dx = n.x * TILE - pt.x;
      const dz = n.z * TILE - pt.z;
      const d = Math.hypot(dx, dz);
      if (d < bestD) {
        bestD = d;
        best = n;
      }
    }
    return best;
  }

  /** RMB latch for party followers (mesh hit or ground near). */
  pickFollower(clientX: number, clientY: number): JobId | null {
    this.pointer.x = (clientX / window.innerWidth) * 2 - 1;
    this.pointer.y = -(clientY / window.innerHeight) * 2 + 1;
    this.raycaster.setFromCamera(this.pointer, this.camera);
    const meshes: THREE.Object3D[] = [];
    for (const [, m] of this.followerMeshes) {
      if (m.visible) meshes.push(m);
    }
    const hits = this.raycaster.intersectObjects(meshes, true);
    if (hits.length) {
      let obj: THREE.Object3D | null = hits[0].object;
      while (obj) {
        if (obj.userData?.jobId) return obj.userData.jobId as JobId;
        obj = obj.parent;
      }
    }
    const pt = this.screenToGround(clientX, clientY);
    if (!pt) return null;
    const maxD = 1.6 * 1.2;
    let best: JobId | null = null;
    let bestD = maxD;
    for (const id of this.followerTrail) {
      const m = this.followerMeshes.get(id);
      if (!m || !m.visible) continue;
      const d = Math.hypot(m.position.x - pt.x, m.position.z - pt.z);
      if (d < bestD) {
        bestD = d;
        best = id;
      }
    }
    return best;
  }

  private playableHalf(): { hx: number; hz: number } {
    if (this.zone === 'act1_road') return { hx: HALF_X - 0.5, hz: HALF_Z - 0.5 };
    const half = (GRID * TILE) / 2 - 0.4;
    return { hx: half, hz: half };
  }

  moveToWorld(point: THREE.Vector3): void {
    const { hx, hz } = this.playableHalf();
    point.x = Math.max(-hx, Math.min(hx, point.x));
    point.z = Math.max(-hz, Math.min(hz, point.z));
    const pos = this.playerMesh.position;
    const dx = point.x - pos.x;
    const dz = point.z - pos.z;
    if (Math.hypot(dx, dz) > 0.05) {
      this.intentYaw = Math.atan2(dx, dz);
      this.wallSlideTimer = 0;
      // Optional stop-turn: if stopped and click needs >90°, plant and turn briefly
      const moving = this.pathTarget != null;
      const arc = Math.abs(this.shortestYawDelta(this.playerMesh.rotation.y, this.intentYaw));
      if (!moving && arc > Math.PI * 0.5) {
        this.stopTurnUntil = this.clock.getElapsedTime() + 0.35;
      } else {
        this.stopTurnUntil = 0;
      }
    }
    this.pathTarget = point;
    this.marker.position.set(point.x, 0.05, point.z);
    this.marker.visible = true;
  }

  nearestNpc(maxDist = 1.6 * 1.2): NpcDef | null {
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
      this.intentYaw = null;
      this.wallSlideTimer = 0;
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
      this.intentYaw = null;
      this.wallSlideTimer = 0;
      this.stopTurnUntil = 0;
      this.marker.visible = false;
      this.playerX = pos.x / TILE;
      this.playerZ = pos.z / TILE;
      this.onArrive?.();
      this.layoutFollowers(false, dt);
      this.updateCamera();
      return;
    }

    // Optional stop-turn: yaw in place toward intent before stepping
    const now = this.clock.getElapsedTime();
    if (this.stopTurnUntil > now && this.intentYaw != null) {
      const before = this.playerMesh.rotation.y;
      const maxStep = STOP_TURN_RATE * dt;
      const delta = this.shortestYawDelta(before, this.intentYaw);
      const stepYaw = Math.abs(delta) <= maxStep ? delta : Math.sign(delta) * maxStep;
      this.playerMesh.rotation.y = before + stepYaw;
      if (Math.abs(this.shortestYawDelta(this.playerMesh.rotation.y, this.intentYaw)) < 0.12) {
        this.stopTurnUntil = 0;
      }
      this.layoutFollowers(false, dt);
      this.updateCamera();
      return;
    }
    this.stopTurnUntil = 0;

    const step = Math.min(dist, this.moveSpeed * dt);
    const wantX = pos.x + (dx / dist) * step;
    const wantZ = pos.z + (dz / dist) * step;
    const fromX = pos.x;
    const fromZ = pos.z;
    const resolved = this.resolveCollision(fromX, fromZ, wantX, wantZ);
    const movedX = resolved.x - fromX;
    const movedZ = resolved.z - fromZ;
    const moved = Math.hypot(movedX, movedZ);
    if (moved < 1e-4 && dist > 0.15) {
      this.pathTarget = null;
      this.intentYaw = null;
      this.wallSlideTimer = 0;
      this.marker.visible = false;
    } else {
      pos.x = resolved.x;
      pos.z = resolved.z;
      this.updateControlledYaw(movedX, movedZ, dt, dx, dz);
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
