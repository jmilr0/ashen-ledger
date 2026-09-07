"""Blender: Berna (Broken Seal) — Corbières yard contact GLB + previews.

Practical local, wool/leather, worn — lean traveler/host silhouette.
Dirt-and-mail Occitania 1208–10. No fantasy glow.
Rebuild:
  /usr/bin/blender -b -P tools/make_berna.py
"""
from __future__ import annotations
import math, os, sys
import bmesh
from mathutils import Matrix, Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import character_common as cc

TARGET_HEIGHT = 1.68
MAX_WIDTH = 0.54
P = 'Berna'


def make_tunic(wool):
    profile = [
        (0.68, 0.150, 0.118, 0.012),
        (0.82, 0.145, 0.112, 0.014),
        (0.96, 0.138, 0.105, 0.016),
        (1.10, 0.148, 0.112, 0.014),
        (1.22, 0.158, 0.120, 0.010),
        (1.30, 0.130, 0.100, 0.006),
        (1.36, 0.055, 0.050, 0.000),
    ]
    skirt = [
        (0.54, 0.158, 0.122, 0.016),
        (0.40, 0.150, 0.116, 0.014),
        (0.28, 0.138, 0.108, 0.012),
    ]
    return cc.make_lathe_body(f'{P}_Tunic', wool, profile, segs=20, fold_amp=0.012,
                              fold_freq=5, skirt=skirt, hem_scale=1.03, subdiv=1)


def make_vest(leather):
    """Short open leather jerkin — host/traveler read, worn."""
    bm = bmesh.new()
    segs = 18
    profile = [(0.86, 0.160, 0.125), (1.00, 0.155, 0.120), (1.14, 0.162, 0.125),
               (1.26, 0.168, 0.130), (1.32, 0.140, 0.108)]
    rings = []
    for z, rx, ry in profile:
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            # open at front (gap around +Y)
            if 0.15 < a < math.tau - 0.15 and abs(a - math.pi) > 0.0:
                pass
            # skip a front slit
            front = abs((a + math.pi / 2) % math.tau - math.pi)
            if front < 0.35:
                continue
            wave = 1.0 + 0.012 * math.sin(a * 5 + z * 4)
            row.append(bm.verts.new((rx * wave * math.cos(a), ry * wave * math.sin(a), z)))
        if len(row) >= 3:
            rings.append(row)
    # Simpler closed vest with front panels instead
    bm.free()
    bm = bmesh.new()
    u_segs, v_segs = 14, 12
    for front in (1, -1):
        grid = []
        for i in range(v_segs + 1):
            v = i / v_segs
            z = 1.32 - v * 0.48
            w = 0.12 + 0.02 * v
            row = []
            for j in range(u_segs + 1):
                t = j / u_segs
                x = (t - 0.5) * 2 * w
                y = front * (0.130 + 0.015 * v + 0.008 * math.sin(t * math.pi * 2 + v * 3))
                if front > 0 and abs(t - 0.5) < 0.08:
                    y *= 0.7  # slight open front
                row.append(bm.verts.new((x, y, z)))
            grid.append(row)
        for i in range(v_segs):
            for j in range(u_segs):
                if front > 0:
                    bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
                else:
                    bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    return cc.bm_to_object(f'{P}_Vest', bm, leather)


def make_shawl(wool):
    """Worn wool wrap over one shoulder — lean host silhouette."""
    bm = bmesh.new()
    u_segs, v_segs = 20, 10
    grid = []
    for i in range(v_segs + 1):
        v = i / v_segs
        # drapes from R shoulder across chest to L hip
        z = 1.34 - v * 0.55
        row = []
        for j in range(u_segs + 1):
            t = j / u_segs
            ang = math.radians(-40) + math.radians(200) * t
            r = 0.16 + 0.06 * v + 0.015 * math.sin(t * 8 + v * 4)
            x = r * math.cos(ang) * 0.95
            y = 0.02 + r * math.sin(ang) * 0.75
            z_adj = z + 0.04 * (1 - t) * (1 - v)
            row.append(bm.verts.new((x, y, z_adj)))
        grid.append(row)
    for i in range(v_segs):
        for j in range(u_segs):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    return cc.bm_to_object(f'{P}_Shawl', bm, wool)


def make_kit(leather, wood, iron):
    """Belt pouch + small wooden cup / host token + knife."""
    parts = []
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.036)
    for v in bm.verts:
        v.co.x *= 0.80
        v.co.z *= 1.15
        v.co += Vector((0.16, 0.13, 0.88))
    parts.append(cc.bm_to_object('_pouch', bm, leather))
    # wooden cup / bowl token
    bm = bmesh.new()
    segs = 14
    rings = []
    for z, r in ((0.92, 0.028), (0.90, 0.032), (0.87, 0.026), (0.85, 0.014)):
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            row.append(bm.verts.new((-0.12 + r * math.cos(a), 0.135 + r * 0.35 * math.sin(a), z)))
        rings.append(row)
    for i in range(len(rings) - 1):
        for j in range(segs):
            j2 = (j + 1) % segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i + 1][j2], rings[i + 1][j]))
    c = sum((v.co for v in rings[-1]), Vector()) / len(rings[-1])
    center = bm.verts.new(c)
    for j in range(segs):
        bm.faces.new((center, rings[-1][(j + 1) % segs], rings[-1][j]))
    parts.append(cc.bm_to_object('_cup', bm, wood))
    # belt knife
    bm = bmesh.new()
    cc.tube(bm, [Vector((-0.02, 0.14, 0.92)), Vector((-0.02, 0.145, 0.78))],
            [0.011, 0.009], segs=8)
    parts.append(cc.bm_to_object('_scab', bm, leather))
    bm = bmesh.new()
    cc.tube(bm, [Vector((-0.02, 0.145, 0.93)), Vector((-0.02, 0.145, 0.97))],
            [0.007, 0.003], segs=6)
    parts.append(cc.bm_to_object('_blade', bm, iron))
    return cc.join_named(f'{P}_Kit', parts)


def build():
    cc.clear_scene()
    skin = cc.mat(f'{P}_Skin', (0.74, 0.56, 0.44), 0.56, specular=0.38)
    wool = cc.mat(f'{P}_Wool', (0.42, 0.36, 0.28), 0.90, specular=0.14)
    shawl = cc.mat(f'{P}_Shawl', (0.36, 0.32, 0.26), 0.92, specular=0.12)
    leather = cc.mat(f'{P}_Leather', (0.24, 0.16, 0.10), 0.84, specular=0.22)
    hair_m = cc.mat(f'{P}_Hair', (0.20, 0.12, 0.08), 0.76)
    brow_m = cc.mat(f'{P}_Brow', (0.14, 0.09, 0.06), 0.80)
    wood = cc.mat(f'{P}_Wood', (0.40, 0.28, 0.15), 0.80)
    iron = cc.mat(f'{P}_Iron', (0.34, 0.32, 0.30), 0.55, metallic=0.50)
    hose = cc.mat(f'{P}_Hose', (0.30, 0.26, 0.20), 0.86)
    boots = cc.mat(f'{P}_Boots', (0.14, 0.10, 0.07), 0.92)

    meshes = [
        make_tunic(wool),
        make_vest(leather),
        make_shawl(shawl),
        cc.make_head(P, skin, hair_m, brow_m, hair_style='short'),
        cc.make_belt(P, leather, rx=0.152, ry=0.115),
        make_kit(leather, wood, iron),
        cc.make_limbs(P, wool, skin, hose, boots, build='lean', bare_forearms=True),
    ]
    return cc.finish_character(
        'berna', meshes, f'{P}_Armature', TARGET_HEIGHT, MAX_WIDTH,
        look_note='Corbières yard contact: lean wool tunic, worn leather vest, shoulder shawl, pouch+cup+knife — practical local host',
    )


if __name__ == '__main__':
    build()
