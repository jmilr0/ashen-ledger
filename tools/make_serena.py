"""Blender: Na Serena (Broken Seal) — hooded local noble/agent contact GLB + previews.

Hooded/local noble or agent; wax-and-mud elegance, no glow.
Dirt-and-mail Occitania 1208–10.
Rebuild:
  /usr/bin/blender -b -P tools/make_serena.py
"""
from __future__ import annotations
import math, os, sys
import bmesh
from mathutils import Matrix, Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import character_common as cc

TARGET_HEIGHT = 1.66
MAX_WIDTH = 0.54
P = 'Serena'


def make_gown(wool):
    """Fitted wool gown — local noble cut, earth tones, soft folds."""
    profile = [
        (0.66, 0.155, 0.120, 0.014),
        (0.80, 0.148, 0.114, 0.016),
        (0.94, 0.142, 0.108, 0.018),
        (1.08, 0.155, 0.118, 0.014),
        (1.20, 0.168, 0.128, 0.010),
        (1.28, 0.140, 0.108, 0.006),
        (1.34, 0.058, 0.052, 0.000),
    ]
    skirt = [
        (0.52, 0.175, 0.138, 0.020),
        (0.36, 0.190, 0.148, 0.022),
        (0.20, 0.185, 0.145, 0.018),
    ]
    return cc.make_lathe_body(f'{P}_Gown', wool, profile, segs=22, fold_amp=0.014,
                              fold_freq=6, skirt=skirt, hem_scale=1.04, subdiv=2)


def make_cloak(cloak_m):
    """Waxed travel cloak — mud elegance, open front, no glow."""
    bm = bmesh.new()
    u_segs, v_segs = 32, 14
    theta0, theta1 = math.radians(50), math.radians(310)
    grid = []
    for i in range(v_segs + 1):
        v = i / v_segs
        z = 1.36 - v * 1.08
        row = []
        for j in range(u_segs + 1):
            t = j / u_segs
            ang = theta0 + (theta1 - theta0) * t
            base = 0.180 + 0.090 * v
            fold = 0.020 * math.sin(t * math.tau * 4 + v * 5)
            hang = 0.012 * (v ** 2) * math.sin(ang * 2)
            r = base + fold + hang
            x = r * math.cos(ang)
            y = -0.025 - 0.05 * (1 - v) + r * math.sin(ang) * 0.86
            z_adj = z + 0.016 * abs(math.sin(ang)) * (1 - v)
            row.append(bm.verts.new((x, y, z_adj)))
        grid.append(row)
    for i in range(v_segs):
        for j in range(u_segs):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    for edge_j in (0, u_segs):
        for i in range(v_segs):
            a, b = grid[i][edge_j], grid[i + 1][edge_j]
            ai = bm.verts.new((a.co.x * 0.62, a.co.y * 0.42, a.co.z))
            bi = bm.verts.new((b.co.x * 0.62, b.co.y * 0.42, b.co.z))
            if edge_j == 0:
                bm.faces.new((a, b, bi, ai))
            else:
                bm.faces.new((a, ai, bi, b))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    for v in bm.verts:
        ang = math.atan2(v.co.y + 0.06, v.co.x)
        n = Vector((v.co.x, v.co.y + 0.06, 0))
        if n.length > 0.05:
            n.normalize()
            v.co += n * (0.007 * math.sin(ang * 5 + v.co.z * 6))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return cc.bm_to_object(f'{P}_Cloak', bm, cloak_m)


def make_hood(cloak_m):
    """Deep hood — noble/agent contact, face partly shadowed."""
    bm = bmesh.new()
    segs_u, segs_v = 20, 12
    grid = []
    for i in range(segs_v + 1):
        v = i / segs_v
        z = 1.56 - v * 0.30
        row = []
        for j in range(segs_u + 1):
            t = j / segs_u
            ang = math.radians(38) + math.radians(284) * t
            rx = 0.122 + 0.042 * v
            ry = 0.135 + 0.050 * v
            peak = 0.035 * (1 - v) * math.cos((t - 0.5) * math.pi)
            x = rx * math.cos(ang)
            y = -0.02 - 0.09 * v + ry * math.sin(ang) * 0.72 + peak
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for i in range(segs_v):
        for j in range(segs_u):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    crown = []
    for j in range(segs_u + 1):
        t = j / segs_u
        ang = math.radians(38) + math.radians(284) * t
        crown.append(bm.verts.new((0.078 * math.cos(ang), -0.015 + 0.055 * math.sin(ang), 1.58)))
    c = bm.verts.new((0, -0.01, 1.615))
    for j in range(segs_u):
        bm.faces.new((c, crown[j], crown[j + 1]))
        bm.faces.new((crown[j], grid[0][j], grid[0][j + 1], crown[j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    return cc.bm_to_object(f'{P}_Hood', bm, cloak_m)


def make_seal_pouch(leather, wax, cord):
    """Small sealed letter pouch — wax seal, mud-edged elegance, NO glow."""
    parts = []
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.070
        v.co.y *= 0.042
        v.co.z *= 0.095
        v.co += Vector((-0.175, 0.100, 0.90))
    cc.subdivide_bm(bm, 2)
    center = Vector((-0.175, 0.100, 0.90))
    for v in bm.verts:
        d = v.co - center
        if d.length > 1e-6:
            v.co += d.normalized() * 0.005
    parts.append(cc.bm_to_object('_pouch', bm, leather))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.075
        v.co.y *= 0.018
        v.co.z *= 0.050
        v.co += Vector((-0.175, 0.125, 0.950))
    parts.append(cc.bm_to_object('_flap', bm, leather))
    # dull wax seal
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.016)
    for v in bm.verts:
        v.co.y *= 0.45
        v.co.z *= 0.70
        v.co += Vector((-0.175, 0.145, 0.948))
    parts.append(cc.bm_to_object('_wax', bm, wax))
    # strap
    bm = bmesh.new()
    path, radii = [], []
    for i in range(14):
        t = i / 13
        x = -0.175 + 0.34 * t
        y = 0.10 - 0.04 * math.sin(t * math.pi)
        z = 0.92 + 0.40 * math.sin(min(t, 0.85) / 0.85 * math.pi * 0.5)
        if t > 0.85:
            z = 1.28 - (t - 0.85) / 0.15 * 0.10
        path.append(Vector((x, y, z)))
        radii.append(0.009)
    cc.tube(bm, path, radii, segs=8)
    parts.append(cc.bm_to_object('_strap', bm, leather))
    bm = bmesh.new()
    cc.tube(bm, [Vector((-0.195, 0.128, 0.93)), Vector((-0.175, 0.138, 0.92)),
                 Vector((-0.155, 0.128, 0.93))], [0.004] * 3, segs=5)
    parts.append(cc.bm_to_object('_cord', bm, cord))
    return cc.join_named(f'{P}_Pouch', parts)


def make_mud(mud):
    parts = []
    spots = [
        (0.09, 0.08, 0.04, 0.018),
        (-0.08, 0.09, 0.032, 0.015),
        (0.12, -0.04, 0.22, 0.014),
        (-0.14, 0.02, 0.20, 0.012),
        (0.16, 0.05, 0.45, 0.011),
        (-0.18, 0.03, 0.40, 0.010),
    ]
    for i, (x, y, z, r) in enumerate(spots):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=r)
        for v in bm.verts:
            v.co.z *= 0.45
            v.co.x *= 1.3
            v.co += Vector((x, y, z))
        parts.append(cc.bm_to_object(f'_mud{i}', bm, mud))
    return cc.join_named(f'{P}_Mud', parts)


def build():
    cc.clear_scene()
    skin = cc.mat(f'{P}_Skin', (0.76, 0.58, 0.48), 0.52, specular=0.40)
    wool = cc.mat(f'{P}_Wool', (0.34, 0.30, 0.28), 0.88, specular=0.16)  # muted plum-earth
    cloak_m = cc.mat(f'{P}_Cloak', (0.22, 0.24, 0.22), 0.92, specular=0.12)
    leather = cc.mat(f'{P}_Leather', (0.22, 0.14, 0.09), 0.84)
    hair_m = cc.mat(f'{P}_Hair', (0.14, 0.08, 0.05), 0.74)
    brow_m = cc.mat(f'{P}_Brow', (0.10, 0.06, 0.04), 0.80)
    hose = cc.mat(f'{P}_Hose', (0.28, 0.24, 0.22), 0.86)
    boots = cc.mat(f'{P}_Boots', (0.12, 0.09, 0.06), 0.92)
    wax = cc.mat(f'{P}_Wax', (0.45, 0.16, 0.12), 0.72, specular=0.20)
    cord = cc.mat(f'{P}_Cord', (0.48, 0.40, 0.28), 0.88)
    mud = cc.mat(f'{P}_Mud', (0.28, 0.22, 0.14), 0.97, specular=0.05)

    meshes = [
        make_gown(wool),
        make_cloak(cloak_m),
        make_hood(cloak_m),
        cc.make_head(P, skin, hair_m, brow_m, hair_style='lean'),
        cc.make_belt(P, leather, rx=0.150, ry=0.112, z0=0.855, z1=0.895),
        make_seal_pouch(leather, wax, cord),
        make_mud(mud),
        cc.make_limbs(P, wool, skin, hose, boots, build='lean', bare_forearms=True),
    ]
    return cc.finish_character(
        'serena', meshes, f'{P}_Armature', TARGET_HEIGHT, MAX_WIDTH,
        look_note='Na Serena: hooded local noble/agent, muted wool gown, wax-and-mud cloak+hood, sealed pouch — elegance without glow',
    )


if __name__ == '__main__':
    build()
