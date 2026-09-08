"""Blender: Simple canvas/wood wayside market stall (Broken Seal).

Narbonne / road-market lean frame: oak posts, crossbeams, faded canvas awning,
plank counter, empty crates. Dirt-and-mail Occitania 1208 — no glow, no Kenney.
Rebuild:
  /usr/bin/blender -b -P tools/make_market_stall.py
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

STEM = 'market_stall'
# Footprint ~2.2 x 1.4 m — place off-lane beside road


def make_frame(oak, oak_dark):
    parts = []
    # Four corner posts
    posts = [(-0.95, -0.55), (0.95, -0.55), (-0.95, 0.55), (0.95, 0.55)]
    heights = [1.85, 1.85, 2.15, 2.15]  # rear taller for lean awning
    for i, ((px, py), h) in enumerate(zip(posts, heights)):
        bm = bmesh.new()
        bc.box_bm(bm, px - 0.05, px + 0.05, py - 0.05, py + 0.05, 0.0, h)
        for v in bm.verts:
            v.co.x += 0.003 * math.sin(v.co.z * 9 + i)
        parts.append(bc.bm_to_object(f'_post{i}', bm, oak, False))

    # Top rails
    for (y, z0, z1) in ((-0.55, 1.78, 1.88), (0.55, 2.08, 2.18)):
        bm = bmesh.new()
        bc.box_bm(bm, -1.0, 1.0, y - 0.04, y + 0.04, z0, z1)
        parts.append(bc.bm_to_object(f'_rail{y}', bm, oak_dark, False))
    # Side rails
    for x in (-0.95, 0.95):
        bm = bmesh.new()
        # slanted top side beam
        bc.box_bm(bm, x - 0.04, x + 0.04, -0.58, 0.58, 1.80, 1.90)
        for v in bm.verts:
            # raise toward +Y (rear)
            t = (v.co.y + 0.58) / 1.16
            v.co.z += 0.28 * t
        parts.append(bc.bm_to_object(f'_siderail{x}', bm, oak, False))

    # Cross brace under counter
    bm = bmesh.new()
    bc.box_bm(bm, -0.9, 0.9, -0.08, 0.08, 0.55, 0.62)
    parts.append(bc.bm_to_object('Stall_Brace', bm, oak_dark, False))

    return bc.join_named('Stall_Frame', parts)


def make_awning(canvas, canvas_dark, rope_mat):
    parts = []
    # Canvas roof — lean from rear high to front low, slight sag
    bm = bmesh.new()
    # grid of verts
    nx, ny = 6, 4
    grid = []
    for j in range(ny + 1):
        row = []
        ty = j / ny
        y = -0.62 + ty * 1.24
        for i in range(nx + 1):
            tx = i / nx
            x = -1.05 + tx * 2.10
            z_edge = 1.88 + ty * 0.28
            sag = 0.06 * math.sin(tx * math.pi) * math.sin(ty * math.pi + 0.2)
            # scalloped front edge
            if j == 0:
                sag -= 0.04 * abs(math.sin(tx * math.pi * 3))
            row.append(bm.verts.new((x, y, z_edge - sag)))
        grid.append(row)
    # underside offset
    grid2 = []
    for j in range(ny + 1):
        row = []
        for i in range(nx + 1):
            v = grid[j][i]
            row.append(bm.verts.new((v.co.x, v.co.y, v.co.z - 0.025)))
        grid2.append(row)
    bm.verts.ensure_lookup_table()
    for j in range(ny):
        for i in range(nx):
            bm.faces.new((grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]))
            bm.faces.new((grid2[j][i], grid2[j + 1][i], grid2[j + 1][i + 1], grid2[j][i + 1]))
    # sides
    for j in range(ny):
        bm.faces.new((grid[j][0], grid[j + 1][0], grid2[j + 1][0], grid2[j][0]))
        bm.faces.new((grid[j][nx], grid2[j][nx], grid2[j + 1][nx], grid[j + 1][nx]))
    for i in range(nx):
        bm.faces.new((grid[0][i], grid2[0][i], grid2[0][i + 1], grid[0][i + 1]))
        bm.faces.new((grid[ny][i], grid[ny][i + 1], grid2[ny][i + 1], grid2[ny][i]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    parts.append(bc.bm_to_object('Stall_Canvas', bm, canvas, False))

    # Front scallop flaps
    for i, x in enumerate((-0.7, -0.2, 0.3, 0.75)):
        bm = bmesh.new()
        bc.box_bm(bm, x - 0.12, x + 0.12, -0.68, -0.58, 1.55, 1.82)
        for v in bm.verts:
            if v.co.z < 1.65:
                v.co.x *= 0.85
                v.co.y -= 0.02
        parts.append(bc.bm_to_object(f'_flap{i}', bm, canvas_dark if i % 2 else canvas, False))

    # Tie ropes at corners
    for i, (x, y, z0, z1) in enumerate((
        (-1.0, -0.55, 1.85, 1.70), (1.0, -0.55, 1.85, 1.70),
    )):
        bm = bmesh.new()
        segs = 5
        path = []
        for k in range(segs):
            t = k / (segs - 1)
            path.append(Vector((x + 0.02 * math.sin(t * 4), y - 0.08 * t, z0 + (z1 - z0) * t)))
        # simple tube
        r = 0.012
        rings = []
        for p in path:
            ring = []
            for s in range(5):
                a = (s / 5) * math.tau
                ring.append(bm.verts.new((p.x + r * math.cos(a), p.y + r * math.sin(a), p.z)))
            rings.append(ring)
        bm.verts.ensure_lookup_table()
        for k in range(len(rings) - 1):
            for s in range(5):
                s2 = (s + 1) % 5
                bm.faces.new((rings[k][s], rings[k][s2], rings[k + 1][s2], rings[k + 1][s]))
        parts.append(bc.bm_to_object(f'_rope{i}', bm, rope_mat, True))

    return bc.join_named('Stall_Awning', parts)


def make_counter(oak, oak_dark, canvas):
    parts = []
    # Plank counter
    bm = bmesh.new()
    bc.box_bm(bm, -0.95, 0.95, -0.45, 0.35, 0.78, 0.88)
    for v in bm.verts:
        v.co.z += 0.004 * math.sin(v.co.x * 8)
    parts.append(bc.bm_to_object('Stall_Counter', bm, oak, False))

    # Legs
    for x in (-0.75, 0.75):
        for y in (-0.30, 0.20):
            bm = bmesh.new()
            bc.box_bm(bm, x - 0.04, x + 0.04, y - 0.04, y + 0.04, 0.0, 0.80)
            parts.append(bc.bm_to_object(f'_cleg{x}{y}', bm, oak_dark, False))

    # Rear shelf plank
    bm = bmesh.new()
    bc.box_bm(bm, -0.85, 0.85, 0.35, 0.50, 1.05, 1.12)
    parts.append(bc.bm_to_object('Stall_Shelf', bm, oak, False))

    # Empty crates
    for i, (cx, cy, cz) in enumerate(((-0.55, 0.05, 0.0), (0.50, -0.15, 0.0))):
        bm = bmesh.new()
        s = 0.28
        # crate as open box walls
        t = 0.025
        bc.box_bm(bm, cx - s, cx + s, cy - s, cy + s, cz, cz + t)  # bottom
        bc.box_bm(bm, cx - s, cx + s, cy - s, cy - s + t, cz, cz + 0.28)
        bc.box_bm(bm, cx - s, cx + s, cy + s - t, cy + s, cz, cz + 0.28)
        bc.box_bm(bm, cx - s, cx - s + t, cy - s, cy + s, cz, cz + 0.28)
        bc.box_bm(bm, cx + s - t, cx + s, cy - s, cy + s, cz, cz + 0.28)
        parts.append(bc.bm_to_object(f'_crate{i}', bm, oak_dark, False))

    # Cloth remnant on counter
    bm = bmesh.new()
    bc.box_bm(bm, -0.25, 0.35, -0.35, -0.05, 0.88, 0.90)
    for v in bm.verts:
        v.co.z += 0.01 * math.sin(v.co.x * 10)
        if v.co.y < -0.25:
            v.co.z -= 0.15  # drapes over front
            v.co.y -= 0.05
    parts.append(bc.bm_to_object('Stall_Cloth', bm, canvas, False))

    # Mud under posts
    mud = bc.mat('Stall_Mud', bc.PALETTE['mud'], 0.97, specular=0.05)
    for i, (mx, my) in enumerate(((-0.95, -0.55), (0.95, -0.55), (-0.95, 0.55), (0.95, 0.55))):
        bm = bmesh.new()
        bmesh.ops.create_uvsphere(bm, u_segments=6, v_segments=3, radius=0.08)
        for v in bm.verts:
            v.co.z *= 0.3
            v.co += Vector((mx, my, 0.015))
            if v.co.z < 0:
                v.co.z = 0.002
        parts.append(bc.bm_to_object(f'_mud{i}', bm, mud, True))

    return bc.join_named('Stall_Goods', parts)


def build():
    bc.clear_scene()
    oak = bc.mat('Stall_Oak', bc.PALETTE['oak'], 0.88, specular=0.18)
    oak_dark = bc.mat('Stall_OakDark', bc.PALETTE['oak_dark'], 0.90, specular=0.15)
    # Faded sun-bleached canvas — dusty ochre/linen, no bright market fantasy
    canvas = bc.mat('Stall_Canvas', (0.52, 0.46, 0.34), 0.93, specular=0.08)
    canvas_dark = bc.mat('Stall_CanvasDark', (0.42, 0.36, 0.26), 0.94, specular=0.07)
    rope_mat = bc.mat('Stall_Rope', (0.40, 0.34, 0.22), 0.92, specular=0.1)
    meshes = [
        make_frame(oak, oak_dark),
        make_awning(canvas, canvas_dark, rope_mat),
        make_counter(oak, oak_dark, canvas),
    ]
    meshes = [m for m in meshes if m]
    bc.plant_and_center(meshes)
    return meshes


def main():
    meshes = build()
    glb = os.path.join(bc.OUT_DIR, f'{STEM}.glb')
    bc.export_glb(glb)
    print('Exported', glb)
    bc.render_previews(STEM, cam_target=(0, 0, 1.1),
                       views=[
                           ('front', (0.0, -4.5, 1.5)),
                           ('threequarter', (3.5, -3.5, 2.0)),
                       ])
    bc.cleanup_preview_helpers()
    bc.export_glb(glb)
    mesh_objs = [o for o in bpy.context.scene.objects if o.type == 'MESH']
    bc.write_scale(STEM, mesh_objs, [
        'footprint_target_m~=2.2x1.4',
        'reads=canvas_wood_wayside_market_stall',
        'collision=tight_to_mesh',
        'style=occitan_wayside_stall_1208_no_glow',
        'off_lane=1',
        'road_clear_m=2.4',
        'road_crown_x=[-1.2,1.2]_no_colliders',
        'place_band=soft_shoulder_|x|_1.2-4_or_hub_pocket',
        'hub_anchor_hint=Narbonne_gate_(+5,-44)_or_mile_(0,+22)_shoulder',
        'place=off_road_narbonne_road_market_edge',
    ])


if __name__ == '__main__':
    main()
