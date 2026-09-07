"""Blender: The Sergeant (Broken Seal) — Hospitaller / household man-at-arms GLB + previews.

Dirt-and-mail Occitania 1208-10. Mail hauberk/coif, spear, dull iron — no chrome plate.
Rebuild:
  /usr/bin/blender -b -P tools/make_sergeant.py
"""
from __future__ import annotations
import math, os, sys
import bmesh
from mathutils import Matrix, Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import character_common as cc

TARGET_HEIGHT = 1.78
MAX_WIDTH = 0.58
P = 'Sergeant'


def make_hauberk(mail):
    profile = [
        (0.72, 0.195, 0.150, 0.010),
        (0.88, 0.185, 0.142, 0.012),
        (1.02, 0.175, 0.135, 0.014),
        (1.16, 0.190, 0.145, 0.012),
        (1.28, 0.200, 0.150, 0.008),
        (1.36, 0.155, 0.120, 0.005),
        (1.42, 0.070, 0.065, 0.000),
    ]
    skirt = [
        (0.58, 0.200, 0.155, 0.016),
        (0.44, 0.192, 0.148, 0.018),
        (0.32, 0.175, 0.138, 0.014),
    ]
    return cc.make_lathe_body(f'{P}_Hauberk', mail, profile, segs=22, fold_amp=0.008,
                              fold_freq=10, skirt=skirt, hem_scale=1.02, subdiv=2)


def make_coif(mail):
    bm = bmesh.new()
    segs_u, segs_v = 24, 14
    grid = []
    theta0, theta1 = math.radians(50), math.radians(310)
    for i in range(segs_v + 1):
        v = i / segs_v
        z = 1.70 - v * 0.36
        rx = 0.112 + 0.025 * (0.5 - abs(v - 0.4)) + (0.045 * max(0, v - 0.65) / 0.35)
        ry = 0.118 + 0.02 * math.sin(v * math.pi) + (0.03 * max(0, v - 0.65) / 0.35)
        row = []
        for j in range(segs_u + 1):
            t = j / segs_u
            ang = theta0 + (theta1 - theta0) * t
            rmod = 1.0 + 0.03 * math.sin(ang * 12 + v * 8)
            x = rx * rmod * math.cos(ang)
            y = -0.01 + ry * rmod * math.sin(ang) * 0.95
            z_adj = z + (0.02 if v < 0.1 else 0)
            row.append(bm.verts.new((x, y, z_adj)))
        grid.append(row)
    for i in range(segs_v):
        for j in range(segs_u):
            bm.faces.new((grid[i][j], grid[i][j+1], grid[i+1][j+1], grid[i+1][j]))
    for edge_j in (0, segs_u):
        for i in range(segs_v):
            a, b = grid[i][edge_j], grid[i+1][edge_j]
            ai = bm.verts.new((a.co.x*0.75, a.co.y*0.5, a.co.z))
            bi = bm.verts.new((b.co.x*0.75, b.co.y*0.5, b.co.z))
            if edge_j == 0:
                bm.faces.new((a, b, bi, ai))
            else:
                bm.faces.new((a, ai, bi, b))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    return cc.bm_to_object(f'{P}_Coif', bm, mail)


def make_surcoat(wool):
    bm = bmesh.new()
    segs = 20
    profile = [(0.78, 0.205, 0.158), (0.95, 0.195, 0.150), (1.12, 0.200, 0.155),
               (1.26, 0.210, 0.160), (1.34, 0.165, 0.125)]
    rings = []
    for z, rx, ry in profile:
        row = []
        for j in range(segs):
            a = (j / segs) * math.tau
            side = abs(math.cos(a))
            rscale = 1.0 + 0.04 * (1 - side)
            wave = 1.0 + 0.01 * math.sin(a * 4 + z * 3)
            row.append(bm.verts.new((rx*rscale*wave*math.cos(a), ry*wave*math.sin(a), z)))
        rings.append(row)
    for i in range(len(rings)-1):
        for j in range(segs):
            j2 = (j+1)%segs
            bm.faces.new((rings[i][j], rings[i][j2], rings[i+1][j2], rings[i+1][j]))
    prev = rings[0]
    for z, rx, ry in ((0.62, 0.210, 0.162), (0.48, 0.200, 0.155)):
        row = []
        for j in range(segs):
            a = (j/segs)*math.tau
            row.append(bm.verts.new((rx*math.cos(a), ry*math.sin(a), z)))
        for j in range(segs):
            j2=(j+1)%segs
            bm.faces.new((prev[j], prev[j2], row[j2], row[j]))
        prev = row
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    cc.subdivide_bm(bm, 1)
    parts = [cc.bm_to_object(f'{P}_SurcoatBase', bm, wool)]
    for scale, loc in [
        ((0.022, 0.012, 0.13), (0, 0.168, 1.10)),
        ((0.09, 0.012, 0.022), (0, 0.168, 1.10)),
    ]:
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1.0)
        for v in bm.verts:
            v.co.x *= scale[0]; v.co.y *= scale[1]; v.co.z *= scale[2]
            v.co += Vector(loc)
        parts.append(cc.bm_to_object('_cross', bm, wool))
    return cc.join_named(f'{P}_Surcoat', parts)


def make_spear(wood, iron):
    parts = []
    bm = bmesh.new()
    path, radii = [], []
    for i in range(24):
        t = i / 23
        z = 0.02 + t * 1.78
        path.append(Vector((-0.24, 0.06, z)))
        radii.append(0.016 - 0.004 * t)
    cc.tube(bm, path, radii, segs=10)
    parts.append(cc.bm_to_object('_shaft', bm, wood))
    bm = bmesh.new()
    tip_path = [Vector((-0.24, 0.06, 1.78)), Vector((-0.24, 0.06, 1.86)),
                Vector((-0.24, 0.06, 1.93)), Vector((-0.24, 0.06, 1.98))]
    cc.tube(bm, tip_path, [0.018, 0.022, 0.012, 0.002], segs=8)
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.020, radius2=0.016, depth=0.04,
                          matrix=Matrix.Translation((-0.24, 0.06, 1.76)))
    parts.append(cc.bm_to_object('_head', bm, iron))
    bm = bmesh.new()
    cc.tube(bm, [Vector((-0.24,0.06,0.02)), Vector((-0.24,0.06,-0.04))], [0.014, 0.004], segs=8)
    parts.append(cc.bm_to_object('_butt', bm, iron))
    return cc.join_named(f'{P}_Spear', parts)


def make_kit(leather, iron):
    parts = []
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.038)
    for v in bm.verts:
        v.co.x *= 0.75; v.co.z *= 1.2
        v.co += Vector((0.18, 0.14, 0.88))
    parts.append(cc.bm_to_object('_pouch', bm, leather))
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=0.042)
    for v in bm.verts:
        v.co.x *= 0.7; v.co.z *= 1.35
        v.co += Vector((-0.10, 0.15, 0.90))
    parts.append(cc.bm_to_object('_skin', bm, leather))
    bm = bmesh.new()
    cc.tube(bm, [Vector((0.12, 0.14, 0.92)), Vector((0.12, 0.15, 0.78))], [0.012, 0.010], segs=8)
    parts.append(cc.bm_to_object('_scab', bm, leather))
    bm = bmesh.new()
    cc.tube(bm, [Vector((0.12, 0.145, 0.93)), Vector((0.12, 0.145, 0.97))], [0.008, 0.004], segs=6)
    parts.append(cc.bm_to_object('_knife', bm, iron))
    return cc.join_named(f'{P}_Kit', parts)


def build():
    cc.clear_scene()
    skin = cc.mat(f'{P}_Skin', (0.72, 0.55, 0.42), 0.55, specular=0.4)
    mail = cc.mat(f'{P}_Mail', (0.42, 0.42, 0.40), 0.48, metallic=0.55, specular=0.45)
    iron = cc.mat(f'{P}_Iron', (0.28, 0.27, 0.25), 0.55, metallic=0.7, specular=0.4)
    wool = cc.mat(f'{P}_Surcoat', (0.62, 0.58, 0.48), 0.90, specular=0.15)
    leather = cc.mat(f'{P}_Leather', (0.22, 0.14, 0.09), 0.82, specular=0.25)
    hair_m = cc.mat(f'{P}_Hair', (0.18, 0.12, 0.08), 0.75)
    brow_m = cc.mat(f'{P}_Brow', (0.14, 0.09, 0.06), 0.8)
    wood = cc.mat(f'{P}_Oak', (0.38, 0.26, 0.14), 0.78, specular=0.3)
    hose = cc.mat(f'{P}_Hose', (0.28, 0.24, 0.20), 0.85)
    boots = cc.mat(f'{P}_Boots', (0.12, 0.09, 0.07), 0.9)
    meshes = [
        make_hauberk(mail),
        make_coif(mail),
        make_surcoat(wool),
        cc.make_head(P, skin, hair_m, brow_m, hair_style='coif_ready'),
        cc.make_belt(P, leather, rx=0.175, ry=0.132),
        make_spear(wood, iron),
        make_kit(leather, iron),
        cc.make_limbs(P, mail, skin, hose, boots, build='stocky', bare_forearms=False),
    ]
    return cc.finish_character('sergeant', meshes, f'{P}_Armature', TARGET_HEIGHT, MAX_WIDTH,
        look_note='Hospitaller man-at-arms: mail hauberk+coif, dusty linen surcoat with cloth cross, spear, travel kit, dull iron')


if __name__ == '__main__':
    build()
