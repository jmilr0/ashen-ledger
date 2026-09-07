"""Blender: The Surgeon (Broken Seal) — barber / infirmary hand GLB + previews.

Apron over tunic, tool roll / knife case, optional basin belt prop. No prayer FX.
Rebuild:
  /usr/bin/blender -b -P tools/make_surgeon.py
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
MAX_WIDTH = 0.56
P = 'Surgeon'


def make_tunic(wool):
    profile = [
        (0.70, 0.170, 0.132, 0.012),
        (0.85, 0.162, 0.125, 0.014),
        (1.00, 0.155, 0.118, 0.014),
        (1.14, 0.165, 0.125, 0.012),
        (1.26, 0.175, 0.132, 0.008),
        (1.34, 0.145, 0.112, 0.005),
        (1.40, 0.062, 0.056, 0.000),
    ]
    skirt = [
        (0.55, 0.175, 0.138, 0.016),
        (0.40, 0.165, 0.130, 0.014),
        (0.28, 0.150, 0.118, 0.010),
    ]
    return cc.make_lathe_body(f'{P}_Tunic', wool, profile, segs=20, fold_amp=0.011,
                              fold_freq=5, skirt=skirt, hem_scale=1.02, subdiv=2)


def make_apron(linen):
    bm = bmesh.new()
    u_segs, v_segs = 16, 20
    grid = []
    for i in range(v_segs + 1):
        v = i / v_segs
        z = 1.22 - v * 0.92
        w = 0.14 + 0.04 * v
        row = []
        for j in range(u_segs + 1):
            t = j / u_segs
            x = (t - 0.5) * 2 * w
            y = 0.148 + 0.015 * v + 0.012 * math.sin(t * math.pi * 3 + v * 4)
            # slight stain-darkening is material; geometry fold only
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for i in range(v_segs):
        for j in range(u_segs):
            bm.faces.new((grid[i][j], grid[i][j+1], grid[i+1][j+1], grid[i+1][j]))
    # bib up to chest
    bib = []
    for j in range(u_segs + 1):
        t = j / u_segs
        x = (t - 0.5) * 2 * 0.10
        bib.append(bm.verts.new((x, 0.155, 1.28)))
    top = grid[0]
    # reconnect: apron top is grid[0] at z=1.22; bib higher
    for j in range(u_segs):
        # taper bib to apron top width
        pass
    # straps
    for sx in (-1, 1):
        path = [Vector((sx*0.08, 0.15, 1.28)), Vector((sx*0.12, 0.05, 1.35)),
                Vector((sx*0.10, -0.08, 1.30)), Vector((sx*0.06, -0.12, 1.20))]
        cc.tube(bm, path, [0.008]*4, segs=6)
    # neck strap join
    cc.tube(bm, [Vector((-0.06, 0.02, 1.36)), Vector((0, 0.05, 1.40)), Vector((0.06, 0.02, 1.36))],
            [0.007]*3, segs=6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 2)
    return cc.bm_to_object(f'{P}_Apron', bm, linen)


def make_tool_roll(leather, iron, wood):
    parts = []
    # rolled leather case on belt
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=14, radius1=0.032, radius2=0.032, depth=0.14,
                          matrix=Matrix.Translation((0.16, 0.145, 0.90)) @ Matrix.Rotation(math.radians(90), 4, 'Y'))
    parts.append(cc.bm_to_object('_roll', bm, leather))
    # tie
    bm = bmesh.new()
    cc.tube(bm, [Vector((0.10, 0.145, 0.90)), Vector((0.16, 0.16, 0.92)), Vector((0.22, 0.145, 0.90))],
            [0.005]*3, segs=5)
    parts.append(cc.bm_to_object('_tie', bm, leather))
    # protruding tool handles
    for i, oz in enumerate((0.02, 0.0, -0.02)):
        bm = bmesh.new()
        cc.tube(bm, [Vector((0.23, 0.145, 0.90+oz)), Vector((0.28, 0.15, 0.90+oz))], [0.006, 0.005], segs=6)
        parts.append(cc.bm_to_object(f'_handle{i}', bm, wood if i < 2 else iron))
    return cc.join_named(f'{P}_ToolRoll', parts)


def make_basin(pewter):
    bm = bmesh.new()
    # shallow bowl hung at left hip
    segs = 20
    # outer rim
    rings = []
    for z, r in ((0.95, 0.055), (0.93, 0.058), (0.90, 0.050), (0.88, 0.030)):
        row = []
        for j in range(segs):
            a = (j/segs)*math.tau
            row.append(bm.verts.new((-0.14 + r*math.cos(a), 0.145 + r*0.4*math.sin(a), z)))
        rings.append(row)
    for i in range(len(rings)-1):
        for j in range(segs):
            j2=(j+1)%segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]))
    # bottom cap
    c = sum((v.co for v in rings[-1]), Vector())/len(rings[-1])
    center = bm.verts.new(c)
    for j in range(segs):
        bm.faces.new((center, rings[-1][(j+1)%segs], rings[-1][j]))
    # bail handle
    path = [Vector((-0.18, 0.145, 0.95)), Vector((-0.16, 0.12, 1.02)),
            Vector((-0.14, 0.12, 1.02)), Vector((-0.10, 0.145, 0.95))]
    cc.tube(bm, path, [0.005]*4, segs=6)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return cc.bm_to_object(f'{P}_Basin', bm, pewter)


def make_knife_case(leather, iron):
    parts = []
    bm = bmesh.new()
    cc.tube(bm, [Vector((-0.05, 0.145, 0.94)), Vector((-0.05, 0.15, 0.80))], [0.014, 0.012], segs=8)
    parts.append(cc.bm_to_object('_case', bm, leather))
    bm = bmesh.new()
    cc.tube(bm, [Vector((-0.05, 0.148, 0.95)), Vector((-0.05, 0.148, 0.99))], [0.008, 0.004], segs=6)
    parts.append(cc.bm_to_object('_razor', bm, iron))
    return cc.join_named(f'{P}_KnifeCase', parts)


def build():
    cc.clear_scene()
    skin = cc.mat(f'{P}_Skin', (0.78, 0.62, 0.50), 0.52, specular=0.4)
    wool = cc.mat(f'{P}_Wool', (0.38, 0.36, 0.40), 0.88, specular=0.15)  # slate undyed
    linen = cc.mat(f'{P}_Apron', (0.72, 0.68, 0.55), 0.85, specular=0.18)  # stained linen
    leather = cc.mat(f'{P}_Leather', (0.22, 0.14, 0.09), 0.82)
    hair_m = cc.mat(f'{P}_Hair', (0.28, 0.22, 0.14), 0.75)  # cropped sandy
    brow_m = cc.mat(f'{P}_Brow', (0.20, 0.15, 0.10), 0.8)
    wood = cc.mat(f'{P}_Wood', (0.40, 0.28, 0.15), 0.78)
    iron = cc.mat(f'{P}_Iron', (0.32, 0.32, 0.30), 0.45, metallic=0.65, specular=0.45)
    pewter = cc.mat(f'{P}_Pewter', (0.45, 0.45, 0.42), 0.40, metallic=0.5, specular=0.4)
    hose = cc.mat(f'{P}_Hose', (0.30, 0.28, 0.26), 0.85)
    boots = cc.mat(f'{P}_Boots', (0.12, 0.09, 0.07), 0.9)

    meshes = [
        make_tunic(wool),
        make_apron(linen),
        cc.make_head(P, skin, hair_m, brow_m, hair_style='cropped'),
        cc.make_belt(P, leather, rx=0.165, ry=0.125),
        make_tool_roll(leather, iron, wood),
        make_basin(pewter),
        make_knife_case(leather, iron),
        cc.make_limbs(P, wool, skin, hose, boots, build='average', bare_forearms=True),
    ]
    return cc.finish_character('surgeon', meshes, f'{P}_Armature', TARGET_HEIGHT, MAX_WIDTH,
        look_note='Barber-surgeon: slate tunic, stained linen apron, tool roll, pewter basin, knife case')


if __name__ == '__main__':
    build()
