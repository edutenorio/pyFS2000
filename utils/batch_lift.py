import os
from icecream import ic

from pyFS2000 import Model

# model = r'C:\Models\J003339 Yggdrasil Spools & Wye Detailed Design\FS2000 WYE\YOP WYE.XYZ'
model = r'C:\Models\J003339 Yggdrasil Spools & Wye Detailed Design\FS2000 PLEM\YGP PLEM.xyz'
# model = r'C:\Models\J003339 Yggdrasil Spools & Wye Detailed Design\FS2000 WYE with Valve Support\YOP Wye w Valve Support.XYZ'

# FS2000 load combinations
lcomb = {
    'aux':  200,              # Auxiliary lift load combination
    '1.30': (201, 202, 203),  # Combinations for 1.30 consequence factor
    '1.15': (204, 205, 206),  # Combinations for 1.15 consequence factor
    '1.00': (207, 208, 209),  # Combinations for 1.00 consequence factor
}

load_case = {
    'weight_comb': 115,   # Unfactored in-air weight combination
    'weight_basic': 105,  # Unfactored in-air weight generated basic load case
    'lift_point': 29,     # Lift point load case
}

group_set = {
    '1.30': (6, 1),  # (Group set, group) for elements 1.30 consequence factor
    '1.15': (6, 2),  # (Group set, group) for elements 1.15 consequence factor
    '1.00': (6, 3),  # (Group set, group) for elements 1.00 consequence factor
    'hook': (5, 1),  # (Group set, group) for slings and hook
    'foundation': (10, 1),  # (Group set, group) for in-place foundation couple
}

result_set = {
    '1.30': 1,  # Result set for 1.30 consequence factor
    '1.15': 2,  # Result set for 1.30 consequence factor
    '1.00': 3,  # Result set for 1.30 consequence factor
    'all': 4,   # Result set for all lifting cases
}


# Start of lifting process
m1 = Model()
m1.load(model)

def run_line(cmd):
    cmd = cmd.strip()
    if len(cmd) == 0:
        return
    if cmd[0] == '*':
        return
    cmd_args = cmd.split()
    cmd_exec = cmd_args[0]
    cmd_parameters = ' '.join(cmd_args[1:])
    if cmd_exec == 'MFCOPY':
        source_file = os.path.join(m1.ModelDir, f'{m1.NAME}.{cmd_args[1][1:-1]}')
        dest_file = os.path.join(m1.ModelDir, f'{m1.NAME}.{cmd_args[2][1:-1]}')
        os_cmd = f'copy "{source_file}" "{dest_file}" /Y'
        print(f'> {cmd}')
        print(f'> {os_cmd}')
        print(f'')
        os.system(os_cmd)
        return
    os_cmd = '"' + os.path.join(os.path.join(m1.SystemPath, 'System'), f'{cmd_exec}.exe') + f'" {cmd_parameters}'
    print(f'> {cmd}')
    print(f'> {os_cmd}')
    print(f'')
    os.system(os_cmd)


# First auxiliary lift loop
print('Running self-weight to find CoG. . .')
run_line(f'MODMERGE M/MDL/UM_RESET/')
run_line(f'MODMERGE M/MDL/UM_INPLACE/')
run_line(f'WINFRAM I')
run_line(f'WINFRAM LC/{load_case["weight_comb"]}/{load_case["weight_basic"]}/Unfactored In-Air Weight (Installation)/')
run_line(f'BAND {m1.NodeList.first().NODE}')
run_line(f'LOADA C{lcomb["aux"]}/1/0/0/1/')
run_line(f'PILE3D')
run_line(f'POST6 C{lcomb["aux"]}')
run_line(f'OUT6 -{lcomb["aux"]}/0/0/3/1/0/0/3/.4/{group_set["foundation"][0]}/{group_set["foundation"][1]}'
         f'/0/LIFT_PRELIMINARY/')

# Check CoG
file = open(os.path.join(m1.ModelDir, f'{m1.NAME}.LIFT_PRELIMINARY.O{lcomb["aux"]}'), 'r')
lines = file.read().split('\n')
i = 0
while i < len(lines):
    i = i + 1
    if lines[i] == '*** SPRING/COUPLE FORCES - NODE to GROUND ***':
        break
reactions = lines[i+5].split()
fy, mx, mz = float(reactions[3]), float(reactions[5]), float(reactions[7])
cog_x, cog_z = mz / fy, -mx / fy
file.close()
# print(f'CoG at [{cog_x:.4f}, {cog_z:.4f}]')
ic(cog_x, cog_z)

# Change UM_LIFT file
print('Updating UM_LIFT file with new CoG')
file = open(os.path.join(m1.ModelDir, f'{m1.NAME}.UM_LIFT'), 'r')
lines = file.read().split('\n')
for i, line in enumerate(lines):
    if line.strip()[:2] == 'N,':
        line_parameters = line.split(',')
        line_parameters[2], line_parameters[4] = f'{cog_x:.4f}', f'{cog_z:.4f}'
        lines[i] = ','.join(line_parameters)
        ic(lines[i])
file.close()
file = open(os.path.join(m1.ModelDir, f'{m1.NAME}.UM_LIFT'), 'w')
file.write('\n'.join(lines))
file.close()

# Second auxiliary lift loop
print('Running lifting with both nodes fixed to find balanced reaction. . .')
run_line(f'MODMERGE M/MDL/UM_RESET/')
run_line(f'MODMERGE M/MDL/UM_LIFT/')
run_line(f'MODMERGE M/MDL/UM_LIFT_PRELIMINARY/')
run_line(f'WINFRAM I')
run_line(f'WINFRAM LC/{load_case["weight_comb"]}/{load_case["weight_basic"]}/Unfactored In-Air Weight (Installation)/')
run_line(f'BAND {m1.NodeList.first().NODE}')
run_line(f'LOADA C{lcomb["aux"]}/1/0/0/1/')
run_line(f'PILE3D')
run_line(f'POST6 C{lcomb["aux"]}')
run_line(f'OUT6 -{lcomb["aux"]}/0/0/3/1/0/0/3/.4/{group_set["hook"][0]}/{group_set["hook"][1]}/0/LIFT_PRELIMINARY/')

# Read sling reacion
file = open(os.path.join(m1.ModelDir, f'{m1.NAME}.LIFT_PRELIMINARY.O{lcomb["aux"]}'), 'r')
lines = file.read().split('\n')
i = 0
while i < len(lines):
    i = i + 1
    if lines[i] == '*** SPRING/COUPLE FORCES - NODE to GROUND ***':
        break
reactions = lines[i+6].split()
fy = float(reactions[3])
# print(f'Sling reaction is {fy} kN.')
ic(fy)

# Update the lift point load case
print(f'Updating file {m1.NAME}.L{load_case["lift_point"]} with the calculated reaction')
file = open(os.path.join(m1.ModelDir, f'{m1.NAME}.L{load_case["lift_point"]}'), 'r')
lines = file.read().split('\n')
for i, line in enumerate(lines):
    if line.strip()[:3] == 'NF,':
        line_parameters = line.split(',')
        line_parameters[3] = f'{fy*1000:.0f}'
        lines[i] = ','.join(line_parameters)
        ic(lines[i])
file.close()
file = open(os.path.join(m1.ModelDir, f'{m1.NAME}.L{load_case["lift_point"]}'), 'w')
file.write('\n'.join(lines))
file.close()

# Run the lift cases
print('Running the final lift cases. . .')
run_line(f'MODMERGE M/MDL/UM_RESET/')
run_line(f'MODMERGE M/MDL/UM_LIFT/')
run_line(f'WINFRAM I')
run_line(f'WINFRAM LC/{load_case["weight_comb"]}/{load_case["weight_basic"]}/Unfactored In-Air Weight (Installation)/')
run_line(f'')
run_line(f'*** RUN LIFT ANALYSIS')
run_line(f'BAND {m1.NodeList.first().NODE}')
for cf in ['1.30', '1.15', '1.00']:
    for lc in lcomb[cf]:
        run_line(f'LOADA C{lc}/1/0/0/1/')
        run_line(f'PILE3D')
        run_line(f'POST6 {lc}')
# run_line(f'POST6 {lcomb_lift[0]}-{lcomb_lift[-1]}')
run_line(f'')
run_line(f'*** CODE CHECK - ULS')
run_line(f'MFCOPY "UEC3RF_ULS" "UEC3RF"')
run_line(f'')
run_line(f'*** MEMBER CHECK')
for cf in ['1.30', '1.15', '1.00']:
    for lc in lcomb[cf]:
        run_line(f'EC3 {lc}/2/3/1/.4/{group_set[cf][0]}/{group_set[cf][1]}/0/LIFT_EL/0/')
# run_line(f'EC3 201-203/2/3/1/.4/6/1/0/LIFT_EL/0/')
# run_line(f'EC3 204-206/2/3/1/.4/6/2/0/LIFT_EL/0/')
# run_line(f'EC3 207-209/2/3/1/.4/6/3/0/LIFT_EL/0/')
run_line(f'')
run_line(f'*** JOINT CHECK')
for cf in ['1.30', '1.15', '1.00']:
    for lc in lcomb[cf]:
        run_line(f'PUNCH {lc}/2/.4/1/EC3/O/{group_set[cf][0]}/{group_set[cf][1]}/0/LIFT_JT/')
# run_line(f'PUNCH 201-203/2/.4/1/EC3/O/6/1/0/LIFT_JT/')
# run_line(f'PUNCH 204-206/2/.4/1/EC3/O/6/2/0/LIFT_JT/')
# run_line(f'PUNCH 207-209/2/.4/1/EC3/O/6/3/0/LIFT_JT/')
run_line(f'')
run_line(f'*** PROCESS CODE CHECK RESULTS')
run_line(f'URSORT MR/S{result_set["all"]}/1/.4/0/LIFT/LIFT_EL/')
run_line(f'URSORT JR/S{result_set["all"]}/1/.4//LIFT/LIFT_JT/')
run_line(f'')
run_line(f'*** EXTRACT SLING FORCES AND HOOK LOAD')
run_line(f'MOUT6 -{result_set["1.00"]}/0/1/3/0/0/0/3/.4/{group_set["hook"][0]}/{group_set["hook"][1]}'
         f'/0/LIFT_SLING_FORCES/')
run_line(f'MOUT6 -{result_set["1.00"]}/0/0/3/1/0/0/3/.4/{group_set["hook"][0]}/{group_set["hook"][1]}'
         f'/0/LIFT_HOOK_FORCES/')
