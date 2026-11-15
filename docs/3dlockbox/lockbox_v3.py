"""WirelessLock V3: wet/dry split housing, sealed lid, battery house with a sealed side lid.

Built on the V2 vendor geometry (WirelessLockV2.xbf). Model axes, front view (key side):
x right (battery/board side), y into the box (front skin y=0.4, lid top y=43.4), z up.

Rooms
- Wet room (x < ~3): top strike slot, electric lock, physical lock. Water may enter at the
  slot and leaves through the original drain channel in the bottom wall (the only one kept).
- Dry room (battery house + wireless board box): closed by an L-shaped partition wall and a
  gasket loop in the lid underside. The battery slides out of its house through a side
  opening framed on all four sides, closed by a plug lid with a closed gasket ring and two
  side screws.

Unchanged: button, mask, physical lock, electric lock, battery cell, wireless board box.
"""
from pathlib import Path

import build123d as bd
from cad import model, xbf

SRC = Path(__file__).with_name("WirelessLockV2.xbf")

# ---- shared numbers (mm) -------------------------------------------------------------
FLOOR_Y = 5.43          # inside face of the front skin
LID_Y = 33.43           # lid underside / body ledge
WALL = 4.0              # partition thickness
V1_X = 3.5              # partition centre, left of the battery house
H_Z = 131.75            # partition centre, over the battery house
V2_X = 39.0             # upright partition centre (x 37..41): e-lock reaches x 36.16
PATCH_X = 43.8          # jog round the e-lock side tab (x <= 41.24, z 159.4..164.4)
PATCH_Z0, PATCH_Z1 = 156.8, 166.9   # jog starts / ends (bars clear the tab by 0.5)
CAV_BOTTOM = 52.9       # cavity floor (inner bottom)
TOP_IN = 228.0          # cavity roof (inner top)

GASKET_W, GASKET_D = 2.5, 1.8   # groove for a 2.5 mm silicone/TPU cord
LOOP_BOTTOM_Z = 50.5
LOOP_TOP_Z = 230.5
LOOP_RIGHT_X = 115.5

# original diagonal drain channel under the battery: filled (dry room)
OLD_DRAIN_DRY = (69.46, 97.46, 5.43, 15.43, 22.88, 52.88)

GROMMET_D = 5.0
GROMMET_Z, GROMMET_Y = 161.5, 30.0   # between the jog's bars (z 158.8..164.9)

# battery house (fixed, in the housing) and battery lid (the old drawer end cap)
HOUSE_X0 = 6.3
HOUSE_Y1 = 31.4                 # top of the house walls (lid underside at 33.43)
HOUSE_IN_Y0 = 8.4               # house floor face
HOUSE_Z0, HOUSE_Z1 = 59.0, 129.1
OPEN_Y1 = LID_Y                 # side opening now y 5.43..33.43 (back bar above)
LEDGE_X1, LEDGE_Y0 = 117.7, 31.8  # lid ledge runs into the side wall; battery lid notched round it
SILL_H = 6.0                    # solid sill under the battery opening
# battery lid end cap: fill the mounting-tab pocket (smooth face)
CAP_X0, CAP_Y_FLAT, CAP_R = 117.46, 18.43, 25.0   # cap outline: flat to y 18.43, then R25
CAP_POCKET_Z = (80.9, 106.2)                      # tab pocket height (81.05..106.05)
# battery lid retention, screwed from the right side (the front face goes against the wall):
# an ear above and below the end cap sits flush in a recess in the housing side wall, and an
# M3 countersunk screw goes through each ear into a heat-set insert in the housing.
# Ears and screws are outboard of the cap gasket (x 128..130.5): wet side of the seal.
CAP_Z0, CAP_Z1 = 61.1, 157.1
EAR_T, EAR_H = 5.0, 11.0                   # ear thickness (x) and reach beyond the cap (z)
EAR_Y0, EAR_Y1 = FLOOR_Y, 17.43            # on the flat part of the cap side (y < 18.43)
EAR_CLEAR = 0.3                            # recess clearance round each ear
LOCK_CLEAR_D, LOCK_CSK_D = 3.4, 6.6        # M3 clearance, 90 deg countersink head
INSERT_D, INSERT_DEPTH = 4.0, 8.0          # M3 heat-set insert in the housing
CAP_FACE_X = 142.46

# battery house extents (from the V2 battery tray)
TRAY_TOP_Z = 129.1
TRAY_BOT_Z = 61.1
TRAY_X0, TRAY_X1 = 6.3, 117.5
BODY_X1 = TRAY_X1 - 0.5   # body features stop short of the battery lid


def _node(path):
    node = xbf.read(SRC)
    for name in path:
        node = next(k for k in node.children if k.label == name)
    return node


def _solid(path, index):
    return bd.Solid(_node(path).solids()[index].wrapped)


def box(x0, x1, y0, y1, z0, z1):
    return bd.Box(x1 - x0, y1 - y0, z1 - z0, align=bd.Align.MIN).moved(bd.Location((x0, y0, z0)))


def strip_path(points, width, y0, y1):
    """Union of axis-aligned bars of `width` along a polyline in XZ, from y0 to y1."""
    h = width / 2
    out = None
    for (xa, za), (xb, zb) in zip(points, points[1:]):
        bar = box(min(xa, xb) - h, max(xa, xb) + h, y0, y1, min(za, zb) - h, max(za, zb) + h)
        out = bar if out is None else out + bar
    return out


# ---- housing ---------------------------------------------------------------------------
def housing_body():
    body = _solid(["Box", "COMPOUND"], 0)

    # L-shaped partition: floor to lid, wet room left/above, dry room right/below
    # L-shaped partition, floor to lid; the upright jogs round the e-lock side tab and
    # stays 2.5 mm clear of the LED hole in the front (x 43.5..48.5, z 177.5..182.5)
    partition = strip_path(
        [(V1_X, CAV_BOTTOM - 3), (V1_X, H_Z), (V2_X, H_Z), (V2_X, PATCH_Z0),
         (PATCH_X, PATCH_Z0), (PATCH_X, PATCH_Z1), (V2_X, PATCH_Z1), (V2_X, TOP_IN + 3)],
        WALL, FLOOR_Y - 0.5, LID_Y,
    )
    # battery house: fixed U-channel (floor, two side walls, inner end wall), open at the side
    # opening (+x) and towards the lid (+y). The battery slides in and out along x.
    house = (box(HOUSE_X0, CAP_X0 - 0.15, FLOOR_Y - 0.5, HOUSE_Y1, HOUSE_Z0, HOUSE_Z1)
             - box(HOUSE_X0 + 3, CAP_X0 + 1, HOUSE_IN_Y0, HOUSE_Y1 + 1, HOUSE_Z0 + 5.1, HOUSE_Z1 - 3))
    # back bar: closes the side opening's back edge (it was open to the lid side), so the
    # battery lid is framed on all four sides and its gasket ring is one closed loop
    back_bar = cap_outline(CAP_Z0 - SILL_H, CAP_Z1 + 0.01) & box(CAP_X0, CAP_FACE_X, OPEN_Y1, 44.0,
                                                               CAP_Z0 - SILL_H, CAP_Z1 + 0.01)
    old_drain_fill = box(*OLD_DRAIN_DRY)
    # old battery-cap mounting-screw hole through the front skin (x 127.89, z 93.55): filled
    front_screw_fill = bd.Cylinder(4.15, 5.0, rotation=(90, 0, 0)).moved(
        bd.Location((127.89, 2.93, 93.55)))
    # dry floor plinth: closes the old bottom channel under the battery, carries the house
    plinth = box(V1_X + WALL / 2, BODY_X1, FLOOR_Y - 0.5, 31.0, 50.0, 59.6)
    # lid ledge on the right wall, so the gasket loop has a land there
    # (runs into the side wall / back bar: no hairline gap for water to bypass the loop)
    ledge = box(LOOP_RIGHT_X - 2, LEDGE_X1, LEDGE_Y0, LID_Y, CAV_BOTTOM - 1, TOP_IN + 1)

    # sill: solid floor under the whole battery opening (the back strip was hollow, open to the
    # outside groove below), so the lid's bottom gasket has a land all the way across
    sill = cap_outline(CAP_Z0 - SILL_H, CAP_Z0 - 0.02) & box(CAP_X0, CAP_FACE_X, FLOOR_Y, OPEN_Y1,
                                                          CAP_Z0 - SILL_H, CAP_Z0 - 0.02)
    body = (body + partition + house + back_bar + sill + plinth + ledge + old_drain_fill
            + front_screw_fill)

    # cable grommet through the patch (electric lock harness to the board), above the e-lock
    grommet = bd.Cylinder(GROMMET_D / 2, 8, rotation=(0, 90, 0)).moved(
        bd.Location((PATCH_X, GROMMET_Y, GROMMET_Z)))
    # re-open the bottom-right lid screw hole the plinth covers (blind, r1.4, from V2)
    screw = bd.Cylinder(1.4, LID_Y - FLOOR_Y, rotation=(90, 0, 0)).moved(
        bd.Location((109.96, (FLOOR_Y + LID_Y) / 2, 55.38)))
    # ear recesses and insert holes in the side wall, above and below the battery opening
    c = EAR_CLEAR
    ex0 = CAP_FACE_X - EAR_T
    recesses = (box(ex0 - c, CAP_FACE_X + 1, EAR_Y0 - c, EAR_Y1 + c, CAP_Z0 - EAR_H - c, CAP_Z0 + 0.05)
                + box(ex0 - c, CAP_FACE_X + 1, EAR_Y0 - c, EAR_Y1 + c, CAP_Z1 - 0.05, CAP_Z1 + EAR_H + c))
    inserts = None
    for z in ear_screw_zs():
        ins = bd.Cylinder(INSERT_D / 2, INSERT_DEPTH, rotation=(0, -90, 0),
                          align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).moved(
            bd.Location((ex0 - c + 0.01, ear_screw_y(), z)))
        inserts = ins if inserts is None else inserts + ins
    for x, z in board_screw_points():
        inserts = inserts + bd.Cylinder(BOARD_INSERT_D / 2, BOARD_INSERT_DEPTH, rotation=(90, 0, 0),
                                        align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).moved(
            bd.Location((x, FLOOR_Y + 0.01, z)))
    body = body - grommet - screw - recesses - inserts - box(*BAT_NOTCH) - pry_housing_cuts()
    return body


def ear_screw_zs():
    return (CAP_Z0 - EAR_H / 2, CAP_Z1 + EAR_H / 2)


def ear_screw_y():
    return (EAR_Y0 + EAR_Y1) / 2


def housing_lid():
    lid = _solid(["Box", "COMPOUND"], 1)
    # closed gasket loop round the dry room, cut into the lid underside
    loop = strip_path(
        [
            (V1_X, LOOP_BOTTOM_Z), (LOOP_RIGHT_X, LOOP_BOTTOM_Z), (LOOP_RIGHT_X, LOOP_TOP_Z),
            (V2_X, LOOP_TOP_Z), (V2_X, PATCH_Z1), (PATCH_X, PATCH_Z1), (PATCH_X, PATCH_Z0),
            (V2_X, PATCH_Z0), (V2_X, H_Z), (V1_X, H_Z), (V1_X, LOOP_BOTTOM_Z),
        ],
        GASKET_W, LID_Y - 0.01, LID_Y + GASKET_D,
    )
    return lid - loop


def cap_outline(z0, z1):
    """The side cap's outline over z0..z1: flat side to y 18.43, then the R25 back corner."""
    corner = bd.Cylinder(CAP_R, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
                         ).moved(bd.Location((CAP_X0, CAP_Y_FLAT, z0)))
    return (box(CAP_X0, CAP_FACE_X, FLOOR_Y, CAP_Y_FLAT, z0, z1)
            + (corner & box(CAP_X0, CAP_FACE_X, CAP_Y_FLAT, CAP_Y_FLAT + CAP_R, z0, z1)))


def battery_lid_body():
    """The V2 battery tray's end cap on its own, as a plug lid for the side opening."""
    tray = _solid(["Battery"], 1) & box(CAP_X0 - 0.05, CAP_FACE_X + 0.1, FLOOR_Y - 0.1, OPEN_Y1,
                                         CAP_Z0 - 0.1, CAP_Z1 + 0.1)
    # fill the mounting-tab pocket (and its screw hole) so the end cap face is smooth:
    # the cap's own outline (flat face + R25 back corner), over the pocket's height
    z0, z1 = CAP_POCKET_Z
    corner = bd.Cylinder(CAP_R, z1 - z0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
                         ).moved(bd.Location((CAP_X0, CAP_Y_FLAT, z0)))
    pocket_fill = (box(CAP_X0, CAP_FACE_X, FLOOR_Y, CAP_Y_FLAT, z0, z1)
                   + (corner & box(CAP_X0, CAP_FACE_X, CAP_Y_FLAT, CAP_Y_FLAT + CAP_R, z0, z1)))
    # fill the button access hole (r2.5 along x, y 19.43, z 143.09), trimmed to the cap outline
    bz0, bz1 = 140.0, 146.2
    b_corner = bd.Cylinder(CAP_R, bz1 - bz0, align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)
                           ).moved(bd.Location((CAP_X0, CAP_Y_FLAT, bz0)))
    b_env = (box(CAP_X0, CAP_FACE_X, FLOOR_Y, CAP_Y_FLAT, bz0, bz1)
             + (b_corner & box(CAP_X0, CAP_FACE_X, CAP_Y_FLAT, CAP_Y_FLAT + CAP_R, bz0, bz1)))
    button_fill = bd.Cylinder(2.55, CAP_FACE_X - 131.0 + 1, rotation=(0, 90, 0)).moved(
        bd.Location(((131.0 + CAP_FACE_X + 1) / 2, 19.43, 143.09))) & b_env
    tray = ((tray + pocket_fill + button_fill)
            & box(CAP_X0 - 0.05, CAP_FACE_X + 0.1, FLOOR_Y - 0.1, OPEN_Y1, CAP_Z0 - 0.1, CAP_Z1 + 0.1)
            ).clean()
    # ears above and below the end cap, each with a countersunk M3 clearance hole
    ex0 = CAP_FACE_X - EAR_T
    ears = (box(ex0, CAP_FACE_X, EAR_Y0, EAR_Y1, CAP_Z0 - EAR_H, CAP_Z0 + 0.5)
            + box(ex0, CAP_FACE_X, EAR_Y0, EAR_Y1, CAP_Z1 - 0.5, CAP_Z1 + EAR_H))
    tray = tray + ears
    for z in ear_screw_zs():
        hole = bd.Cylinder(LOCK_CLEAR_D / 2, EAR_T + 0.2, rotation=(0, 90, 0)).moved(
            bd.Location((CAP_FACE_X - EAR_T / 2, ear_screw_y(), z)))
        csk_h = (LOCK_CSK_D - LOCK_CLEAR_D) / 2
        csk = bd.Cone(LOCK_CSK_D / 2, LOCK_CLEAR_D / 2, csk_h, rotation=(0, -90, 0),
                      align=(bd.Align.CENTER, bd.Align.CENTER, bd.Align.MIN)).moved(
            bd.Location((CAP_FACE_X + 0.01, ear_screw_y(), z)))
        tray = tray - hole - csk
    # clear the main-lid ledge where it runs past the battery lid's inner back edge
    ledge_relief = box(CAP_X0 - 0.2, LEDGE_X1 + 0.2, LEDGE_Y0 - 0.2, OPEN_Y1 + 0.1,
                       CAP_Z0 - 0.2, CAP_Z1 + 0.2)
    return tray - lid_ring() - ledge_relief - pry_lid_cuts()


LID_RING_X = 128.0     # closed gasket ring round the battery lid (all four sides)
# pry notches on the back seam (battery lid / back bar, y 33.43), at two heights. Two
# rectangles 1 x 8 mm sketched on the outer surface either side of the seam, each cut 2 mm
# deep square to the surface (the seam sits on the R25 corner): one in the housing, one in
# the lid. Together they make a 2 x 8 x 2 mm pocket for a screwdriver tip. Outside the lid
# gasket ring (x 128..130.5).
PRY_W, PRY_L, PRY_DEPTH = 1.0, 8.0, 2.0
PRY_ZS = (85.0, 133.0)
BACK_SEAM_X = 137.46                   # outer surface at the back seam (R25 corner at y 33.43)


def _pry_cut(z, side):
    """side +1: housing side of the seam, -1: lid side. Square to the R25 corner surface."""
    seam = bd.Vector(BACK_SEAM_X, OPEN_Y1, z)
    n = (seam - bd.Vector(CAP_X0, CAP_Y_FLAT, z)).normalized()       # outward surface normal
    t = bd.Vector(-n.Y, n.X, 0)                                       # tangent, towards the back
    plane = bd.Plane(origin=seam, x_dir=t, z_dir=n)
    x0, x1 = (0.0, PRY_W) if side > 0 else (-PRY_W, 0.0)
    return plane * bd.Box(x1 - x0, PRY_L, PRY_DEPTH + 1.0, align=bd.Align.MIN).moved(
        bd.Location((x0, -PRY_L / 2, -PRY_DEPTH)))


def pry_housing_cuts():
    out = None
    for z in PRY_ZS:
        out = _pry_cut(z, +1) if out is None else out + _pry_cut(z, +1)
    return out


def pry_lid_cuts():
    out = None
    for z in PRY_ZS:
        out = _pry_cut(z, -1) if out is None else out + _pry_cut(z, -1)
    return out


def lid_ring(depth=GASKET_D):
    g0, g1 = LID_RING_X, LID_RING_X + GASKET_W
    y0, y1, z0, z1 = FLOOR_Y, OPEN_Y1, CAP_Z0, CAP_Z1
    return (box(g0, g1, y0 - 0.01, y1 + 0.01, z0 - 0.01, z0 + depth)        # bottom
            + box(g0, g1, y0 - 0.01, y1 + 0.01, z1 - depth, z1 + 0.01)      # top
            + box(g0, g1, y0 - 0.01, y0 + depth, z0, z1)                    # front
            + box(g0, g1, y1 - depth, y1 + 0.01, z0, z1))                   # back


# ---- wireless board box: two ears screwed to the housing floor ----------------------------
# Ears sit on the floor (front skin) beside the box: one off the left side near the top, one
# off the bottom near the right, diagonal for stability. M3 pan-head screw from inside (lid
# off) into a short M3 heat-set insert in the 5 mm front skin (1 mm left to the outside).
BOARD_EAR_T = 3.0                         # ear thickness (y), from the box's floor face
BOARD_EAR_W, BOARD_EAR_L = 7.0, 10.0      # reach out from the box, length along its side
BOARD_EARS = ((47.93, 215.0), (98.0, 153.2))   # screw centres (x, z)
BOARD_SCREW_D = 3.4
BOARD_INSERT_D, BOARD_INSERT_DEPTH = 4.0, 4.0
BOARD_Y0 = 5.5                            # board box floor face


# cable entries: slot in the box floor under the 10-pin JST, hole in the right wall for the
# button lead (to the 4-pin JST)
BOX_SLOT = (64.0, 91.0, 10.5, 19.0, 158.3, 160.1)
BOX_SIDE_HOLE = dict(d=4.0, y=23.0, z=197.5)
BOX_LED_HOLE = dict(d=3.0, y=20.0, z=207.0)    # left wall, LED lead in

# status LED: 5 mm (T-1 3/4) in the front hole (x 46, z 180), dome flush with the front face,
# flange on the inside of the front skin; fit with a drop of clear sealant
LED_X, LED_Z = 46.0, 180.0
FRONT_Y = 0.43


def board_screw_points():
    return BOARD_EARS


def board_tray_body():
    tray = _solid(["WirelessBoard", "COMPOUND"], 1)
    (lx, lz), (bx, bz) = BOARD_EARS
    y0, y1 = BOARD_Y0, BOARD_Y0 + BOARD_EAR_T
    left = box(lx - BOARD_EAR_W / 2, 51.43 + 0.01, y0, y1, lz - BOARD_EAR_L / 2, lz + BOARD_EAR_L / 2)
    bottom = box(bx - BOARD_EAR_L / 2, bx + BOARD_EAR_L / 2, y0, y1, bz - BOARD_EAR_W / 2, 158.45 + 0.01)
    tray = tray + left + bottom
    for x, z in BOARD_EARS:
        tray = tray - bd.Cylinder(BOARD_SCREW_D / 2, BOARD_EAR_T + 0.2, rotation=(90, 0, 0)).moved(
            bd.Location((x, (y0 + y1) / 2, z)))
    tray = tray - box(*BOX_SLOT)
    tray = tray - bd.Cylinder(BOX_SIDE_HOLE["d"] / 2, 3, rotation=(0, 90, 0)).moved(
        bd.Location((105.2, BOX_SIDE_HOLE["y"], BOX_SIDE_HOLE["z"])))
    tray = tray - bd.Cylinder(BOX_LED_HOLE["d"] / 2, 3, rotation=(0, 90, 0)).moved(
        bd.Location((52.2, BOX_LED_HOLE["y"], BOX_LED_HOLE["z"])))
    return tray


def led_body():
    r = 2.5
    dome_c = FRONT_Y + r                          # dome tip flush with the front face
    body = bd.Solid.make_cylinder(r, FLOOR_Y - dome_c, bd.Plane(origin=(LED_X, dome_c, LED_Z),
                                                                 z_dir=(0, 1, 0)))
    dome = bd.Solid.make_sphere(r, bd.Plane(origin=(LED_X, dome_c, LED_Z))) & box(
        LED_X - r, LED_X + r, FRONT_Y, dome_c, LED_Z - r, LED_Z + r)
    flange = bd.Solid.make_cylinder(2.9, 1.0, bd.Plane(origin=(LED_X, FLOOR_Y, LED_Z), z_dir=(0, 1, 0)))
    return body + dome + flange


# ---- cables -------------------------------------------------------------------------------
# Routed as round bundles. Pin assignment on the PCB is not known: the lock and battery
# leads land on the 10-pin JST (left / right end), the button lead on the 4-pin JST.
CABLES = {
    # electric lock wire tab (x 36.3..41.2, y 17.8..22.8, z 159.4..164.4) -> up off the tab
    # -> straight through the partition grommet -> under the PCB box -> 10-pin JST, left end
    "cable_lock": (3.5, [(39.0, 22.9, 161.9), (39.0, 30.0, GROMMET_Z), (48.5, 30.0, GROMMET_Z),
                         (48.5, 30.0, 153.0), (68.0, 16.3, 153.0), (68.0, 16.3, 165.7)]),
    # battery lead: cell top, right end -> plug, both sit in the battery house next to the lid
    "cable_battery_lead": (3.0, [(110.5, 22.0, 108.0), (114.5, 24.5, 110.0), (114.5, 24.5, 115.0),
                                 (112.0, 24.5, 115.0)]),
    # PCB side: 10-pin JST -> down into the house through a notch in its top wall -> slack
    # loop over the battery (~110 mm spare: slide the battery ~60 mm out, unplug outside)
    # -> socket
    "cable_battery_pcb": (3.0, [(88.0, 16.3, 165.7), (88.0, 16.3, 152.0), (88.0, 28.5, 147.0),
                                (88.0, 28.5, 123.0), (30.0, 28.5, 123.0), (30.0, 28.5, 118.5),
                                (95.0, 24.5, 115.0), (100.0, 24.5, 115.0)]),
    # status LED (back of its flange) -> up beside the PCB box -> left-wall hole -> 2-pin header
    "cable_led": (2.0, [(LED_X, FLOOR_Y + 1.0, LED_Z), (LED_X, 12.0, LED_Z), (48.5, 20.0, 186.0),
                        (48.5, 20.0, 207.0), (78.4, 20.0, 207.0), (78.4, 18.6, 206.8)]),
    # reset button terminals -> up beside the PCB box -> right-wall hole -> 4-pin JST
    "cable_button": (2.5, [(105.0, 19.4, 143.1), (105.0, 19.4, 150.5), (107.6, 23.0, 152.0),
                           (107.6, 23.0, 197.5), (101.1, 23.0, 197.5), (101.1, 20.6, 197.5)]),
}
BAT_NOTCH = (85.0, 91.0, 23.5, 31.6, 125.9, 129.3)   # cable notch in the house's top wall
# inline battery connector pair (2-pin, e.g. JST-VH or XT30 size), on top of the battery at
# its lid end: open the lid, slide the battery out, unplug
BAT_PLUG = (106.0, 112.0, 22.0, 27.0, 112.0, 118.0)    # on the battery lead
BAT_SOCKET = (100.0, 106.0, 22.0, 27.0, 112.0, 118.0)  # on the PCB lead


def cable(points, d):
    """Straight runs between the route points, joined by ball elbows."""
    r = d / 2
    pts = [bd.Vector(*p) for p in points]
    out = None
    for a, b in zip(pts, pts[1:]):
        seg = b - a
        run = bd.Solid.make_cylinder(r, seg.length, bd.Plane(origin=a, z_dir=seg))
        out = run if out is None else out + run
    for p in pts[1:-1]:
        out = out + bd.Solid.make_sphere(r, bd.Plane(origin=p))
    return out


def _named(shape, label, color):
    shape.label = label
    shape.color = color
    return shape


@model
def housing():
    return _named(housing_body(), "housing", "#3b4cc0")


@model
def lid():
    return _named(housing_lid(), "lid", "#6f7fd8")


@model
def battery_lid():
    return _named(battery_lid_body(), "battery_lid", "#d9605a")


@model
def status_led():
    return _named(led_body(), "status_led", "#ff3b30cc")


@model
def board_box_tray():
    return _named(board_tray_body(), "board_box_tray", "#8a8a8a")


@model
def cables():
    parts = []
    colors = {"cable_lock": "#e8a33d", "cable_battery_lead": "#c0392b",
              "cable_battery_pcb": "#c0392b", "cable_button": "#2e86c1", "cable_led": "#27ae60"}
    for name, (d, pts) in CABLES.items():
        parts.append(_named(cable(pts, d), name, colors[name]))
    parts.append(_named(box(*BAT_PLUG), "battery_plug", "#f2f2f2"))
    parts.append(_named(box(*BAT_SOCKET), "battery_socket", "#222222"))
    return bd.Compound(children=parts, label="cables")


@model
def lockbox_v3():
    keep = [_node([name]) for name in ("Button_12mm.step", "Mask", "Physical_Lock", "Electric_Lock")]
    pcb = next(k for k in _node(["WirelessBoard"]).children if k.label != "COMPOUND")
    board_lid = _named(_solid(["WirelessBoard", "COMPOUND"], 0), "board_box_lid", "#b0b0b0")
    keep.append(bd.Compound(children=[pcb, board_box_tray().shape, board_lid], label="WirelessBoard"))
    cell = _named(_solid(["Battery"], 0), "battery_cell", "#555555")
    return bd.Compound(
        children=[housing().shape, lid().shape, battery_lid().shape, cell, status_led().shape, *keep,
                  cables().shape],
        label="lockbox_v3",
    )


if __name__ == "__main__":
    lockbox_v3()
