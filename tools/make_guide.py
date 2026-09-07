"""Blender: The Guide (Broken Seal) — mountain/draille guide GLB + previews.

Travel cloak, satchel, staff + knife, lean stealthy read. Dirt-and-mail Occitania.
Rebuild:
  /usr/bin/blender -b -P tools/make_guide.py
"""
from __future__ import annotations
import math, os, sys
import bmesh
from mathutils import Matrix, Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import character_common as cc

TARGET_HEIGHT = 1.72
MAX_WIDTH = 0.54
P = 'Guide'


def make_tunic(wool):
    profile = [
        (0.70, 0.155, 0.120, 0.010),
        (0.84, 0.148, 0.115, 0.012),
        (0.98, 0.140, 0.108, 0.014),
        (1.12, 0.150, 0.115, 0.012),
        (1.24, 0.160, 0.122, 0.008),
        (1.32, 0.135, 0.105, 0.005),
        (1.38, 0.058, 0.052, 0.000),
    ]
    skirt = [
        (0.55, 0.160, 0.125, 0.014),
        (0.42, 0.150, 0.118, 0.012),
        (0.30, 0.138, 0.108, 0.010),
    ]
    return cc.make_lathe_body(f'{P}_Tunic', wool, profile, segs=20, fold_amp=0.010,
                              fold_freq=5, skirt=skirt, hem_scale=1.02, subdiv=1)


def make_cloak(cloak_m):
    bm = bmesh.new()
    u_segs, v_segs = 32, 14
    theta0, theta1 = math.radians(55), math.radians(305)
    grid = []
    for i in range(v_segs + 1):
        v = i / v_segs
        z = 1.36 - v * 1.05
        row = []
        for j in range(u_segs + 1):
            t = j / u_segs
            ang = theta0 + (theta1 - theta0) * t
            base = 0.175 + 0.08 * v
            fold = 0.020 * math.sin(t * math.tau * 4 + v * 5)
            r = base + fold
            x = r * math.cos(ang)
            y = -0.04 - 0.06 * (1 - v) + r * math.sin(ang) * 0.85
            z_adj = z + 0.02 * abs(math.sin(ang)) * (1 - v)
            row.append(bm.verts.new((x, y, z_adj)))
        grid.append(row)
    for i in range(v_segs):
        for j in range(u_segs):
            bm.faces.new((grid[i][j], grid[i][j+1], grid[i+1][j+1], grid[i+1][j]))
    for edge_j in (0, u_segs):
        for i in range(v_segs):
            a, b = grid[i][edge_j], grid[i+1][edge_j]
            ai = bm.verts.new((a.co.x*0.65, a.co.y*0.45, a.co.z))
            bi = bm.verts.new((b.co.x*0.65, b.co.y*0.45, b.co.z))
            if edge_j == 0:
                bm.faces.new((a, b, bi, ai))
            else:
                bm.faces.new((a, ai, bi, b))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    for v in bm.verts:
        ang = math.atan2(v.co.y + 0.08, v.co.x)
        n = Vector((v.co.x, v.co.y + 0.08, 0))
        if n.length > 0.05:
            n.normalize()
            v.co += n * (0.007 * math.sin(ang * 5 + v.co.z * 6))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return cc.bm_to_object(f'{P}_Cloak', bm, cloak_m)


def make_hood(cloak_m):
    bm = bmesh.new()
    segs_u, segs_v = 18, 10
    grid = []
    for i in range(segs_v + 1):
        v = i / segs_v
        z = 1.55 - v * 0.28
        row = []
        for j in range(segs_u + 1):
            t = j / segs_u
            ang = math.radians(40) + math.radians(280) * t
            rx = 0.12 + 0.04 * v
            ry = 0.13 + 0.05 * v
            x = rx * math.cos(ang)
            y = -0.05 - 0.08 * v + ry * math.sin(ang) * 0.7
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for i in range(segs_v):
        for j in range(segs_u):
            bm.faces.new((grid[i][j], grid[i][j+1], grid[i+1][j+1], grid[i+1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    return cc.bm_to_object(f'{P}_Hood', bm, cloak_m)


def make_satchel(leather):
    parts = []
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.070; v.co.y *= 0.045; v.co.z *= 0.100
        v.co += Vector((0.195, 0.08, 0.90))
    cc.subdivide_bm(bm, 2)
    center = Vector((0.195, 0.08, 0.90))
    for v in bm.verts:
        d = v.co - center
        if d.length > 1e-6:
            v.co += d.normalized() * 0.008
    parts.append(cc.bm_to_object('_bag', bm, leather))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.075; v.co.y *= 0.020; v.co.z *= 0.055
        v.co += Vector((0.195, 0.110, 0.955))
    parts.append(cc.bm_to_object('_flap', bm, leather))
    bm = bmesh.new()
    path, radii = [], []
    for i in range(14):
        t = i / 13
        x = 0.195 - 0.32 * t
        y = 0.08 - 0.04 * math.sin(t * math.pi)
        z = 0.92 + 0.40 * math.sin(min(t, 0.85) / 0.85 * math.pi * 0.5)
        if t > 0.85:
            z = 1.28 - (t - 0.85) / 0.15 * 0.12
        path.append(Vector((x, y, z)))
        radii.append(0.010)
    cc.tube(bm, path, radii, segs=8)
    parts.append(cc.bm_to_object('_strap', bm, leather))
    return cc.join_named(f'{P}_Satchel', parts)


def make_staff(wood):
    bm = bmesh.new()
    path, radii = [], []
    for i in range(20):
        t = i / 19
        z = 0.02 + t * 1.55
        x = -0.22 - 0.02 * (t if t > 0.7 else 0)
        y = 0.05 + 0.015 * math.sin(t * math.pi)
        path.append(Vector((x, y, z)))
        radii.append(0.015 - 0.003 * t)
    cc.tube(bm, path, radii, segs=10)
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=8, radius=0.024,
                              matrix=Matrix.Translation((-0.24, 0.055, 1.58)))
    return cc.bm_to_object(f'{P}_Staff', bm, wood)


def make_knife(leather, iron):
    parts = []
    bm = bmesh.new()
    cc.tube(bm, [Vector((-0.08, 0.14, 0.92)), Vector((-0.08, 0.145, 0.78))], [0.011, 0.009], segs=8)
    parts.append(cc.bm_to_object('_scab', bm, leather))
    bm = bmesh.new()
    cc.tube(bm, [Vector((-0.08, 0.145, 0.93)), Vector((-0.08, 0.145, 0.98))], [0.007, 0.003], segs=6)
    parts.append(cc.bm_to_object('_blade', bm, iron))
    return cc.join_named(f'{P}_Knife', parts)


def build():
    cc.clear_scene()
    skin = cc.mat(f'{P}_Skin', (0.70, 0.52, 0.40), 0.58, specular=0.35)
    wool = cc.mat(f'{P}_Wool', (0.32, 0.30, 0.26), 0.88, specular=0.15)
    cloak_m = cc.mat(f'{P}_Cloak', (0.22, 0.24, 0.20), 0.92, specular=0.10)
    leather = cc.mat(f'{P}_Leather', (0.18, 0.12, 0.08), 0.85)
    hair_m = cc.mat(f'{P}_Hair', (0.10, 0.08, 0.06), 0.75)
    brow_m = cc.mat(f'{P}_Brow', (0.08, 0.06, 0.05), 0.8)
    wood = cc.mat(f'{P}_Wood', (0.36, 0.25, 0.14), 0.80)
    iron = cc.mat(f'{P}_Iron', (0.30, 0.30, 0.28), 0.55, metallic=0.55)
    hose = cc.mat(f'{P}_Hose', (0.25, 0.22, 0.18), 0.85)
    boots = cc.mat(f'{P}_Boots', (0.10, 0.08, 0.06), 0.92)
    meshes = [
        make_tunic(wool),
        make_cloak(cloak_m),
        make_hood(cloak_m),
        cc.make_head(P, skin, hair_m, brow_m, hair_style='lean'),
        cc.make_belt(P, leather, rx=0.155, ry=0.115),
        make_satchel(leather),
        make_staff(wood),
        make_knife(leather, iron),
        cc.make_limbs(P, wool, skin, hose, boots, build='lean', bare_forearms=True),
    ]
    return cc.finish_character('guide', meshes, f'{P}_Armature', TARGET_HEIGHT, MAX_WIDTH,
        look_note='Draille guide: lean build, green-grey travel cloak+hood, satchel, staff, belt knife')


if __name__ == '__main__':
    build()
