import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

const loader = new GLTFLoader();
const cache = new Map<string, THREE.Group>();

/** Load a GLB once; returns a cloned Group (safe to place many times). */
export async function loadModel(url: string): Promise<THREE.Group | null> {
  try {
    let proto = cache.get(url);
    if (!proto) {
      const gltf = await loader.loadAsync(url);
      proto = gltf.scene;
      proto.traverse((obj) => {
        const m = obj as THREE.Mesh;
        if (m.isMesh) {
          m.castShadow = true;
          m.receiveShadow = true;
          const mat = m.material;
          if (mat && !Array.isArray(mat) && (mat as THREE.MeshStandardMaterial).isMeshStandardMaterial) {
            const sm = mat as THREE.MeshStandardMaterial;
            sm.roughness = Math.min(1, (sm.roughness ?? 0.7) + 0.05);
            sm.envMapIntensity = 0.6;
          }
        }
      });
      cache.set(url, proto);
    }
    return proto.clone(true);
  } catch (err) {
    console.warn('Failed to load model', url, err);
    return null;
  }
}

export function fitToHeight(root: THREE.Object3D, height: number): void {
  const box = new THREE.Box3().setFromObject(root);
  const size = new THREE.Vector3();
  box.getSize(size);
  if (size.y < 1e-4) return;
  const s = height / size.y;
  root.scale.multiplyScalar(s);
  // sit on ground (y=0)
  const after = new THREE.Box3().setFromObject(root);
  root.position.y -= after.min.y;
}

export function tintMeshes(root: THREE.Object3D, color: number, strength = 0.35): void {
  const tint = new THREE.Color(color);
  root.traverse((obj) => {
    const m = obj as THREE.Mesh;
    if (!m.isMesh) return;
    const mats = Array.isArray(m.material) ? m.material : [m.material];
    for (const mat of mats) {
      if (!mat || !(mat as THREE.MeshStandardMaterial).color) continue;
      const sm = (mat as THREE.MeshStandardMaterial).clone();
      sm.color.lerp(tint, strength);
      m.material = sm;
    }
  });
}
