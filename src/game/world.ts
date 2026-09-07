import * as THREE from 'three';
import { NPCS } from './data';
import { fitToHeight, loadModel, tintMeshes } from './assets';

const TILE = 1.2;
const GRID = 11; // -5..5
const PLAYER_RADIUS = 0.32;
const ORBIT_DIST = 18;
const ORBIT_PITCH_MIN = 0.35;
const ORBIT_PITCH_MAX = 1.25;

const PATH = {
  player: './models/characters/rowan.glb',
  mirelle: './models/characters/mirelle.glb',
  brin: './models/characters/brin.glb',
  wraith: './models/graveyard/character-ghost.glb',
  wallDoor: './models/fantasy/wall-door.glb',
  wallWindow: './models/fantasy/wall-window-shutters.glb',
  wallBlock: './models/fantasy/wall-block.glb',
  wallCorner: './models/fantasy/wall-corner.glb',
  wallArch: './models/fantasy/wall-arch.glb',
  wallArchTop: './models/fantasy/wall-arch-top.glb',
  roofGable: './models/fantasy/roof-gable.glb',
  roofHigh: './models/fantasy/roof-high-gable.glb',
  stallGreen: './models/fantasy/stall-green.glb',
  stallRed: './models/fantasy/stall-red.glb',
  lantern: './models/fantasy/lantern.glb',
  cart: './models/fantasy/cart.glb',
  fountain: './models/fantasy/fountain-square.glb',
  crypt: './models/graveyard/crypt.glb',
  cryptSmall: './models/graveyard/crypt-small.glb',
  lightpost: './models/graveyard/lightpost-single.glb',
  bench: './models/graveyard/bench.glb',
  fence: './models/graveyard/iron-fence.glb',
  pine: './models/graveyard/pine-fall.glb',
  pillar: './models/graveyard/pillar-square.glb',
  boat: './models/pirate/boat-row-small.glb',
  barrel: './models/pirate/barrel.glb',
  crate: './models/pirate/crate.glb',
  dock: './models/pirate/structure-platform-dock-small.glb',
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
  private pathTarget: THREE.Vector3 | null = null;
  private readonly moveSpeed = 4.5;
  private marker!: THREE.Mesh;
  private clock = new THREE.Clock();
  private lanternFlickers: Array<{ light: THREE.PointLight; base: number }> = [];
  private colliders: Collider[] = [];
  /** Orbit yaw (around Y) and pitch (elevation from horizon). */
  private camYaw = Math.PI / 4;
  private camPitch = 0.72;
  private camDist = ORBIT_DIST;
  private frustumSize = 9;
  playerX = 0;
  playerZ = 2;
  onArrive: (() => void) | null = null;

  constructor(canvas: HTMLCanvasElement) {
    this.scene.background = new THREE.Color(0x12101a);
    this.scene.fog = new THREE.FogExp2(0x1a1520, 0.045);

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
    this.renderer.toneMappingExposure = 1.05;

    this.setupLights();
    this.buildBaseHub();

    this.playerMesh = this.makeCharacter(0xc07040, 0.55);
    this.scene.add(this.playerMesh);
    this.setPlayerPos(this.playerX, this.playerZ);

    for (const n of NPCS) {
      const g = this.makeCharacter(n.color, 0.5);
      g.position.set(n.x * TILE, 0, n.z * TILE);
      g.userData.npcId = n.id;
      this.scene.add(g);
      this.npcMeshes.set(n.id, g);
      // soft collider so player doesn't clip through NPCs
      this.addCircleCollider(n.x * TILE, n.z * TILE, 0.4);
    }

    const mGeo = new THREE.RingGeometry(0.15, 0.28, 24);
    mGeo.rotateX(-Math.PI / 2);
    this.marker = new THREE.Mesh(
      mGeo,
      new THREE.MeshBasicMaterial({ color: 0xd4a574, transparent: true, opacity: 0.7 })
    );
    this.marker.visible = false;
    this.scene.add(this.marker);

    window.addEventListener('resize', () => this.onResize());
    this.updateCamera();
    this.ready = this.polishWithModels();
  }

  /** Rotate orbit camera by delta yaw / pitch (radians). */
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
    const ambient = new THREE.AmbientLight(0x3a3048, 0.28);
    this.scene.add(ambient);

    const hemi = new THREE.HemisphereLight(0x8a7a90, 0x1a1018, 0.55);
    this.scene.add(hemi);

    const moon = new THREE.DirectionalLight(0xb8c4e0, 0.55);
    moon.position.set(-8, 16, -4);
    moon.castShadow = true;
    moon.shadow.mapSize.set(1024, 1024);
    moon.shadow.camera.near = 1;
    moon.shadow.camera.far = 40;
    const s = 12;
    moon.shadow.camera.left = -s;
    moon.shadow.camera.right = s;
    moon.shadow.camera.top = s;
    moon.shadow.camera.bottom = -s;
    moon.shadow.bias = -0.0008;
    moon.shadow.normalBias = 0.02;
    this.scene.add(moon);

    const warm = new THREE.DirectionalLight(0xffb080, 0.35);
    warm.position.set(5, 8, 6);
    this.scene.add(warm);
  }

  private addLanternLight(x: number, y: number, z: number, intensity = 1.1): void {
    const light = new THREE.PointLight(0xff9a4a, intensity, 8, 2);
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
    // approximate circle with AABB for MVP (tight enough for walk-block)
    this.addBoxCollider(cx, cz, r * 0.85, r * 0.85);
  }

  /** Resolve proposed XZ against AABBs with wall-slide. */
  private resolveCollision(fromX: number, fromZ: number, toX: number, toZ: number): { x: number; z: number } {
    let x = toX;
    let z = toZ;
    const r = PLAYER_RADIUS;

    // Try full move; if blocked, slide on X then Z
    const hits = (px: number, pz: number) => {
      for (const c of this.colliders) {
        if (px + r > c.minX && px - r < c.maxX && pz + r > c.minZ && pz - r < c.maxZ) return c;
      }
      return null;
    };

    if (!hits(x, z)) return { x, z };

    // slide X only
    if (!hits(x, fromZ)) return { x, z: fromZ };
    // slide Z only
    if (!hits(fromX, z)) return { x: fromX, z };
    // blocked both — stay
    return { x: fromX, z: fromZ };
  }

  private buildBaseHub(): void {
    const groundMat = new THREE.MeshStandardMaterial({
      color: 0x2e2824,
      roughness: 0.92,
      metalness: 0.04,
    });
    const geo = new THREE.PlaneGeometry(GRID * TILE, GRID * TILE);
    geo.rotateX(-Math.PI / 2);
    this.ground = new THREE.Mesh(geo, groundMat);
    this.ground.receiveShadow = true;
    this.ground.name = 'ground';
    this.scene.add(this.ground);

    const canal = new THREE.Mesh(
      new THREE.BoxGeometry(GRID * TILE * 0.32, 0.12, GRID * TILE),
      new THREE.MeshStandardMaterial({
        color: 0x142838,
        roughness: 0.25,
        metalness: 0.45,
        emissive: 0x061018,
        emissiveIntensity: 0.35,
      })
    );
    canal.position.set(-GRID * TILE * 0.3, -0.04, 0);
    canal.receiveShadow = true;
    this.scene.add(canal);
    // canal is walkable via bridge; block deep water sides as soft barriers
    this.addAABB(-GRID * TILE * 0.46, -GRID * TILE * 0.14, -GRID * TILE * 0.5, -0.7);
    this.addAABB(-GRID * TILE * 0.46, -GRID * TILE * 0.14, 0.7, GRID * TILE * 0.5);

    const bridge = new THREE.Mesh(
      new THREE.BoxGeometry(2.4, 0.18, 1.2),
      new THREE.MeshStandardMaterial({ color: 0x4a3828, roughness: 0.85 })
    );
    bridge.position.set(-2.4, 0.12, 0);
    bridge.castShadow = true;
    bridge.receiveShadow = true;
    bridge.name = 'temp-bridge';
    this.scene.add(bridge);

    const places: Array<[number, number, number, number, number]> = [
      [-4, -4, 1.6, 1.8, 0x4a3028],
      [-5, 2, 1.4, 2.2, 0x3a2830],
      [5, -3, 1.8, 1.5, 0x403028],
      [5, 3, 1.5, 2.0, 0x352820],
      [0, -5, 2.4, 1.2, 0x2a2030],
      [-1, 5, 1.3, 1.6, 0x453528],
    ];
    for (const [gx, gz, w, h, col] of places) {
      const b = new THREE.Mesh(
        new THREE.BoxGeometry(w, h, w * 0.85),
        new THREE.MeshStandardMaterial({ color: col, roughness: 0.85 })
      );
      const px = gx * TILE * 0.85;
      const pz = gz * TILE * 0.85;
      b.position.set(px, h / 2, pz);
      b.castShadow = true;
      b.receiveShadow = true;
      b.name = 'temp-building';
      this.scene.add(b);
      this.addBoxCollider(px, pz, w * 0.5, w * 0.85 * 0.5);
    }

    const archMat = new THREE.MeshStandardMaterial({ color: 0x5a4858, roughness: 0.8 });
    const archL = new THREE.Mesh(new THREE.BoxGeometry(0.35, 2.4, 0.35), archMat);
    const archR = archL.clone();
    const archTop = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.35, 0.35), archMat.clone());
    archL.position.set(2.2 * TILE, 1.2, -4 * TILE);
    archR.position.set(3.8 * TILE, 1.2, -4 * TILE);
    archTop.position.set(3 * TILE, 2.35, -4 * TILE);
    for (const a of [archL, archR, archTop]) {
      a.castShadow = true;
      a.name = 'temp-arch';
      this.scene.add(a);
    }
    this.addBoxCollider(2.2 * TILE, -4 * TILE, 0.28, 0.28);
    this.addBoxCollider(3.8 * TILE, -4 * TILE, 0.28, 0.28);

    const grid = new THREE.GridHelper(GRID * TILE, GRID, 0x241c18, 0x241c18);
    grid.position.y = 0.01;
    (grid.material as THREE.Material).transparent = true;
    (grid.material as THREE.Material).opacity = 0.25;
    this.scene.add(grid);
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
    const urls = [
      PATH.player,
      PATH.mirelle,
      PATH.brin,
      PATH.wraith,
      PATH.wallDoor,
      PATH.wallWindow,
      PATH.wallBlock,
      PATH.wallCorner,
      PATH.wallArch,
      PATH.wallArchTop,
      PATH.roofGable,
      PATH.roofHigh,
      PATH.stallGreen,
      PATH.stallRed,
      PATH.lantern,
      PATH.cart,
      PATH.fountain,
      PATH.crypt,
      PATH.cryptSmall,
      PATH.lightpost,
      PATH.bench,
      PATH.fence,
      PATH.pine,
      PATH.pillar,
      PATH.boat,
      PATH.barrel,
      PATH.crate,
      PATH.dock,
    ];
    const loaded = await Promise.all(urls.map((u) => loadModel(u)));
    const byUrl = new Map<string, THREE.Group | null>();
    urls.forEach((u, i) => byUrl.set(u, loaded[i]));

    const take = (key: keyof typeof PATH) => byUrl.get(PATH[key])?.clone(true) ?? null;

    await this.upgradeCharacter('player', take('player'), 1.55, 0xc07040);
    await this.upgradeNpc('mirelle', take('mirelle'), 1.5, 0x6a4a8a);
    await this.upgradeNpc('brin', take('brin'), 1.5, 0x4a6a5a);
    await this.upgradeNpc('wraith', take('wraith'), 1.55, 0x2a1018, 0.55);

    // Clear temp building colliders — rebuild from placed props
    this.colliders = this.colliders.filter(() => false);
    // re-add canal barriers
    this.addAABB(-GRID * TILE * 0.46, -GRID * TILE * 0.14, -GRID * TILE * 0.5, -0.7);
    this.addAABB(-GRID * TILE * 0.46, -GRID * TILE * 0.14, 0.7, GRID * TILE * 0.5);
    for (const n of NPCS) {
      this.addCircleCollider(n.x * TILE, n.z * TILE, 0.4);
    }

    this.removeNamed('temp-building');
    this.removeNamed('temp-arch');
    this.removeNamed('temp-bridge');

    this.placeBuilding(-4.2, -4.2, take, 'stone');
    this.placeBuilding(-5.2, 2.0, take, 'wood');
    this.placeBuilding(5.0, -3.2, take, 'stone');
    this.placeBuilding(5.0, 3.0, take, 'crypt');
    this.placeBuilding(0.2, -5.2, take, 'stall');
    this.placeBuilding(-1.0, 5.0, take, 'wood');

    const pillarL = take('pillar');
    const pillarR = take('pillar');
    const archTop = take('wallArchTop') ?? take('wallArch');
    if (pillarL && pillarR && archTop) {
      fitToHeight(pillarL, 2.3);
      fitToHeight(pillarR, 2.3);
      fitToHeight(archTop, 0.55);
      pillarL.position.set(2.2 * TILE, 0, -4 * TILE);
      pillarR.position.set(3.8 * TILE, 0, -4 * TILE);
      archTop.position.set(3 * TILE, 2.2, -4 * TILE);
      archTop.rotation.y = Math.PI / 2;
      this.scene.add(pillarL, pillarR, archTop);
      this.addBoxCollider(2.2 * TILE, -4 * TILE, 0.3, 0.3);
      this.addBoxCollider(3.8 * TILE, -4 * TILE, 0.3, 0.3);
    } else {
      const archMat = new THREE.MeshStandardMaterial({ color: 0x5a4858, roughness: 0.8 });
      const aL = new THREE.Mesh(new THREE.BoxGeometry(0.35, 2.4, 0.35), archMat);
      const aR = aL.clone();
      const aT = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.35, 0.35), archMat);
      aL.position.set(2.2 * TILE, 1.2, -4 * TILE);
      aR.position.set(3.8 * TILE, 1.2, -4 * TILE);
      aT.position.set(3 * TILE, 2.35, -4 * TILE);
      this.scene.add(aL, aR, aT);
      this.addBoxCollider(2.2 * TILE, -4 * TILE, 0.28, 0.28);
      this.addBoxCollider(3.8 * TILE, -4 * TILE, 0.28, 0.28);
    }

    const dock = take('dock');
    if (dock) {
      fitToHeight(dock, 0.55);
      dock.position.set(-2.6, 0, 0.1);
      dock.rotation.y = Math.PI / 2;
      this.scene.add(dock);
    } else {
      const bridge = new THREE.Mesh(
        new THREE.BoxGeometry(2.4, 0.18, 1.2),
        new THREE.MeshStandardMaterial({ color: 0x4a3828, roughness: 0.85 })
      );
      bridge.position.set(-2.4, 0.12, 0);
      this.scene.add(bridge);
    }

    const boat = take('boat');
    if (boat) {
      fitToHeight(boat, 0.55);
      boat.position.set(-4.2, -0.05, 2.5);
      boat.rotation.y = 0.4;
      this.scene.add(boat);
      this.addBoxCollider(-4.2, 2.5, 0.7, 0.35);
    }

    for (const [x, z] of [
      [-3.2, 1.2],
      [-3.5, 1.6],
      [4.2, 2.2],
    ] as const) {
      const barrel = take('barrel');
      if (!barrel) break;
      fitToHeight(barrel, 0.45);
      barrel.position.set(x, 0, z);
      this.scene.add(barrel);
      this.addCircleCollider(x, z, 0.28);
    }

    const crate = take('crate');
    if (crate) {
      fitToHeight(crate, 0.4);
      crate.position.set(3.6, 0, 2.0);
      this.scene.add(crate);
      this.addBoxCollider(3.6, 2.0, 0.3, 0.3);
    }

    const cart = take('cart');
    if (cart) {
      fitToHeight(cart, 0.85);
      cart.position.set(1.5, 0, 4.2);
      cart.rotation.y = -0.6;
      this.scene.add(cart);
      this.addBoxCollider(1.5, 4.2, 0.7, 0.4);
    }

    const fountain = take('fountain');
    if (fountain) {
      fitToHeight(fountain, 0.9);
      fountain.position.set(0.5, 0, -1.2);
      this.scene.add(fountain);
      this.addCircleCollider(0.5, -1.2, 0.55);
    }

    const bench = take('bench');
    if (bench) {
      fitToHeight(bench, 0.45);
      bench.position.set(-1.8, 0, -3.2);
      bench.rotation.y = 0.3;
      this.scene.add(bench);
      this.addBoxCollider(-1.8, -3.2, 0.55, 0.25);
    }

    for (const [x, z] of [
      [-2.0, 0.8],
      [2.5, -3.5],
      [-4.0, -2.5],
      [4.0, 0.5],
    ] as const) {
      const post = take('lightpost') ?? take('lantern');
      if (!post) continue;
      fitToHeight(post, 2.0);
      post.position.set(x, 0, z);
      this.scene.add(post);
      this.addCircleCollider(x, z, 0.18);
      this.addLanternLight(x, 1.6, z, 1.25);
    }

    const fence = take('fence');
    if (fence) {
      fitToHeight(fence, 1.1);
      fence.position.set(1.4 * TILE, 0, -4.6 * TILE);
      this.scene.add(fence);
      this.addBoxCollider(1.4 * TILE, -4.6 * TILE, 0.7, 0.12);
      const fence2 = fence.clone(true);
      fence2.position.set(4.4 * TILE, 0, -4.6 * TILE);
      this.scene.add(fence2);
      this.addBoxCollider(4.4 * TILE, -4.6 * TILE, 0.7, 0.12);
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
    kind: 'stone' | 'wood' | 'crypt' | 'stall'
  ): void {
    if (kind === 'crypt') {
      const c = take('crypt') ?? take('cryptSmall');
      if (c) {
        fitToHeight(c, 2.2);
        c.position.set(x, 0, z);
        this.scene.add(c);
        this.addBoxCollider(x, z, 0.9, 0.9);
        return;
      }
    }
    if (kind === 'stall') {
      const s = take('stallGreen') ?? take('stallRed');
      if (s) {
        fitToHeight(s, 1.4);
        s.position.set(x, 0, z);
        this.scene.add(s);
        this.addBoxCollider(x, z, 0.7, 0.55);
        const s2 = take('stallRed');
        if (s2) {
          fitToHeight(s2, 1.3);
          s2.position.set(x + 1.6, 0, z + 0.4);
          this.scene.add(s2);
          this.addBoxCollider(x + 1.6, z + 0.4, 0.7, 0.55);
        }
        return;
      }
    }

    const wallA = kind === 'wood' ? take('wallBlock') : take('wallDoor') ?? take('wallBlock');
    const wallB = take('wallWindow') ?? take('wallBlock');
    const roof = take('roofHigh') ?? take('roofGable');
    if (!wallA || !wallB) {
      const h = 1.8;
      const b = new THREE.Mesh(
        new THREE.BoxGeometry(1.6, h, 1.4),
        new THREE.MeshStandardMaterial({ color: kind === 'wood' ? 0x453528 : 0x403028, roughness: 0.85 })
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
    wallA.position.set(0, 0, 0.55);
    wallB.position.set(0, 0, -0.55);
    wallB.rotation.y = Math.PI;
    g.add(wallA, wallB);
    const wallC = take('wallBlock');
    const wallD = take('wallCorner') ?? take('wallBlock');
    if (wallC && wallD) {
      fitToHeight(wallC, 1.35);
      fitToHeight(wallD, 1.35);
      wallC.position.set(0.55, 0, 0);
      wallC.rotation.y = Math.PI / 2;
      wallD.position.set(-0.55, 0, 0);
      wallD.rotation.y = -Math.PI / 2;
      g.add(wallC, wallD);
    }
    if (roof) {
      fitToHeight(roof, 0.7);
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
      new THREE.MeshStandardMaterial({ color, roughness: 0.7 })
    );
    body.position.y = ((0.7 * scale) / 0.5) * 0.55;
    body.castShadow = true;
    const head = new THREE.Mesh(
      new THREE.SphereGeometry((0.22 * scale) / 0.5, 14, 14),
      new THREE.MeshStandardMaterial({ color: 0xe8d4b8 })
    );
    head.position.y = ((1.15 * scale) / 0.5) * 0.55;
    head.castShadow = true;
    g.add(body, head);
    return g;
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

  /** Raycast NPCs under cursor; returns NPC data or null. */
  pickNpc(clientX: number, clientY: number): (typeof NPCS)[number] | null {
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
        return NPCS.find((n) => n.id === id) ?? null;
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

  nearestNpc(maxDist = 1.6): (typeof NPCS)[number] | null {
    let best: (typeof NPCS)[number] | null = null;
    let bestD = maxDist;
    const px = this.playerX * TILE;
    const pz = this.playerZ * TILE;
    for (const n of NPCS) {
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
      f.light.intensity = f.base * (0.85 + 0.15 * Math.sin(t * 6 + i * 1.7));
    }

    if (!this.pathTarget) {
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
    // If barely moved toward target due to wall, cancel path
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
    this.updateCamera();
  }

  render(): void {
    this.renderer.render(this.scene, this.camera);
  }

  dispose(): void {
    this.renderer.dispose();
  }
}
