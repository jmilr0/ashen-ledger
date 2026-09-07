"""Blender: Rural parish nave exterior shell (Broken Seal) — complements parish_porch.

Limestone Romanesque nave, small round-arch windows, simple gable, optional shut
side door. Dirt-and-mail Occitania 1208 — NO fantasy kits.
Rebuild:
  /usr/bin/blender -b -P tools/make_parish_nave_shell.py
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

STEM = 'parish_nave_shell'
# Nave footprint ~8.0 x 5.0 m; eaves ~4.0, ridge ~6.2 — porch attaches at -Y end
W, D = 8.0, 5.0
TW = 0.45
ZEAVE, ZRIDGE = 4.0, 6.15


def make_walls(limestone, limestone_dark):
    parts = []
    hx, hy = W * 0.5, D * 0.5

    # Plinth
    bm = bmesh.new()
    bc.box_bm(bm, -hx - 0.08, hx + 0.08, -hy - 0.08, hy + 0.08, 0.0, 0.35)
    bc.wear_stone(bm, 0.012, 1.5)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Nave_Plinth', bm, limestone_dark, False))

    # Front (-Y): open for porch attach — wall with large arched doorway opening
    # Build as left/right piers + above-arch wall (no door leaf — porch has the door)
    bm = bmesh.new()
    # left / right masses
    bc.box_bm(bm, -hx, -1.15, -hy, -hy + TW, 0.35, ZEAVE)
    bc.box_bm(bm, 1.15, hx, -hy, -hy + TW, 0.35, ZEAVE)
    # above springing (~2.4)
    bc.box_bm(bm, -1.15, 1.15, -hy, -hy + TW, 2.55, ZEAVE)
    # thin reveal around opening
    bc.box_bm(bm, -1.25, -1.05, -hy - 0.04, -hy + TW + 0.02, 0.35, 2.55)
    bc.box_bm(bm, 1.05, 1.25, -hy - 0.04, -hy + TW + 0.02, 0.35, 2.55)
    bc.wear_stone(bm, 0.01, 2.2)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Nave_Front', bm, limestone, False))

    # Archivolt over porch opening
    bm = bmesh.new()
    bc.arch_opening_ring(bm, 0.0, 0.0, 1.95, 1.05, 1.28, -hy - 0.05, -hy + TW + 0.05, segs=16)
    bc.wear_stone(bm, 0.007, 3.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Nave_FrontArch', bm, limestone_dark, True))

    # Rear (+Y) with three small Romanesque windows
    win_centers = (-2.2, 0.0, 2.2)
    bm = bmesh.new()
    # build rear as segments around windows
    edges = [-hx] + [c - 0.45 for c in win_centers] + [c + 0.45 for c in win_centers] + [hx]
    # simpler: full wall then cut conceptually via segments
    x_cursor = -hx
    for cx in win_centers:
        # solid to left of window
        if cx - 0.48 > x_cursor:
            bc.box_bm(bm, x_cursor, cx - 0.48, hy - TW, hy, 0.35, ZEAVE)
        # under / over window
        bc.box_bm(bm, cx - 0.48, cx + 0.48, hy - TW, hy, 0.35, 1.55)
        bc.box_bm(bm, cx - 0.48, cx + 0.48, hy - TW, hy, 2.55, ZEAVE)
        # jambs already in under/over; side pier next loop
        x_cursor = cx + 0.48
    if x_cursor < hx:
        bc.box_bm(bm, x_cursor, hx, hy - TW, hy, 0.35, ZEAVE)
    # fill between windows (between right of win and left of next) — already via x_cursor
    # Add mid piers between windows explicitly
    for i in range(len(win_centers) - 1):
        a = win_centers[i] + 0.48
        b = win_centers[i + 1] - 0.48
        if b > a:
            bc.box_bm(bm, a, b, hy - TW, hy, 0.35, ZEAVE)
    bc.wear_stone(bm, 0.011, 4.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Nave_Rear', bm, limestone, False))

    # Rear window arches
    for cx in win_centers:
        bm = bmesh.new()
        bc.arch_opening_ring(bm, cx, 0.0, 2.10, 0.38, 0.52, hy - TW - 0.02, hy + 0.04, segs=12)
        parts.append(bc.bm_to_object(f'_rarch{cx}', bm, limestone_dark, True))

    # Side walls ±X: long run with 2 windows each; +X has shut side door
    for sx, name, has_door in ((-1, 'L', False), (1, 'R', True)):
        bm = bmesh.new()
        x_out = sx * hx
        x_in = sx * (hx - TW)
        xa, xb = min(x_out, x_in), max(x_out, x_in)
        # windows at y = -1.2 and +1.2 (if door, skip +1.2 for door bay)
        win_ys = [-1.3, 1.3] if not has_door else [-1.3]
        y_cursor = -hy + TW
        # door bay on +X around y=1.0
        segments_y = [-hy + TW]
        for wy in win_ys:
            segments_y.extend([wy - 0.42, wy + 0.42])
        if has_door:
            segments_y.extend([0.40, 1.70])  # door opening y range, clear 1.30 m
        segments_y.append(hy - TW)
        # Build continuous solid strips and punch openings
        # Approach: solid strips between openings
        openings = []
        for wy in win_ys:
            openings.append(('win', wy - 0.40, wy + 0.40, 1.45, 2.45))
        if has_door:
            openings.append(('door', 0.40, 1.70, 0.35, 2.35))
        openings.sort(key=lambda o: o[1])

        y0 = -hy + TW
        for kind, ya, yb, zlo, zhi in openings:
            if ya > y0 + 0.02:
                bc.box_bm(bm, xa, xb, y0, ya, 0.35, ZEAVE)
            # under opening
            if zlo > 0.35:
                bc.box_bm(bm, xa, xb, ya, yb, 0.35, zlo)
            # over opening
            if zhi < ZEAVE:
                bc.box_bm(bm, xa, xb, ya, yb, zhi, ZEAVE)
            y0 = yb
        if y0 < hy - TW:
            bc.box_bm(bm, xa, xb, y0, hy - TW, 0.35, ZEAVE)

        bc.wear_stone(bm, 0.01, 6 + sx)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bc.bm_to_object(f'Nave_Side{name}', bm, limestone, False))

        # window frames
        for wy in win_ys:
            bm2 = bmesh.new()
            bc.arch_opening_ring(bm2, sx * (hx - TW * 0.5), 0.0, 2.05, 0.32, 0.45,
                                 wy - 0.02 if False else (xa - 0.02 if sx < 0 else xb - 0.02),
                                 (xa + 0.02 if sx < 0 else xb + 0.02) if False else (
                                     min(xa, xb) - 0.04 if sx < 0 else max(xa, xb) + 0.04
                                 ), segs=10)
            # redo cleaner: arch in YZ plane is awkward with helper — use simple stone frame boxes
            bm2.free()
            bm2 = bmesh.new()
            if sx < 0:
                xf0, xf1 = xa - 0.05, xa + 0.06
            else:
                xf0, xf1 = xb - 0.06, xb + 0.05
            bc.box_bm(bm2, xf0, xf1, wy - 0.42, wy + 0.42, 1.40, 1.48)
            bc.box_bm(bm2, xf0, xf1, wy - 0.42, wy + 0.42, 2.42, 2.52)
            bc.box_bm(bm2, xf0, xf1, wy - 0.42, wy - 0.32, 1.48, 2.42)
            bc.box_bm(bm2, xf0, xf1, wy + 0.32, wy + 0.42, 1.48, 2.42)
            parts.append(bc.bm_to_object(f'_sframe{name}{wy}', bm2, limestone_dark, False))

    # Corner buttress stubs (Romanesque massing)
    for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
        bm = bmesh.new()
        x0 = sx * hx
        y0 = sy * hy
        bc.box_bm(bm,
                  min(x0, x0 + sx * 0.55), max(x0, x0 + sx * 0.55),
                  min(y0, y0 + sy * 0.55), max(y0, y0 + sy * 0.55),
                  0.0, ZEAVE - 0.15)
        # taper top
        for v in bm.verts:
            if v.co.z > ZEAVE - 0.6:
                v.co.x -= sx * 0.08
                v.co.y -= sy * 0.08
        bc.wear_stone(bm, 0.01, 9)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        parts.append(bc.bm_to_object(f'_butt{sx}{sy}', bm, limestone_dark, False))

    return bc.join_named('Nave_Stone', parts)


def make_roof(tile, oak):
    parts = []
    hx, hy = W * 0.5 + 0.25, D * 0.5 + 0.22
    bm = bmesh.new()
    bc.pitch_roof_bm(bm, -hx, hx, -hy, hy, ZEAVE - 0.08, ZRIDGE, ridge_along_x=True)
    for v in bm.verts:
        if v.co.z > ZEAVE:
            v.co.z += 0.02 * math.sin(v.co.x * 2.8)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Nave_Roof', bm, tile, False))

    bm = bmesh.new()
    bc.box_bm(bm, -hx + 0.15, hx - 0.15, -0.1, 0.1, ZRIDGE - 0.05, ZRIDGE + 0.1)
    parts.append(bc.bm_to_object('Nave_Ridge', bm, tile, False))

    # Gable end coping on ±X
    for sx in (-1, 1):
        bm = bmesh.new()
        # thin gable triangle suggestion
        x = sx * (W * 0.5)
        bc.box_bm(bm, x - 0.08 if sx > 0 else x, x if sx > 0 else x + 0.08,
                  -hy + 0.1, hy - 0.1, ZEAVE - 0.1, ZEAVE + 0.15)
        parts.append(bc.bm_to_object(f'_gable{sx}', bm, oak, False))

    return bc.join_named('Nave_RoofGroup', parts)


def make_side_door(oak, iron):
    parts = []
    # Shut wooden side door on +X — leaf fills 1.30 m clear opening (GD ≥1.2)
    x = W * 0.5 - TW * 0.55
    y0, y1 = 0.45, 1.65  # 1.20 m leaf inside 1.30 clear
    bm = bmesh.new()
    bc.box_bm(bm, x - 0.04, x + 0.02, y0, y1, 0.40, 2.30)
    for v in bm.verts:
        if abs(v.co.x - (x + 0.02)) < 0.01:
            seam = abs((v.co.y - y0) % 0.2 - 0.1)
            if seam < 0.015:
                v.co.x += 0.006
    parts.append(bc.bm_to_object('Nave_SideDoor', bm, oak, False))
    for z in (0.7, 1.3, 1.95):
        bm = bmesh.new()
        bc.box_bm(bm, x + 0.01, x + 0.03, y0 + 0.05, y0 + 0.45, z - 0.03, z + 0.03)
        parts.append(bc.bm_to_object(f'_dstrap{z}', bm, iron, False))
    bm = bmesh.new()
    bc.box_bm(bm, x + 0.015, x + 0.035, y1 - 0.28, y1 - 0.12, 1.35, 1.50)
    parts.append(bc.bm_to_object('Nave_Latch', bm, iron, False))
    return bc.join_named('Nave_Wood', parts)


def make_mud(mud):
    parts = []
    for i, (mx, my, mr) in enumerate((
        (-2.5, -2.8, 0.3), (1.5, -2.9, 0.25), (3.5, 0.5, 0.2),
        (-3.8, 1.2, 0.22), (0.0, 2.7, 0.28),
    )):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=5, radius=mr)
        for v in bm.verts:
            v.co.z *= 0.32
            v.co.x *= 1.4
            v.co += Vector((mx, my, 0.02))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bc.bm_to_object(f'_mud{i}', bm, mud, True))
    return bc.join_named('Nave_Mud', parts)


def build():
    bc.clear_scene()
    limestone = bc.mat('Nave_Limestone', bc.PALETTE['limestone'], 0.90, specular=0.16)
    limestone_dark = bc.mat('Nave_LimestoneDark', bc.PALETTE['limestone_dark'], 0.92, specular=0.12)
    tile = bc.mat('Nave_Tile', bc.PALETTE['tile_dark'], 0.88, specular=0.16)
    oak = bc.mat('Nave_Oak', bc.PALETTE['oak'], 0.84, specular=0.20)
    iron = bc.mat('Nave_Iron', bc.PALETTE['iron'], 0.48, metallic=0.55, specular=0.35)
    mud = bc.mat('Nave_Mud', bc.PALETTE['mud'], 0.96, specular=0.06)
    meshes = [
        make_walls(limestone, limestone_dark),
        make_roof(tile, oak),
        make_side_door(oak, iron),
        make_mud(mud),
    ]
    meshes = [m for m in meshes if m]
    bc.plant_and_center(meshes)
    return meshes


def main():
    meshes = build()
    glb = os.path.join(bc.OUT_DIR, f'{STEM}.glb')
    bc.export_glb(glb)
    print('Exported', glb)
    bc.render_previews(STEM, cam_target=(0, 0, 3.0), dist_scale=1.15)
    bc.cleanup_preview_helpers()
    bc.export_glb(glb)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bc.write_scale(STEM, mesh_objs, [
        'footprint_target_m~=8.0x5.0',
        'doorway_clear_w_m=2.10',
        'doorway_front=-Y_porch_attach clear_inner_arch_m=2.10',
        'doorway_side_clear_w_m=1.30',
        'side_door=+X_shut',
        'collision=tight_to_mesh',
        'style=romanesque_rural_parish_occitan_1208',
    ])


if __name__ == '__main__':
    main()
