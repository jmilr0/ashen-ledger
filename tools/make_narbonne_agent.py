"""Blender: Narbonne Agent / hooded courier (Broken Seal) — GLB + previews.

Hooded city courier: wax and mud, travel cloak, sealed letter pouch — NO glow.
Same hero quality as party companions. Dirt-and-mail Occitania 1208.
Rebuild:
  /usr/bin/blender -b -P tools/make_narbonne_agent.py
"""
from __future__ import annotations
import math, os, sys
import bmesh
from mathutils import Matrix, Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import character_common as cc

TARGET_HEIGHT = 1.73
MAX_WIDTH = 0.55
P = 'Narbonne'


def make_tunic(wool):
    profile = [
        (0.70, 0.165, 0.125, 0.012),
        (0.84, 0.158, 0.120, 0.014),
        (0.98, 0.150, 0.112, 0.016),
        (1.12, 0.160, 0.120, 0.014),
        (1.24, 0.170, 0.128, 0.010),
        (1.32, 0.145, 0.110, 0.006),
        (1.38, 0.060, 0.055, 0.000),
    ]
    skirt = [
        (0.55, 0.175, 0.135, 0.016),
        (0.42, 0.168, 0.130, 0.014),
        (0.28, 0.155, 0.120, 0.012),
    ]
    return cc.make_lathe_body(f'{P}_Tunic', wool, profile, segs=20, fold_amp=0.011,
                              fold_freq=5, skirt=skirt, hem_scale=1.03, subdiv=1)


def make_cloak(cloak_m):
    """Heavy travel cloak — waxed/mud-stained road look, open at front."""
    bm = bmesh.new()
    u_segs, v_segs = 34, 16
    theta0, theta1 = math.radians(48), math.radians(312)
    grid = []
    for i in range(v_segs + 1):
        v = i / v_segs
        z = 1.38 - v * 1.10
        row = []
        for j in range(u_segs + 1):
            t = j / u_segs
            ang = theta0 + (theta1 - theta0) * t
            base = 0.185 + 0.095 * v
            fold = 0.022 * math.sin(t * math.tau * 4.5 + v * 6)
            # mud-weight hang at hem
            hang = 0.015 * (v ** 2) * math.sin(ang * 2)
            r = base + fold + hang
            x = r * math.cos(ang)
            y = -0.03 - 0.05 * (1 - v) + r * math.sin(ang) * 0.88
            z_adj = z + 0.018 * abs(math.sin(ang)) * (1 - v) - 0.01 * v
            row.append(bm.verts.new((x, y, z_adj)))
        grid.append(row)
    for i in range(v_segs):
        for j in range(u_segs):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    # inner facing on cloak edges
    for edge_j in (0, u_segs):
        for i in range(v_segs):
            a, b = grid[i][edge_j], grid[i + 1][edge_j]
            ai = bm.verts.new((a.co.x * 0.62, a.co.y * 0.40, a.co.z))
            bi = bm.verts.new((b.co.x * 0.62, b.co.y * 0.40, b.co.z))
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
            v.co += n * (0.008 * math.sin(ang * 5 + v.co.z * 7))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return cc.bm_to_object(f'{P}_Cloak', bm, cloak_m)


def make_hood(cloak_m):
    """Deep courier hood — face partly shadowed, no glow."""
    bm = bmesh.new()
    segs_u, segs_v = 20, 12
    grid = []
    for i in range(segs_v + 1):
        v = i / segs_v
        z = 1.58 - v * 0.32
        row = []
        for j in range(segs_u + 1):
            t = j / segs_u
            ang = math.radians(35) + math.radians(290) * t
            rx = 0.125 + 0.045 * v
            ry = 0.140 + 0.055 * v
            # pull forward peak of hood
            peak = 0.04 * (1 - v) * math.cos((t - 0.5) * math.pi)
            x = rx * math.cos(ang)
            y = -0.02 - 0.10 * v + ry * math.sin(ang) * 0.72 + peak
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for i in range(segs_v):
        for j in range(segs_u):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    # hood crown fill
    crown = []
    for j in range(segs_u + 1):
        t = j / segs_u
        ang = math.radians(35) + math.radians(290) * t
        crown.append(bm.verts.new((0.08 * math.cos(ang), -0.02 + 0.06 * math.sin(ang), 1.60)))
    c = bm.verts.new((0, -0.01, 1.635))
    for j in range(segs_u):
        bm.faces.new((c, crown[j], crown[j + 1]))
        bm.faces.new((crown[j], grid[0][j], grid[0][j + 1], crown[j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    return cc.bm_to_object(f'{P}_Hood', bm, cloak_m)


def make_letter_pouch(leather, wax, cord):
    """Sealed letter pouch — wax seal on flap, mud on edges. NO glow."""
    parts = []
    # Main pouch body
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.085
        v.co.y *= 0.050
        v.co.z *= 0.115
        v.co += Vector((-0.195, 0.095, 0.92))
    cc.subdivide_bm(bm, 2)
    center = Vector((-0.195, 0.095, 0.92))
    for v in bm.verts:
        d = v.co - center
        if d.length > 1e-6:
            v.co += d.normalized() * 0.006
    parts.append(cc.bm_to_object('_pouch', bm, leather))

    # Flap
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.090
        v.co.y *= 0.022
        v.co.z *= 0.060
        v.co += Vector((-0.195, 0.125, 0.980))
    parts.append(cc.bm_to_object('_flap', bm, leather))

    # Dull red/brown wax seal blob on flap — matte, no emission
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.018)
    for v in bm.verts:
        v.co.y *= 0.45
        v.co.z *= 0.70
        v.co += Vector((-0.195, 0.148, 0.975))
    parts.append(cc.bm_to_object('_wax', bm, wax))

    # Tiny impressed mark on wax (cross / key — readable, not glowing)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.006
        v.co.y *= 0.004
        v.co.z *= 0.010
        v.co += Vector((-0.195, 0.155, 0.978))
    parts.append(cc.bm_to_object('_waxmark_v', bm, wax))
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    for v in bm.verts:
        v.co.x *= 0.010
        v.co.y *= 0.004
        v.co.z *= 0.005
        v.co += Vector((-0.195, 0.155, 0.978))
    parts.append(cc.bm_to_object('_waxmark_h', bm, wax))

    # Shoulder strap
    bm = bmesh.new()
    path, radii = [], []
    for i in range(16):
        t = i / 15
        x = -0.195 + 0.36 * t
        y = 0.095 - 0.05 * math.sin(t * math.pi)
        z = 0.94 + 0.42 * math.sin(min(t, 0.88) / 0.88 * math.pi * 0.5)
        if t > 0.88:
            z = 1.30 - (t - 0.88) / 0.12 * 0.10
        path.append(Vector((x, y, z)))
        radii.append(0.011)
    cc.tube(bm, path, radii, segs=8)
    parts.append(cc.bm_to_object('_strap', bm, leather))

    # Cord tie under flap
    bm = bmesh.new()
    path = [
        Vector((-0.22, 0.130, 0.95)),
        Vector((-0.195, 0.140, 0.94)),
        Vector((-0.17, 0.130, 0.95)),
    ]
    cc.tube(bm, path, [0.005, 0.005, 0.005], segs=6)
    parts.append(cc.bm_to_object('_cord', bm, cord))

    return cc.join_named(f'{P}_Pouch', parts)


def make_mud_spatters(mud):
    """Mud spatters on boots/cloak hem — road grit, not FX."""
    parts = []
    spots = [
        (0.10, 0.08, 0.04, 0.022),
        (-0.09, 0.10, 0.035, 0.018),
        (0.14, -0.05, 0.25, 0.016),
        (-0.16, 0.02, 0.22, 0.014),
        (0.05, 0.12, 0.32, 0.012),
        (-0.12, -0.08, 0.15, 0.015),
        (0.18, 0.06, 0.55, 0.012),
        (-0.20, 0.04, 0.48, 0.011),
    ]
    for i, (x, y, z, r) in enumerate(spots):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=r)
        for v in bm.verts:
            v.co.z *= 0.45
            v.co.x *= 1.35
            v.co += Vector((x, y, z))
        parts.append(cc.bm_to_object(f'_mud{i}', bm, mud))
    return cc.join_named(f'{P}_Mud', parts)


def make_side_knife(leather, iron):
    """Small utility knife — courier, not soldier."""
    parts = []
    bm = bmesh.new()
    cc.tube(bm, [Vector((0.12, 0.14, 0.90)), Vector((0.12, 0.145, 0.78))],
            [0.012, 0.010], segs=8)
    parts.append(cc.bm_to_object('_scab', bm, leather))
    bm = bmesh.new()
    cc.tube(bm, [Vector((0.12, 0.145, 0.91)), Vector((0.12, 0.145, 0.96))],
            [0.007, 0.003], segs=6)
    parts.append(cc.bm_to_object('_blade', bm, iron))
    return cc.join_named(f'{P}_Knife', parts)


def make_travel_scroll_tube(leather, wood):
    """Secondary message tube on belt — sealed courier kit."""
    parts = []
    bm = bmesh.new()
    cc.tube(bm, [Vector((0.18, 0.05, 0.88)), Vector((0.18, 0.05, 1.02))],
            [0.022, 0.022], segs=12)
    parts.append(cc.bm_to_object('_tube', bm, leather))
    # Cap
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=10, v_segments=6, radius=0.024,
                              matrix=Matrix.Translation((0.18, 0.05, 1.035)))
    for v in bm.verts:
        if v.co.z < 1.02:
            v.co.z = 1.02
    parts.append(cc.bm_to_object('_cap', bm, wood))
    # Strap loop
    bm = bmesh.new()
    cc.tube(bm, [Vector((0.16, 0.05, 0.90)), Vector((0.14, 0.08, 0.89)),
                 Vector((0.12, 0.10, 0.885))], [0.005, 0.005, 0.005], segs=5)
    parts.append(cc.bm_to_object('_tloop', bm, leather))
    return cc.join_named(f'{P}_Tube', parts)


def build():
    cc.clear_scene()
    # Weathered road courier palette — muted, muddy, no fantasy accents
    skin = cc.mat(f'{P}_Skin', (0.68, 0.50, 0.38), 0.60, specular=0.32)
    wool = cc.mat(f'{P}_Wool', (0.38, 0.34, 0.28), 0.90, specular=0.14)
    cloak_m = cc.mat(f'{P}_Cloak', (0.26, 0.24, 0.20), 0.93, specular=0.10)
    leather = cc.mat(f'{P}_Leather', (0.20, 0.13, 0.08), 0.86)
    hair_m = cc.mat(f'{P}_Hair', (0.12, 0.09, 0.06), 0.78)
    brow_m = cc.mat(f'{P}_Brow', (0.09, 0.07, 0.05), 0.82)
    iron = cc.mat(f'{P}_Iron', (0.32, 0.30, 0.28), 0.55, metallic=0.50)
    hose = cc.mat(f'{P}_Hose', (0.28, 0.24, 0.18), 0.88)
    boots = cc.mat(f'{P}_Boots', (0.12, 0.09, 0.06), 0.94)
    wax = cc.mat(f'{P}_Wax', (0.48, 0.18, 0.14), 0.70, specular=0.22)
    cord = cc.mat(f'{P}_Cord', (0.50, 0.42, 0.28), 0.88)
    mud = cc.mat(f'{P}_Mud', (0.30, 0.24, 0.15), 0.97, specular=0.05)
    wood = cc.mat(f'{P}_Wood', (0.34, 0.24, 0.14), 0.82)

    meshes = [
        make_tunic(wool),
        make_cloak(cloak_m),
        make_hood(cloak_m),
        cc.make_head(P, skin, hair_m, brow_m, hair_style='cropped'),
        cc.make_belt(P, leather, rx=0.160, ry=0.120),
        make_letter_pouch(leather, wax, cord),
        make_side_knife(leather, iron),
        make_travel_scroll_tube(leather, wood),
        make_mud_spatters(mud),
        cc.make_limbs(P, wool, skin, hose, boots, build='average', bare_forearms=True),
    ]
    return cc.finish_character(
        'narbonne_agent', meshes, f'{P}_Armature', TARGET_HEIGHT, MAX_WIDTH,
        look_note='Hooded Narbonne courier: wax-and-mud travel cloak+hood, sealed letter pouch, belt tube, knife — NO glow',
    )


if __name__ == '__main__':
    build()
