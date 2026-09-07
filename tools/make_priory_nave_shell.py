"""Blender: Ruined priory nave shell for hold_door (Broken Seal).

Damaged roof, stone walls — interior/exterior readable at isometric orbit.
Dirt-and-mail Occitania 1208 Corbières ruin — complements false_altar / yard_rope.
Rebuild:
  /usr/bin/blender -b -P tools/make_priory_nave_shell.py
"""
from __future__ import annotations
import math, os, sys
import bmesh
import bpy
from mathutils import Vector

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)
import building_shell_common as bc

STEM = 'priory_nave_shell'
# Footprint ~10 x 6.5 m; walls ~4.5–5.5 m; roof partially collapsed
W, D = 10.0, 6.5
TW = 0.50
ZEAVE = 4.6
ZRIDGE = 6.8


def make_walls(limestone, limestone_dark):
    parts = []
    hx, hy = W * 0.5, D * 0.5

    bm = bmesh.new()
    bc.box_bm(bm, -hx - 0.1, hx + 0.1, -hy - 0.1, hy + 0.1, 0.0, 0.30)
    bc.wear_stone(bm, 0.014, 1.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('PNave_Plinth', bm, limestone_dark, False))

    # Front (-Y): wide doorway for hold_door (open — no door leaf; yard_rope props handle)
    bm = bmesh.new()
    bc.box_bm(bm, -hx, -1.4, -hy, -hy + TW, 0.30, 4.2)
    bc.box_bm(bm, 1.4, hx, -hy, -hy + TW, 0.30, 3.6)  # right lower (damage)
    bc.box_bm(bm, -1.4, 1.4, -hy, -hy + TW, 2.8, 4.5)
    for v in bm.verts:
        if v.co.x > 2.0 and v.co.z > 2.5:
            v.co.z -= 0.35 * ((v.co.x - 2.0) / 3.0)
    bc.wear_stone(bm, 0.015, 2.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('PNave_Front', bm, limestone, False))

    bm = bmesh.new()
    bc.arch_opening_ring(bm, 0.0, 0.0, 2.15, 1.25, 1.55, -hy - 0.06, -hy + TW + 0.06, segs=16)
    parts.append(bc.bm_to_object('PNave_FrontArch', bm, limestone_dark, True))

    # Rear wall — more intact with 3 empty windows, uneven top
    win = (-2.8, 0.0, 2.8)
    bm = bmesh.new()
    x0 = -hx
    for cx in win:
        bc.box_bm(bm, x0, cx - 0.55, hy - TW, hy, 0.30, 4.8)
        bc.box_bm(bm, cx - 0.55, cx + 0.55, hy - TW, hy, 0.30, 1.5)
        bc.box_bm(bm, cx - 0.55, cx + 0.55, hy - TW, hy, 2.7, 4.5)
        x0 = cx + 0.55
    bc.box_bm(bm, x0, hx, hy - TW, hy, 0.30, 4.4)
    for v in bm.verts:
        if v.co.z > 3.5:
            v.co.z -= 0.25 * abs(math.sin(v.co.x * 1.8))
    bc.wear_stone(bm, 0.014, 3.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('PNave_Rear', bm, limestone, False))

    for cx in win:
        bm = bmesh.new()
        bc.arch_opening_ring(bm, cx, 0.0, 2.15, 0.42, 0.58, hy - TW - 0.04, hy + 0.05, segs=12)
        parts.append(bc.bm_to_object(f'_parch{cx}', bm, limestone_dark, True))

    # Left wall (-X) — mostly intact, sheep-gate end toward +Y can be open-ish
    bm = bmesh.new()
    xa, xb = -hx, -hx + TW
    # solid with two windows
    for wy in (-1.5, 1.2):
        pass
    # build: full height strips
    bc.box_bm(bm, xa, xb, -hy + TW, -2.0, 0.30, 5.0)
    bc.box_bm(bm, xa, xb, -2.0, -1.0, 0.30, 1.45)
    bc.box_bm(bm, xa, xb, -2.0, -1.0, 2.55, 4.8)
    bc.box_bm(bm, xa, xb, -1.0, 0.7, 0.30, 4.9)
    bc.box_bm(bm, xa, xb, 0.7, 1.7, 0.30, 1.45)
    bc.box_bm(bm, xa, xb, 0.7, 1.7, 2.55, 4.6)
    bc.box_bm(bm, xa, xb, 1.7, hy - TW - 0.8, 0.30, 4.5)
    # sheep-gate gap toward +Y rear corner (open lower)
    bc.box_bm(bm, xa, xb, hy - TW - 0.8, hy - TW, 2.2, 4.2)
    bc.wear_stone(bm, 0.012, 4.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('PNave_SideL', bm, limestone, False))

    # Right wall (+X) — heavily damaged / open to sky in places
    bm = bmesh.new()
    xa, xb = hx - TW, hx
    bc.box_bm(bm, xa, xb, -hy + TW, -0.5, 0.30, 4.2)
    bc.box_bm(bm, xa, xb, -0.5, 1.0, 0.30, 2.4)  # collapsed mid
    bc.box_bm(bm, xa, xb, 1.0, hy - TW, 0.30, 3.5)
    for v in bm.verts:
        if 0.0 < v.co.y < 2.0 and v.co.z > 1.8:
            v.co.z -= 0.5 * abs(math.sin(v.co.y * 2))
            v.co.x -= 0.08
    bc.wear_stone(bm, 0.016, 5.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('PNave_SideR', bm, limestone, False))

    # Interior floor suggestion (thin slab — readable from above)
    bm = bmesh.new()
    bc.box_bm(bm, -hx + TW, hx - TW, -hy + TW, hy - TW, 0.02, 0.12)
    # wear / missing slabs
    for v in bm.verts:
        v.co.z += 0.015 * math.sin(v.co.x * 3) * math.cos(v.co.y * 2.5)
    parts.append(bc.bm_to_object('PNave_Floor', bm, limestone_dark, False))

    # Corner piers
    for sx, sy in ((-1, -1), (1, -1), (-1, 1)):
        bm = bmesh.new()
        bc.box_bm(bm,
                  min(sx * hx, sx * hx + sx * 0.6), max(sx * hx, sx * hx + sx * 0.6),
                  min(sy * hy, sy * hy + sy * 0.6), max(sy * hy, sy * hy + sy * 0.6),
                  0.0, 4.0 if sx < 0 else 3.2)
        bc.wear_stone(bm, 0.012, 8)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bc.bm_to_object(f'_ppier{sx}{sy}', bm, limestone_dark, False))

    return bc.join_named('PNave_Stone', parts)


def make_damaged_roof(tile, oak, limestone):
    parts = []
    hx, hy = W * 0.5 + 0.15, D * 0.5 + 0.15

    # Intact roof left half (x < 0.5)
    bm = bmesh.new()
    # custom half-roof: verts for left portion with ridge
    ymid = 0.0
    verts_data = [
        (-hx, -hy, ZEAVE), (0.8, -hy, ZEAVE), (0.8, hy, ZEAVE), (-hx, hy, ZEAVE),
        (-hx, ymid, ZRIDGE - 0.3), (0.8, ymid, ZRIDGE - 0.5),
    ]
    vs = [bm.verts.new(p) for p in verts_data]
    bm.verts.ensure_lookup_table()
    bm.faces.new((vs[0], vs[1], vs[2], vs[3]))
    bm.faces.new((vs[0], vs[1], vs[5], vs[4]))
    bm.faces.new((vs[3], vs[2], vs[5], vs[4]))
    bm.faces.new((vs[0], vs[4], vs[3]))
    bm.faces.new((vs[1], vs[2], vs[5]))
    for v in bm.verts:
        if v.co.z > ZEAVE:
            v.co.z += 0.03 * math.sin(v.co.x * 2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('PNave_RoofLeft', bm, tile, False))

    # Fallen / tilted roof slabs on right
    for i, (cx, cy, rot, sc) in enumerate((
        (2.5, -1.2, 0.35, 1.0), (3.5, 0.8, -0.5, 0.85), (2.0, 1.8, 0.7, 0.7),
    )):
        bm = bmesh.new()
        bc.box_bm(bm, -1.2 * sc, 1.2 * sc, -0.7 * sc, 0.7 * sc, 0.0, 0.12)
        for v in bm.verts:
            # tilt
            v.co.z += rot * (v.co.y + 0.5)
            v.co += Vector((cx, cy, 1.2 + i * 0.3))
        parts.append(bc.bm_to_object(f'_rslab{i}', bm, tile, False))

    # Broken oak beams spanning mid
    for i, (x0, x1, y, z) in enumerate((
        (-3.5, 2.0, -0.8, 4.3), (-2.0, 3.5, 0.5, 4.0), (-4.0, 0.5, 1.5, 4.5),
    )):
        bm = bmesh.new()
        bc.box_bm(bm, x0, x1, y - 0.1, y + 0.1, z - 0.1, z + 0.1)
        # sag
        for v in bm.verts:
            mid = (x0 + x1) * 0.5
            v.co.z -= 0.25 * (1.0 - abs(v.co.x - mid) / max(abs(x1 - x0) * 0.5, 0.1))
        parts.append(bc.bm_to_object(f'_beam{i}', bm, oak, False))

    # Fallen beam on floor
    bm = bmesh.new()
    bc.box_bm(bm, 1.0, 4.2, -0.15, 0.15, 0.15, 0.35)
    for v in bm.verts:
        v.co.y += 0.3 * ((v.co.x - 1.0) / 3.2)
        v.co.z += 0.05 * math.sin(v.co.x)
    parts.append(bc.bm_to_object('PNave_FallenBeam', bm, oak, False))

    return bc.join_named('PNave_RoofGroup', parts)


def make_debris(limestone, rubble, mud, oak):
    parts = []
    for i, (mx, my, mr, mz) in enumerate((
        (-3.0, -2.5, 0.3, 0.2), (2.5, -2.0, 0.35, 0.25), (3.5, 1.5, 0.28, 0.18),
        (-1.0, 2.5, 0.32, 0.22), (0.5, -0.5, 0.4, 0.15), (4.0, -1.0, 0.25, 0.2),
        (-4.0, 0.0, 0.22, 0.15), (1.5, 2.8, 0.2, 0.12),
    )):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=1, radius=mr)
        for v in bm.verts:
            v.co.x *= 1.4
            v.co.z *= 0.65
            v.co += Vector((mx, my, mz * 0.5))
            if v.co.z < 0:
                v.co.z = 0.01
        parts.append(bc.bm_to_object(f'_prub{i}', bm, rubble if i % 2 else limestone, False))

    for i, (mx, my, mr) in enumerate((
        (-2.0, -3.2, 0.4), (3.0, -3.0, 0.35), (0.0, 3.2, 0.3),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=mr)
        for v in bm.verts:
            v.co.z *= 0.28
            v.co.x *= 1.5
            v.co += Vector((mx, my, 0.02))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bc.bm_to_object(f'_pmud{i}', bm, mud, True))

    # Charred timber scraps
    for i, (mx, my) in enumerate(((2.2, 0.2), (3.0, -1.5), (-0.5, 1.0))):
        bm = bmesh.new()
        bc.box_bm(bm, mx - 0.4, mx + 0.5, my - 0.08, my + 0.08, 0.08, 0.2)
        parts.append(bc.bm_to_object(f'_char{i}', bm, oak, False))

    return bc.join_named('PNave_Debris', parts)


def build():
    bc.clear_scene()
    limestone = bc.mat('PNave_Limestone', (0.52, 0.48, 0.38), 0.92, specular=0.12)
    limestone_dark = bc.mat('PNave_LimestoneDark', (0.40, 0.36, 0.28), 0.94, specular=0.10)
    tile = bc.mat('PNave_Tile', (0.32, 0.24, 0.17), 0.90, specular=0.14)
    oak = bc.mat('PNave_Oak', (0.24, 0.16, 0.09), 0.88, specular=0.16)
    rubble = bc.mat('PNave_Rubble', bc.PALETTE['rubble'], 0.95, specular=0.08)
    mud = bc.mat('PNave_Mud', bc.PALETTE['mud'], 0.97, specular=0.05)
    meshes = [
        make_walls(limestone, limestone_dark),
        make_damaged_roof(tile, oak, limestone),
        make_debris(limestone, rubble, mud, oak),
    ]
    meshes = [m for m in meshes if m]
    bc.plant_and_center(meshes)
    return meshes


def main():
    meshes = build()
    glb = os.path.join(bc.OUT_DIR, f'{STEM}.glb')
    bc.export_glb(glb)
    print('Exported', glb)
    bc.render_previews(STEM, cam_target=(0, 0, 3.2), dist_scale=1.35)
    bc.cleanup_preview_helpers()
    bc.export_glb(glb)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bc.write_scale(STEM, mesh_objs, [
        'footprint_target_m~=10.0x6.5',
        'doorway_clear_w_m=2.50',
        'doorway_front=-Y_hold_door clear_inner_arch_m=2.50',
        'sheep_gate_corner=+Y_-X',
        'collision=tight_to_mesh',
        'style=corbieres_ruined_nave_occitan_1208',
    ])


if __name__ == '__main__':
    main()
