import * as THREE from 'three';
import { NPCS } from './data';

const TILE = 1.2;
const GRID = 11; // -5..5

export class World {
  readonly scene = new THREE.Scene();
  readonly camera: THREE.OrthographicCamera;
  readonly renderer: THREE.WebGLRenderer;
  readonly raycaster = new THREE.Raycaster();
  readonly pointer = new THREE.Vector2();

  private ground!: THREE.Mesh;
  private playerMesh!: THREE.Group;
  private npcMeshes = new Map<string, THREE.Group>();
  private pathTarget: THREE.Vector3 | null = null;
  private readonly moveSpeed = 4.5;
  private marker!: THREE.Mesh;
  playerX = 0;
  playerZ = 2;
  onArrive: (() => void) | null = null;

  constructor(canvas: HTMLCanvasElement) {
    this.scene.background = new THREE.Color(0x1a1410);
    this.scene.fog = new THREE.Fog(0x1a1410, 18, 36);

    const aspect = window.innerWidth / window.innerHeight;
    const frustum = 8;
    this.camera = new THREE.OrthographicCamera(
      -frustum * aspect, frustum * aspect, frustum, -frustum, 0.1, 80
    );
    this.camera.position.set(12, 14, 12);
    this.camera.lookAt(0, 0, 0);
    this.camera.updateProjectionMatrix();

    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.setSize(window.innerWidth, window.innerHeight);

    const hemi = new THREE.HemisphereLight(0xc4b8a0, 0x2a1810, 0.85);
    this.scene.add(hemi);
    const dir = new THREE.DirectionalLight(0xffe0c0, 0.65);
    dir.position.set(6, 12, 4);
    this.scene.add(dir);

    this.buildHub();
    this.playerMesh = this.makeCharacter(0xc07040, 0.55);
    this.scene.add(this.playerMesh);
    this.setPlayerPos(this.playerX, this.playerZ);

    for (const n of NPCS) {
      const g = this.makeCharacter(n.color, 0.5);
      g.position.set(n.x * TILE, 0, n.z * TILE);
      g.userData.npcId = n.id;
      this.scene.add(g);
      this.npcMeshes.set(n.id, g);
    }

    const mGeo = new THREE.RingGeometry(0.15, 0.28, 24);
    mGeo.rotateX(-Math.PI / 2);
    this.marker = new THREE.Mesh(mGeo, new THREE.MeshBasicMaterial({ color: 0xd4a574, transparent: true, opacity: 0.7 }));
    this.marker.visible = false;
    this.scene.add(this.marker);

    window.addEventListener('resize', () => this.onResize());
  }

  private buildHub(): void {
    const groundMat = new THREE.MeshStandardMaterial({ color: 0x3a3228, roughness: 0.9, metalness: 0.05 });
    const geo = new THREE.PlaneGeometry(GRID * TILE, GRID * TILE);
    geo.rotateX(-Math.PI / 2);
    this.ground = new THREE.Mesh(geo, groundMat);
    this.ground.receiveShadow = true;
    this.ground.name = 'ground';
    this.scene.add(this.ground);

    // canal strip
    const canal = new THREE.Mesh(
      new THREE.BoxGeometry(GRID * TILE * 0.35, 0.15, GRID * TILE),
      new THREE.MeshStandardMaterial({ color: 0x1a3040, roughness: 0.35, metalness: 0.2 })
    );
    canal.position.set(-GRID * TILE * 0.28, -0.05, 0);
    this.scene.add(canal);

    // lantern bridge hint
    const bridge = new THREE.Mesh(
      new THREE.BoxGeometry(2.2, 0.2, 1.1),
      new THREE.MeshStandardMaterial({ color: 0x5a4030 })
    );
    bridge.position.set(-2.2, 0.15, 0);
    this.scene.add(bridge);

    // buildings / stalls (placeholder boxes)
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
      b.position.set(gx * TILE * 0.85, h / 2, gz * TILE * 0.85);
      this.scene.add(b);
    }

    // east arch (combat landmark)
    const archL = new THREE.Mesh(new THREE.BoxGeometry(0.35, 2.4, 0.35), new THREE.MeshStandardMaterial({ color: 0x5a4858 }));
    const archR = archL.clone();
    const archTop = new THREE.Mesh(new THREE.BoxGeometry(2.2, 0.35, 0.35), new THREE.MeshStandardMaterial({ color: 0x6a5868 }));
    archL.position.set(2.2 * TILE, 1.2, -4 * TILE);
    archR.position.set(3.8 * TILE, 1.2, -4 * TILE);
    archTop.position.set(3 * TILE, 2.35, -4 * TILE);
    this.scene.add(archL, archR, archTop);

    // grid lines subtle
    const grid = new THREE.GridHelper(GRID * TILE, GRID, 0x2a2218, 0x2a2218);
    grid.position.y = 0.01;
    this.scene.add(grid);
  }

  private makeCharacter(color: number, scale: number): THREE.Group {
    const g = new THREE.Group();
    const body = new THREE.Mesh(
      new THREE.CapsuleGeometry(0.28 * scale / 0.5, 0.55 * scale / 0.5, 4, 8),
      new THREE.MeshStandardMaterial({ color, roughness: 0.7 })
    );
    body.position.y = 0.7 * scale / 0.5 * 0.55;
    const head = new THREE.Mesh(
      new THREE.SphereGeometry(0.22 * scale / 0.5, 12, 12),
      new THREE.MeshStandardMaterial({ color: 0xe8d4b8 })
    );
    head.position.y = 1.15 * scale / 0.5 * 0.55;
    g.add(body, head);
    return g;
  }

  setPlayerPos(x: number, z: number): void {
    this.playerX = x;
    this.playerZ = z;
    this.playerMesh.position.set(x * TILE, 0, z * TILE);
    this.camera.position.set(x * TILE + 12, 14, z * TILE + 12);
    this.camera.lookAt(x * TILE, 0, z * TILE);
  }

  hideNpc(id: string, hide: boolean): void {
    const m = this.npcMeshes.get(id);
    if (m) m.visible = !hide;
  }

  private onResize(): void {
    const aspect = window.innerWidth / window.innerHeight;
    const frustum = 8;
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
    if (!this.pathTarget) return;
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
      return;
    }
    const step = Math.min(dist, this.moveSpeed * dt);
    pos.x += (dx / dist) * step;
    pos.z += (dz / dist) * step;
    this.playerX = pos.x / TILE;
    this.playerZ = pos.z / TILE;
    this.camera.position.set(pos.x + 12, 14, pos.z + 12);
    this.camera.lookAt(pos.x, 0, pos.z);
  }

  render(): void {
    this.renderer.render(this.scene, this.camera);
  }

  dispose(): void {
    this.renderer.dispose();
  }
}
