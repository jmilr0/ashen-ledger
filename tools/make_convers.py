"""Blender: The Convers (Broken Seal) — abbey lay brother GLB + previews.

Wool habit/tunic, keys on belt, short cudgel, barn-practical silhouette.
Rebuild:
  /usr/bin/blender -b -P tools/make_convers.py
"""
from __future__ import annotations
import math, os, sys
import bmesh
from mathutils import Matrix, Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import character_common as cc

TARGET_HEIGHT = 1.74
MAX_WIDTH = 0.56
P = 'Convers'


def make_habit(wool):
    profile = [
        (0.68, 0.185, 0.145, 0.016),
        (0.82, 0.175, 0.138, 0.018),
        (0.98, 0.165, 0.128, 0.020),
        (1.12, 0.175, 0.135, 0.016),
        (1.26, 0.188, 0.142, 0.012),
        (1.34, 0.155, 0.120, 0.008),
        (1.40, 0.065, 0.060, 0.000),
    ]
    skirt = [
        (0.52, 0.200, 0.155, 0.022),
        (0.36, 0.210, 0.162, 0.024),
        (0.22, 0.195, 0.150, 0.018),
    ]
    return cc.make_lathe_body(f'{P}_Habit', wool, profile, segs=22, fold_amp=0.014,
                              fold_freq=6, skirt=skirt, hem_scale=1.04, subdiv=2)


def make_scapular(scap):
    bm = bmesh.new()
    u_segs, v_segs = 12, 18
    for front in (1, -1):
        grid = []
        for i in range(v_segs + 1):
            v = i / v_segs
            z = 1.38 - v * 1.10
            w = 0.095 + 0.025 * v
            row = []
            for j in range(u_segs + 1):
                t = j / u_segs
                x = (t - 0.5) * 2 * w
                y = front * (0.145 + 0.02 * v + 0.01 * math.sin(t * math.pi * 2 + v * 4))
                fold = 0.008 * math.sin(t * math.pi * 3 + z * 5)
                row.append(bm.verts.new((x, y + fold, z)))
            grid.append(row)
        for i in range(v_segs):
            for j in range(u_segs):
                if front > 0:
                    bm.faces.new((grid[i][j], grid[i][j+1], grid[i+1][j+1], grid[i+1][j]))
                else:
                    bm.faces.new((grid[i][j], grid[i+1][j], grid[i+1][j+1], grid[i][j+1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    return cc.bm_to_object(f'{P}_Scapular', bm, scap)


def make_keys(iron, leather):
    parts = []
    bm = bmesh.new()
    segs = 16
    path = [Vector((0.14 + 0.028*math.cos(a), 0.148, 0.88 + 0.028*math.sin(a))) for a in
            [(i/segs)*math.tau for i in range(segs+1)]]
    cc.tube(bm, path, [0.005]*(segs+1), segs=6, close_caps=False)
    parts.append(cc.bm_to_object('_ring', bm, iron))
    for i, (ox, oz) in enumerate(((0.14, 0.84), (0.155, 0.82), (0.125, 0.81))):
        bm = bmesh.new()
        cc.tube(bm, [Vector((ox, 0.15, oz+0.06)), Vector((ox, 0.15, oz))], [0.006, 0.005], segs=6)
        parts.append(cc.bm_to_object(f'_keyshaft{i}', bm, iron))
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= 0.018; v.co.y *= 0.006; v.co.z *= 0.012
            v.co += Vector((ox + 0.012, 0.15, oz))
        parts.append(cc.bm_to_object(f'_keybit{i}', bm, iron))
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.012,
                                  matrix=Matrix.Translation((ox, 0.15, oz+0.07)))
        parts.append(cc.bm_to_object(f'_keybow{i}', bm, iron))
    bm = bmesh.new()
    cc.tube(bm, [Vector((0.08, 0.13, 0.90)), Vector((0.12, 0.145, 0.89)), Vector((0.14, 0.148, 0.88))],
            [0.004, 0.004, 0.004], segs=5)
    parts.append(cc.bm_to_object('_thong', bm, leather))
    return cc.join_named(f'{P}_Keys', parts)


def make_cudgel(wood):
    bm = bmesh.new()
    path, radii = [], []
    for i in range(16):
        t = i / 15
        z = 0.55 + t * 0.55
        x = 0.26 + 0.01 * math.sin(t * 3)
        path.append(Vector((x, 0.05, z)))
        radii.append(0.022 + 0.018 * (t ** 1.5))
    cc.tube(bm, path, radii, segs=12)
    cc.subdivide_bm(bm, 1)
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.038,
                              matrix=Matrix.Translation((0.27, 0.05, 1.12)))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return cc.bm_to_object(f'{P}_Cudgel', bm, wood)


def make_rope_belt(hemp):
    bm = bmesh.new()
    segs = 28
    z = 0.88
    path = [Vector((0.175 * math.cos(a), 0.135 * math.sin(a), z + 0.01 * math.sin(a * 3)))
            for a in [(j/segs)*math.tau for j in range(segs+1)]]
    cc.tube(bm, path, [0.014]*(segs+1), segs=8, close_caps=False)
    cc.tube(bm, [Vector((0.05, 0.14, 0.88)), Vector((0.04, 0.15, 0.70)), Vector((0.035, 0.15, 0.55))],
            [0.012, 0.011, 0.010], segs=6)
    return cc.bm_to_object(f'{P}_RopeBelt', bm, hemp)


def build():
    cc.clear_scene()
    skin = cc.mat(f'{P}_Skin', (0.76, 0.58, 0.46), 0.55, specular=0.4)
    wool = cc.mat(f'{P}_Wool', (0.48, 0.44, 0.36), 0.92, specular=0.12)
    scap = cc.mat(f'{P}_Scapular', (0.40, 0.36, 0.30), 0.90, specular=0.12)
    leather = cc.mat(f'{P}_Leather', (0.20, 0.13, 0.08), 0.82)
    hair_m = cc.mat(f'{P}_Hair', (0.22, 0.16, 0.10), 0.75)
    brow_m = cc.mat(f'{P}_Brow', (0.16, 0.11, 0.07), 0.8)
    wood = cc.mat(f'{P}_Wood', (0.35, 0.24, 0.13), 0.80)
    iron = cc.mat(f'{P}_Iron', (0.35, 0.34, 0.32), 0.50, metallic=0.6, specular=0.4)
    hose = cc.mat(f'{P}_Hose', (0.32, 0.28, 0.22), 0.85)
    boots = cc.mat(f'{P}_Boots', (0.14, 0.10, 0.08), 0.9)
    hemp = cc.mat(f'{P}_Hemp', (0.55, 0.48, 0.32), 0.88)
    meshes = [
        make_habit(wool),
        make_scapular(scap),
        cc.make_head(P, skin, hair_m, brow_m, hair_style='tonsure'),
        make_rope_belt(hemp),
        make_keys(iron, leather),
        make_cudgel(wood),
        cc.make_limbs(P, wool, skin, hose, boots, build='broad', bare_forearms=True),
    ]
    return cc.finish_character('convers', meshes, f'{P}_Armature', TARGET_HEIGHT, MAX_WIDTH,
        look_note='Abbey lay brother: undyed wool habit+scapular, tonsure, rope belt, iron keys, short cudgel')


if __name__ == '__main__':
    build()
