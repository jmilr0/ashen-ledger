import * as THREE from 'three';

/** Same threshold as FACE_MOVE_EPS — walk vs idle. */
export const LOCO_MOVE_EPS = 0.15;

export type LocoState = {
  mixer?: THREE.AnimationMixer;
  walk?: THREE.AnimationAction;
  idle?: THREE.AnimationAction;
  current: 'walk' | 'idle' | 'none';
  baseY: number;
  phase: number;
  rest: Array<{ obj: THREE.Object3D; x: number; y: number; z: number }>;
};

function findNamed(root: THREE.Object3D, names: string[]): THREE.Object3D | null {
  const want = new Set(names);
  let found: THREE.Object3D | null = null;
  root.traverse((o) => {
    if (found || !want.has(o.name)) return;
    found = o;
  });
  return found;
}

function collectStrideTargets(root: THREE.Object3D): THREE.Object3D[] {
  const pairs: Array<[string, string[]]> = [
    ['thighL', ['Thigh_L', 'Clerk_ThighL', 'leg_L']],
    ['thighR', ['Thigh_R', 'Clerk_ThighR', 'leg_R']],
    ['calfL', ['Calf_L', 'Clerk_CalfL']],
    ['calfR', ['Calf_R', 'Clerk_CalfR']],
    ['footL', ['Foot_L']],
    ['footR', ['Foot_R']],
  ];
  const out: THREE.Object3D[] = [];
  for (const [, names] of pairs) {
    const n = findNamed(root, names);
    if (n) out.push(n);
  }
  return out;
}

/** Bind Walk/Idle mixers when Art clips exist; else stride-bob targets. */
export function bindLoco(mesh: THREE.Object3D, clips: THREE.AnimationClip[]): LocoState {
  unbindLoco(mesh);
  const walkClip = clips.find((c) => c.name === 'Walk');
  const idleClip = clips.find((c) => c.name === 'Idle');
  const state: LocoState = {
    current: 'none',
    baseY: mesh.position.y,
    phase: 0,
    rest: [],
  };
  if (walkClip || idleClip) {
    const mixer = new THREE.AnimationMixer(mesh);
    state.mixer = mixer;
    if (walkClip) {
      state.walk = mixer.clipAction(walkClip);
      state.walk.setLoop(THREE.LoopRepeat, Infinity);
      state.walk.clampWhenFinished = false;
    }
    if (idleClip) {
      state.idle = mixer.clipAction(idleClip);
      state.idle.setLoop(THREE.LoopRepeat, Infinity);
      state.idle.clampWhenFinished = false;
      state.idle.play();
      state.current = 'idle';
    }
  } else {
    for (const obj of collectStrideTargets(mesh)) {
      state.rest.push({ obj, x: obj.rotation.x, y: obj.rotation.y, z: obj.rotation.z });
    }
  }
  mesh.userData.loco = state;
  mesh.userData.isMoving = false;
  mesh.userData.moveSpeed = 0;
  mesh.userData.facingYaw = mesh.rotation.y;
  return state;
}

export function unbindLoco(mesh: THREE.Object3D): void {
  const prev = mesh.userData.loco as LocoState | undefined;
  prev?.mixer?.stopAllAction();
  mesh.userData.loco = undefined;
}

export function rememberBaseY(mesh: THREE.Object3D): void {
  const loco = mesh.userData.loco as LocoState | undefined;
  if (loco) loco.baseY = mesh.position.y;
}

/** Drive Walk/Idle or procedural stride from horizontal speed (m/s). */
export function tickLoco(
  mesh: THREE.Object3D,
  speed: number,
  dt: number,
  nominalSpeed = 4.5
): void {
  const loco = mesh.userData.loco as LocoState | undefined;
  if (!loco) return;
  const moving = speed >= LOCO_MOVE_EPS;
  mesh.userData.isMoving = moving;
  mesh.userData.moveSpeed = speed;
  mesh.userData.facingYaw = mesh.rotation.y;

  if (loco.mixer && (loco.walk || loco.idle)) {
    const want: LocoState['current'] =
      moving && loco.walk ? 'walk' : loco.idle ? 'idle' : moving ? 'walk' : 'none';
    if (want !== loco.current) {
      const next = want === 'walk' ? loco.walk : want === 'idle' ? loco.idle : undefined;
      const prev =
        loco.current === 'walk' ? loco.walk : loco.current === 'idle' ? loco.idle : undefined;
      if (next) {
        next.enabled = true;
        next.setEffectiveWeight(1);
        if (prev && prev !== next) {
          next.play();
          prev.crossFadeTo(next, 0.18, false);
        } else {
          next.reset().play();
        }
      } else if (prev) {
        prev.fadeOut(0.12);
      }
      loco.current = want;
    }
    if (loco.walk && loco.current === 'walk') {
      const scale = Math.max(0.65, Math.min(1.35, speed / Math.max(0.5, nominalSpeed)));
      loco.walk.setEffectiveTimeScale(scale);
    }
    loco.mixer.update(dt);
    mesh.position.y = loco.baseY;
    return;
  }

  // No Art clips yet — tiny stride so the party does not read as ice-skate.
  const dtC = Math.max(0.001, dt);
  if (moving) {
    const cadence = 7.2 * Math.max(0.55, speed / Math.max(0.5, nominalSpeed));
    loco.phase += dtC * cadence;
    const swing = Math.sin(loco.phase * Math.PI * 2);
    const bob = Math.abs(Math.sin(loco.phase * Math.PI)) * 0.042;
    mesh.position.y = loco.baseY + bob;
    mesh.rotation.z = THREE.MathUtils.damp(mesh.rotation.z, swing * 0.03, 10, dtC);
    for (const r of loco.rest) {
      const name = r.obj.name;
      const left = /L$|_L$|ThighL|CalfL|leg_L/.test(name);
      const side = left ? 1 : -1;
      if (/Thigh|leg_/.test(name)) {
        r.obj.rotation.x = r.x + swing * side * 0.55;
      } else if (/Calf/.test(name)) {
        r.obj.rotation.x = r.x + Math.max(0, -swing * side) * 0.35;
      } else if (/Foot/.test(name)) {
        r.obj.rotation.x = r.x + swing * side * 0.18;
      }
    }
  } else {
    loco.phase = 0;
    mesh.position.y = THREE.MathUtils.damp(mesh.position.y, loco.baseY, 14, dtC);
    mesh.rotation.z = THREE.MathUtils.damp(mesh.rotation.z, 0, 12, dtC);
    for (const r of loco.rest) {
      r.obj.rotation.x = THREE.MathUtils.damp(r.obj.rotation.x, r.x, 12, dtC);
      r.obj.rotation.y = THREE.MathUtils.damp(r.obj.rotation.y, r.y, 12, dtC);
      r.obj.rotation.z = THREE.MathUtils.damp(r.obj.rotation.z, r.z, 12, dtC);
    }
  }
}
