"""Weld duplicate vertices in a 3MF so each object is one closed mesh.

`cad model export ... x.3mf` writes each B-rep face with its own vertices. Slicers
(Bambu Studio) then see open patches, not a solid, and slice almost nothing.
Run after every 3MF export:

    python weld_3mf.py 3MF/print_plate.3mf 3MF/rice_print_plate.3mf
"""

import re
import shutil
import sys
import tempfile
import zipfile

import numpy as np

VERT = re.compile(r'<vertex x="([^"]+)" y="([^"]+)" z="([^"]+)"\s*/>')
TRI = re.compile(r'<triangle v1="(\d+)" v2="(\d+)" v3="(\d+)"([^>]*)/>')
MESH = re.compile(r"<mesh>(.*?)</mesh>", re.S)


def weld(mesh_xml: str) -> str:
    v = np.array(VERT.findall(mesh_xml), float)
    tris = TRI.findall(mesh_xml)
    f = np.array([t[:3] for t in tris], int)
    uniq, inv = np.unique(v.round(4), axis=0, return_inverse=True)
    f = inv.ravel()[f]
    keep = (f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])
    e = np.sort(np.concatenate([f[keep][:, [0, 1]], f[keep][:, [1, 2]], f[keep][:, [2, 0]]]), axis=1)
    _, cnt = np.unique(e, axis=0, return_counts=True)
    if (cnt != 2).any():
        raise SystemExit(f"mesh not closed after weld: {(cnt != 2).sum()} bad edges")
    verts = "".join(f'<vertex x="{x:.6g}" y="{y:.6g}" z="{z:.6g}"/>' for x, y, z in uniq)
    out = "".join(
        f'<triangle v1="{a}" v2="{b}" v3="{c}"{tris[i][3]}/>'
        for i, (a, b, c) in enumerate(f)
        if keep[i]
    )
    return f"<mesh><vertices>{verts}</vertices><triangles>{out}</triangles></mesh>"


def main(path: str) -> None:
    with zipfile.ZipFile(path) as zin, tempfile.NamedTemporaryFile(suffix=".3mf", delete=False) as tmp:
        with zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename.endswith(".model"):
                    data = MESH.sub(lambda m: weld(m.group(1)), data.decode()).encode()
                zout.writestr(item, data)
    shutil.move(tmp.name, path)
    print("welded", path)


if __name__ == "__main__":
    for p in sys.argv[1:]:
        main(p)
