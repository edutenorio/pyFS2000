import os
import numpy as np
import tkinter as tk
from tkinter import filedialog
from icecream import ic

from pyFS2000 import Model

# file_path = r'C:\Models\J003448 HEP Tie-in Module FEED\FS2000 TIM\TIM_Stack_041224.XYZ'
# file_path = ''
#
# Select the model file
# if file_path == '':
#     root = tk.Tk()
#     root.withdraw()
#     file_path = filedialog.askopenfilename(defaultextension='XYZ',
#                                            filetypes=[('FS2000 Model', '*.XYZ'), ('All files', '*.*')],
#                                            initialdir=r'C:\Models')
#     ic(file_path)
file_path = r'data\Grane Wye.MDL'

# Load model
m1 = Model()
m1.load(file_path)
f = open(os.path.join('spaceclaim', f'FS2000_{m1.NAME}.py'), 'w')
f.write(f'ClearAll()\n')

# elemList = m1.ElementList.copy().filter(MAT=4, GEOM__in=[47, 52])
elemList = m1.ElementList.copy()
# elemList = m1.ElementList.copy()
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
    # Create solid
    geom = element.GEOM
    dimensions = geom.get_dimensions()
    if dimensions is None:
        continue
    if dimensions['FORMAT'] == 'P':
        # Pipe (Tubular) - check if element is a bend
        if element.TYPE in [2, 3]:
            # Bend element
            f.write(f'element = SpaceClaimBend(')
            f.write(f'BENDCENT=[{", ".join(str(x) for x in element.bendcent)}], ')
            f.write(f'BENDRAD={element.BENDRAD}, ')
            f.write(f'BENDANG={element.bendang}, ')
        else:
            # Straight pipe element
            f.write(f'element = SpaceClaimTubular(')
        f.write(f'Desig="TUB {element.GEOM.od*1000:.1f} x {element.GEOM.wt*1000:.2f}", ')
    elif dimensions['FORMAT'] == 'B':
        # Box section
        f.write(f'element = SpaceClaimBox(')
    elif dimensions['FORMAT'] in ['I', '2']:
        # I-Section
        f.write(f'element = SpaceClaimISection(')
    elif dimensions['FORMAT'] == 'C':
        # I-Section
        f.write(f'element = SpaceClaimChannel(')
    else:
        continue
    f.write(f'MODEL_UNIT=' + ('"S.I."' if m1.is_SI() else '"USA-Units"') + ', ')
    f.write(', '.join([f'{k}={dimensions[k]}' for k in list(dimensions.keys())[1:]]) + ', ')
    f.write(f'p1=[{", ".join([str(x) for x in p1])}], ')
    f.write(f'p2=[{", ".join([str(x) for x in p2])}], ')
    f.write(f'i=[{", ".join([str(x) for x in element.localX])}], ')
    f.write(f'j=[{", ".join([str(x) for x in element.localY])}], ')
    f.write(f'k=[{", ".join([str(x) for x in element.localZ])}], ')
    f.write(f'material="M{element.MAT.pk}", geometry="P{element.GEOM.pk}", ')
    f.write(f'name="E{element.pk}", ')
    f.write(f').create_body()\n')
    e0 = element
f.close()
