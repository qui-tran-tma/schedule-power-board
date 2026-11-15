# Wireless Lock Box — V3 design

V3 reworks the V2 lock box (`WirelessLockV2.step`) so the battery and the wireless board stay dry.
It also makes the battery replaceable through a sealed side lid, and adds the cables and status LED.

The model is a build123d script (`lockbox_v3.py`) that text-to-cad builds. The V2 STEP is the base
geometry; the script reads it through `WirelessLockV2.xbf`.

## Viewer links

These links open in the local text-to-cad viewer (CAD Viewer). They only work while its server is
running on this machine, and the `token` changes between sessions. To get fresh links, run the
script; each model prints its `view:` line:

```bash
cd docs/3dlockbox
cad run lockbox_v3.py
```

| Model | Document id | Link (this session) |
|---|---|---|
| Full assembly `lockbox_v3` | `419c08d2-59bb-5db8-a768-b7b40d475ca1` | http://127.0.0.1:3245/419c08d2-59bb-5db8-a768-b7b40d475ca1?token=4948242302.RfraQPs7-Zw54h_3iDzQwP-FSETHjKuIfK6qvrYd02s |
| Housing | `17577857-b398-5698-a524-24d3f23247c5` | http://127.0.0.1:3245/17577857-b398-5698-a524-24d3f23247c5?token=4948242302.RfraQPs7-Zw54h_3iDzQwP-FSETHjKuIfK6qvrYd02s |
| Main lid | `42c2bc70-7913-5cc0-8c33-019e6c93188e` | http://127.0.0.1:3245/42c2bc70-7913-5cc0-8c33-019e6c93188e?token=4948242302.RfraQPs7-Zw54h_3iDzQwP-FSETHjKuIfK6qvrYd02s |
| Battery lid | `44858c92-f576-5e81-83b1-6b414bce1f9d` | http://127.0.0.1:3245/44858c92-f576-5e81-83b1-6b414bce1f9d?token=4948242302.RfraQPs7-Zw54h_3iDzQwP-FSETHjKuIfK6qvrYd02s |
| PCB box tray | `6aaf72af-4af5-506c-93ce-f74ac3fad1e6` | http://127.0.0.1:3245/6aaf72af-4af5-506c-93ce-f74ac3fad1e6?token=4948242302.RfraQPs7-Zw54h_3iDzQwP-FSETHjKuIfK6qvrYd02s |
| Status LED | `c75c85b3-f0af-53f3-997e-f52bb69399a5` | http://127.0.0.1:3245/c75c85b3-f0af-53f3-997e-f52bb69399a5?token=4948242302.RfraQPs7-Zw54h_3iDzQwP-FSETHjKuIfK6qvrYd02s |
| Cables | `1feb2fc2-3f77-5529-8880-fc5d0d79e4e0` | http://127.0.0.1:3245/1feb2fc2-3f77-5529-8880-fc5d0d79e4e0?token=4948242302.RfraQPs7-Zw54h_3iDzQwP-FSETHjKuIfK6qvrYd02s |
| `WirelessLockV3.step` (exported file) | `cb01cb68-0139-5f02-90f3-fcf678b76868` | http://127.0.0.1:3245/cb01cb68-0139-5f02-90f3-fcf678b76868?token=4948242302.RfraQPs7-Zw54h_3iDzQwP-FSETHjKuIfK6qvrYd02s |
| `WirelessLockV2.step` (original) | `bf480d12-7ebf-52e4-b842-45ec27b68544` | http://127.0.0.1:3245/bf480d12-7ebf-52e4-b842-45ec27b68544?token=4948242302.RfraQPs7-Zw54h_3iDzQwP-FSETHjKuIfK6qvrYd02s |

To open a file page without the script, run `cad viewer --json docs/3dlockbox/WirelessLockV3.step`.
It prints the current link.

## Files

| File | What it is |
|---|---|
| `WirelessLockV2.step` | The original V2 assembly (input). |
| `WirelessLockV2.xbf` | The V2 STEP converted to xbf once, so the script reads it faster. |
| `lockbox_v3.py` | The V3 model: housing, both lids, PCB box tray, status LED, cables, and the full assembly. |
| `source_parts.py` | Read-only views of the original V2 parts, used to study the geometry. |
| `WirelessLockV3.step` | Export of the full V3 assembly: 164 parts, 225.8 × 86.8 × 224.7 mm. |

## Axes

All coordinates are in mm, seen from the front face (key side):

- **x** points right, towards the battery and board side.
- **y** points into the box. The front face is at y 0.4 and the top of the lid at y 43.4.
- **z** points up.

The front face mounts against the wall. The main lid is on the opposite side.

## Design summary

### Two rooms

- **Wet room:** the top strike slot, the electric lock, and the key cylinder with its thumb-turn.
  Water can come in at the slot. It drains through the one original drain channel in the bottom
  wall; the other three bottom holes were removed.
- **Dry room:** the battery house and the PCB box. It is closed off by:
  - **Partition wall:** an L-shaped wall, 4 mm thick, from the floor up to the lid. It runs beside
    the battery house, across its top, then up between the electric lock and the PCB box. The
    upright part steps around a tab on the electric lock, and stays clear of the LED hole (at least
    1.5 mm everywhere; the nearest edge is 2.5 mm away).
  - **Main lid gasket:** a closed groove in the lid underside, 2.5 × 1.8 mm for a 2.5 mm silicone
    or TPU cord. It runs over the partition and round the dry room. A ledge on the right wall gives
    the gasket a surface to press on, and runs into the wall so there is no gap for water to get
    round it.
  - **Cable grommet:** a Ø5 hole through the partition (z 161.5) for the electric lock harness.
    Seal it with a grommet or silicone.

### Battery

- **Battery house:** a fixed channel built into the housing, open towards the side opening and the
  main lid. The battery slides in and out along x. The drawer and its rails are gone.
- **Side opening:** framed on all four sides. A back strip and a 6 mm sill were added, so the
  battery lid's seal is one closed loop.
- **Battery lid:** a plug that fits into the opening, with a closed gasket ring on all four sides.
  - Two ears, above and below, hold it with M3 countersunk screws from the side into heat-set
    inserts in the housing.
  - The ears and screws sit outside the gasket ring.
  - **Pry notches:** two pockets on the back seam (battery lid against the housing strip
    behind it), at z 85 and z 133. Each is two 1 × 8 mm rectangles on the outer surface, one
    each side of the seam, both cut 2 mm deep square to the curved surface: one into the
    housing, one into the lid. Together they make a 2 × 8 × 2 mm pocket for a screwdriver tip.
    They are outside the gasket ring.
  - The lid face is smooth. The only holes in it are the two screw holes in the ears.
- **Battery connectors:** an inline plug and socket (2-pin, JST-VH or XT30 size) sit on top of the
  battery at the lid end.
  - The PCB lead drops into the house through a notch in its top wall.
  - The spare cable folds over the battery, about 130 mm of spare length.
- **To change the battery:**
  1. Undo the 2 side screws. Put two small flat screwdrivers in the pry notches on the back seam and work the battery lid out.
  2. Slide the battery out about 60 mm.
  3. Unplug, fit the new battery, plug in.
  4. Push the battery back in, refit the lid and tighten the screws.

### PCB box

- Two ears, placed diagonally (left side near the top, bottom edge near the right). M3 pan-head
  screws go through them into short heat-set inserts in the floor. The insert holes are blind, with
  1 mm of front panel left.
- **Cable entries:**
  - a slot in the box floor under the 10-pin JST;
  - a Ø4 hole in the right wall for the button lead;
  - a Ø3 hole in the left wall for the LED lead.

### Cables

The PCB pin assignment is not known, so the landing points are assumptions:

| Cable | Route | Lands on |
|---|---|---|
| Electric lock (Ø3.5) | Lock wire tab → through the partition grommet → under the PCB box | 10-pin JST, left end |
| Battery (Ø3) | Cell → plug and socket in the house → spare loop → up | 10-pin JST, right end |
| Reset button (Ø2.5) | Button terminals → beside the PCB box → right-wall hole | 4-pin JST |
| Status LED (Ø2) | LED → beside the PCB box → left-wall hole | 2-pin 1.27 mm header |

### Status LED

A 5 mm LED sits in the front hole (x 46, z 180), with the dome flush with the front face and the
flange against the inside of the front panel. Seal it with clear sealant or a light pipe with an
O-ring.

### Unchanged from V2

The electric lock, key cylinder, escutcheon (`Mask`), reset button, battery cell, PCB, and the PCB
box lid.

## Review checks (last run)

| Check | Result |
|---|---|
| Interference (`cad model interference`) | No new overlaps. Only overlaps already in V2 remain: housing into the electric lock (955 mm³), key cylinder into the electric lock, and PCB connectors into the PCB. Lid-on-housing and lid-in-opening are touching faces only. |
| Dry room sealing (geometry test: both lids on, gaskets compressed, LED hole and grommet plugged) | The dry room has no path to the outside or to the wet room. |
| Battery slide-out (0 to 135 mm, in steps) | The battery, plug, socket and lead clear the housing and lid at every step. The PCB lead has enough spare length and clears the housing. The lead is tested as a straight line from where it enters the house to the socket. |
| Wet-room drain | The original channel is open; the old channel under the battery is filled. |
| Screw paths (battery lid ears, PCB box ears) | Clear, with at least 1.5 mm of solid material round each insert. |
| LED clearance | No wall material within 1.5 mm of the LED bore. |
| STEP export | Read back: 164 parts, same overall size as V2. |

## Hardware

| Qty | Part | Use |
|---|---|---|
| 2 | M3 × 10 countersunk screw (ISO 10642) | Battery lid ears |
| 2 | M3 heat-set insert, Ø4 hole, about 6 mm long | Housing, for the battery lid screws |
| 2 | M3 × 6 pan-head screw | PCB box ears |
| 2 | M3 heat-set insert, short (4 mm) | Housing floor, for the PCB box |
| — | 2.5 mm silicone or TPU cord | Main lid gasket loop and battery lid ring |
| 1 | 2-pin inline connector pair (JST-VH / XT30 size) | Battery |
| 1 | Cable grommet, or silicone potting | Electric lock harness through the partition |
| 1 | 5 mm LED + clear sealant (or a light pipe with an O-ring) | Status LED |

## Open items and suggestions

- **PCB pin assignment:** confirm which connector each cable lands on.
- **Main lid clamping:** it has 4 corner screws only. Add 2–3 lid screws along the partition so the
  gasket is squeezed evenly across the middle.
- **Print settings:** for FDM, print the floor, partition and battery lid with at least 4
  perimeters and 100% infill (PETG or ASA). Optionally coat the inside of the dry room with epoxy.
- **Breathing:** add an ePTFE vent membrane in the lid over the dry room, and a silica-gel pack
  near the battery.
- **Wet-room drain:** consider enlarging it to Ø8–10 and sloping the floor towards it.
- **Spare cable:** tie the battery cable's spare loop loosely so it folds back neatly.
- **Reset button:** it can only be reached with the battery lid off.
- **Manufacturing check:** none has been run. No process or material is set in the model.
