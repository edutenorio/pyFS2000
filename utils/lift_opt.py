import logging
from icecream import ic
import numpy as np
import os
from pyFS2000 import Model, set_logger


set_logger(logger_name='FS2000', level=logging.DEBUG, log_file='batch_test.log')

m1 = Model()
m1.load_active()
ic(m1)

batch_commands = """
MODMERGE M/MDL/UM_LIFTOPT/
WINFRAM I
LOADA C101/0/0/
OFRAME 
POST6 C101
OUT6 -101/0/1/3/0/0/0/3/.4/1/1/0/SLINGS/
"""

# dist_opt, force_opt = -1, -1
# N31, N5, N6, v = None, None, None, None
# for dist in np.arange(7.5, 8.5, 0.1):
#     m1.load_active()
#     N31, N5, N6 = m1.NodeList.get(31), m1.NodeList.get(5), m1.NodeList.get(6)
#     v = N5.xyz - N31.xyz
#     v /= np.linalg.norm(v)
#     N6.xyz = N31.xyz + v * dist
#     with open(os.path.join(os.path.dirname(m1.FilePath), f"{m1.NAME}.UM_LIFTOPT"), "w") as f:
#         f.write(f"{N6}\n")
#         f.close()
#     m1.run_batch(batch_commands)
#     with open(os.path.join(os.path.dirname(m1.FilePath), f"{m1.NAME}.SLINGS.O101"), "r") as f:
#         lines = f.read().split("\n")
#         forces = [float(lines[i].split()[2]) for i in [46, 50, 54, 58]]
#         max_force = max(forces)
#         ic(dist, forces, max_force)
#         if max_force < force_opt or force_opt < 0:
#             force_opt = max_force
#             dist_opt = dist
#         f.close()

def update_um(node):
    with open(os.path.join(os.path.dirname(m1.FilePath), f"{m1.NAME}.UM_LIFTOPT"), "w") as f:
        f.write(f"{node}\n")
        f.close()

def get_max_force():
    with open(os.path.join(os.path.dirname(m1.FilePath), f"{m1.NAME}.SLINGS.O101"), "r") as f:
        lines = f.read().split("\n")
        forces = [float(lines[i].split()[2]) for i in [46, 50, 54, 58]]
        max_force = max(forces)
        f.close()
    return max_force

m1.load_active()
N_Str, N_End, N_Flex = m1.NodeList.get(2), m1.NodeList.get(32), m1.NodeList.get(3)
P0 = N_Flex.xyz.copy()
v = N_End.xyz - N_Str.xyz
v /= np.linalg.norm(v)
step = 2
force_left, force_mid, force_right = None, None, None
count = 0
while step > 0.01:
    if not force_left:
        N_Flex.xyz = P0 - v * step
        update_um(N_Flex)
        m1.run_batch(batch_commands)
        force_left = get_max_force()
        count += 1
        ic(N_Flex.xyz, force_left)

    if not force_right:
        N_Flex.xyz = P0 + v * step
        update_um(N_Flex)
        m1.run_batch(batch_commands)
        force_right = get_max_force()
        count += 1
        ic(N_Flex.xyz, force_right)

    if not force_mid:
        N_Flex.xyz = P0.copy()
        update_um(N_Flex)
        m1.run_batch(batch_commands)
        force_mid = get_max_force()
        count += 1
        ic(N_Flex.xyz, force_mid)

    ic(force_left, force_mid, force_right)
    if force_mid <= force_left and force_mid <= force_right:
        force_left, force_right = None, None
        step /= 2
        ic("reduce step", step)
    elif force_left < force_right:
        ic("go left")
        P0 -= v * step
        force_left, force_mid, force_right = None, force_left, force_mid
    else:
        ic("go right")
        P0 += v * step
        force_left, force_mid, force_right = force_mid, force_right, None

ic(count, N_Flex, force_mid)
