from tkinter import filedialog
from icecream import ic
import os
import numpy as np
from operator import itemgetter
# import pandas as pd

from pyFS2000 import Model

active_model = Model.get_active_model()
if not active_model:
    exit(1)
file_path = filedialog.askopenfilename(defaultextension='XYZ',
                                       filetypes=[('FS2000 Model', '*.XYZ'), ('All files', '*.*')],
                                       initialdir=active_model['PATH'])
if not file_path:
    exit(1)

m1 = Model()
m1.load(file_path)
f = open(os.path.join("cad_script", f"{m1.NAME}.scr"), "w")

def cad_RSC(section):
    with (open(os.path.join("data", "RSC.csv"), "r") as f):
        lines = f.read().splitlines()
        headers = lines[0].split(",")
        values = {}
        for line in lines[1:]:
            if not line:
                continue
            items = line.split(",")
            values[items[0]] = {k: str(v) for k, v in zip(headers[:2], items[:2])} | {k: float(v) for k, v in zip(headers[2:], items[2:])}
        f.close()
    row = values[section]
    h, b, s, t, r1, r2, alpha, d, Cy = itemgetter("h", "b", "s", "t", "r1", "r2", "alpha", "d", "Cy")(row)
    theta, alpha, Cy = np.radians(90-alpha), np.radians(alpha), Cy*10
    c1 = [s+r1, d/2]
    c2 = [b-r2, d/2+r1*np.sin(theta)+(b-s-(r1+r2)*(1-np.cos(theta)))*np.tan(alpha)+r2*np.sin(theta)]
    pts = [
        # arc centre at (s+r1, d/2), radius = r1, included angle = theta, three points:
        (c1[0] + r1*np.cos(np.pi)            , c1[1] + r1*np.sin(np.pi)),
        (c1[0] + r1*np.cos(np.pi - theta / 2), c1[1] + r1*np.sin(np.pi - theta / 2)),
        (c1[0] + r1*np.cos(np.pi - theta)    , c1[1] + r1*np.sin(np.pi - theta)),
        # arc centre at (b-r2,d/2+r1*sin(theta)+(b-s-(r1+r2)*(1-cos(theta)))*tan(alpha)+r2*sin(theta)), radius = r2, included angle = theta, three points:
        (c2[0] + r2*np.cos(0-theta)  , c2[1] + r2*np.sin(0-theta)),
        (c2[0] + r2*np.cos(0-theta/2), c2[1] + r2*np.sin(0-theta/2)),
        (c2[0] + r2*np.cos(0)        , c2[1] + r2*np.sin(0)),
        (b, h/2),
        (0, h/2),
        None, None, None, None, None, None, None, None
    ]
    for i in range(8, 16):
        pts[i] = (pts[15-i][0], -pts[15-i][1])
    result = (f"pl\n{pts[0][0]},{pts[0][1]}\na\ns\n{pts[1][0]},{pts[1][1]}\n{pts[2][0]},{pts[2][1]}\nl\n"
              f"{pts[3][0]},{pts[3][1]}\na\ns\n{pts[4][0]},{pts[4][1]}\n{pts[5][0]},{pts[5][1]}\nl\n"
              f"{pts[6][0]},{pts[6][1]}\n{pts[7][0]},{pts[7][1]}\n"
              f"{pts[8][0]},{pts[8][1]}\n{pts[9][0]},{pts[9][1]}\n"
              f"{pts[10][0]},{pts[10][1]}\na\ns\n{pts[11][0]},{pts[11][1]}\n{pts[12][0]},{pts[12][1]}\nl\n"
              f"{pts[13][0]},{pts[13][1]}\na\ns\n{pts[14][0]},{pts[14][1]}\n{pts[15][0]},{pts[15][1]}\nl\nc\n"
              f"move\n?\nl\n\n0,0\n{-Cy},0\n")
    return result

def cad_I(d, bf, tw, tf, r):
    if np.isclose(r, 0.0):
        pts = [
            (tw/2, d/2-tf),
            (bf/2, d/2-tf),
            (bf/2, d/2),
        ]
        pts += [(-pt[0],  pt[1]) for pt in reversed(pts)]
        pts += [( pt[0], -pt[1]) for pt in reversed(pts)]
        result = f"pl\n" + "\n".join([f"{pt[0]},{pt[1]}" for pt in pts]) + f"\nc\n"
    else:
        c = [tw/2+r, d/2-tf-r]
        pts = [
            (c[0] + r*np.cos(np.pi)    , c[1] + r*np.sin(np.pi)),
            (c[0] + r*np.cos(3*np.pi/4), c[1] + r*np.sin(3*np.pi/4)),
            (c[0] + r*np.cos(np.pi/2)  , c[1] + r*np.sin(np.pi/2)),
            (bf/2, d/2-tf),
            (bf/2, d/2),
        ]
        pts += [(-pt[0],  pt[1]) for pt in reversed(pts)]
        pts += [( pt[0], -pt[1]) for pt in reversed(pts)]
        result = (f"pl\n"
                  f"{pts[0][0]},{pts[0][1]}\na\ns\n{pts[1][0]},{pts[1][1]}\n{pts[2][0]},{pts[2][1]}\nl\n"
                  f"{pts[3][0]},{pts[3][1]}\n{pts[4][0]},{pts[4][1]}\n"
                  f"{pts[5][0]},{pts[5][1]}\n{pts[6][0]},{pts[6][1]}\n{pts[7][0]},{pts[7][1]}\n"
                  f"a\ns\n{pts[8][0]},{pts[8][1]}\n{pts[9][0]},{pts[9][1]}\nl\n"
                  f"{pts[10][0]},{pts[10][1]}\na\ns\n{pts[11][0]},{pts[11][1]}\n{pts[12][0]},{pts[12][1]}\nl\n"
                  f"{pts[13][0]},{pts[13][1]}\n{pts[14][0]},{pts[14][1]}\n{pts[15][0]},{pts[15][1]}\n"
                  f"{pts[16][0]},{pts[16][1]}\n{pts[17][0]},{pts[17][1]}\n"
                  f"a\ns\n{pts[18][0]},{pts[18][1]}\n{pts[19][0]},{pts[19][1]}\nl\nc\n")
    return result

# elemList = m1.ElementList.copy().filter(MAT=4, GEOM__in=[47, 52])
elemList = m1.ElementList.copy()
while len(elemList) > 0:
    # Find string of elements
    element = elemList.pop(0)
    n1, p1, n2, p2 = element.N1, element.p1, element.N2, element.p2
    # Check for an element that ends where the string starts or starts where the string ends
    otherList = elemList.filter(N2=n1, GEOM=element.GEOM, MAT=element.MAT) + elemList.filter(N1=n2, GEOM=element.GEOM,
                                                                                             MAT=element.MAT)
    while otherList.count() > 0:
        other = otherList.pop(0)
        i_parallel = np.isclose(np.dot(element.localX, other.localX), 1.0, rtol=1e-2, atol=1e-3)
        j_parallel = np.isclose(np.dot(element.localY, other.localY), 1.0, rtol=1e-2, atol=1e-3)
        k_parallel = np.isclose(np.dot(element.localZ, other.localZ), 1.0, rtol=1e-2, atol=1e-3)
        if i_parallel and j_parallel and k_parallel:
            if n1 == other.N2:
                n1, p1 = other.N1, other.p1
            if n2 == other.N1:
                n2, p2 = other.N2, other.p2
            elemList.remove(other)
            otherList = elemList.filter(N2=n1, GEOM=element.GEOM, MAT=element.MAT) + elemList.filter(N1=n2,
                                                                                                     GEOM=element.GEOM,
                                                                                                     MAT=element.MAT)
    # Local coordinate system and element length
    p1, p2 = 1000 * p1, 1000 * p2
    i, j, k = element.localX, element.localY, element.localZ
    length = np.linalg.norm(p2-p1)
    # Generate UCS
    f.write("UCS\nw\n")
    f.write("UCS\n")
    f.write(",".join([str(x) for x in p1]) + "\n")
    f.write(",".join([str(x) for x in (p1 - k * length)]) + "\n")
    f.write(",".join([str(x) for x in (p1 + j * length)]) + "\n")
    # Create solid
    geom = element.GEOM
    dimensions = geom.get_dimensions()
    if dimensions is None:
        continue
    if dimensions['FORMAT'] == 'P':
        # Pipe (Tubular) - check if element is a bend
        if element.TYPE in [2, 3]:
            # Bend element
            ic("Generate bend")
        else:
            # Straight pipe element
            od_, id_ = dimensions['OD'] * 1000, (dimensions['OD'] - 2 * dimensions['WT']) * 1000
            f.write(f"c\n0,0\nd\n{od_}\n")
            f.write("region\n?\nl\n\n")
            f.write("-group\nc\nsect01\nSection\n?\nl\n\n")
            if not np.isclose(id_, 0.0):
                f.write(f"c\n0,0\nd\n{id_}\n")
                f.write("region\n?\nl\n\n")
                f.write("-group\nc\nsect02\nSection\n?\nl\n\n")
                f.write("subtract\n?\ng\nsect01\n\n?\ng\nsect02\n\n")
                f.write("-group\nr\nsect02\nall\n\n")
                f.write("-purge\ng\nsect02\nn\n")
            f.write("-group\nr\nsect01\nall\n\n")
            f.write("-purge\ng\nsect01\nn\n")
    elif dimensions['FORMAT'] == 'B':
        # Box section
        ic("Generate box, to be implemented")
    elif dimensions['FORMAT'] in ['I', '2']:
        # I-Section
        d, bf, tw, tf, r = dimensions["D"], dimensions["B"], dimensions["t"], dimensions["T"], dimensions["r"]
        f.write(cad_I(d, bf, tw, tf, r))
    elif dimensions['FORMAT'] == 'C':
        # C-Section
        if 'RSC' in dimensions["Desig"]:
            f.write(cad_RSC(dimensions["Desig"].split()[-1]))
        else:
            d, bf, tw, tf, r = dimensions["D"], dimensions["B"], dimensions["t"], dimensions["T"], dimensions["r"]
            ic("normal C to be implemented")
    else:
        # Return UCS to previous
        f.write("UCS\nw\n")
        continue
    # Extrude the section
    f.write(f"extrude\n?\nl\n\n{length}\n")
    # Return UCS to previous
    f.write("UCS\nw\n")

# Rotate model so that Z is vertical
f.write("rotate3d\nall\n\nx\n0,0,0\n90\n")
f.close()
