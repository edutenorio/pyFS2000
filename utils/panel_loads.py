from pyFS2000 import Model
from datetime import datetime
from icecream import ic
import os


file_path = r'C:\Models\J003339 Yggdrasil Spools & Wye Detailed Design\FS2000 PLEM\YGP PLEM.xyz'

q = -0.015 * 7850 * 9.81
load_number, load_description = 5, 'Mudmat (15mm)'
# For each panel, the first and last nodes define the rectangle, any other node is used to define the boundary in case
# there are nodes at multiple elevations
# If the first node is negative, all the panels found in that area will be excluded. They should be defined after the
# positive ones, otherwise they will be included again.
macro_panels = [(941, 936, 21, 30, 556), (-34, 928, 47, 556)]

q = -0.015 * 7850 * 9.81  # 15mm plate
load_number, load_description = 9, 'Interface Plates & Diver Grating'
macro_panels = [(843, 64), (841, 840, 63)]  # Interface plate

q = -51.7*9.81  # 51.7 kg/m2 Grating
load_number, load_description = 9, 'Interface Plates & Diver Grating'
macro_panels = [(577, 571), (573, 564, 931, 910)]  # Interface plate



m1 = Model()
m1.load(file_path)

area = 0
panels = []
for rect_nodes in macro_panels:
    # Inclusion Mode or Exclusion mode
    include = rect_nodes[0] > 0
    rect_nodes = [abs(n) for n in rect_nodes]
    # Get boundaries
    xbounds = (lambda v: (min(v), max(v)))([m1.NodeList.get(n).X for n in rect_nodes])
    ybounds = (lambda v: (min(v), max(v)))([m1.NodeList.get(n).Y for n in rect_nodes])
    zbounds = (lambda v: (min(v), max(v)))([m1.NodeList.get(n).Z for n in rect_nodes])

    # Calculate area
    area += (1 if include else -1) * (max(xbounds) - min(xbounds)) * (max(zbounds) - min(zbounds))

    # Filter nodes inside the rectangle

    # nlist = m1.NodeList.filter(X__range=xbounds, Y__range=ybounds, Z__range=zbounds).order_by('X').order_by('Z')
    # elist = m1.ElementList.filter(N1__in=nlist, N2__in=nlist)
    elist = m1.ElementList.filter(p1__func=lambda p: (xbounds[0] <= p[0] <= xbounds[1]) and
                                                     (ybounds[0] <= p[1] <= ybounds[1]) and
                                                     (zbounds[0] <= p[2] <= zbounds[1]),
                                  p2__func=lambda p: (xbounds[0] <= p[0] <= xbounds[1]) and
                                                     (ybounds[0] <= p[1] <= ybounds[1]) and
                                                     (zbounds[0] <= p[2] <= zbounds[1]))
    nlist = m1.NodeList.filter(NODE__in=[e.N1 for e in elist] + [e.N2 for e in elist])
    ic(elist)
    ic(nlist)

    # Look for panels
    # start_node_list = m1.NodeList.filter(NODE=nlist.first())
    start_node_list = m1.NodeList.filter(NODE=rect_nodes[0])
    while len(start_node_list) > 0:
        try:
            start_node = start_node_list.pop(0)
            # Walk in x-direction until we find a transversal element
            has_vertical = False
            current_node = start_node
            while not has_vertical:
                next_element = (elist.filter(N1=current_node, N2__X__gt=current_node.X, N2__Z=current_node.Z) +
                                elist.filter(N2=current_node, N1__X__gt=current_node.X, N1__Z=current_node.Z)).first()
                next_node = next_element.N2 if current_node == next_element.N1 else next_element.N1
                has_vertical = len(elist.filter(N1=next_node, N2__Z__gt=next_node.Z, N2__X=next_node.X) +
                                   elist.filter(N2=next_node, N1__Z__gt=next_node.Z, N1__X=next_node.X)) > 0
                current_node = next_node
            xmin, xmax = start_node.X, current_node.X
            # Walk in z-direction until we find a horizontal element
            has_horizontal = False
            current_node = start_node
            while not has_horizontal:
                next_element = (elist.filter(N1=current_node, N2__Z__gt=current_node.Z, N2__X=current_node.X) +
                                elist.filter(N2=current_node, N1__Z__gt=current_node.Z, N1__X=current_node.X)).first()
                next_node = next_element.N2 if current_node == next_element.N1 else next_element.N1
                has_horizontal = len(elist.filter(N1=next_node, N2__X__gt=next_node.X, N2__Z=next_node.Z) +
                                     elist.filter(N2=next_node, N1__X__gt=next_node.X, N1__Z=next_node.Z)) > 0
                current_node = next_node
            zmin, zmax = start_node.Z, current_node.Z
            # Add to panels
            new_panel = (nlist.filter(X=xmin, Z=zmin).first().pk, nlist.filter(X=xmax, Z=zmax).first().pk)
            if include and (new_panel not in panels):
                panels.append(new_panel)
            elif (not include) and (new_panel in panels):
                panels.remove(new_panel)
            # if include:
            #     if new_panel not in panels:
            #         panels.append(new_panel)
            # else:
            #     if new_panel in panels:
            #         panels.remove(new_panel)
            # Add next nodes to start_node_list
            start_node_list.add_or_replace(nlist.filter(X=xmin, Z=zmax).first())
            start_node_list.add_or_replace(nlist.filter(X=xmax, Z=zmin).first())
            start_node_list.add_or_replace(nlist.filter(X=xmax, Z=zmax).first())
        except (IndexError, AttributeError):
            continue

ic(panels)
ic(area)

loads = dict()
ylim = (lambda v: (min(v), max(v)))([m1.NodeList.get(n).Y for panel in panels for n in panel])
area_checksum = 0
for panel in panels:
    # n1 = m1.NodeList.get(panel[0])
    # n3 = m1.NodeList.get(panel[1])
    # n2 = m1.NodeList.filter(X=n3.X, Z=n1.Z, Y=n1.Y).first()
    # n4 = m1.NodeList.filter(X=n1.X, Z=n3.Z, Y=n1.Y).first()
    xlim = (lambda v: (min(v), max(v)))([m1.NodeList.get(n).X for n in panel])
    # ylim = (lambda v: (min(v), max(v)))([m1.NodeList.get(n).Y for n in panel])
    zlim = (lambda v: (min(v), max(v)))([m1.NodeList.get(n).Z for n in panel])
    n1 = m1.NodeList.filter(X=xlim[0], Z=zlim[0], Y__range=ylim).first()
    n2 = m1.NodeList.filter(X=xlim[1], Z=zlim[0], Y__range=ylim).first()
    n3 = m1.NodeList.filter(X=xlim[1], Z=zlim[1], Y__range=ylim).first()
    n4 = m1.NodeList.filter(X=xlim[0], Z=zlim[1], Y__range=ylim).first()
    a0, b0 = abs(n2.X - n1.X), abs(n3.Z - n2.Z)
    # Horizontal elements
    h1 = m1.ElementList.filter(N1__X__ge=min([n1.X, n2.X]), N1__X__le=max([n1.X, n2.X]), N1__Y__range=ylim, N1__Z=n1.Z,
                               N2__X__ge=min([n1.X, n2.X]), N2__X__le=max([n1.X, n2.X]), N2__Y__range=ylim, N2__Z=n1.Z)
    h2 = m1.ElementList.filter(N1__X__ge=min([n1.X, n2.X]), N1__X__le=max([n1.X, n2.X]), N1__Y__range=ylim, N1__Z=n3.Z,
                               N2__X__ge=min([n1.X, n2.X]), N2__X__le=max([n1.X, n2.X]), N2__Y__range=ylim, N2__Z=n3.Z)
    # Vertical elements
    v1 = m1.ElementList.filter(N1__X=n1.X, N1__Y__range=ylim, N1__Z__ge=min([n1.Z, n3.Z]), N1__Z__le=max([n1.Z, n3.Z]),
                               N2__X=n1.X, N2__Y__range=ylim, N2__Z__ge=min([n1.Z, n3.Z]), N2__Z__le=max([n1.Z, n3.Z]))
    v2 = m1.ElementList.filter(N1__X=n2.X, N1__Y__range=ylim, N1__Z__ge=min([n1.Z, n3.Z]), N1__Z__le=max([n1.Z, n3.Z]),
                               N2__X=n2.X, N2__Y__range=ylim, N2__Z__ge=min([n1.Z, n3.Z]), N2__Z__le=max([n1.Z, n3.Z]))
    # Organize elements so that a is the larger side and b is the shorter side
    a_elements = h1 + h2 if a0 > b0 else v1 + v2
    b_elements = v1 + v2 if a0 > b0 else h1 + h2
    a, b = max([a0, b0]), min([a0, b0])
    area_checksum += a * b
    q_b = q * b / 4
    q_a = q * b * (2 * a - b) / (4 * a)
    for element in a_elements:
        if element.pk in loads:
            loads[element.pk] += q_a
        else:
            loads[element.pk] = q_a
    for element in b_elements:
        if element.pk in loads:
            loads[element.pk] += q_b
        else:
            loads[element.pk] = q_b

ic(area_checksum)

# Sort loads by element
loads = {k: loads[k] for k in sorted(loads.keys())}

# Write loads to load file
file_path_l5 = os.path.join(os.path.dirname(file_path), f'{m1.NAME}.L{load_number}')

if os.path.exists(file_path_l5):
    f = open(file_path_l5, 'r')
    lines = f.read().split('\n')
    f.close()
    f = open(file_path_l5, 'w')
    f.write('\n'.join(lines[:5] if lines[0].strip() == 'REFORMAT' else lines[:4]) + '\n')
else:
    f = open(file_path_l5, 'w')
    f.write(f'REFORMAT\n')
    f.write(f'MODEL,{m1.NAME}\n')
    f.write(f'TITLE,{m1.TITLE}\n')
    f.write(f'LCASE,{load_number}\n')
    f.write(f'LDESC,{load_description}\n')
f.write(f'LDATE,{datetime.now().strftime('%d/%m/%Y')} \n')
f.write(f'LTIME,{datetime.now().strftime('%H:%M:%S')}\n')
f.write(f'ACCEL,0,0,0\n')
for element, load in loads.items():
    f.write(f'UDL,{element},0,{load},0,1\n')
f.write('END OF FILE\n')
f.close()
