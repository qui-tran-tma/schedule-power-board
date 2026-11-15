"""Servo button pusher: SG90 + rack-and-pinion presses a 30 mm button, ESP32 mini controlled.

FDM printed (Bambu), PETG, 0.2 mm layers. Printed parts: base, top_plate, rack, push_pad, pinion.
Reference (not printed): SG90 servo, 30 mm button, ESP32 mini board.

Layout (mm, +Z up, base 100 x 50):
  - button pocket in left third, centred at BUTTON_X
  - button ring: 3 snap clips hook 0.8 mm over the button housing rim, 3 ribs hold it centred
  - 4 corner columns carry the top plate (M3 screws into the columns)
  - SG90 lies on its side behind a vertical wall on the top plate, held by its two ear screws,
    output shaft horizontal (along -Y); pinion on the shaft drives a vertical rack
  - rack slides in a slot + guide channel; a D18 round push pad with a square collar takes the
    rack's plain 6 x 6 end 11 mm deep (no twist) and is locked by one M2 cross screw (or a
    1.75 mm filament pin), pushes the D20 button cap
  - ESP32 mini (32 x 22) slides in from the open front edge (-Y) along two grooved rails that hold
    its two 22 mm ends (1 mm under each lip), stops on an end block, a 0.3 mm bump snaps it in

Check: cad model dfm "$ID" --build-volume 256x256x256
"""

import math

import build123d as bd
from cad import model
from bd_materials import plastics
from bd_materials.processes import fdm

# ---------------------------------------------------------------- parameters
BASE_L, BASE_W, BASE_T = 100.0, 50.0, 4.0
FIT = 0.3  # FDM clearance between mating parts

# button pocket (button D30, retaining wall 8 mm high)
BUTTON_D = 30.0
BUTTON_X, BUTTON_Y = -31.0, 0.0
POCKET_R = BUTTON_D / 2 + FIT
WALL_T = 2.0
WALL_H = 8.0
# assumed button: housing 10 mm tall, cap D18 3 mm tall -> cap top at z 17
BUTTON_HOUSING_H, BUTTON_CAP_D, BUTTON_CAP_H = 10.0, 20.0, 3.0  # inner press cap D20
# button retention: 3 snap clips hook over the housing's top rim, 3 crush ribs stop side play
CLIP_ANGLES = (60.0, 180.0, 300.0)  # deg about the button centre, 0 = +X (lead notch)
CLIP_W = 7.0  # tab width (tangential)
CLIP_SLIT = 1.0  # slit width either side of each tab
CLIP_HOOK = 0.8  # hook reach over the housing rim
CLIP_HOOK_H = 1.5
CLIP_GAP = 0.2  # hook underside above the housing top
RIB_ANGLES = (0.0, 120.0, 240.0)
RIB_W = 1.0
BUTTON_TOP_Z = BASE_T + BUTTON_HOUSING_H + BUTTON_CAP_H

# columns + top plate
COL = 10.0
COL_X, COL_Y = BASE_L / 2 - COL / 2, BASE_W / 2 - COL / 2
PLATE_Z = 40.0  # underside of top plate
PLATE_T = 4.0
PLATE_TOP = PLATE_Z + PLATE_T
M3_PILOT_D, M3_CLEAR_D = 2.5, 3.4

# gears: 20 teeth pinion, 20 deg pressure angle (no undercut from 17 teeth up).
# Module comes from the stroke: 180 deg of servo moves the rack half the pitch circumference,
# STROKE_180 = pi * RP, so m = 2 * STROKE_180 / (pi * Z) = 1.273 for 40 mm.
# Big teeth (2.9 mm deep, 4.0 mm pitch) print cleanly on FDM; the old 12 T m1.25 pinion did not.
# travel = RP * angle: 12.73 mm * pi/180 = 0.222 mm per servo degree (4.5 deg per mm).
# Force: SG90 stall ~0.18 N.m / 12.73 mm = ~14 N at the rack (old pinion ~24 N).
STROKE_180 = 40.0
Z_TEETH, PA = 20, math.radians(20)
MOD = 2 * STROKE_180 / (math.pi * Z_TEETH)
RP = MOD * Z_TEETH / 2
RA = RP + MOD  # tip radius
BACKLASH = 0.2
GEAR_T = 6.0  # face width (pinion and rack)

# rack: square 6 x 6 backing centred on the button, teeth on +X face
RACK_W = 6.0
RACK_BACK_X = BUTTON_X - RACK_W / 2
RACK_ROOT_X = BUTTON_X + RACK_W / 2
RACK_PITCH_X = RACK_ROOT_X + 1.25 * MOD
RACK_TIP_X = RACK_PITCH_X + 1.0 * MOD
FOOT_GAP = 5.0  # rest gap above the button cap
FOOT_Z = BUTTON_TOP_Z + FOOT_GAP
FOOT_H = 3.0  # pad disc thickness
PAD_FLOOR = 2.0  # pad material under the rack end
COLLAR_H = 10.0  # square collar above the pad disc; top (z 35) stays below the lowest tooth
COLLAR_WALL = 2.5
SOCKET_FIT = 0.1  # per side: snug slide fit on the 6 x 6 rack end
PIN_Z = FOOT_Z + PAD_FLOOR + 6.0  # M2 cross screw / 1.75 filament pin, along Y
PIN_PILOT_D, PIN_CLEAR_D = 1.8, 2.2  # self-tap into rack, clearance in collar
FOOT_D = 18.0  # round push pad, 1 mm inside the D20 button cap all round
# V rail on the guide back wall runs in a V groove down the rack's back face (45 deg flanks)
VRAIL_H = 1.0  # rail height off the wall (base half-width equals it)
VGROOVE_D = 1.3  # groove depth into the rack back (opening half-width equals it)
RACK_EXTRA_TEETH = 5  # extra teeth at the top for more stroke
RACK_TOP_Z = 74.0 + RACK_EXTRA_TEETH * math.pi * MOD
TEETH_Z0, TEETH_Z1 = 38.0, RACK_TOP_Z

# servo SG90 (nominal datasheet dims), lying on its side, shaft along -Y
SHAFT_X = RACK_PITCH_X + RP + 0.15  # pinion centre, +0.15 for print fit
SHAFT_Z = PLATE_TOP + RA + 2.0  # gear tips clear the top plate by 2 mm (shaft z 60)
SG_L, SG_W, SG_H = 22.5, 12.2, 22.7  # body length (X), width (Z), height (Y)
SG_EAR_L, SG_EAR_T = 32.2, 2.5
SG_EAR_FROM_TOP = 4.5  # ear top face below the shaft face
SG_HOLE_SPACING = 27.5
SG_SHAFT_FROM_END = 5.9
SG_TOP_Y = 4.5  # shaft face of the servo body
SG_BODY_CX = SHAFT_X + SG_L / 2 - SG_SHAFT_FROM_END
EAR_Y0 = SG_TOP_Y + SG_EAR_FROM_TOP
MOUNT_Y0 = EAR_Y0 + SG_EAR_T  # servo wall front face (ears seat here)
MOUNT_T = 4.0

# ESP32 mini cradle
ESP_L, ESP_W, ESP_T = 32.0, 22.0, 1.6  # X (long), Y (short), thickness
ESP_X, ESP_Y = 20.0, 0.0
ESP_SEAT_Z = BASE_T + 3.0
ESP_GRIP = 1.0  # board edge held under each rail lip (board has 1-1.5 mm free margin)
ESP_SLOT_FIT = 0.3  # groove height over board thickness, and edge clearance
ESP_LIP_T = 1.2
ESP_RAIL_OUT = 2.2  # rail wall beyond the groove
ESP_BUMP = 0.3  # snap bump at the entry end

def box(x0, x1, y0, y1, z0, z1):
    return bd.Box(x1 - x0, y1 - y0, z1 - z0).move(
        bd.Location(((x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2))
    )


def zcyl(r, z0, z1, x=0.0, y=0.0):
    return bd.Cylinder(r, z1 - z0).move(bd.Location((x, y, (z0 + z1) / 2)))


def ycyl(r, y0, y1, x=0.0, z=0.0):
    c = bd.Cylinder(r, y1 - y0).rotate(bd.Axis.X, 90)
    return c.move(bd.Location((x, (y0 + y1) / 2, z)))


def printed(part, color, label):
    part.material = plastics.petg(process=fdm(layer_height_mm=0.2))
    part.color = color
    part.label = label
    return part


# ---------------------------------------------------------------- gear geometry
def inv(a):
    return math.tan(a) - a


def pinion_profile_points():
    rb = RP * math.cos(PA)
    ra = RP + MOD
    rf = RP - 1.25 * MOD
    psi = math.pi / (2 * Z_TEETH) - (BACKLASH / 2) / (2 * RP)
    theta_b = psi + inv(PA)
    pts = []
    n = 8
    for k in range(Z_TEETH):
        c = 2 * math.pi * k / Z_TEETH

        def pol(r, a):
            return (r * math.cos(a), r * math.sin(a))

        pts.append(pol(rf, c - theta_b))
        flank = [rb + (ra - rb) * i / n for i in range(n + 1)]
        for r in flank:
            pts.append(pol(r, c - (psi + inv(PA) - inv(math.acos(rb / r)))))
        for r in reversed(flank):
            pts.append(pol(r, c + (psi + inv(PA) - inv(math.acos(rb / r)))))
        pts.append(pol(rf, c + theta_b))
    return pts


def pinion_body():
    """Pinion built axis +Z, servo-side hub at -Z (z -4..-3), then turned onto the shaft."""
    face = bd.Face(bd.Wire.make_polygon([bd.Vector(x, y, 0) for x, y in pinion_profile_points()], close=True))
    gear = bd.extrude(face, amount=GEAR_T).move(bd.Location((0, 0, -GEAR_T / 2)))
    hub = zcyl(5.0, -GEAR_T / 2 - 1.0, -GEAR_T / 2 + 0.01)
    body = gear + hub
    # SG90 spline bore (tune 4.7-4.9 for press fit) from hub face, M2 horn screw through
    body -= zcyl(2.4, -GEAR_T / 2 - 1.0, -GEAR_T / 2 - 1.0 + 3.5)
    body -= zcyl(1.1, -10, 10)
    return body


def v_prism(x_base, h, z0, z1):
    """Vertical 45 deg V ridge at y=0: base on the plane x=x_base, apex at x_base + h."""
    pts = [bd.Vector(x_base, -h, z0), bd.Vector(x_base, h, z0), bd.Vector(x_base + h, 0, z0)]
    return bd.extrude(bd.Face(bd.Wire.make_polygon(pts, close=True)), amount=z1 - z0, dir=(0, 0, 1))


def rack_body():
    p = math.pi * MOD
    t = math.tan(PA)
    half_s = p / 4 - BACKLASH / 4
    w_root = half_s + 1.25 * MOD * t
    w_tip = half_s - 1.0 * MOD * t
    z_bot = FOOT_Z + PAD_FLOOR
    pts = [(RACK_BACK_X, z_bot), (RACK_ROOT_X, z_bot)]
    # tooth centres phased so a gap sits on the pinion centre line (pinion tooth at 180 deg)
    k0 = math.ceil((TEETH_Z0 - SHAFT_Z - p / 2) / p)
    k = k0
    while True:
        zc = SHAFT_Z + p / 2 + k * p
        if zc + w_root > TEETH_Z1:
            break
        pts += [
            (RACK_ROOT_X, zc - w_root),
            (RACK_TIP_X, zc - w_tip),
            (RACK_TIP_X, zc + w_tip),
            (RACK_ROOT_X, zc + w_root),
        ]
        k += 1
    pts += [(RACK_ROOT_X, RACK_TOP_Z), (RACK_BACK_X, RACK_TOP_Z)]
    face = bd.Face(bd.Wire.make_polygon([bd.Vector(x, 0, z) for x, z in pts], close=True))
    bar = bd.extrude(face, amount=GEAR_T / 2, both=True)
    bar -= ycyl(PIN_PILOT_D / 2, -GEAR_T, GEAR_T, BUTTON_X, PIN_Z)
    bar -= v_prism(RACK_BACK_X - 0.5, VGROOVE_D + 0.5, z_bot - 1, RACK_TOP_Z + 1)  # guide groove
    return bar


def push_pad_body():
    pad = zcyl(FOOT_D / 2, FOOT_Z, FOOT_Z + FOOT_H, BUTTON_X, BUTTON_Y)
    pad = bd.chamfer(pad.edges().group_by(bd.Axis.Z)[0], 0.4)  # bed edge: elephant foot
    sx = RACK_W / 2 + SOCKET_FIT
    sy = GEAR_T / 2 + SOCKET_FIT
    cx, cy = sx + COLLAR_WALL, sy + COLLAR_WALL
    collar = box(BUTTON_X - cx, BUTTON_X + cx, BUTTON_Y - cy, BUTTON_Y + cy,
                 FOOT_Z + FOOT_H - 0.01, FOOT_Z + FOOT_H + COLLAR_H)
    collar = bd.fillet(collar.edges().filter_by(bd.Axis.Z), 1.0)
    pad += collar
    pad -= box(BUTTON_X - sx, BUTTON_X + sx, BUTTON_Y - sy, BUTTON_Y + sy,
               FOOT_Z + PAD_FLOOR, FOOT_Z + FOOT_H + COLLAR_H + 1)
    pad -= ycyl(PIN_CLEAR_D / 2, -cy - 1, cy + 1, BUTTON_X, PIN_Z)
    return pad


# ---------------------------------------------------------------- printed parts
@model
def base():
    body = box(-BASE_L / 2, BASE_L / 2, -BASE_W / 2, BASE_W / 2, 0, BASE_T)
    body = bd.fillet(body.edges().filter_by(bd.Axis.Z), 4.0)

    # button retaining ring
    ring = zcyl(POCKET_R + WALL_T, BASE_T - 0.01, BASE_T + WALL_H, BUTTON_X, BUTTON_Y)
    ring -= zcyl(POCKET_R, BASE_T - 0.02, BASE_T + WALL_H + 1, BUTTON_X, BUTTON_Y)
    # lead notch toward +X
    ring -= box(BUTTON_X + POCKET_R - 1, BUTTON_X + POCKET_R + WALL_T + 1, -3, 3, BASE_T - 0.1, BASE_T + 4)
    at = lambda shape, ang: shape.rotate(bd.Axis.Z, ang).move(bd.Location((BUTTON_X, BUTTON_Y, 0)))
    # snap clips: slit the wall either side, extend the tab up past the housing and hook inward
    housing_top = BASE_T + BUTTON_HOUSING_H
    hook_z0 = housing_top + CLIP_GAP
    hook_z1 = hook_z0 + CLIP_HOOK_H
    r_out = POCKET_R + WALL_T
    for ang in CLIP_ANGLES:
        for side in (-1, 1):
            yc = side * (CLIP_W / 2 + CLIP_SLIT / 2)
            ring -= at(box(POCKET_R - 2.0, r_out + 0.8, yc - CLIP_SLIT / 2, yc + CLIP_SLIT / 2,
                           BASE_T + 1.0, BASE_T + WALL_H + 1), ang)
        tab = box(POCKET_R, r_out, -CLIP_W / 2, CLIP_W / 2, BASE_T + WALL_H - 0.5, hook_z1)
        hook = box(BUTTON_D / 2 - CLIP_HOOK, POCKET_R + 0.01, -CLIP_W / 2, CLIP_W / 2, hook_z0, hook_z1)
        lead = hook.edges().filter_by(bd.Axis.Y).group_by(bd.Axis.Z)[-1].sort_by(bd.Axis.X)[0]
        hook = bd.chamfer(lead, 0.8)  # 45 deg lead-in ramp, 0.7 mm retaining face below it
        ring += at(tab + hook, ang)
    # crush ribs: touch the housing (zero clearance) so it cannot slide sideways
    for ang in RIB_ANGLES:
        ring += at(box(BUTTON_D / 2, POCKET_R + 0.01, -RIB_W / 2, RIB_W / 2, BASE_T + 4.5, BASE_T + WALL_H), ang)
    body += ring
    # lead hole under the button
    body -= zcyl(5.0, -1, BASE_T + 1, BUTTON_X, BUTTON_Y)

    # corner columns with M3 pilot holes
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * COL_X, sy * COL_Y
            col = box(x - COL / 2, x + COL / 2, y - COL / 2, y + COL / 2, BASE_T - 0.01, PLATE_Z)
            col = bd.fillet(col.edges().filter_by(bd.Axis.Z), 4.0)  # matches base corner radius
            col -= zcyl(M3_PILOT_D / 2, PLATE_Z - 12, PLATE_Z + 1, x, y)
            body += col

    # ESP32 slide-in rails on the two 22 mm ends (board edges at x = ESP_X +/- ESP_L/2), running
    # along Y out to the open front edge (-Y): the board slides out the front, clear of the button.
    y_in = ESP_Y - ESP_W / 2  # board entry edge (-Y, front)
    y_end = ESP_Y + ESP_W / 2 + 0.2  # end stop face (+Y)
    y_front = -BASE_W / 2 + 1.0  # rails run to the front edge to guide the board in
    groove_top = ESP_SEAT_Z + ESP_T + ESP_SLOT_FIT
    lip_top = groove_top + ESP_LIP_T
    for s in (-1, 1):
        e = ESP_X + s * ESP_L / 2
        inner, outer = e - s * ESP_GRIP, e + s * (ESP_SLOT_FIT + ESP_RAIL_OUT)
        rail = box(min(inner, outer), max(inner, outer), y_front, y_end + 2.0, BASE_T - 0.01, lip_top)
        g_out = e + s * ESP_SLOT_FIT
        g_in = inner - s * 0.5  # cut runs past the rail's inner face
        rail -= box(min(g_in, g_out), max(g_in, g_out), y_front - 1, y_end, ESP_SEAT_Z, groove_top)
        # snap bump just outside the board's entry edge
        rail += box(min(inner, g_out), max(inner, g_out), y_in - 1.1, y_in - 0.1, ESP_SEAT_Z - 0.01, ESP_SEAT_Z + ESP_BUMP)
        body += rail
    return printed(body, "#3d5a80", "base")


@model
def top_plate():
    plate = box(-BASE_L / 2, BASE_L / 2, -BASE_W / 2, BASE_W / 2, PLATE_Z, PLATE_TOP)
    plate = bd.fillet(plate.edges().filter_by(bd.Axis.Z), 4.0)
    for sx in (-1, 1):
        for sy in (-1, 1):
            plate -= zcyl(M3_CLEAR_D / 2, PLATE_Z - 1, PLATE_TOP + 1, sx * COL_X, sy * COL_Y)

    # rack guide channel: back wall + two side walls, open toward the pinion
    gy = GEAR_T / 2 + FIT
    gx0 = RACK_BACK_X - FIT
    plate += box(gx0 - 2.5, gx0, -gy - 2, gy + 2, PLATE_TOP - 0.01, SHAFT_Z + 8)
    plate += v_prism(gx0 - 0.01, VRAIL_H + 0.01, PLATE_TOP - 0.01, SHAFT_Z + 8)  # guide rail
    for s in (-1, 1):
        y0, y1 = (gy, gy + 2) if s > 0 else (-gy - 2, -gy)
        plate += box(gx0 - 2.5, RACK_TIP_X - 0.5, y0, y1, PLATE_TOP - 0.01, PLATE_TOP + 8)
    # rack slot through the plate
    plate -= box(gx0, RACK_TIP_X + FIT, -gy, gy, PLATE_Z - 1, PLATE_TOP + 1)

    # servo wall: window for the body, two ear-screw pilot holes (M2 / SG90 self-tappers)
    wx0, wx1 = SG_BODY_CX - SG_EAR_L / 2 - 3, SG_BODY_CX + SG_EAR_L / 2 + 3
    wall = box(wx0, wx1, MOUNT_Y0, MOUNT_Y0 + MOUNT_T, PLATE_TOP - 0.01, SHAFT_Z + SG_W / 2 + 7)
    wall -= box(SG_BODY_CX - SG_L / 2 - FIT, SG_BODY_CX + SG_L / 2 + FIT, MOUNT_Y0 - 1, MOUNT_Y0 + MOUNT_T + 1,
                SHAFT_Z - SG_W / 2 - FIT, SHAFT_Z + SG_W / 2 + FIT)
    for s in (-1, 1):
        wall -= ycyl(0.9, MOUNT_Y0 - 1, MOUNT_Y0 + MOUNT_T + 1, SG_BODY_CX + s * SG_HOLE_SPACING / 2, SHAFT_Z)
    # gussets behind the wall
    for gx in (wx0, wx1 - 3):
        g = box(gx, gx + 3, MOUNT_Y0 + MOUNT_T - 0.01, MOUNT_Y0 + MOUNT_T + 8, PLATE_TOP - 0.01, PLATE_TOP + 8)
        g = bd.chamfer(g.edges().filter_by(bd.Axis.X).sort_by(bd.Axis.Z)[-1:].sort_by(bd.Axis.Y)[-1:], 7.9)
        wall += g
    plate += wall
    # servo cable pass-through
    plate -= zcyl(4.0, PLATE_Z - 1, PLATE_TOP + 1, 14.0, 19.0)
    return printed(plate, "#98c1d9", "top_plate")


@model
def rack():
    return printed(rack_body(), "#ee6c4d", "rack")


@model
def push_pad():
    return printed(push_pad_body(), "#f4a261", "push_pad")


@model
def pinion():
    g = pinion_body().rotate(bd.Axis.X, 90).move(bd.Location((SHAFT_X, 0, SHAFT_Z)))
    return printed(g, "#e0fbfc", "pinion")


# ---------------------------------------------------------------- reference parts
def sg90():
    body = box(SG_BODY_CX - SG_L / 2, SG_BODY_CX + SG_L / 2, SG_TOP_Y, SG_TOP_Y + SG_H,
               SHAFT_Z - SG_W / 2, SHAFT_Z + SG_W / 2)
    ears = box(SG_BODY_CX - SG_EAR_L / 2, SG_BODY_CX + SG_EAR_L / 2, EAR_Y0, EAR_Y0 + SG_EAR_T,
               SHAFT_Z - SG_W / 2, SHAFT_Z + SG_W / 2)
    for s in (-1, 1):
        ears -= ycyl(1.0, EAR_Y0 - 1, EAR_Y0 + SG_EAR_T + 1, SG_BODY_CX + s * SG_HOLE_SPACING / 2, SHAFT_Z)
    shaft = ycyl(2.35, GEAR_T / 2 + 1.0 - 3.5, SG_TOP_Y + 0.01, SHAFT_X, SHAFT_Z)
    s = body + ears + shaft
    s.color = "#1f4ea8"
    s.label = "sg90"
    return s


def button_ref():
    b = zcyl(BUTTON_D / 2, BASE_T, BASE_T + BUTTON_HOUSING_H, BUTTON_X, BUTTON_Y)
    b += zcyl(BUTTON_CAP_D / 2, BASE_T + BUTTON_HOUSING_H - 0.01, BUTTON_TOP_Z, BUTTON_X, BUTTON_Y)
    b.color = "#d62828"
    b.label = "button"
    return b


def esp32_ref():
    z0 = ESP_SEAT_Z
    pcb = box(ESP_X - ESP_L / 2, ESP_X + ESP_L / 2, ESP_Y - ESP_W / 2, ESP_Y + ESP_W / 2, z0, z0 + ESP_T)
    pcb += box(ESP_X - 2, ESP_X + 12, ESP_Y - 6, ESP_Y + 6, z0 + ESP_T - 0.01, z0 + ESP_T + 2.5)
    pcb.color = "#2b2d42"
    pcb.label = "esp32_mini"
    return pcb


# ---------------------------------------------------------------- assemblies
@model
def assembly():
    parts = [base().shape, top_plate().shape, rack().shape, push_pad().shape, pinion().shape,
             sg90(), button_ref(), esp32_ref()]
    a = bd.Compound(children=parts)
    a.label = "button_pusher"
    return a


def on_bed(shape):
    """Drop a shape onto z=0, centred on the origin."""
    bb = shape.bounding_box()
    return shape.moved(bd.Location((-bb.center().X, -bb.center().Y, -bb.min.Z)))


@model
def rack_print():
    """Rack in print orientation: on its side, teeth profile in the bed plane."""
    r = on_bed(rack().shape.rotate(bd.Axis.X, -90))
    r.label = "rack"
    return r


@model
def pinion_print():
    """Pinion in print orientation: axis vertical, gear face on the bed, hub up."""
    p = on_bed(pinion().shape.moved(bd.Location((-SHAFT_X, 0, -SHAFT_Z))).rotate(bd.Axis.X, 90))
    p.label = "pinion"
    return p


@model
def print_plate():
    """Printable parts laid flat for Bambu (256 x 256 bed)."""
    b = base().shape.moved(bd.Location((0, -40, 0)))
    tp = top_plate().shape.moved(bd.Location((0, 35, -PLATE_Z)))
    # rack on its side: Y face down, teeth profile in the bed plane
    r = rack().shape.rotate(bd.Axis.X, -90)
    rb = r.bounding_box()
    r = r.moved(bd.Location((75 - rb.center().X, -40 - rb.center().Y, -rb.min.Z)))
    # pinion hub up? hub down gives a flat gear face on the bed: turn axis to Z, gear face down
    pn = pinion().shape.moved(bd.Location((-SHAFT_X, 0, -SHAFT_Z))).rotate(bd.Axis.X, 90)
    pb = pn.bounding_box()
    pn = pn.moved(bd.Location((80 - pb.center().X, 20 - pb.center().Y, -pb.min.Z)))
    pd = push_pad().shape
    pdb = pd.bounding_box()
    pd = pd.moved(bd.Location((105 - pdb.center().X, -40 - pdb.center().Y, -pdb.min.Z)))
    out = bd.Compound(children=[b, tp, r, pn, pd])
    out.label = "print_plate"
    return out


if __name__ == "__main__":
    for m in (base, top_plate, rack, push_pad, pinion, rack_print, pinion_print):
        m()
    assembly()
    print_plate()
