"""Blender: Fontfroide dormitory bay shell (Broken Seal) — game-ready GLB + previews.

Abbey outbuilding / dormitory bay: limestone walls, small Romanesque windows,
low tiled stone roof. Modular ~5 m bay for Engineering placement.
Dirt-and-mail Occitania 1208 — NO fantasy half-timber / Kenney colors.
Rebuild:
  /usr/bin/blender -b -P tools/make_fontfroide_dormer.py
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

STEM = 'fontfroide_dormer'
# Modular bay footprint ~5.0 x 4.2 m; wall height ~3.2 to eaves, ridge ~4.4
W, D = 5.0, 4.2   # outer footprint
TW = 0.38         # wall thickness
ZEAVE, ZRIDGE = 3.15, 4.35


def make_walls(limestone, limestone_dark):
    parts = []
    hx, hy = W * 0.5, D * 0.5
    # Outer shell as four walls with window punches (solid piers between)
    # Front (-Y): two small windows + door stub (boarded)
    pier_xs = [-2.35, -0.85, 0.85, 2.35]
    # Continuous base plinth
    bm = bmesh.new()
    bc.box_bm(bm, -hx, hx, -hy, hy, 0.0, 0.28)
    bc.wear_stone(bm, 0.01, 2.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Dorm_Plinth', bm, limestone_dark, smooth=False))

    # Front wall segments
    # Door clear width 1.30 m (GD lock ≥1.2); windows flank door
    # Door x in [-0.65, 0.65]; windows at ±1.55
    segs = [
        (-hx, -1.95, -hy, -hy + TW, 0.28, ZEAVE),           # left solid
        (-1.95, -1.15, -hy, -hy + TW, 0.28, 1.20),          # under L win
        (-1.95, -1.15, -hy, -hy + TW, 2.15, ZEAVE),          # over L win
        (-1.15, -0.65, -hy, -hy + TW, 0.28, ZEAVE),          # pier L of door
        (-0.65, 0.65, -hy, -hy + TW, 2.35, ZEAVE),           # lintel over door
        (0.65, 1.15, -hy, -hy + TW, 0.28, ZEAVE),            # pier R of door
        (1.15, 1.95, -hy, -hy + TW, 0.28, 1.20),            # under R win
        (1.15, 1.95, -hy, -hy + TW, 2.15, ZEAVE),            # over R win
        (1.95, hx, -hy, -hy + TW, 0.28, ZEAVE),              # right solid
    ]
    bm = bmesh.new()
    for xmin, xmax, ymin, ymax, z0, z1 in segs:
        bc.box_bm(bm, xmin, xmax, ymin, ymax, z0, z1)
    bc.wear_stone(bm, 0.011, 3.1)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Dorm_Front', bm, limestone, smooth=False))

    # Back wall (+Y) with three small slit windows
    bm = bmesh.new()
    # full back with slits: build as continuous + leave gaps via segments
    back_segs = [
        (-hx, -1.7, hy - TW, hy, 0.28, ZEAVE),
        (-1.7, -1.15, hy - TW, hy, 0.28, 1.4),
        (-1.7, -1.15, hy - TW, hy, 2.2, ZEAVE),
        (-1.15, -0.55, hy - TW, hy, 0.28, ZEAVE),
        (-0.55, 0.0, hy - TW, hy, 0.28, 1.4),
        (-0.55, 0.0, hy - TW, hy, 2.2, ZEAVE),
        (0.0, 0.55, hy - TW, hy, 0.28, ZEAVE),
        (0.55, 1.1, hy - TW, hy, 0.28, 1.4),
        (0.55, 1.1, hy - TW, hy, 2.2, ZEAVE),
        (1.1, 1.7, hy - TW, hy, 0.28, ZEAVE),
        (1.7, hx, hy - TW, hy, 0.28, ZEAVE),
    ]
    for s in back_segs:
        bc.box_bm(bm, *s)
    bc.wear_stone(bm, 0.01, 4.2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Dorm_Back', bm, limestone, smooth=False))

    # Side walls ±X solid with one small window each
    for sx, name in ((-1, 'L'), (1, 'R')):
        bm = bmesh.new()
        x0 = sx * hx
        x1 = sx * (hx - TW)
        xa, xb = min(x0, x1), max(x0, x1)
        # below / above window, and flanks
        bc.box_bm(bm, xa, xb, -hy + TW, -0.45, 0.28, ZEAVE)
        bc.box_bm(bm, xa, xb, 0.45, hy - TW, 0.28, ZEAVE)
        bc.box_bm(bm, xa, xb, -0.45, 0.45, 0.28, 1.35)
        bc.box_bm(bm, xa, xb, -0.45, 0.45, 2.15, ZEAVE)
        bc.wear_stone(bm, 0.01, 5.0 + sx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bc.bm_to_object(f'Dorm_Side{name}', bm, limestone, smooth=False))

    # Window surrounds (stone frames) — readable at iso
    for cx, cy, in_front in (
        (-1.55, -hy + TW * 0.5, True),
        (1.55, -hy + TW * 0.5, True),
        (-hx + TW * 0.5, 0.0, False),
        (hx - TW * 0.5, 0.0, False),
    ):
        bm = bmesh.new()
        if in_front:
            bc.box_bm(bm, cx - 0.42, cx + 0.42, cy - 0.04, cy + 0.06, 1.10, 1.18)
            bc.box_bm(bm, cx - 0.42, cx + 0.42, cy - 0.04, cy + 0.06, 2.00, 2.10)
            bc.box_bm(bm, cx - 0.42, cx - 0.32, cy - 0.04, cy + 0.06, 1.18, 2.00)
            bc.box_bm(bm, cx + 0.32, cx + 0.42, cy - 0.04, cy + 0.06, 1.18, 2.00)
        else:
            bc.box_bm(bm, cx - 0.06, cx + 0.06, cy - 0.42, cy + 0.42, 1.30, 1.38)
            bc.box_bm(bm, cx - 0.06, cx + 0.06, cy - 0.42, cy + 0.42, 2.10, 2.20)
            bc.box_bm(bm, cx - 0.06, cx + 0.06, cy - 0.42, cy - 0.32, 1.38, 2.10)
            bc.box_bm(bm, cx - 0.06, cx + 0.06, cy + 0.32, cy + 0.42, 1.38, 2.10)
        parts.append(bc.bm_to_object(f'_wframe{cx:.1f}', bm, limestone_dark, smooth=False))

    # Corner quoins (slightly proud)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bm = bmesh.new()
        bc.box_bm(bm, sx * hx - sx * 0.12, sx * hx + sx * 0.02,
                  sy * hy - sy * 0.12, sy * hy + sy * 0.02, 0.28, ZEAVE)
        # fix min/max
        bm.free()
        bm = bmesh.new()
        xa = sx * hx - 0.14 if sx < 0 else sx * hx - 0.02
        xb = sx * hx + 0.02 if sx < 0 else sx * hx + 0.14
        ya = sy * hy - 0.14 if sy < 0 else sy * hy - 0.02
        yb = sy * hy + 0.02 if sy < 0 else sy * hy + 0.14
        bc.box_bm(bm, min(xa, xb), max(xa, xb), min(ya, yb), max(ya, yb), 0.28, ZEAVE)
        bc.wear_stone(bm, 0.006, 8 + sx + sy)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bc.bm_to_object(f'_quoin{sx}{sy}', bm, limestone_dark, smooth=False))

    return bc.join_named('Dorm_Stone', parts)


def make_roof(tile, oak):
    parts = []
    hx, hy = W * 0.5 + 0.18, D * 0.5 + 0.18  # overhang
    bm = bmesh.new()
    bc.pitch_roof_bm(bm, -hx, hx, -hy, hy, ZEAVE - 0.05, ZRIDGE, ridge_along_x=True)
    # thicken: duplicate slightly raised ridge shell as second surface via vert nudge on top
    for v in bm.verts:
        if v.co.z > ZEAVE + 0.1:
            v.co.z += 0.04 * math.sin(v.co.x * 3.5) * 0.15  # subtle tile undulation
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Dorm_Roof', bm, tile, smooth=False))

    # Ridge beam / coping
    bm = bmesh.new()
    bc.box_bm(bm, -hx + 0.1, hx - 0.1, -0.08, 0.08, ZRIDGE - 0.04, ZRIDGE + 0.08)
    parts.append(bc.bm_to_object('Dorm_Ridge', bm, tile, smooth=False))

    # Eave oak plates
    for sy in (-1, 1):
        bm = bmesh.new()
        y = sy * (D * 0.5)
        bc.box_bm(bm, -hx + 0.05, hx - 0.05, y - 0.06, y + 0.06, ZEAVE - 0.12, ZEAVE + 0.02)
        parts.append(bc.bm_to_object(f'_eave{sy}', bm, oak, smooth=False))

    # Simple stone corbels under eaves (front)
    for i, x in enumerate((-1.8, -0.6, 0.6, 1.8)):
        bm = bmesh.new()
        bc.box_bm(bm, x - 0.12, x + 0.12, -D * 0.5 - 0.08, -D * 0.5 + TW,
                  ZEAVE - 0.35, ZEAVE - 0.02)
        parts.append(bc.bm_to_object(f'_corbel{i}', bm, oak, smooth=False))

    return bc.join_named('Dorm_RoofGroup', parts)


def make_wood(oak, iron):
    parts = []
    # Boarded shutters in front windows (recessed)
    hy = -D * 0.5 + TW * 0.55
    for cx in (-1.55, 1.55):
        bm = bmesh.new()
        bc.box_bm(bm, cx - 0.30, cx + 0.30, hy, hy + 0.04, 1.25, 2.10)
        for v in bm.verts:
            if abs(v.co.y - hy) < 0.01:
                seam = abs((v.co.x - cx + 0.3) % 0.15 - 0.075)
                if seam < 0.012:
                    v.co.y -= 0.006
        parts.append(bc.bm_to_object(f'_shut{cx}', bm, oak, smooth=False))

    # Side shutters
    for sx in (-1, 1):
        bm = bmesh.new()
        x = sx * (W * 0.5 - TW * 0.55)
        xa = x - 0.03 if sx < 0 else x - 0.01
        xb = x + 0.01 if sx < 0 else x + 0.03
        bc.box_bm(bm, min(xa, xb), max(xa, xb), -0.30, 0.30, 1.40, 2.10)
        parts.append(bc.bm_to_object(f'_sshut{sx}', bm, oak, smooth=False))

    # Boarded door leaf — fills 1.30 m clear opening (GD ≥1.2); recessed flush
    bm = bmesh.new()
    bc.box_bm(bm, -0.62, 0.62, hy, hy + 0.05, 0.30, 2.30)
    for v in bm.verts:
        if abs(v.co.y - hy) < 0.01:
            seam = abs((v.co.x + 0.62) % 0.20 - 0.10)
            if seam < 0.015:
                v.co.y -= 0.008
    parts.append(bc.bm_to_object('Dorm_DoorLeaf', bm, oak, smooth=False))
    for z in (0.55, 1.15, 1.85):
        bm = bmesh.new()
        bc.box_bm(bm, -0.62, -0.20, hy - 0.015, hy + 0.01, z - 0.03, z + 0.03)
        parts.append(bc.bm_to_object(f'_dhinge{z}', bm, iron, smooth=False))

    # Small iron hinges on front shutters
    for cx in (-1.55, 1.55):
        for z in (1.40, 1.95):
            bm = bmesh.new()
            bc.box_bm(bm, cx - 0.32, cx - 0.18, hy - 0.015, hy + 0.01, z - 0.025, z + 0.025)
            parts.append(bc.bm_to_object(f'_hinge{cx}{z}', bm, iron, smooth=False))

    return bc.join_named('Dorm_Wood', parts)


def make_mud(mud):
    parts = []
    for i, (mx, my, mr) in enumerate((
        (-1.5, -2.35, 0.28), (0.8, -2.4, 0.22), (1.9, -2.2, 0.18),
        (-2.2, 0.5, 0.2), (2.3, -0.8, 0.16),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=mr)
        for v in bm.verts:
            v.co.z *= 0.35
            v.co.x *= 1.5
            v.co += Vector((mx, my, 0.02))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bc.bm_to_object(f'_mud{i}', bm, mud, smooth=True))
    return bc.join_named('Dorm_Mud', parts)


def build():
    bc.clear_scene()
    limestone = bc.mat('Dorm_Limestone', bc.PALETTE['limestone'], 0.90, specular=0.16)
    limestone_dark = bc.mat('Dorm_LimestoneDark', bc.PALETTE['limestone_dark'], 0.92, specular=0.14)
    tile = bc.mat('Dorm_Tile', bc.PALETTE['tile'], 0.88, specular=0.18)
    oak = bc.mat('Dorm_Oak', bc.PALETTE['oak'], 0.84, specular=0.20)
    iron = bc.mat('Dorm_Iron', bc.PALETTE['iron'], 0.50, metallic=0.5, specular=0.35)
    mud = bc.mat('Dorm_Mud', bc.PALETTE['mud'], 0.96, specular=0.06)

    meshes = [make_walls(limestone, limestone_dark), make_roof(tile, oak),
              make_wood(oak, iron), make_mud(mud)]
    meshes = [m for m in meshes if m]
    bc.plant_and_center(meshes)
    return meshes


def main():
    meshes = build()
    glb = os.path.join(bc.OUT_DIR, f'{STEM}.glb')
    bc.export_glb(glb)
    print('Exported', glb)
    bc.render_previews(STEM, cam_target=(0, 0, 2.4), dist_scale=0.85)
    bc.cleanup_preview_helpers()
    bc.export_glb(glb)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bc.write_scale(STEM, mesh_objs, [
        'footprint_target_m~=5.0x4.2',
        'doorway_clear_w_m=1.30',
        'doorway=-Y_boarded',
        'collision=tight_to_mesh',
        'modular_bay=fontfroide_dormitory',
        'style=cistercian_fontfroide_occitan_1208',
    ])


if __name__ == '__main__':
    main()
