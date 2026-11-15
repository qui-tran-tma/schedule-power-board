"""Rice cooker button pusher: compact unit set between a wall and the cooker, SG90 + horizontal rack
pushes a 20 mm button at 70 mm height.

FDM printed (Bambu), PETG, 0.2 mm layers. Printed parts: stand, cap, h_rack, h_pad, h_pinion.
Reference (not printed): SG90 servo, rice cooker front face with its button.

Layout (mm, +Z up, +X toward the rice cooker, ground z = 0):
  - wall | stand | cooker: the stand's back is one flat face (x = X_BACK) up to the rack height, set
    against a wall. The press reaction goes straight back into the wall at rack height, so the unit
    cannot tip or slide back; a small base only has to stand it up.
  - tower: a solid spine carries the rack channel at button height (rack centre z = 70), a V rail
    on the channel floor and a hold-down lip keep the rack straight; a box beside it holds the SG90
    upright on its two ear screws, shaft up
  - pinion (20 teeth, module 1.273, as button_pusher) turns flat, drives the rack along X:
    0.222 mm per servo degree, ~36 deg for 5 mm gap + 3 mm press. Its tips overhang the servo box
    edge by ~4 mm (uncovered, nothing in the way)
  - D16 push pad on the rack's front end (square collar + M2 cross screw), 5 mm off the button at rest
  - rack stays >= 6 mm inside the back face at rest, so it never reaches the wall
  - beside the spine (-Y): LiPo 800 mAh flat against the spine, a low fence, then the ESP32 mini
    (32 x 22) in slide-in rails, out the side edge (-Y)
  - battery held by 2 tabs on the spine (+Y edge) and 2 snap clips (-Y edge): tuck it under the tabs,
    press the other edge down past the clips
  - cap over battery + board against splashes: side walls sit in rabbets on the base, it slides
    toward the spine so its top tucks under a 45 deg rain ledge, one M2 screw through the skirt
  - set the 5 mm gap by where the cooker stands from the wall

Check: cad model dfm "$ID" --build-volume 256x256x256
"""

import math
import os
import sys

import build123d as bd
from cad import model

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import button_pusher as bp  # noqa: E402  (shared gear profile, helpers, servo dims)

box, zcyl, printed = bp.box, bp.zcyl, bp.printed
FIT = bp.FIT

# ---------------------------------------------------------------- parameters
BUTTON_FROM_COUNTER = 70.0  # counter to button centre, cooker standing on the counter
PRESS_GAP = 5.0  # pad face to button at rest
PRESS_DEPTH = 3.0

# base: just the tower's footprint plus the ESP32 bay; flat back face at X_BACK goes against the wall
X_BACK = -32.0
BASE_X0, BASE_X1 = X_BACK, 15.0  # front edge at BASE_X1
# bay on the -Y side of the spine, outward: battery, ESP32 board, then the base edge; a cap covers all
BASE_T = 5.0
BUTTON_Z = BUTTON_FROM_COUNTER  # cooker stands on the counter

# rack (horizontal, along X, teeth on +Y face)
RACK_W = 6.0  # Y
RACK_H = 6.0  # Z
RACK_Z0 = BUTTON_Z - RACK_H / 2
RACK_ROOT_Y = RACK_W / 2
RACK_PITCH_Y = RACK_ROOT_Y + 1.25 * bp.MOD
RACK_TIP_Y = RACK_PITCH_Y + 1.0 * bp.MOD
SHAFT_X = -12.0
SHAFT_Y = RACK_PITCH_Y + bp.RP + 0.15  # +0.15 for print fit
RACK_X0 = X_BACK + 6.0  # back end: 6 mm clear of the wall at rest
TEETH_X0, TEETH_X1 = RACK_X0 + 2.0, 12.0  # 9 teeth; front stops short of the pad collar

# push pad (axis X)
PAD_FACE_X = BASE_X1 + 15.0  # pad face at rest, 15 mm past the base front edge
PAD_D, PAD_T = 16.0, 3.0  # 2 mm inside the D20 button all round
PAD_FLOOR = 2.0
COLLAR_L, COLLAR_WALL = 10.0, 2.5
SOCKET_FIT = 0.1
RACK_X1 = PAD_FACE_X - PAD_T + (PAD_T - PAD_FLOOR)  # rack front end, inside the pad
PIN_X = RACK_X1 - 5.5  # M2 cross screw, vertical
PIN_PILOT_D, PIN_CLEAR_D = 1.8, 2.2

# channel + spine
CH_X0, CH_X1 = X_BACK, BASE_X1
CH_FLOOR_Z = RACK_Z0 - FIT
SPINE_Y0 = -10.3
SPINE_Y1 = 5.9  # stops short of the servo ears
LIP_T = 1.2
LIP_REACH = 1.8  # over the rack's back edge
VRAIL_H, VGROOVE_D = 1.0, 1.3

# servo SG90 upright, shaft up, body along X
SG_TOP_Z = BUTTON_Z - bp.GEAR_T / 2 - 1.0 - 0.5  # shaft face just under the pinion hub
SG_BODY_CX = SHAFT_X + bp.SG_L / 2 - bp.SG_SHAFT_FROM_END
EAR_Z0 = SG_TOP_Z - bp.SG_EAR_FROM_TOP - bp.SG_EAR_T  # ear underside = shelf top
SHELF_T = 4.0
BOX_HALF = bp.SG_EAR_L / 2 + 4.0  # servo box half length (X)
BOX_WALL = 3.0
BOX_Y1 = SHAFT_Y + bp.SG_W / 2 + 4.0
CABLE_WIN = (12.0, 10.0)  # cable window through the spine, board bay to servo box (X, Z)
CABLE_Z = 9.0  # window bottom above the base top, over the battery

# ESP32 mini bay beside the spine (-Y): same slide-in rails as button_pusher, exits the side edge (-Y)
ESP_L, ESP_W, ESP_T = bp.ESP_L, bp.ESP_W, bp.ESP_T  # 32 (X) x 22 (Y)
ESP_SEAT_Z = BASE_T + 3.0

# LiPo 3.7 V 800 mAh, 42 x 25 x 5 mm: lies flat against the spine, held with tape
BAT_L, BAT_W, BAT_T = 42.0, 25.0, 5.0  # X, Y, Z
BAT_FIT = 1.0
BAT_CABLE = 3.0  # extra room between battery and fence for its cable
BAT_X = (BASE_X0 + BASE_X1) / 2
BAT_Y1 = SPINE_Y0 - BAT_FIT  # battery +Y face
BAT_Y0 = BAT_Y1 - BAT_W
FENCE_T, FENCE_H = 2.5, 3.0  # low wall between battery and board
# battery holders: 2 tabs from the spine over its +Y edge, 2 snap clips over its -Y edge
BAT_HOLD_X = (-12.0, 12.0)  # holder positions from BAT_X
HOLD_W = 6.0
TAB_OVER, TAB_T = 1.5, 1.5  # spine tab reach over the battery, thickness
CLIP_T, CLIP_HOOK, CLIP_TOP_T = 1.2, 0.8, 1.8  # snap post thickness, hook reach, hook height
BAT_TOP_FIT = 0.3

# board goes outboard of the battery fence
ESP_X = BAT_X
ESP_Y = BAT_Y0 - BAT_FIT - BAT_CABLE - FENCE_T - 2.0 - 0.2 - ESP_W / 2  # rail end stops butt the fence
BASE_Y0 = ESP_Y - ESP_W / 2 - 4.0

# cap: covers battery + board, slides on toward the spine and tucks under a rain ledge on the spine
CAP_WALL = 2.0
CAP_BAY_H = 25.0  # clear height inside the cap, base top to cap ceiling (board + cables)
CAP_TOP_Z = BASE_T + CAP_BAY_H + CAP_WALL  # outer top
CAP_RABBET = 1.5  # cap side walls sit in rabbets along the base's x edges
CAP_SKIRT_Z = 0.5  # -Y skirt hangs over the base edge down to here
CAP_SLIDE = 4.0  # sideways travel to tuck under the ledge
LEDGE_OUT, LEDGE_T = 3.5, 2.0  # rain ledge over the cap's spine edge
CAP_SCREW_Z = BASE_T / 2  # M2 through the skirt into the base edge

# cooker reference
COOKER_FACE_X = PAD_FACE_X + PRESS_GAP + 3.0  # button cap stands 3 mm proud of the face
BUTTON_CAP_D = 20.0


def xcyl(r, x0, x1, y=0.0, z=0.0):
    return bd.Cylinder(r, x1 - x0).rotate(bd.Axis.Y, 90).move(bd.Location(((x0 + x1) / 2, y, z)))


def v_ridge_x(z_base, h, x0, x1, y=0.0):
    """45 deg V ridge running along X: base on the plane z=z_base, apex at z_base + h."""
    pts = [bd.Vector(x0, y - h, z_base), bd.Vector(x0, y + h, z_base), bd.Vector(x0, y, z_base + h)]
    return bd.extrude(bd.Face(bd.Wire.make_polygon(pts, close=True)), amount=x1 - x0, dir=(1, 0, 0))


# ---------------------------------------------------------------- parts
def rack_shape():
    p = math.pi * bp.MOD
    t = math.tan(bp.PA)
    half_s = p / 4 - bp.BACKLASH / 4
    w_root = half_s + 1.25 * bp.MOD * t
    w_tip = half_s - 1.0 * bp.MOD * t
    pts = [(RACK_X0, -RACK_W / 2), (RACK_X1, -RACK_W / 2), (RACK_X1, RACK_ROOT_Y)]
    # teeth from front to back along +Y face; a gap is centred on the pinion (pinion tooth at 270 deg)
    centres = []
    k = math.floor((TEETH_X1 - SHAFT_X - p / 2) / p)
    while True:
        xc = SHAFT_X + p / 2 + k * p
        if xc - w_root < TEETH_X0:
            break
        if xc + w_root <= TEETH_X1:
            centres.append(xc)
        k -= 1
    for xc in centres:  # descending X
        pts += [(xc + w_root, RACK_ROOT_Y), (xc + w_tip, RACK_TIP_Y), (xc - w_tip, RACK_TIP_Y), (xc - w_root, RACK_ROOT_Y)]
    pts += [(RACK_X0, RACK_ROOT_Y)]
    face = bd.Face(bd.Wire.make_polygon([bd.Vector(x, y, RACK_Z0) for x, y in pts], close=True))
    bar = bd.extrude(face, amount=RACK_H, dir=(0, 0, 1))
    bar -= v_ridge_x(RACK_Z0 - 0.5, VGROOVE_D + 0.5, RACK_X0 - 1, RACK_X1 + 1)  # guide groove
    bar -= zcyl(PIN_PILOT_D / 2, RACK_Z0 - 1, RACK_Z0 + RACK_H + 1, PIN_X, 0)
    return bar


def pad_shape():
    x_face = PAD_FACE_X
    pad = xcyl(PAD_D / 2, x_face - PAD_T, x_face, 0, BUTTON_Z)
    pad = bd.chamfer(pad.edges().group_by(bd.Axis.X)[-1], 0.4)
    sy, sz = RACK_W / 2 + SOCKET_FIT, RACK_H / 2 + SOCKET_FIT
    cy, cz = sy + COLLAR_WALL, sz + COLLAR_WALL
    collar = box(x_face - PAD_T - COLLAR_L, x_face - PAD_T + 0.01, -cy, cy, BUTTON_Z - cz, BUTTON_Z + cz)
    collar = bd.fillet(collar.edges().filter_by(bd.Axis.X), 1.0)
    pad += collar
    pad -= box(x_face - PAD_T - COLLAR_L - 1, x_face - PAD_FLOOR, -sy, sy, BUTTON_Z - sz, BUTTON_Z + sz)
    pad -= zcyl(PIN_CLEAR_D / 2, BUTTON_Z - cz - 1, BUTTON_Z + cz + 1, PIN_X, 0)
    return pad


def stand_shape():
    # base plate: front corners rounded, back edge square so the back face sits flat on the wall
    bx0, bx1 = X_BACK, SG_BODY_CX + BOX_HALF
    assert bx0 <= SG_BODY_CX - BOX_HALF, "servo box must stay inside the back face"
    plate = box(BASE_X0, BASE_X1, BASE_Y0, BOX_Y1, 0, BASE_T)
    plate = bd.fillet(plate.edges().filter_by(bd.Axis.Z).group_by(bd.Axis.X)[-1].sort_by(bd.Axis.Y)[-1], 4.0)
    body = plate
    # rabbets for the cap's side walls, open at the -Y edge so the cap slides in
    for x0, x1 in ((BASE_X0 - 1, BASE_X0 + CAP_WALL + FIT), (BASE_X1 - CAP_WALL - FIT, BASE_X1 + 1)):
        body -= box(x0, x1, BASE_Y0 - 1, SPINE_Y0, BASE_T - CAP_RABBET, BASE_T + 1)
    # battery fence on the board side
    body += box(BAT_X - BAT_L / 2, BAT_X + BAT_L / 2, BAT_Y0 - BAT_FIT - BAT_CABLE - FENCE_T, BAT_Y0 - BAT_FIT - BAT_CABLE,
                BASE_T - 0.01, BASE_T + FENCE_H)
    body += battery_holders()
    # cap screw pilot in the base's -Y edge
    body -= ycyl(0.8, BASE_Y0 - 1, BASE_Y0 + 8, ESP_X, CAP_SCREW_Z)

    # spine: solid block from the base up to the channel floor, rear wall + hold-down lip
    body += box(CH_X0, CH_X1, SPINE_Y0, SPINE_Y1, BASE_T - 0.01, CH_FLOOR_Z)
    back_y = -RACK_W / 2 - FIT
    lip_top = RACK_Z0 + RACK_H + FIT + LIP_T
    body += box(CH_X0, CH_X1, SPINE_Y0, back_y, CH_FLOOR_Z - 0.01, lip_top)
    body += box(CH_X0, CH_X1, back_y - 0.01, back_y + LIP_REACH, lip_top - LIP_T, lip_top)
    body += v_ridge_x(CH_FLOOR_Z - 0.01, VRAIL_H + 0.01, CH_X0, CH_X1)

    # servo box: side walls, front wall, shelf with body cut-out + ear pilot holes
    shelf_top = EAR_Z0
    servo_box = box(bx0, bx1, SPINE_Y1 - 0.01, BOX_Y1, BASE_T - 0.01, shelf_top)
    servo_box -= box(bx0 + BOX_WALL, bx1 - BOX_WALL, SPINE_Y1 - 1, BOX_Y1 - BOX_WALL, BASE_T, shelf_top - SHELF_T)
    servo_box -= box(SG_BODY_CX - bp.SG_L / 2 - FIT, SG_BODY_CX + bp.SG_L / 2 + FIT,
                     SHAFT_Y - bp.SG_W / 2 - FIT, SHAFT_Y + bp.SG_W / 2 + FIT, BASE_T, shelf_top + 1)
    for s in (-1, 1):
        servo_box -= zcyl(0.9, shelf_top - SHELF_T - 1, shelf_top + 1, SG_BODY_CX + s * bp.SG_HOLE_SPACING / 2, SHAFT_Y)
    body += servo_box
    # cable window through the spine: ESP32 bay (-Y side) into the servo box hollow
    cw, ch = CABLE_WIN
    body -= box(SG_BODY_CX - cw / 2, SG_BODY_CX + cw / 2, SPINE_Y0 - 1, SPINE_Y1 + 0.5,
                BASE_T + CABLE_Z, BASE_T + CABLE_Z + ch)
    body += esp_rails()
    # rain ledge over the cap's spine edge, top sloped 45 deg to shed water
    lz = CAP_TOP_Z + 0.3
    pts = [bd.Vector(BASE_X0, SPINE_Y0 + 0.01, lz), bd.Vector(BASE_X0, SPINE_Y0 - LEDGE_OUT, lz),
           bd.Vector(BASE_X0, SPINE_Y0 - LEDGE_OUT, lz + LEDGE_T),
           bd.Vector(BASE_X0, SPINE_Y0 + 0.01, lz + LEDGE_T + LEDGE_OUT)]
    body += bd.extrude(bd.Face(bd.Wire.make_polygon(pts, close=True)), amount=BASE_X1 - BASE_X0, dir=(1, 0, 0))
    return body


def ycyl(r, y0, y1, x=0.0, z=0.0):
    return bd.Cylinder(r, y1 - y0).rotate(bd.Axis.X, 90).move(bd.Location((x, (y0 + y1) / 2, z)))


def cap_shape():
    """Cap over battery + board: two side walls in the base rabbets, -Y skirt over the base edge
    (M2 screw), top tucked under the spine ledge, open toward the spine."""
    y_back = SPINE_Y0 - FIT  # cap edge at the spine
    y_skirt0 = BASE_Y0 - FIT - CAP_WALL
    z_wall = BASE_T - CAP_RABBET + 0.2
    outer = box(BASE_X0, BASE_X1, y_skirt0, y_back, z_wall, CAP_TOP_Z)
    cap = outer - box(BASE_X0 + CAP_WALL, BASE_X1 - CAP_WALL, y_skirt0 + CAP_WALL, y_back + 1, z_wall - 1,
                      CAP_TOP_Z - CAP_WALL)
    cap += box(BASE_X0, BASE_X1, y_skirt0, y_skirt0 + CAP_WALL, CAP_SKIRT_Z, z_wall + 0.01)  # skirt
    cap = bd.fillet(cap.edges().filter_by(bd.Axis.Z).group_by(bd.Axis.Y)[0], 1.5)
    cap -= ycyl(1.1, y_skirt0 - 1, y_skirt0 + CAP_WALL + 1, ESP_X, CAP_SCREW_Z)
    return cap


def battery_holders():
    z_top = BASE_T + BAT_T + BAT_TOP_FIT  # holder undersides, just over the battery
    out = None
    for dx in BAT_HOLD_X:
        x0, x1 = BAT_X + dx - HOLD_W / 2, BAT_X + dx + HOLD_W / 2
        # spine tab: from the spine face over the battery's +Y edge
        tab = box(x0, x1, BAT_Y1 - TAB_OVER, SPINE_Y0 + 0.01, z_top, z_top + TAB_T)
        # snap clip: thin post in the cable gap, hook over the battery's -Y edge, 45 deg lead-in on top
        y_post1 = BAT_Y0 - 0.2
        post = box(x0, x1, y_post1 - CLIP_T, y_post1, BASE_T - 0.01, z_top + CLIP_TOP_T)
        hook_pts = [bd.Vector(x0, y_post1 - 0.01, z_top), bd.Vector(x0, y_post1 + CLIP_HOOK, z_top),
                    bd.Vector(x0, y_post1 + CLIP_HOOK, z_top + CLIP_TOP_T - CLIP_HOOK),
                    bd.Vector(x0, y_post1 - 0.01, z_top + CLIP_TOP_T)]
        hook = bd.extrude(bd.Face(bd.Wire.make_polygon(hook_pts, close=True)), amount=HOLD_W, dir=(1, 0, 0))
        part = tab + post + hook
        out = part if out is None else out + part
    return out


def battery_ref():
    b = box(BAT_X - BAT_L / 2, BAT_X + BAT_L / 2, BAT_Y0, BAT_Y1, BASE_T, BASE_T + BAT_T)
    b.color = "#c0c0c0"
    b.label = "lipo_800mah"
    return b


def esp_rails():
    """Rails hold the board's two 22 mm ends (x = ESP_X +/- ESP_L/2), slide in/out from the -Y edge."""
    y_in = ESP_Y - ESP_W / 2  # entry edge (-Y side)
    y_stop = ESP_Y + ESP_W / 2 + 0.2  # end stop face (toward the spine)
    y_open = BASE_Y0 + 1.0
    fence_y = BAT_Y0 - BAT_FIT - BAT_CABLE - FENCE_T
    groove_top = ESP_SEAT_Z + ESP_T + bp.ESP_SLOT_FIT
    lip_top = groove_top + bp.ESP_LIP_T
    rails = None
    for s in (-1, 1):
        e = ESP_X + s * ESP_L / 2
        inner, outer = e - s * bp.ESP_GRIP, e + s * (bp.ESP_SLOT_FIT + bp.ESP_RAIL_OUT)
        rail = box(min(inner, outer), max(inner, outer), y_open, fence_y + 0.01, BASE_T - 0.01, lip_top)  # rail joins the fence
        g_out = e + s * bp.ESP_SLOT_FIT
        g_in = inner - s * 0.5
        rail -= box(min(g_in, g_out), max(g_in, g_out), y_open - 1, y_stop, ESP_SEAT_Z, groove_top)
        rail += box(min(inner, g_out), max(inner, g_out), y_in - 1.1, y_in - 0.1, ESP_SEAT_Z - 0.01,
                    ESP_SEAT_Z + bp.ESP_BUMP)
        rails = rail if rails is None else rails + rail
    return rails


def esp32_ref():
    z0 = ESP_SEAT_Z
    pcb = box(ESP_X - ESP_L / 2, ESP_X + ESP_L / 2, ESP_Y - ESP_W / 2, ESP_Y + ESP_W / 2, z0, z0 + ESP_T)
    pcb += box(ESP_X - 2, ESP_X + 12, ESP_Y - 6, ESP_Y + 6, z0 + ESP_T - 0.01, z0 + ESP_T + 2.5)
    pcb.color = "#2b2d42"
    pcb.label = "esp32_mini"
    return pcb


@model
def stand():
    return printed(stand_shape(), "#3d5a80", "stand")


@model
def cap():
    return printed(cap_shape(), "#98c1d9", "cap")


@model
def h_rack():
    return printed(rack_shape(), "#ee6c4d", "h_rack")


@model
def h_pad():
    return printed(pad_shape(), "#f4a261", "h_pad")


@model
def h_pinion():
    g = bp.pinion_body().move(bd.Location((SHAFT_X, SHAFT_Y, BUTTON_Z)))
    return printed(g, "#e0fbfc", "h_pinion")


# ---------------------------------------------------------------- reference parts
def sg90_upright():
    zc = SG_TOP_Z - bp.SG_H / 2
    body = box(SG_BODY_CX - bp.SG_L / 2, SG_BODY_CX + bp.SG_L / 2, SHAFT_Y - bp.SG_W / 2, SHAFT_Y + bp.SG_W / 2,
               SG_TOP_Z - bp.SG_H, SG_TOP_Z)
    ears = box(SG_BODY_CX - bp.SG_EAR_L / 2, SG_BODY_CX + bp.SG_EAR_L / 2, SHAFT_Y - bp.SG_W / 2,
               SHAFT_Y + bp.SG_W / 2, EAR_Z0, EAR_Z0 + bp.SG_EAR_T)
    for s in (-1, 1):
        ears -= zcyl(1.0, EAR_Z0 - 1, EAR_Z0 + 4, SG_BODY_CX + s * bp.SG_HOLE_SPACING / 2, SHAFT_Y)
    shaft = zcyl(2.35, SG_TOP_Z - 0.01, BUTTON_Z - bp.GEAR_T / 2 - 1.0 + 3.5, SHAFT_X, SHAFT_Y)
    s = body + ears + shaft
    s.color = "#1f4ea8"
    s.label = "sg90"
    del zc
    return s


def wall_ref():
    w = box(X_BACK - 15, X_BACK, -100, 100, 0, 130)
    w.color = "#bfb6a8"
    w.label = "wall"
    return w


def cooker_ref():
    face = box(COOKER_FACE_X, COOKER_FACE_X + 60, -100, 100, 0, 130)
    face.color = "#d9d9d9"
    face.label = "rice_cooker"
    btn = xcyl(BUTTON_CAP_D / 2, COOKER_FACE_X - 3.0, COOKER_FACE_X, 0, BUTTON_Z)
    btn.color = "#d62828"
    btn.label = "cooker_button"
    return [face, btn]


# ---------------------------------------------------------------- assemblies
@model
def rice_pusher():
    parts = [wall_ref(), stand().shape, h_rack().shape, h_pad().shape, h_pinion().shape, sg90_upright(), esp32_ref(),
             battery_ref(), cap().shape, *cooker_ref()]
    a = bd.Compound(children=parts)
    a.label = "rice_pusher"
    return a


@model
def h_rack_print():
    """Rack as printed: flat, V groove down (as built)."""
    r = bp.on_bed(h_rack().shape)
    r.label = "h_rack"
    return r


@model
def h_pad_print():
    """Pad as printed: disc face on the bed, collar up."""
    p = bp.on_bed(h_pad().shape.rotate(bd.Axis.Y, 90))
    p.label = "h_pad"
    return p


@model
def cap_print():
    """Cap as printed: top on the bed."""
    c = bp.on_bed(cap().shape.rotate(bd.Axis.X, 180))
    c.label = "cap"
    return c


@model
def h_pinion_print():
    """Gear face on the bed, hub up: no overhang (hub-down hung the whole gear over a D10 hub)."""
    p = bp.on_bed(h_pinion().shape.rotate(bd.Axis.X, 180))
    p.label = "h_pinion"
    return p


@model
def rice_print_plate():
    """Printable parts laid out for a 256 x 256 bed."""
    s = stand().shape
    r = h_rack_print().shape.rotate(bd.Axis.Z, 90).moved(bd.Location((-70, 10, 0)))
    pd = h_pad_print().shape.moved(bd.Location((-60, -50, 0)))
    pn = h_pinion_print().shape.moved(bd.Location((-60, -75, 0)))
    cp = cap_print().shape.moved(bd.Location((50, -30, 0)))
    out = bd.Compound(children=[s, r, pd, pn, cp])
    out.label = "rice_print_plate"
    return out


if __name__ == "__main__":
    for m in (stand, cap, cap_print, h_rack, h_pad, h_pinion, rice_pusher, h_rack_print, h_pad_print, h_pinion_print,
              rice_print_plate):
        m()
