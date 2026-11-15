"""Original WirelessLockV2 parts, read from the vendor STEP (via its xbf), one model each.

Read-only views of the source, used to study the geometry before editing.
"""
from pathlib import Path

import build123d as bd
from cad import model, xbf

SRC = Path(__file__).with_name("WirelessLockV2.xbf")


def _node(path):
    node = xbf.read(SRC)
    for name in path:
        node = next(k for k in node.children if k.label == name)
    return node


def _solid(path, index, label, color):
    s = _node(path).solids()[index]
    s = bd.Solid(s.wrapped)
    s.label = label
    s.color = color
    return s


@model
def src_box_body():
    return _solid(["Box", "COMPOUND"], 0, "box_body", "#3b4cc0")


@model
def src_box_lid():
    return _solid(["Box", "COMPOUND"], 1, "box_lid", "#6f7fd8")


@model
def src_battery_tray():
    return _solid(["Battery"], 1, "battery_tray", "#d9605a")


@model
def src_board_tray():
    return _solid(["WirelessBoard", "COMPOUND"], 1, "board_tray", "#8a8a8a")


@model
def src_board_lid():
    return _solid(["WirelessBoard", "COMPOUND"], 0, "board_lid", "#b0b0b0")


if __name__ == "__main__":
    for m in (src_box_body, src_box_lid, src_battery_tray, src_board_tray, src_board_lid):
        m()
