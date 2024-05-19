import logging

import numpy as np
import scipy.spatial.transform.rotation as rot

from .aux_functions import calc_ijk
from .base import FS2000Entity, ListedMixin, CalculatedMixin
from .exceptions import ParameterInvalid


class Element(ListedMixin, CalculatedMixin, FS2000Entity):
    """Defines an FS2000 model beam element."""
    type = 'E'
    parameters = ['ELEM', 'N1', 'N2', 'N3', 'ROT', 'GEOM', 'MAT', 'RELZ', 'RELY', 'TAPER', 'TYPE', 'CO', 'BENDRAD']
    paramdefaults = [0, 0, 0, 0, 0.0, 1, 1, 0, 0, 0, 0, 0, 0.0]

    def __init__(self, model, *args, **kwargs):
        """Create an element within the model."""
        self._N1, self._N2, self._N3, self._ROT, self._GEOM, self._MAT = 0, 0, 0, 0.0, 1, 1
        self._RELZ, self._RELY, self._TAPER, self._TYPE, self._CO, self._BENDRAD = 0, 0, 0, 0, 0, 0.0
        self._p1, self._p2, self._p3 = None, None, None
        self._i, self._j, self._k = None, None, None
        self._off1, self._off2 = np.zeros(3), np.zeros(3)
        self._bendang, self._length, self._bendcent, self._cog = 0.0, 0.0, np.zeros(3), np.zeros(3)
        super().__init__(model, *args, **kwargs)

    def __repr__(self):
        self.calculate()
        bend_comp = '' if np.isclose(self._BENDRAD, 0.0) else f'  Bend Radius = {self._BENDRAD:.4f}  ' \
                                                              f'Angle = {np.degrees(self._bendang):.2f}'
        return f'Elem Nod1 Nod2 Nod3    Rot    Length Geom Tapered Mat RelZ RelY Type CO\n' \
               f'{self.pk:>4} {self._N1:>4} {self._N2:>4} {self._N3 if self._N3 > 0 else "":>4} {self._ROT:>6.1f} ' \
               f'{self._length:>9.4f} {self._GEOM:>4} {self._TAPER if self._TAPER > 0 else "":>7} {self._MAT:>3} ' \
               f'{self._RELZ:>4} {self._RELY:>4} {self._TYPE:>4} {self._CO:>2}{bend_comp}'

    def commit(self, replace=True, update_items=None):
        super().commit()
        # Update active constants
        self._model._ACTN1 = self._N2
        self._model._ACTN3 = self._N3
        self._model._ACTROT = self._ROT
        self._model._ACTGEOM = self._GEOM
        self._model._ACTMAT = self._MAT
        self._model._ACTRELZ = self._RELZ
        self._model._ACTRELY = self._RELY
        self._model._ACTTYPE = self._TYPE
        self._model._ACTCON = self._CO
        self._model._LASTELEM = self

    # def create_en(self, cmd):
    #     """
    #     Create an element from the command:
    #     EN, Elem, x, y, z, N2
    #         The EN command is used to define an individual element and its end
    #         node. The start node of the element is the previously defined end
    #         node or the node defined by the ACTN command. This command is very
    #         useful for defining string elements since it creates node and
    #         elements on a 'from' to basis.
    #         Elem  : The element number to be assigned. Previous will be
    #                 re-defined. (Default: EMAX+1)
    #         x,y,z : Node location in global co-ordinate system. If a co-ordinate
    #                 value is omitted the node co-ordinate will be taken to be
    #                 the same as that of the last node defined.
    #         N2    : Node number for final node (default = NMAX+1)
    #     Obs: FS2000 is not using the values of ACTTYPE and ACTCON to define
    #          element TYPE and CO. Algorithm is adapted to match FS2000.
    #     """
    #     cmd_vals = self._cmd_split(cmd, 6)
    #     self._set_newpk(cmd_vals[1])
    #     # Use the current N1 node
    #     self._N1 = self._model.ACTN1
    #     # Create the new node N2
    #     logging.debug('Creating node from the EN command: {}'.format(
    #         'N,{node},{x},{y},{z},0'.format(node=cmd_vals[5], x=cmd_vals[2], y=cmd_vals[3], z=cmd_vals[4])))
    #     self._model.cmd(f'N,{cmd_vals[5]},{cmd_vals[2]},{cmd_vals[3]},{cmd_vals[4]}')
    #     self._N2 = self._model.LASTNODE.CODE
    #     # Attribute other parameters
    #     self._N3 = self._model.ACTN3
    #     self._ROT = self._model.ACTROT
    #     self._GEOM = self._model.ACTGEOM
    #     self._MAT = self._model.ACTMAT
    #     self._RELZ = self._model.ACTRELZ
    #     self._RELY = self._model.ACTRELY
    #     self._TAPER = 0
    #     self._TYPE = 0  # should be 'self._model._ACTTYPE', FS2000 creates as '0'
    #     self._CO = 0  # should be 'self._model._ACTCON', FS2000 creates as '0'
    #     self._BENDRAD = 0.0
    #     # Consolidate object
    #     self._consolidate()
    #
    # def create_enr(self, cmd):
    #     """
    #     Create an element from the command:
    #     ENR, Elem, x, y, z, N2
    #         This is identical to EN but the node co-ordinates are relative to
    #         the last node defined. Refer to help(Element.create_EN).
    #     Obs: FS2000 is not using the values of ACTTYPE and ACTCON to define
    #          element TYPE and CO. Algorithm is adapted to match FS2000.
    #     """
    #     cmd_vals = self._cmd_split(cmd, 6)
    #     self._set_newpk(cmd_vals[1])
    #     # Use the current N1 node
    #     self._N1 = self._model.ACTN1
    #     # Create the new node N2
    #     n2_origin = self._model.LASTNODE.xyzg if self._model.LASTNODE is not None else np.array([0, 0, 0])
    #     delta = np.array([try_float(cmd_vals[2]), try_float(cmd_vals[3]), try_float(cmd_vals[4])])
    #     n2 = n2_origin + delta
    #     logging.debug('Creating node from the ENR command: {}'.format(
    #         'N,{node},{x},{y},{z},0'.format(node=cmd_vals[5], x=n2[0], y=n2[1], z=n2[2])))
    #     self._model.cmd(f'N,{cmd_vals[5]},{n2[0]},{n2[1]},{n2[2]},0')
    #     self._N2 = self._model.LASTNODE.CODE
    #     # Attribute other parameters
    #     self._N3 = self._model.ACTN3
    #     self._ROT = self._model.ACTROT
    #     self._GEOM = self._model.ACTGEOM
    #     self._MAT = self._model.ACTMAT
    #     self._RELZ = self._model.ACTRELZ
    #     self._RELY = self._model.ACTRELY
    #     self._TAPER = 0
    #     self._TYPE = 0  # should be 'self._model._ACTTYPE', FS2000 creates as '0'
    #     self._CO = 0  # should be 'self._model._ACTCON', FS2000 creates as '0'
    #     self._BENDRAD = 0.0
    #     # Consolidate object
    #     self._consolidate()
    #
    # def create_egen(self, cmd):
    #     """
    #     Create an element from the command:
    #     EGEN, N1, N2, NINC, E1, EINC
    #         The EGEN command is used to generate line elements using a node
    #         pattern of existing line nodes. Use the ACT command to select
    #         property codes etc.
    #         N1   : First existing node (no default)
    #         N2   : Last existing node (no default)
    #         NINC : Increment of existing node pattern (default = 1)
    #         E1   : First element in set to be generated (default = EMAX+1)
    #         EINC : Increment for element to be generated (default = 1)
    #     """
    #     cmd_vals = self._cmd_split(cmd, 6)
    #     try:
    #         n1 = int(cmd_vals[1])
    #         n2 = int(cmd_vals[2])
    #     except ValueError:
    #         logging.error(f'No default values for N1 and N2 in EGEN command: {cmd}')
    #         raise NoDefault(f'No default values for N1 and N2 in EGEN command: {cmd}')
    #     ninc = try_int(cmd_vals[3], 1)
    #     e1 = try_int(cmd_vals[4], self._model.EMAX + 1)
    #     einc = try_int(cmd_vals[5], 1)
    #     nodes = range(n1, n2 + ninc, ninc)
    #     # Check for node range consistency
    #     if nodes[-1] != n2:
    #         logging.warning(f'Node range badly defined in EGEN command, watch out for weird results. {cmd}')
    #     logging.debug(f'Creating {len(nodes) - 1} elements from the EGEN command.')
    #     for i in range(0, len(nodes) - 1):
    #         Element(self._model, Elem=e1, N1=nodes[i], N2=nodes[i + 1])
    #         e1 += einc
    #
    # def create_ecopy(self, cmd):
    #     """
    #     Create an element from the command:
    #     ECOPY, E1, E2, EINC, NTIMES, EST, NINC
    #         The ECOPY command is used to copy an existing pattern of line
    #         elements using a pattern of existing nodes.
    #         E1     : First element in existing element pattern (default = 1)
    #         E2     : Last element in existing element pattern (default = E1)
    #         EINC   : Element increment in existing element pattern (default = 1)
    #         NTIMES : No of copies required (default = 1)
    #         EST    : First element (default = EMAX+1)
    #         NINC   : Node increment between existing node sets (default = 1)
    #
    #     OBS. FS2000 documentation says that 'The element numbering pattern will
    #          be preserved.', however the program does not preserve it when we
    #          use the ECOPY command. It creates sequential elements from EST.
    #          Algorithm changed to mimic the actual software behaviour.
    #     """
    #     cmd_vals = self._cmd_split(cmd, 7)
    #     e1 = try_int(cmd_vals[1], 1)
    #     e2 = try_int(cmd_vals[2], e1)
    #     einc = try_int(cmd_vals[3], 1)
    #     ntimes = try_int(cmd_vals[4], 1)
    #     est = try_int(cmd_vals[5], self._model.EMAX + 1)
    #     ninc = try_int(cmd_vals[6], 1)
    #     # List elements
    #     elements = []
    #     for e in range(e1, e2 + 1, einc):
    #         if e in self._model.Elements:
    #             elements.append(self._model.get_element(e))
    #             # elements[-1].calculate()
    #     for i in range(1, ntimes + 1):
    #         for elem in elements:
    #             # Create new element with same attributes then existing element
    #             new_attributes = dict()
    #             new_attributes['ELEM'] = est
    #             new_attributes['N1'] = elem.N1 + i * ninc
    #             new_attributes['N2'] = elem.N2 + i * ninc
    #             new_attributes['N3'] = 0
    #             for attribute in ['ROT', 'GEOM', 'MAT', 'RELZ', 'RELY', 'TAPER', 'TYPE', 'CO', 'BENDRAD']:
    #                 new_attributes[attribute] = getattr(elem, '_' + attribute)
    #             logging.debug('Copying element {}'.format(elem))
    #             Element(self._model, **new_attributes)
    #             # Increment element number
    #             est += 1
    #
    # def create_encopy(self, cmd):
    #     """
    #     Create an element from the command:
    #     ENCOPY, E1, E2, EINC, NTIMES, EST, NST, DX, DY, DZ
    #         The ENCOPY command is used to copy an existing pattern of line
    #         elements and create the nodes for the new elements. The node
    #         numbering pattern will be preserved.
    #         E1       : First element in existing element pattern (default = 1)
    #         E2       : Last element in existing element pattern (default = E1)
    #         EINC     : Element increment in existing element pattern (default=1)
    #         NTIMES   : No of copies required (default = 1)
    #         EST      : First element (default = EMAX+1)
    #         NST      : Start node number for new elements (default = NMAX+1)
    #         DX,DY,DZ : Co-ordinate increment between copies (Default = 0)
    #
    #     OBS. FS2000 documentation says that 'The element numbering pattern will
    #          be preserved.', however the program does not preserve it when we
    #          use the ECOPY command. It creates sequential elements from EST.
    #          Algorithm changed to mimic the actual software behaviour.
    #     """
    #     cmd_vals = self._cmd_split(cmd, 10)
    #     e1 = try_int(cmd_vals[1], 1)
    #     e2 = try_int(cmd_vals[2], e1)
    #     einc = try_int(cmd_vals[3], 1)
    #     ntimes = try_int(cmd_vals[4], 1)
    #     est = try_int(cmd_vals[5], self._model.EMAX + 1)
    #     nst = try_int(cmd_vals[6], self._model.NMAX + 1)
    #     dx, dy, dz = try_float(cmd_vals[7], 0.0), try_float(cmd_vals[8], 0.0), try_float(cmd_vals[9], 0.0)
    #     # edelta = est-e1
    #     # List elements and nodes
    #     elements, nodes = [], []
    #     for e in range(e1, e2 + 1, einc):
    #         if e in self._model.Elements:
    #             elements.append(self._model.get_element(e))
    #             # elements[-1].calculate()
    #             if elements[-1].N1 not in nodes:
    #                 nodes.append(self._model.get_node(elements[-1].N1))
    #             if elements[-1].N2 not in nodes:
    #                 nodes.append(self._model.get_node(elements[-1].N2))
    #     if len(elements) == 0:
    #         logging.warning(f'No elements found in range {e1},{e2},{einc}')
    #         return
    #     ninc = nst - min(nodes).CODE
    #     # Create copies
    #     for i in range(1, ntimes + 1):
    #         for node in nodes:
    #             # Create nodes
    #             self._model.cmd(f'N,{node.CODE + i * ninc},{node.X + i * dx},{node.Y + i * dy},{node.Z + i * dz},'
    #                             f'{node.CSYS}')
    #         for elem in elements:
    #             # Create new element with same attributes then existing element
    #             new_attributes = dict()
    #             new_attributes['ELEM'] = est
    #             new_attributes['N1'] = elem.N1 + i * ninc
    #             new_attributes['N2'] = elem.N2 + i * ninc
    #             new_attributes['N3'] = 0
    #             for attribute in ['ROT', 'GEOM', 'MAT', 'RELZ', 'RELY', 'TAPER', 'TYPE', 'CO', 'BENDRAD']:
    #                 new_attributes[attribute] = getattr(elem, '_' + attribute)
    #             logging.debug('Copying element {}'.format(elem))
    #             Element(self._model, **new_attributes)
    #             # Increment element number
    #             est += 1
    #
    # def create_edel(self, cmd):
    #     """
    #     Delete elements from the command:
    #     EDEL, E1, E2, EINC
    #         The EDEL command is used to delete an existing pattern of line
    #         elements.
    #         E1       : First element in existing element pattern (no default)
    #                    or Group No
    #         E2       : Last element in existing element pattern (default = E1)
    #         EINC     : Element increment in existing element pattern (default=1)
    #
    #         Using Groups: If E1 is defined as a negative value (define E2 and
    #                       EINC = 0) then it will be interpreted as a Group No in
    #                       the current Group SET. See GRPSET command.
    #     """
    #     logging.debug('No new element created')
    #     cmd_vals = self._cmd_split(cmd, 4)
    #     try:
    #         e1 = int(cmd_vals[1])
    #     except ValueError:
    #         logging.error(f'No default values for E1 in EDEL command: {cmd}')
    #         raise NoDefault(f'No default values for E1 in EDEL command: {cmd}')
    #     e2 = try_int(cmd_vals[2], e1)
    #     einc = try_int(cmd_vals[3], 1)
    #     if e1 < 0:
    #         logging.warning('Element group still to be implemented. EDEL command will do nothing.')
    #     else:
    #         for e in range(e1, e2 + 1, einc):
    #             if e in self._model.Elements:
    #                 logging.debug(f'Removing element {e}')
    #                 self._model.Elements.remove(e)
    #
    # def create_emod(self, cmd):
    #     """
    #     Modifies elements from the command:
    #     EMOD, E1, E2, EINC, Attribute, AttValue
    #         The EDEL command is used to delete an existing pattern of line
    #         elements.
    #         E1        : First element in existing element pattern (no default)
    #                     or Group No
    #         E2        : Last element in existing element pattern (default = E1)
    #         EINC      : Element increment in existing element pattern
    #                     (default = 1)
    #         Attribute : This identifies the property to be re-defined
    #                     1 - Geometric Property Code
    #                     2 - Material Property Code
    #                     3 - Element Type
    #                     4 - CO Constant
    #         AttValue  : Specifies the value of the attribute.
    #
    #         Using Groups: If E1 is defined as a negative value (define E2 and
    #                       EINC = 0) then it will be interpreted as a Group No in
    #                       the current Group SET. See GRPSET command.
    #     """
    #     logging.debug('No new element created')
    #     cmd_vals = self._cmd_split(cmd, 6)
    #     try:
    #         e1 = int(cmd_vals[1])
    #     except ValueError:
    #         logging.error(f'No default values for E1 in EMOD command: {cmd}')
    #         raise NoDefault(f'No default values for E1 in EMOD command: {cmd}')
    #     e2 = try_int(cmd_vals[2], e1)
    #     einc = try_int(cmd_vals[3], 1)
    #     try:
    #         attribute = int(cmd_vals[4])
    #     except ValueError:
    #         logging.error(f'No default values for Attribute in EMOD command: {cmd}')
    #         raise NoDefault(f'No default values for Attribute in EMOD command: {cmd}')
    #     if attribute not in [1, 2, 3, 4]:
    #         logging.error(f'Invalid attribute {attribute} in EMOD command: {cmd}')
    #         raise ParameterInvalid(f'Invalid attribute {attribute} in EMOD command: {cmd}')
    #     try:
    #         attvalue = int(cmd_vals[5])
    #     except ValueError:
    #         logging.error(f'No default values for AttValue in EMOD command: {cmd}')
    #         raise NoDefault(f'No default values for AttValue in EMOD command: {cmd}')
    #     attnames = ['GEOM', 'MAT', 'TYPE', 'CO']
    #     for e in range(e1, e2 + 1, einc):
    #         if e in self._model.Elements:
    #             elem = self._model.get_element(e)
    #             logging.debug(f'Changing element {elem.CODE} attribute {attnames[attribute-1]} from '
    #                           f'{getattr(elem, "_" + attnames[attribute-1])} to {attvalue}')
    #             setattr(elem, '_' + attnames[attribute-1], attvalue)
    #
    # def create_egroup(self, cmd):
    #     """
    #     The EGROUP command is used set the current group to which elements will
    #     be assigned.
    #     """
    #     cmd_vals = self._cmd_split(cmd, 2)
    #     self._model._EGROUP = try_int(cmd_vals[1], self._model._EGROUP)
    #     logging.debug(f'Current element group changed to {self._model._EGROUP}. No new element created.')
    #     logging.warning('Element groups not implemented yet.')
    #
    # def create_emax(self, cmd):
    #     """
    #     The EMAX command is uded to define the maximum element label in the
    #     model.
    #     """
    #     cmd_vals = self._cmd_split(cmd, 2)
    #     self._model._EMAX = try_int(cmd_vals[1], self._model._EMAX)
    #     logging.debug(f'Maximum element label set to {self._model._EMAX}. No new element created.')

    def calculate(self):
        """
        Calculate element properties: local coordinate system, bend radius,
        length.
        """
        if self._calculated:
            return
        logger = logging.getLogger('FS2000')
        # Local coordinate system
        # Check if nodes N1 and N2 exist
        if (self._N1 in self._model.NodeList) and (self._N2 in self._model.NodeList):
            # Calculate and save initial and final end point coordinates, and reference point coordinates if any
            self._p1, self._p2 = self._model.NodeList.get(self._N1).xyzg, self._model.NodeList.get(self._N2).xyzg
            self._p3 = self._model.NodeList.get(self._N3).xyzg if self._N3 > 0 else None
            # Calculate and save local CS vectors with no offsets
            self._i, self._j, self._k, self._ROT = calc_ijk(self._p1, self._p2, self._p3, self._ROT)
            # Apply offsets
            eof = self._model.ElemOffsetList.get(self.pk)
            if eof is not None:
                off = [np.array([0, 0, 0]), np.array([0, 0, 0])]
                # Element End id Code: 1 - First node only, 2 - Second node only, 3 - Both nodes
                node_offset_options = [[1, 3], [2, 3]]
                # Node offsets
                for node_end in [0, 1]:
                    if eof.NOEF in node_offset_options[node_end]:
                        if getattr(eof, f'_EREF{node_end + 1}') == 0:
                            # Global coordinates
                            off[node_end] = np.array([getattr(eof, f'_X{node_end + 1}'),
                                                      getattr(eof, f'_Y{node_end + 1}'),
                                                      getattr(eof, f'_Z{node_end + 1}')])
                        else:
                            # Local coordinates, may be from the element itself or another element
                            # eref = self if getattr(eof, f'EREF{node_end+1}') == self.pk else \
                            #     self._model.get_element(getattr(eof, f'EREF{node_end+1}'))
                            eref = self._model.ElementList.get(getattr(eof, f'EREF{node_end + 1}'))
                            if eref != self:
                                eref.calculate()
                            xi = getattr(eof, f'X{node_end + 1}')
                            yi = getattr(eof, f'Y{node_end + 1}')
                            zi = getattr(eof, f'Z{node_end + 1}')
                            off[node_end] = xi * eref._i + yi * eref._j + zi * eref._k
                # Save calculated offsets
                self._off1, self._off2 = off[0], off[1]
                # Recalculate and save offseted p1 and p2
                self._p1, self._p2 = self._p1 + self._off1, self._p2 + self._off2
                # Recalculate and save local CS vectors
                self._i, self._j, self._k, self._ROT = calc_ijk(self._p1, self._p2, self._p3, self._ROT)
        else:
            # Attribute defaults
            self._p1, self._p2, self._p3 = np.zeros(3), np.zeros(3), np.zeros(3)
            self._i = np.array([1, 0, 0], dtype=float)
            self._j = np.array([0, 1, 0], dtype=float)
            self._k = np.array([0, 0, 1], dtype=float)
            # Raise warning
            if (self._N1 not in self._model.NodeList) and (self._N2 not in self._model.NodeList):
                txt = f'Undefined nodes {self._N1} and {self._N2} in element {self.pk}.'
            else:
                txt = f'Undefined node {self._N1 if self._N1 not in self._model.NodeList else self._N2} ' \
                      f'in element {self.pk}'
            logger.warning(txt)
        # Bend angle (if applicable)
        if self._TYPE in [2, 3]:
            # logger.debug('Calculating element {} bend angle.'.format(self.pk))
            # Find end points
            if self._TYPE == 3:
                # If element is type 3, the third node is the bend centre
                pc1, pc2 = self._p1 - self._p3, self._p2 - self._p3
                # Check sizes
                if not (np.isclose(np.linalg.norm(pc1), np.linalg.norm(pc2), atol=1.0E-4) and
                        (np.isclose(np.linalg.norm(pc1), self._BENDRAD, atol=1.0E-4)) and
                        (np.isclose(np.linalg.norm(pc2), self._BENDRAD, atol=1.0E-4))):
                    logger.warning(f'Bend radius does not match node distances in element {self.pk}. '
                                   f'BENDRAD={self._BENDRAD}, dist1={np.linalg.norm(pc1)}, '
                                   f'dist2={np.linalg.norm(pc2)}')
                # Calculate the angle between the two vectors
                self._bendang = np.arccos(np.dot(pc1, pc2) / (np.linalg.norm(pc1) * np.linalg.norm(pc2)))
            else:
                # If element is type 2, the third node is the intersection of the tangents
                pi1, pi2 = self._p1 - self._p3, self._p2 - self._p3
                # Check distances
                if not np.isclose(np.linalg.norm(pi1), np.linalg.norm(pi2), atol=1.0E-4):
                    logger.warning(f'Bend tangent distances do not match in element {self.pk}: '
                                   f'tan1={np.linalg.norm(pi1)}, tan2={np.linalg.norm(pi2)}')
                # Calculate the angle between two vectors. The bend angle is equal to pi minus the angle
                # between the tangents
                self._bendang = np.pi - np.arccos(np.dot(pi1, pi2) / (np.linalg.norm(pi1) * np.linalg.norm(pi2)))
            if self._bendang > np.pi / 2:
                logger.warning(f'FS2000 restricts the bend angle between 0 and 90 degress. '
                               f'Calculated value is {np.degrees(self._bendang):.2f}. Watch out for consistency.')
            # Bend centre
            if self._TYPE == 3:
                # If type is 3, P3 is already the bend centre
                self._bendcent = self._p3
            else:
                # Otherwise, it has to be calculated
                a, b = self._p1 - self._p3, self._p2 - self._p3
                c = np.cross(b, a)
                a, b, c = a / np.linalg.norm(a), b / np.linalg.norm(b), c / np.linalg.norm(c)
                r = rot.Rotation.from_rotvec(np.pi / 2 * c)
                ap, bp = r.apply(a), r.apply(b)
                # System
                # p1 + r1*ap = p2 + r2*bp = centre
                # ap*r1 - bp*r2 = p2 - p1
                # [ [ ap[0], -bp[0] ]       [ [r1]      [ [ p2[0]-p1[0] ]
                #   [ ap[1], -bp[1] ]    *    [r2] ]  =   [ p2[1]-p1[1] ]
                #   [ ap[2], -bp[2] ] ]                   [ p2[2]-p1[2] ] ]
                mat_a = np.array([[ap[0], -bp[0]], [ap[1], -bp[1]], [ap[2], -bp[2]]])
                delta_p = np.array(
                    [[self._p2[0] - self._p1[0]], [self._p2[1] - self._p1[1]], [self._p2[2] - self._p1[2]]])
                mat_r = np.linalg.lstsq(mat_a, delta_p, rcond=None)[0]
                r1, r2 = mat_r[0][0], mat_r[1][0]
                self._bendcent = self._p1 + ap * r1  # could be p2 + bp * r2, supposed to be equivalent
        # Element length and C.o.G.
        if self._TYPE in [2, 3]:
            self._length = self._BENDRAD * self._bendang
            # Bend cog in local coordinate x-y, origin in bend centre, x in direction of p1, y perpendicular
            # in direction of p2
            x, y = self._p1 - self._bendcent, self._p2 - self._bendcent
            py = np.dot(y, x) / np.dot(x, x) * x                 # projection of y in x
            y = y - py                                           # now y is perpendicular to x
            x, y = x / np.linalg.norm(x), y / np.linalg.norm(y)  # Now both vectors are unitary
            x_cog = self._BENDRAD * np.sin(self._bendang) / self._bendang        # CoG x-coordinate in x-y plane
            y_cog = self._BENDRAD * (1 - np.cos(self._bendang)) / self._bendang  # CoG y-coordinate in x-y plane
            self._cog = x_cog * x + y_cog + y  # CoG in global coordinates
        else:
            self._length = np.linalg.norm(self._p2 - self._p1)
            self._cog = (self._p1 + self._p2) / 2
        # Update flag
        super().calculate()

    @property
    def length(self):
        """Element length (considering offsets and bends)"""
        self.calculate()
        return self._length

    @property
    def bendang(self):
        """Angle of a bend element, in degrees"""
        self.calculate()
        if self._TYPE not in [2, 3]:
            return 0.0
        return np.degrees(self._bendang)

    @property
    def ELEM(self):
        """Element number"""
        return self.pk

    @property
    def N1(self):
        """Start node of element"""
        return self._model.NodeList.get(self._N1)

    @N1.setter
    def N1(self, value):
        self._N1 = int(value)
        self._calculated = False

    @property
    def N2(self):
        """End node of element"""
        return self._model.NodeList.get(self._N2)

    @N2.setter
    def N2(self, value):
        self._N2 = int(value)
        self._calculated = False

    @property
    def N3(self):
        """Third node of element used to define local rotation"""
        return self._model.NodeList.get(self._N3)

    @N3.setter
    def N3(self, value):
        self._N3 = int(value)
        self._calculated = False

    @property
    def ROT(self):
        """Local element rotation angle"""
        return self._ROT

    @ROT.setter
    def ROT(self, value):
        # if self._N3 > 0:
        #     logger = logging.getLogger('FS2000')
        #     logger.warning('ROT definition will be meaningless when third node N3 is defined')
        self._ROT = float(value)
        self._calculated = False

    @property
    def GEOM(self):
        """Geometrical property table code"""
        return self._model.GeometryList.get(self._GEOM)

    @GEOM.setter
    def GEOM(self, value):
        self._GEOM = int(value)
        self._calculated = False

    @property
    def MAT(self):
        """Material Property table code"""
        return self._model.MaterialList.get(self._MAT)

    @MAT.setter
    def MAT(self, value):
        self._MAT = int(value)
        self._calculated = False

    @property
    def RELZ(self):
        """Hinge Definition - local-z axis"""
        return self._RELZ

    @RELZ.setter
    def RELZ(self, value):
        value_error, relz = False, 0
        try:
            relz = int(value)
        except ValueError:
            value_error = True
        if (relz not in [0, 1, 2, 3]) or value_error:
            raise ParameterInvalid(f'Invalid RELZ value: {value}. Should be (0, 1, 2 or 3)')
        self._RELZ = relz

    @property
    def RELY(self):
        """Hinge Definition - local-y axis"""
        return self._RELY

    @RELY.setter
    def RELY(self, value):
        value_error, rely = False, 0
        try:
            rely = int(value)
        except ValueError:
            value_error = True
        if (rely not in [0, 1, 2, 3]) or value_error:
            raise ParameterInvalid(f'Invalid RELY value: {value}. Should be (0, 1, 2 or 3)')
        self._RELY = rely

    @property
    def TAPER(self):
        """
        This is used to identify tapered beams by defining the geom property
        code at the end node of an element.
        A +ve value signifies a Type A Taper,
        A -ve value signifies a Type B Taper.
        Default is 0, no taper
        """
        return self._TAPER

    @TAPER.setter
    def TAPER(self, value):
        self._TAPER = int(value)
        self._calculated = False

    @property
    def TYPE(self):
        """Element Type"""
        return self._TYPE

    @TYPE.setter
    def TYPE(self, value):
        value_error, t = False, 0
        try:
            t = int(value)
        except ValueError:
            value_error = True
        if (t not in [0, 2, 3, 6, 7, 8, 15, 16]) or value_error:
            raise ParameterInvalid(f'Invalid Element TYPE value: {value}. Should be (0, 2, 3, 6, 7, 8, 15 or 16)')
        self._TYPE = t
        self._calculated = False

    @property
    def CO(self):
        """Additional CO constant"""
        return self._CO

    @CO.setter
    def CO(self, value):
        self._CO = int(value)
        self._calculated = False

    @property
    def BENDRAD(self):
        """Bend radius for Type 2 and Type 3 elements"""
        return self._BENDRAD

    @BENDRAD.setter
    def BENDRAD(self, value):
        self._BENDRAD = float(value)
        self._calculated = False

    @property
    def bendcent(self):
        """Bend Centre for Type 2 and Type 3 elements"""
        # Return None if element is not a bend
        if self._TYPE not in [2, 3]:
            return None
        self.calculate()
        return self._bendcent

    @property
    def p1(self):
        """Effective initial point coordinates (considering offsets)"""
        self.calculate()
        return self._p1

    @property
    def p2(self):
        """Effective final point coordinates (considering offsets)"""
        self.calculate()
        return self._p2

    @property
    def p3(self):
        """Reference point coordinates"""
        self.calculate()
        return self._p3

    @property
    def cog(self):
        """Element Centre of Gravity"""
        self.calculate()
        return self._cog

    @property
    def localX(self):
        """Element Local-X direction vector"""
        self.calculate()
        return self._i

    @property
    def localY(self):
        """Element Local-X direction vector"""
        self.calculate()
        return self._j

    @property
    def localZ(self):
        """Element Local-X direction vector"""
        self.calculate()
        return self._k
