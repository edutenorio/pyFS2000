# Use commands as classes
import logging

import numpy as np
from icecream import ic

from .load_cases import LoadCase
from .loads import LoadAccel, LoadNF, LoadUDL, LoadPUDL
from .rc import RC
from .ic import IC
from .pparam import PParam
from .element_offset import ElemOffset
from .couple import Couple
from .material import Material
from .ctype import CType
from .geometry import Geometry
from .aux_functions import int_or_default, float_or_default, type_or_default, str_or_blank
from .csys import CSys
from .node import Node
from .element import Element
from .exceptions import CommandError, NoDefault
from .rest import Rest


class CommandMixin:
    """Mixin to add a command line processor to the FS2000 Model"""
    def __init__(self, *args, **kwargs):
        self._CommandCOM = CommandCOM(self)
        # Model Definition Commands
        self._CommandREFORMAT = CommandREFORMAT(self)
        self._CommandNAME = CommandNAME(self)
        self._CommandTITLE = CommandTITLE(self)
        self._CommandUNIT = CommandUNIT(self)
        self._CommandUDEF = CommandUDEF(self)
        self._CommandDATE = CommandDATE(self)
        self._CommandTIME = CommandTIME(self)
        self._CommandBY = CommandBY(self)
        self._CommandREF = CommandREF(self)
        self._CommandDESC = CommandDESC(self)
        # Active Constants
        self._CommandACTCSYS = CommandACTCSYS(self)
        self._CommandACTN = CommandACTN(self)
        self._CommandACTN3 = CommandACTN3(self)
        self._CommandACTROT = CommandACTROT(self)
        self._CommandACTGEOM = CommandACTGEOM(self)
        self._CommandACTMAT = CommandACTMAT(self)
        self._CommandACTRELZ = CommandACTRELZ(self)
        self._CommandACTRELY = CommandACTRELY(self)
        self._CommandACTTYPE = CommandACTTYPE(self)
        self._CommandACTCON = CommandACTCON(self)
        # Co-ordinate Systems
        self._CommandCSYS = CommandCSYS(self)
        # Node related
        self._CommandN = CommandN(self)
        self._CommandNR = CommandNR(self)
        self._CommandNGEN = CommandNGEN(self)
        self._CommandNCOPY = CommandNCOPY(self)
        self._CommandNTRANS = CommandNTRANS(self)
        self._CommandNMAX = CommandNMAX(self)
        # Element related
        self._CommandE = CommandE(self)
        self._CommandEOF = CommandEOF(self)
        self._CommandPPARAM = CommandPPARAM(self)
        self._CommandPDATA = CommandPPARAM(self)
        self._CommandSC = CommandSC(self)
        # Property Data
        self._CommandGTAB1 = CommandGTAB1(self)
        self._CommandGTAB2 = CommandGTAB2(self)
        self._CommandGTAB3 = CommandGTAB3(self)
        self._CommandGTAB4 = CommandGTAB4(self)
        self._CommandGTAB5 = CommandGTAB5(self)
        self._CommandGTABP = CommandGTABP(self)
        self._CommandPIPE = CommandPIPE(self)
        # SECT
        self._CommandMTAB = CommandMTAB(self)
        self._CommandMTABP = CommandMTABP(self)
        self._CommandMTABT = CommandMTABT(self)
        # MTABP
        # MTABT
        self._CommandSTAB = CommandSTAB(self)
        self._CommandIC = CommandIC(self)
        self._CommandRC = CommandRC(self)
        # Groups
        # EGROUP
        # GRPSET
        # NGROUP
        # Active Constants
        # Restraints
        self._CommandREST = CommandREST(self)
        # Load Definition
        self._CommandLCASE = CommandLCASE(self)
        self._CommandLDESC = CommandLDESC(self)
        self._CommandLDATE = CommandLDATE(self)
        self._CommandLTIME = CommandLTIME(self)
        self._CommandACCEL = CommandACCEL(self)
        self._CommandNF = CommandNF(self)
        self._CommandUDL = CommandUDL(self)
        self._CommandPUDL = CommandPUDL(self)
        # Descriptive Model Data
        super().__init__(*args, **kwargs)

    def cmd(self, cmd_line):
        """Process a command line, or multiple lines"""
        if isinstance(cmd_line, str):
            cmd_lines = cmd_line.split('\n')
        elif isinstance(cmd_line, (list, tuple)):
            cmd_lines = cmd_line
        else:
            raise CommandError(f'Invalid type for command line: {type(cmd_line)}')
        logger = logging.getLogger('FS2000')
        # Process each line
        for cmd_line in cmd_lines:
            # cmd_args = [x.strip() for x in cmd_line.split(',')]
            cmd_args = [x for x in cmd_line.split(',')]
            # Use the first command argument to find the function to be called
            cmd_name = cmd_args.pop(0)
            # Check for non-command lines
            if 'FS2000 VERSION' in cmd_name:
                setattr(self, '_fsversion', cmd_name)
                continue
            if 'END OF DATA' in cmd_name:
                return
            # If it is a command, get the function to be called
            func_name = f'_Command{cmd_name}'
            if hasattr(self, func_name):
                func = getattr(self, func_name)
                # Call the function with the remaining arguments, from the second on
                func(*cmd_args)
            else:
                # logger.warning(f'Command "{cmd_name}" interpreter not defined.')
                pass


class Command:
    """Basic Class for all the commands"""
    signature = ''

    def __init__(self, model):
        self.model = model

    def fill_args(self, *args):
        args = list(args)
        n = len(self.signature.split(',')) - 1
        while len(args) < n:
            args.append('')
        return tuple(args)


class CommandCOM(Command):
    """Comment line"""
    signature = 'COM, comment.'

    def __call__(self, *args, **kwargs):
        # Do nothing
        pass


class CommandREFORMAT(Command):
    """
    Activates the reformat mode, which means that when the model is saved, all
    model data written sequentially and comment lines, if any, are omitted. The
    alternative mode is to preserve (Preserve Mode) the existing MDL file format
    including comment lines and to append any additional definition to the
    bottom of the file in a sequential format.
    """
    signature = 'REFORMAT'

    def __call__(self, *args, **kwargs):
        self.model._reformat = True


# Model Definition
class CommandNAME(Command):
    """Defines the model definition NAME"""
    signature = 'NAME, Model Name'

    def __call__(self, *args, **kwargs):
        self.model.NAME = args[0]


class CommandTITLE(Command):
    """Defines the model definition TITLE"""
    signature = 'TITLE, Model Description'

    def __call__(self, *args, **kwargs):
        self.model.TITLE = args[0]


class CommandUNIT(Command):
    """Defines the model definition UNIT"""
    signature = 'UNIT, Units Description'

    def __call__(self, *args, **kwargs):
        self.model.UNIT = args[0]


class CommandUDEF(Command):
    """Defines the Unit type: 0 - SI 1 - US Units"""
    signature = 'UDEF, Unit Type Definition 0 - SI 1 - US Units'

    def __call__(self, *args, **kwargs):
        self.model.UDEF = args[0]


class CommandDATE(Command):
    """Defines the model definition DATE"""
    signature = 'DATE, Current date of Model'

    def __call__(self, *args, **kwargs):
        self.model.DATE = args[0]


class CommandTIME(Command):
    """Defines the model definition TIME"""
    signature = 'TIME, Current time of Model'

    def __call__(self, *args, **kwargs):
        self.model.TIME = args[0]


class CommandBY(Command):
    """Defined the model definition BY"""
    signature = 'BY, Author'

    def __call__(self, *args, **kwargs):
        self.model.BY = args[0]


class CommandREF(Command):
    """Defines the model definition REF"""
    signature = 'REF, Any description'

    def __call__(self, *args, **kwargs):
        self.model.REF = args[0]


class CommandDESC(Command):
    """Defines the model definition DESC"""
    signature = 'DESC, Any description'

    def __call__(self, *args, **kwargs):
        self.model.DESC = args[0]


# Active Constants
class CommandACTCSYS(Command):
    """Sets active constant ACTCSYS"""
    signature = 'ACTCSYS, Value'
    
    def __call__(self, *args, **kwargs):
        self.model.ACTCSYS = args[0] 


class CommandACTN(Command):
    """Sets active constant ACTN"""
    signature = 'ACTN, Value'
    
    def __call__(self, *args, **kwargs):
        self.model.ACTN = args[0] 


class CommandACTN3(Command):
    """Sets active constant ACTN3"""
    signature = 'ACTN3, Value'
    
    def __call__(self, *args, **kwargs):
        self.model.ACTN3 = args[0] 


class CommandACTROT(Command):
    """Sets active constant ACTROT"""
    signature = 'ACTROT, Value'
    
    def __call__(self, *args, **kwargs):
        self.model.ACTROT = args[0] 


class CommandACTGEOM(Command):
    """Sets active constant ACTGEOM"""
    signature = 'ACTGEOM, Value'
    
    def __call__(self, *args, **kwargs):
        self.model.ACTGEOM = args[0] 


class CommandACTMAT(Command):
    """Sets active constant ACTMAT"""
    signature = 'ACTMAT, Value'
    
    def __call__(self, *args, **kwargs):
        self.model.ACTMAT = args[0] 


class CommandACTRELZ(Command):
    """Sets active constant ACTRELZ"""
    signature = 'ACTRELZ, Value'
    
    def __call__(self, *args, **kwargs):
        self.model.ACTRELZ = args[0] 


class CommandACTRELY(Command):
    """Sets active constant ACTRELY"""
    signature = 'ACTRELY, Value'
    
    def __call__(self, *args, **kwargs):
        self.model.ACTRELY = args[0] 


class CommandACTTYPE(Command):
    """Sets active constant ACTTYPE"""
    signature = 'ACTTYPE, Value'
    
    def __call__(self, *args, **kwargs):
        self.model.ACTTYPE = args[0] 


class CommandACTCON(Command):
    """Sets active constant ACTCON"""
    signature = 'ACTCON, Value'
    
    def __call__(self, *args, **kwargs):
        self.model.ACTCON = args[0] 


# Co-ordinate Systems
class CommandCSYS(Command):
    """
    Create a coordinate system from the command:
    'CSYS, No, Type, T1, T2, T3, RX, RY, RZ, P1, P2, N3'
        Creates a user defined coordinate system
        No       : Coordinate System Number. Should be 6 or higher.
        Type     : System Type (0-Cartesian, 1-Cylindrical, 2-Spherical,
                   3-Conical)
        T1,T2,T3 : Coordinates of origin in Global Cartesian or 3 nodes that
                   define the x-y plane if N3 = -1
        RX,RY,RZ : Rotational orientation (degrees), Not used if N3 = -1
        P1,P2    : Parameters
                   For conical systems P1 is the Radius at Z=0 and P2 is the
                   cone angle (from Z axis). These two parameters make the R
                   and Z coordinates interdependent i.e. define a conical
                   surface.
        N3       : If N3 = -1 then T1, T2, T3 are used to identify 3 nodes
                   that define the x-y plane
    """
    signature = 'CSYS, No, Type, T1, T2, T3, RX, RY, RZ, P1, P2, N3'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        no = int_or_default(args[0], None)
        cstype = int_or_default(args[1], CSys.paramdefaults[1])
        n3 = int_or_default(args[10], CSys.paramdefaults[10])
        ti = [type_or_default(args[i], int if n3 == -1 else float, CSys.paramdefaults[i]) for i in [2, 3, 4]]
        ri = [float_or_default(args[i], CSys.paramdefaults[i]) for i in [5, 6, 7]]
        pi = [float_or_default(args[i], CSys.paramdefaults[i]) for i in [8, 9]] if cstype == 3 else [
            CSys.paramdefaults[i] for i in [8, 9]]
        new_csys = CSys(self.model, T1=ti[0], T2=ti[1], T3=ti[2], RX=ri[0], RY=ri[1], RZ=ri[2],
                        P1=pi[0], P2=pi[1], N3=n3)
        new_csys.TYPE = cstype
        new_csys.set_pk(no)
        new_csys.commit()


# Node Related
class CommandN(Command):
    """
    N, Node, X, Y, Z, CSys
        Defines a node in the active co-ordinate system
        Node  : Node number to be assigned. A previous defined node will be
                re-defined (default: NMAX+1)
        X,Y,Z : Node location in local co-ordinate system. If a co-ordinate
                value is omitted, the node co-ordinate will be taken to be
                the same as that of the last node defined.
                Example N,6,1,0,3     (Node 6 at x = 1; y = 0; z = 3)
                        N,8,,9,6      (Node 8 at x = 1; y = 9; z = 6)
                        N,9,3         (Node 9 at x = 3; y = 9; z = 6)
        CSys  : Co-ordinate system number (default = ACTCSYS)
    """
    signature = 'N, Node, X, Y, Z, CSys'

    def __call__(self, *args):
        args = self.fill_args(*args)
        node_number = int_or_default(args[0], None)
        x = float_or_default(args[1], self.model.LASTNODE.X if self.model.LASTNODE is not None else 0.0)
        y = float_or_default(args[2], self.model.LASTNODE.Y if self.model.LASTNODE is not None else 0.0)
        z = float_or_default(args[3], self.model.LASTNODE.Z if self.model.LASTNODE is not None else 0.0)
        csys = int_or_default(args[4], self.model.ACTCSYS)
        new_node = Node(self.model, X=x, Y=y, Z=z, CSYS=csys)
        new_node.set_pk(node_number)
        new_node.commit()


class CommandNR(Command):
    """
    NR, Node, X, Y ,Z
        Defines a node in the active co-ordinate system where X, Y & Z are
        relative to the last node defined. Use ACTN to re-define reference
        node.
        Node  : Node number to be assigned. A previous defined node will be
                re-defined. (default = NMAX+1)
        X,Y,Z : Node location in ACTSYS co-ordinate system relative to the
                co-ordinates used to define the previous node. If a
                co-ordinate value is omitted the node co-ordinate will be
                taken to be the same as that of the last node defined.
                Example N,6,1,0,3     (Node 6 at x = 1; y = 0; z = 3)
                        NR,8,,9,6     (Node 8 at x = 1; y = 9; z = 9)
                        NR,9,3        (Node 9 at x = 4; y = 9; z = 6)
    """
    signature = 'NR, Node, X, Y ,Z'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        if self.model.LASTNODE is None:
            raise CommandError('No previous node defined to execute the NR command.')
        node_number = int_or_default(args[0], None)
        ref_node = self.model.get_node(self.model.ACTN)
        ref_node_in_active_csys = Node(self.model, X=ref_node.X, Y=ref_node.Y, Z=ref_node.Z, CSYS=ref_node.CSYS)
        # if ref_node.CSYS != self.model.ACTCSYS:
        #     ref_node_in_active_csys.convert_to_csys(self.model.ACTCSYS)
        x = ref_node_in_active_csys.X + float_or_default(args[1], 0.0)
        y = ref_node_in_active_csys.Y + float_or_default(args[2], 0.0)
        z = ref_node_in_active_csys.Z + float_or_default(args[3], 0.0)
        new_node = Node(self.model, X=x, Y=y, Z=z, CSYS=self.model.ACTCSYS)
        new_node.set_pk(node_number)
        new_node.commit()


class CommandNGEN(Command):
    """
    Create a node from the command:
    NGEN, N1, N2, NS, NF, NINC
        Generates one or more equally spaced nodes in a straight line
        between two previously defined nodes.
        N1   : First existing node
        N2   : Second existing node
        NS   : Node number of first node to be generated (default = NMAX+1)
        NF   : Node number of last node to be generated (default = NS i.e.
               single node generation)
        NINC : Node increment for generated nodes (default = 1)

    OBS: New nodes are created in global coordinate system, regardless of
         the original nodes coordinate system.
    """
    signature = 'NGEN, N1, N2, NS, NF, NINC'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        try:
            n1, n2 = int(args[0]), int(args[1])
        except (ValueError, TypeError):
            raise NoDefault(f'No default values for N1 and N2 in NGEN command: NGEN,{",".join(args)}')
        ns = int_or_default(args[2], self.model.NMAX + 1)
        nf = int_or_default(args[3], ns)
        ninc = int_or_default(args[4], 1)
        # Array of new node numbers
        new_node_numbers = np.arange(ns, nf + 1, ninc if ninc > 0 else 1, dtype=int)
        # End Points
        p1, p2 = self.model.get_node(n1).xyzg, self.model.get_node(n2).xyzg
        # Increment vector
        delta_p = (p2 - p1) / ((nf + ninc - ns) / ninc + 1)
        # Save the current active coordinate system
        actcsys = self.model.ACTCSYS
        # Create the new nodes in the global coordinate system
        for n in new_node_numbers:
            p1 += delta_p
            new_node = Node(self.model, X=p1[0], Y=p1[1], Z=p1[2], CSYS=0)
            new_node.set_pk(n)
            if actcsys != 0:
                new_node.convert_to_csys(actcsys)
            new_node.commit()
        # Get the active coordinate system back
        self.model._ACTCSYS = actcsys


class CommandNCOPY(Command):
    """
    NCOPY, N1, N2, NINC, NTIME, STNODE, DX, DY, DZ
        The NCOPY command copies a range of node to a location defined by
        coordinate increments. The original node label pattern is preserved
        in newly defined nodes.
        N1         : First existing node to be copied (default = last node
                     defined)
        N2         : Final existing node to be copied (default = N1)
        NINC       : Node increment of nodes to be copied (default = 1)
        NTIME      : Number of copies required (default = 1)
        STNODE     : Start node number for new nodes (default = NMAX+1)
        DX, DY, DZ : Co-ordinate increment between copies (Default = 0)

        OBS. Lack of documentation about copying nodes with diferent
        coordinate systems. Use with care.
    """
    signature = 'NCOPY, N1, N2, NINC, NTIME, STNODE, DX, DY, DZ'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        n1 = int_or_default(args[0], self.model.ACTN)
        n2 = int_or_default(args[1], n1)
        ninc = int_or_default(args[2], 1)
        ntime = int_or_default(args[3], 1)
        stnode = int_or_default(args[4], self.model.NMAX + 1)
        dx, dy, dz = float_or_default(args[5], 0.0), float_or_default(args[6], 0.0), float_or_default(args[7], 0.0)
        # Create the nodes
        delta_n = stnode - n1
        for n in range(n1, n2 + 1, ninc):
            existing_node = self.model.NodeList.get(n)
            if existing_node is not None:
                x, y, z, csys = existing_node.X, existing_node.Y, existing_node.Z, existing_node.CSYS
                # Create new nodes
                for i in range(1, ntime + 1):
                    new_node = Node(self.model, pk=n + i * delta_n, X=x + i * dx, Y=y + i * dy, Z=z + i * dz, CSYS=csys)
                    new_node.commit()


# To implement: NARC, N1,N2, NS, NF, NINC, RAD, N3, ROT

class CommandNTRANS(Command):
    """
    NTRANS, N1, N2, NINC, TX, TY, TX, RX, RY, RZ, Origin
        Translates a set of defined nodes relative to their co-ordinate
        system.
        N1         : First node in set (no default) or Group Number
        N2         : Final node in set (default = N1)
        NINC       : Node increment for set (default = 1)
        TX, TY, TZ : Linear translation
        RX, RY, RZ : Rotational translations
        Origin     : Define rotation origin by node association (default = 0
                     ie global origin)

        Using Group: If N1 is defined as a negative value (define N2 and
        NINC=0) then it will be interpreted as a Group No in the current
        Group SET. See GRPSET command.

        OBS. The NTRANS command perform first the rotations in the order
        XZY, then the linear translations.
    """
    signature = 'NTRANS, N1, N2, NINC, TX, TY, TX, RX, RY, RZ, Origin'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        if args[0] == '':
            raise NoDefault(f'No default value for N1 in NTRANS command.')
        n1 = int(args[0])
        if n1 < 0:
            logger = logging.getLogger('FS2000')
            logger.warning('NTRANS with node group not implemented yet. No node modified.')
            return
        n2 = int_or_default(args[1], n1)
        ninc = int_or_default(args[2], 1)
        tx, ty, tz = float_or_default(args[3], 0.0), float_or_default(args[4], 0.0), float_or_default(args[5], 0.0)
        rx, ry, rz = float_or_default(args[6], 0.0), float_or_default(args[7], 0.0), float_or_default(args[8], 0.0)
        origin = int_or_default(args[9], 0)
        nodes = [i for i in range(n1, n2+1, ninc) if i in self.model.NodeList]
        # Calculate the transformation matrix
        mat_t = np.array([[1, 0, 0, tx],
                          [0, 1, 0, ty],
                          [0, 0, 1, tz],
                          [0, 0, 0, 1]])
        p0 = self.model.NodeList.get(origin).xyz if origin in self.model.NodeList else np.array([0.0, 0.0, 0.0])
        mat_p0s = np.array([[1, 0, 0, -p0[0]],
                           [0, 1, 0, -p0[1]],
                           [0, 0, 1, -p0[2]],
                           [0, 0, 0, 1]])
        mat_p0e = np.array([[1, 0, 0, +p0[0]],
                           [0, 1, 0, +p0[1]],
                           [0, 0, 1, +p0[2]],
                           [0, 0, 0, 1]])
        mat_rx = np.array([[1, 0, 0, 0],
                          [0, np.cos(rx), -np.sin(rx), 0],
                          [0, np.sin(rx), np.cos(rx), 0],
                          [0, 0, 0, 1]])
        mat_ry = np.array([[np.cos(ry), 0, np.sin(ry), 0],
                          [0, 1, 0, 0],
                          [-np.sin(ry), 0, np.cos(ry), 0],
                          [0, 0, 0, 1]])
        mat_rz = np.array([[np.cos(rz), -np.sin(rz), 0, 0],
                          [np.sin(rz), np.cos(rz), 0, 0],
                          [0, 0, 1, 0],
                          [0, 0, 0, 1]])

        # mat_t x matP0e x matRy x matRz x matRx x matP0s
        mat = np.matmul(mat_t, np.matmul(mat_p0e, np.matmul(mat_ry, np.matmul(mat_rz, np.matmul(mat_rx, mat_p0s)))))
        # Pereform the translation
        for n in nodes:
            p = np.matmul(mat, np.array([*self.model.NodeList.get(n).xyz] + [1]))
            self.model.NodeList.get(n).xyz = p


# To implement: NGROUP

class CommandNMAX(Command):
    """
    NMAX, Label
        The NMAX command is used to define the maximum node label in the
        model.
    """
    signature = 'NMAX, Label'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        nmax = int_or_default(args[0], self.model.NMAX)
        self.model.NMAX = nmax


# Element Related
class CommandE(Command):
    """
    E, Elem, N1, N2, N3, ROT, GEOM, MAT, RELZ, RELY, TAPER, TYPE, CO,BendRad
        The E command defines individual elements.
        Elem    : The element number to be assigned. Previous will be
                  re-defined. (Default: EMAX+1)
        N1      : Start node of element (default = previous N2 node or last
                  node defined)
        N2      : End node of element (default = N1+1)
        N3      : Third node of element used to define local rotation
                  (default = ACTN3)
        ROT     : Local element rotation angle (default = ACTROT)
        GEOM    : Geometrical property table code (default = ACTGEOM),
                  GEOM = -1 identifies a rigid link
        MAT     : Material Property table code (default = ACTMAT)
        RELZ    : Hinge Definition - local z axis (0, 1, 2, or 3)
                  (default = ACTRELZ)
        RELY    : Hinge Definition - local y axis (0, 1, 2, or 3)
                  (default = ACTRELY)
        TAPER   : This is used to identify tapered beams by defining the
                  geom property code at the end node of an element. A +ve
                  values signifies a Type A Taper, a -ve value signifies a
                   Type B Taper.  (default = 0, no taper)
        TYPE    : Element Type (default = ACTTYPE)
        CO      : Additional CO constant (default = ACTCON)
        BendRad : Bend radius for Type 2 and Type 3 elements

    Valid element TYPEs are:
        0  : Linear beam (default)
        2  : Linear bend element (3rd node - tangent intersection)
        3  : Linear bend element (3rd node - centre of curvature)
        6  : General Non-linear beams
        7  : Non-linear beam on distributed ground couples
        8  : Non-linear beam on distributed ground non-linear springs
        15 : Spar (Catenary) element with large displacement capability
        16 : Linear beam with large displacement capability

    Valid moment releases for 'RELZ' and 'RELY' are:
        0 : Both ends fixed (default)
        1 : Node 1 (fore) end released Node 2 (aft) end fixed
        2 : Node 1 (fore) end fixed Node 2 (aft) end released
        3 : Both ends released
    """
    signature = 'E, Elem, N1, N2, N3, ROT, GEOM, MAT, RELZ, RELY, TAPER, TYPE, CO, BendRad'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        elem_number = int_or_default(args[0], None)
        n1 = int_or_default(args[1], self.model.ACTN1)
        n2 = int_or_default(args[2], n1+1)
        n3 = int_or_default(args[3], self.model.ACTN3)
        rot = float_or_default(args[4], self.model.ACTROT)
        geom, mat = int_or_default(args[5], self.model.ACTGEOM), int_or_default(args[6], self.model.ACTMAT)
        relz, rely = int_or_default(args[7], self.model.ACTRELZ), int_or_default(args[8], self.model.ACTRELY)
        taper = int_or_default(args[9], 0)
        eltype = int_or_default(args[10], self.model.ACTTYPE)
        co = int_or_default(args[11], self.model.ACTCON)
        bendrad = float_or_default(args[12], 0.0)
        new_element = Element(self.model, N1=n1, N2=n2, N3=n3, ROT=rot, GEOM=geom, MAT=mat, RELZ=relz, RELY=rely,
                              TYPE=eltype, TAPER=taper, CO=co, BENDRAD=bendrad)
        new_element.set_pk(elem_number)
        new_element.commit()


class CommandEOF(Command):
    """
    EOF, Elem, NOEF, EREF1, x1, y1, z1, EREF2, x2, y2, z2
        This command is used to define rigid end offsets for specific beam
        elements.  All defaults are zero unless specified.
        Elem     : The element number to be assigned. Previous will be
                   re-defined.
        NOEF     : Element End ID code: 1 - First Node End Only
                                        2 - Second Node End Only
                                        3 - Both Element Node Ends
                                        0 - No offset (delete if existing)
        EREF1    : Ref Element for Coord sytem for offsets x1, y1, z1 for
                   First Node (0 is global)
        x1,y1,z1 : Element end offsets for first node
        EREF2    : Ref Element for Coord sytem for offsets x2, y2, z2 for
                   Second Node (0 is global)
        x2,y2,z2 : Element end offsets for second node
    """
    signature = 'EOF, Elem, NOEF, EREF1, x1, y1, z1, EREF2, x2, y2, z2'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        elem = int_or_default(args[0], None)
        if elem is None:
            raise NoDefault('The element number must not be empty in EOF command.')
        noef = int_or_default(args[1], 0)
        if noef == 0:
            # Remove the offset if it exists
            self.model.ElemOffsetList.remove(elem)
            return
        eref1 = int_or_default(args[2], 0)
        x1, y1, z1 = float_or_default(args[3], 0.0), float_or_default(args[4], 0.0), float_or_default(args[5], 0.0)
        eref2 = int_or_default(args[6], 0)
        x2, y2, z2 = float_or_default(args[7], 0.0), float_or_default(args[8], 0.0), float_or_default(args[9], 0.0)
        new_offset = ElemOffset(self.model, ELEM=elem, NOEF=noef, EREF1=eref1, X1=x1, Y1=y1, Z1=z1, EREF2=eref2, X2=x2,
                                Y2=y2, Z2=z2)
        new_offset.set_pk(elem)
        new_offset.commit()


class CommandPPARAM(Command):
    """
    PPARAM, ELEM, TYPE, NODE, KFlex, SIFi, SIFo, C1, C2
        Defines the pipework coefficients for many pipework structure types:
        ELEM  : Pipe Element number
        TYPE  : As per list below:
                Bends:
                     1 : Welded elbow or pipe bend (both ends welded)
                     2 : Welded elbow or pipe bend (one end welded other
                         flanged)
                     3 : Welded elbow or pipe bend (both ends flanged)
                     4 : Mitre end bend
                     5 : Socket Welded Elbow
                Tee/Branch:
                     6 : Welding Tee per ANSI B16.9
                     7 : Reinforced fabricated tee with pad or saddle
                         (Header pipe)
                     8 : Unreinforced fabricated tee
                     9 : Extruded welding tee
                    10 : Welded-in contour insert
                    11 : Branch welded on fitting (integrally reinforced)
                Flange/Connectors:
                    12 : Buttwelded joint, reducer or weld neck flange
                    13 : Double-welded slip-on flange
                    14 : Fillet-welded joint or socket weld flange
                    15 : Lap joint flange (with ANSI B16.9 lap joint stub)
                    16 : Screwed pipe joint or screwed flange
                    17 : Corrogated straight pipe or corrugated or creased
                         bend
                    18 : User Defined
                Valves
                    19 : Valves Type Components
        NODE  : Which node of the element is the coefficients applicable to
                1 : First node only (applicable for tee and flanges)
                2 : Second node only (applicable for tee and flanges)
                3 : Both nodes (applicable for all, bends and valves will be
                    always 3)
        KFlex : Flexibility factor
        SIFi  : Stress Intensification Factor - inner face
        SIFo  : Stress Intensification Factor - outer face
        C1,C2 : Additional constant as follows:
                Bends:
                    C1 : Bend Radius
                    C2 : Mitre angle
                Tee/Branch:
                    C1 : Reinforcement thickness
                    C2 : Tee radius
                Flange/Connectors:
                    C1 : Flange table entry index
                    C2 : not used
                Valves
                    C1 : not used
                    C2 : not used

    Obs. Due to lack of documentation, these parameters were defined based
         on tests.
    """
    signature = 'PPARAM, Elem, Type, NodeEnd, KFlex, SIFI, SIFO, C1, C2'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        elem = int_or_default(args[0], None)
        if elem is None:
            raise NoDefault('The element number must not be empty in PPARAM or PDATA command')
        type_ = int_or_default(args[1], -1)
        if type_ == -1:
            raise NoDefault('Pipework coefficient type must not be empty in PPARAM or PDATA command')
        nodeend, kflex = int_or_default(args[2], 0), float_or_default(args[3], 0.0)
        sifi, sifo = float_or_default(args[4], 0.0), float_or_default(args[5], 0.0)
        c1, c2 = float_or_default(args[6], 0.0), float_or_default(args[7], 0.0)
        new_pparam = PParam(self.model, ELEM=elem, TYPE=type_, NODEEND=nodeend, KFLEX=kflex, SIFI=sifi, SIFO=sifo,
                            C1=c1, C2=c2)
        new_pparam.set_pk(elem)
        new_pparam.commit()


class CommandSC(Command):
    """
    SC, Elem, N1, N2, ROT, RefElem, SPCONST, SCCSys
        The SC command defines individual spring/couple elements.
        Elem    : The element number to be assigned. Previous will be
                  re-defined. (Default: SCMAX+1)
        N1      : Start node of element (default = previous N2 node or last
                  node defined)
        N2      : End node of element (default = N1+1)
        ROT     : Local element rotation angle (default = ACTROT)
        RefElem : Orientation - Ref. element for local co-ordinate system
                  (default=0)
        SPCONST : Spring Constant Property table code (default = ACTSPCONST)
        SCCSys  : Orientation - Reference Coordinate System (Default=0)
    """
    signature = 'SC, Elem, N1, N2, ROT, RefElem, SPCONST, SCCSys'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        elem = int_or_default(args[0], None)
        n1 = int_or_default(args[1], self.model.ACTN1)
        n2 = int_or_default(args[2], n1 + 1)
        rot = float_or_default(args[3], self.model.ACTROT)
        refelem = int_or_default(args[4], 0)
        spconst = int_or_default(args[5], self.model.ACTSPCONST)
        sccsys = int_or_default(args[6], 0)
        new_couple = Couple(self.model, N1=n1, N2=n2, ROT=rot, REFELEM=refelem, SPCONST=spconst, SCCSYS=sccsys)
        new_couple.set_pk(elem)
        new_couple.commit()


# Geometry Related
class CommandGTAB1(Command):
    """
    GTAB1, Code, Type, Name, Designation, GType, GOFY, GOFZ
        This optional command is used to define the geometric property type,
        its name and its designation.
        Code        : Code number used by element definition to reference
                      properties. (default = max code label + 1)
        Type        : Type of geometry data 3 = Pipe
                                          10 = Compression only (non-linear)
                                          11 = Tension only (non-linear)
                                          Any other number implies beam data
        Name        : 3 Character Name
        Designation : Up to 9 numeric characters
        GType       : Beam type for Virtual views (optional)
        GOFY        : Graphic offset for virtual views (optional)
        GOFZ        : Graphic offset for virtual view (optional)

        Valid GTypes are:
            P : Pipe (or tubular) elements
            I : I beams and H columns
            B : Box sections
            T : Tee sections
            A : Angle sections (no bending stiffness i.e. pure strut/tie)
            L : Angle sections
            R : Rectangular bar
    """
    signature = 'GTAB1, Code, Type, Name, Designation, GType, GOFY, GOFZ'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], None)
        type_ = int_or_default(args[1], 0)
        name = str_or_blank(args[2], length=3)
        designation = str_or_blank(args[3], length=9)
        gtype = str_or_blank(args[4], length=1)
        gofy, gofz = float_or_default(args[5], 0.0), float_or_default(args[6], 0.0)
        geom = None if code is None else self.model.GeometryList.get(code)
        if geom is None:
            geom = Geometry(self.model)
            geom.set_pk(code)
            geom.commit()
        geom.TYPE, geom.NAME, geom.DESIGNATION, geom.GTYPE = type_, name, designation, gtype
        geom.GOFY, geom.GOFZ = gofy, gofz


class CommandGTAB2(Command):
    """
    GTAB2, Code, C1 to C6
        All default values are zero. If C1 and C2 are specified then GTAB
        related data will be generated.
        Code        : Code number used by element definition to reference
                      properties. (default = max code label + 1)
        C1          : Pipe OD (for pipe data)
        C2          : Pipe wall thickens (for pipe data)
        (All property data will evaluated from pipe data if specified)
        C3          : Area
        C4          : Izz
        C5          : Iyy
        C6          : J
    """
    signature = 'GTAB2, Code, C1, C2, C3, C4, C5, C6'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], None)
        c1, c2 = float_or_default(args[1], 0.0), float_or_default(args[2], 0.0)
        c3, c4 = float_or_default(args[3], 0.0), float_or_default(args[4], 0.0)
        c5, c6 = float_or_default(args[5], 0.0), float_or_default(args[6], 0.0)
        geom = None if code is None else self.model.GeometryList.get(code)
        if geom is None:
            geom = Geometry(self.model)
            geom.set_pk(code)
            geom.commit()
        geom.C1, geom.C2 = c1, c2
        if not np.isclose(c1, 0.0):
            geom.set_to_pipe()
            geom.calculate()
        geom.C3 = c3  # if not np.isclose(c3, 0.0) else geom.C3
        geom.C4 = c4  # if not np.isclose(c4, 0.0) else geom.C4
        geom.C5 = c5  # if not np.isclose(c5, 0.0) else geom.C5
        geom.C6 = c6  # if not np.isclose(c6, 0.0) else geom.C6


class CommandGTAB3(Command):
    """
    GTAB3, Code, C7 to C11
        Optional data depending upon analysis requirements
        Code        : Code number used by element definition to reference
                      properties. (default = ACTGEOM)
        C7          : Ay - Shear area
        C8          : Az - Shear area
        C9          : Plastic Modulus zz axis
        C10         : Plastic Modulus yy axis
        C11         : Plastic Torsional Modulus
    """
    signature = 'GTAB3, Code, C7, C8, C9, C10, C11'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], self.model.ACTGEOM)
        c7, c8, c9 = float_or_default(args[1], 0.0), float_or_default(args[2], 0.0), float_or_default(args[3], 0.0)
        c10, c11 = float_or_default(args[4], 0.0), float_or_default(args[5], 0.0)
        geom = None if code is None else self.model.GeometryList.get(code)
        if geom is None:
            geom = Geometry(self.model)
            geom.set_pk(code)
            geom.commit()
        geom.C7 = c7  # if not np.isclose(c7, 0.0) else geom.C7
        geom.C8 = c8  # if not np.isclose(c8, 0.0) else geom.C8
        geom.C9 = c9  # if not np.isclose(c9, 0.0) else geom.C9
        geom.C10 = c10  # if not np.isclose(c10, 0.0) else geom.C10
        geom.C11 = c11  # if not np.isclose(c11, 0.0) else geom.C11


class CommandGTAB4(Command):
    """
    GTAB4, Code, C12 to C15
        Optional data depending upon analysis requirements.
        Code        : Code number used by element definition to reference
                      properties. (default = ACTGEOM)
        C12         : Stress point 1 y co-ordinate
        C13         : Stress point 1 z co-ordinate
        C14         : Stress point 2 y co-ordinate
        C15         : Stress point 2 z co-ordinate
    """
    signature = 'GTAB4, Code, C12, C13, C14, C15'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], self.model.ACTGEOM)
        c12, c13 = float_or_default(args[1], 0.0), float_or_default(args[2], 0.0)
        c14, c15 = float_or_default(args[3], 0.0), float_or_default(args[4], 0.0)
        geom = None if code is None else self.model.GeometryList.get(code)
        if geom is None:
            geom = Geometry(self.model)
            geom.set_pk(code)
            geom.commit()
        geom.C12 = c12  # if not np.isclose(c12, 0.0) else geom.C12
        geom.C13 = c13  # if not np.isclose(c13, 0.0) else geom.C13
        geom.C14 = c14  # if not np.isclose(c14, 0.0) else geom.C14
        geom.C15 = c15  # if not np.isclose(c15, 0.0) else geom.C15


class CommandGTAB5(Command):
    """
    GTAB5, Code, C16 to C20
        Optional data depending upon analysis requirements.
        Code        : Code number used by element definition to reference
                      properties. (default = ACTGEOM)
        C16         : Stress point 3 y co-ordinate
        C17         : Stress point 3 z co-ordinate
        C18         : Stress point 4 y co-ordinate
        C19         : Stress point 4 y co-ordinate
        C20         : Torsional modulus
    """
    signature = 'GTAB5, Code, C16, C17, C18, C19, C20'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], self.model.ACTGEOM)
        c16, c17 = float_or_default(args[1], 0.0), float_or_default(args[2], 0.0)
        c18, c19, c20 = float_or_default(args[3], 0.0), float_or_default(args[4], 0.0), float_or_default(args[5], 0.0)
        geom = None if code is None else self.model.GeometryList.get(code)
        if geom is None:
            geom = Geometry(self.model)
            geom.set_pk(code)
            geom.commit()
        geom.C16 = c16  # if not np.isclose(c16, 0.0) else geom.C16
        geom.C17 = c17  # if not np.isclose(c17, 0.0) else geom.C17
        geom.C18 = c18  # if not np.isclose(c18, 0.0) else geom.C18
        geom.C19 = c19  # if not np.isclose(c19, 0.0) else geom.C19
        geom.C20 = c20  # if not np.isclose(c20, 0.0) else geom.C20


class CommandGTABP(Command):
    """
    GTABP, Code, CorrAll, MillTol, ContDen, InsulT, InsulDen, LiningT,
                                                                   LiningDen
        The GTABP is used to defined data relating to pipe elements
        Code        : Code number used by element definition to reference
                      properties. (default = ACTGEOM)
        CorrAll     : Corrosion Tolerance
        MillTol     : Mill Tolerance %
        ContDen     : Contents Density
        InsulT      : Insulation Thickness
        InsulDen    : Insulation Density
        LiningT     : Internal Lining Thickness
        LiningDen   : Internal Lining Density
    """
    signature = 'GTABP, Code, CorrAll, MillTol, ContDen, InsulT, InsulDen, LiningT, LiningDen'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], self.model.ACTGEOM)
        corrall, milltol, = float_or_default(args[1], 0.0), float_or_default(args[2], 0.0),
        contden = float_or_default(args[3], 0.0)
        insult, insulden = float_or_default(args[4], 0.0), float_or_default(args[5], 0.0)
        liningt, liningden = float_or_default(args[6], 0.0), float_or_default(args[7], 0.0)
        geom = None if code is None else self.model.GeometryList.get(code)
        if geom is None:
            geom = Geometry(self.model)
            geom.set_pk(code)
            geom.commit()
        geom.CORRALL, geom.MILLTOL, geom.CONTDEN = corrall, milltol, contden
        geom.INSULT, geom.INSULDEN, geom.LININGT, geom.LININGDEN = insult, insulden, liningt, liningden


class CommandPIPE(Command):
    """
    This command combines the GTAB and ACTGEOM command for the definition of
    pipe elements. If Code is omitted the existing property codes will be
    scanned and if one exists with the same parameters it will be made
    active. If one does not exist, one will be created and then made active.
    If Code is specified than that code will be replaced.
        OD   : Pipe outside diameter
        WALL : Pipe wall thickness

    OBS. Existing extended pipe data (GTABP), if any, will remain.
    """
    signature = 'PIPE, OD, WALL, Code'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        try:
            od, wall = float(args[0]), float(args[1])
        except (ValueError, TypeError):
            raise NoDefault(f'No default values for OD and WALL in PIPE command: PIPE,{",".join(args)}')
        code = int_or_default(args[2], None)
        if code is None:
            geom_filter = self.model.GeometryList.filter(od=od, wt=wall)
            if len(geom_filter) > 0:
                # No code, but there is a match for OD and WALL. Turn it active
                self.model.ACTGEOM = geom_filter[0].pk
                return
        # Either the code is defined or not, create a new geometry and assing 'code' to the primary key
        geom = Geometry(self.model, C1=od, C2=wall)
        geom.set_to_pipe()
        geom.calculate()
        geom.set_pk(code)  # If code is None, a new number will be created
        geom.commit()


class CommandMTAB(Command):
    """
    MTAB, Code, E, G, POIS, DENS, ALPHA, YIELD, MatNam, ULT
        This command is used to define the material properties corresponding
        to the material table codes used in element definition. All default
        values are typical values for steel.
        Code   : Code number used by element definition to reference
                 properties. (Default = max code label + 1)
        E      : Modulus of Elasticity (Default = 205E9)
        G      : Modulus of Rigidity (Default based on POIS)
        POIS   : Poisson's ratio (Default = .3)
        DENS   : Density (Default = 7850)
        ALPHA  : Thermal Coefficient of Expansion (Default = 1.1E-5)
        YIELD  : Yield Strength (Default = 250E6)
        MatNam : Material Description (up to 8 characters)
        ULT    : Ultimate Strength (Default = 250E6)
    """
    signature = 'MTAB, Code, E, G, POIS, DENS, ALPHA, YIELD, MatNam, ULT'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], None)
        e, pois = float_or_default(args[1], 205.0E9), float_or_default(args[3], 0.3)
        g = float_or_default(args[2], e / (2 * (1 + pois)))
        dens = float_or_default(args[4], 7850.0)
        alpha = float_or_default(args[5], 1.1E-5)
        yield_ = float_or_default(args[6], 250.0E6)
        matnam = str_or_blank(args[7], length=8)
        ult = float_or_default(args[8], 250.0E6)
        new_mat = Material(self.model, E=e, POIS=pois, G=g, DENS=dens, ALPHA=alpha, YIELD=yield_, MATNAM=matnam,
                           ULT=ult)
        new_mat.set_pk(code)
        new_mat.commit()


class CommandMTABP(Command):
    """
    MTABP, Code, UltStr, ColdAllSt, QualFact, PressCoeff
        This command is used to define the additional material properties
        relating to pipework design
        Code       : Code number used by element definition to reference
                     properties. (Default = max code label +1)
        UltStr     : Ultimate Tensile Strength
        ColdAllSt  : Cold Allowable Stress
        QualFact   : Quality/Joint Factor
        PressCoeff : Pressure Coefficient
    """
    signature = 'MTABP, Code, UltStr, ColdAllSt, QualFact, PressCoeff'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], None)
        ultstr = float_or_default(args[1], 0.0)
        coldallst = float_or_default(args[2], 0.0)
        qualfact = float_or_default(args[3], 0.0)
        presscoeff = float_or_default(args[4], 0.0)
        mat = None if code is None else self.model.MaterialList.get(code)
        if mat is None:
            mat = Material(self.model)
            mat.set_pk(code)
            mat.commit()
        mat.ULTSTR, mat.COLDALLST = ultstr, coldallst
        mat.QUALFACT, mat.PRESSCOEFF = qualfact, presscoeff


class CommandMTABT(Command):
    """
    MTABT, Code, Pt, Temp, ALPHA , E, AllStress
        This command is used to define the additional material properties
        relating to temperature dependancy.
        Code      : Code number used by element definition to reference
                    properties. (Default = max code label +1)
        Pt        : Curve Point (Up to 15 point) Points most be successive
        Temp      : Temperature that the following values refer to
        ALPHA     : Thermal Coefficient of Expansion
        E         : Modulus of Elasticity
        AllStress : Allowable Stress
    """
    signature = 'MTABT, Code, Pt, Temp, ALPHA, E, AllStress'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], None)
        pt = int(args[1])
        temp, alpha = float_or_default(args[2]), float_or_default(args[3])
        e, allstress = float_or_default(args[4]), float_or_default(args[5])
        mat = None if code is None else self.model.MaterialList.get(code)
        if mat is None:
            mat = Material(self.model)
            mat.set_pk(code)
            mat.commit()
        if pt == mat.npts+1:
            mat.add_t_data(temp, alpha, e, allstress)
        else:
            mat.edit_t_data(pt, temp, alpha, e, allstress)


class CommandSTAB(Command):
    """
    STAB, Code, k1, k2, k3, k4, k5, k6, TYPE, CO
        The SPCONST command is used to define the couple element constants
        used by spring/couple elements.
        Code     : Code number used by element definition to reference
                   properties. (Default = max code label + 1)
        k1 to k6 : Spring stiffness for linear couple element TYPE 0
        TYPE     : Element Type (Default = 0, Standard linear couple)
        CO       : Additional CO constant
        Gap Elements are defined by the following.
            Type 10 Compression Gap
            Type 11 Tension Gap
            k1 : Gap stiffness - Normal direction
            k2 : Gap stiffness - Tangential direction
            k3 : Sliding Friction Coefficient - Coulomb friction
            k4 : Sliding Friction Coefficient Local Z
            k5 : Gap Size
            k6 : Initial Gap Status 0 Open
                                    1 Closed
        Other couple types have different meanings for constants k1 to k6.
        Refer to FS2000 manual for more information.
    """
    signature = 'STAB, Code, k1, k2, k3, k4, k5, k6, TYPE, CO'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], None)
        k = [float_or_default(args[i], 0.0) for i in range(1, 7)]
        type_, co = int_or_default(args[7], 0), int_or_default(args[8], 0)
        ctype = CType(self.model, K1=k[0], K2=k[1], K3=k[2], K4=k[3], K5=k[4], K6=k[5], TYPE=type_, CO=co)
        ctype.set_pk(code)
        ctype.commit()


class CommandIC(Command):
    """
    IC, Code, IC0, IC1, IC2, IC3, IC4, IC5, IC6
        The IC command is used to define additional integer constants used
        by some elements.
        Code       : Code number used by element definition to reference
                     properties. (Default = max code label + 1)
        IC0 to IC6 : Integer constants
    """
    signature = 'IC, Code, IC0, IC1, IC2, IC3, IC4, IC5, IC6'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], None)
        ic_ = [int_or_default(args[i], 0) for i in range(0, 7)]
        new_ic = IC(self.model, IC0=ic_[0], IC1=ic_[1], IC2=ic_[2], IC3=ic_[3], IC4=ic_[4], IC5=ic_[5], IC6=ic_[6])
        new_ic.set_pk(code)
        new_ic.commit()


class CommandRC(Command):
    """
    RC, Code, RCx1, RCy1, RCx2, RCy2, RCx3, RCy3, RCx4, RCy4, RCx5, RCy5,
    RCx6, RCy6, RCx7, RCy7
        The RC command is used to define additional real constants used by
        some elements.
        Code       : Code number used by element definition to reference
                     properties. (Default = max code label + 1)
        RCx1, RCy1 : Real constants.
           to
        RCx7, RCy7
    """
    signature = 'RC, Code, RCx1, RCy1, RCx2, RCy2, RCx3, RCy3, RCx4, RCy4, RCx5, RCy5, RCx6, RCy6, RCx7, RCy7'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        code = int_or_default(args[0], None)
        rcx = [float_or_default(args[i], 0.0) for i in range(1, 15, 2)]
        rcy = [float_or_default(args[i], 0.0) for i in range(2, 15, 2)]
        new_rc = RC(self.model, RCX1=rcx[0], RCY1=rcy[0], RCX2=rcx[1], RCY2=rcy[1], RCX3=rcx[2], RCY3=rcy[2],
                    RCX4=rcx[3], RCY4=rcy[3], RCX5=rcx[4], RCY5=rcy[4], RCX6=rcx[5], RCY6=rcy[5], RCX7=rcx[6],
                    RCY7=rcy[6])
        new_rc.set_pk(code)
        new_rc.commit()


class CommandREST(Command):
    """
    REST, NODE, X, Y, Z, RX, RY, RZ
        Defines the restraint of a node in the global co-ordinate system
        NODE       : Node number to be restrained. A previous defined node
                     will be re-defined (default = 0)
        X, Y, Z    : Translation restraint direction in global co-ordinate
                     system
        RX, RY, RZ : Rotational restraint direction in global co-ordinate
                     system
                         0 signifies free
                         1 signifies fixed
        Obs. If NODE is not specified or is zero, no restraint will be
        created.
    """
    signature = 'REST, NODE, X, Y, Z, RX, RY, RZ'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        node = int_or_default(args[0], 0)
        if node == 0:
            return
        x, y, z = int_or_default(args[1], 0), int_or_default(args[2], 0), int_or_default(args[3], 0)
        rx, ry, rz = int_or_default(args[4], 0), int_or_default(args[5], 0), int_or_default(args[6], 0)
        new_rest = Rest(self.model, X=x, Y=y, Z=z, RX=rx, RY=ry, RZ=rz)
        new_rest.set_pk(node)
        new_rest.commit()


# Load related commands
class CommandLCASE(Command):
    """
    LCASE, LCASENUM
        Opens a load case.
    """
    signature = 'LCASE, LCASENUM'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        lcasenum = int_or_default(args[0], None)
        if lcasenum is None:
            raise NoDefault('Load Case number is required')
        new_lcase = LoadCase(self.model)
        new_lcase.set_pk(lcasenum)
        new_lcase.commit()
        self.model.ACTLCASE = lcasenum
        # logger = logging.getLogger('FS2000')
        # logger.debug(f'Reading load case {lcasenum}')


class CommandLDESC(Command):
    """
    LDESC, Load Case Description
    """
    signature = 'LDESC, Load Case Description'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        lcase = self.model.LoadCaseList.get(self.model.ACTLCASE)
        lcase.LDESC = ','.join([str_or_blank(arg) for arg in args])


class CommandLDATE(Command):
    """
    LDATE,Current Date of Load Case
    """
    signature = 'LDATE,Current Date of Load Case'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        lcase = self.model.LoadCaseList.get(self.model.ACTLCASE)
        lcase.LDATE = str_or_blank(args[0])


class CommandLTIME(Command):
    """
    LTIME, Current time of Load Case
    """
    signature = 'LTIME, Current time of Load Case'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        lcase = self.model.LoadCaseList.get(self.model.ACTLCASE)
        lcase.LTIME = str_or_blank(args[0])


class CommandACCEL(Command):
    """
    ACCEL, Gx, Gy, Gz
        The ACCEL command is used to define the acceleration constants in
        the global co-ordinate system
    """
    signature = 'ACCEL, Gx, Gy, Gz'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        lcase = self.model.LoadCaseList.get(self.model.ACTLCASE)
        gx, gy, gz = float_or_default(args[0], 0.0), float_or_default(args[1], 0.0), float_or_default(args[2], 0.0)
        new_load = LoadAccel(self.model, lcase, GX=gx, GY=gy, GZ=gz)
        new_load.commit()


class CommandNF(Command):
    """
    NF, Node, Fx , Fy, Fz, Mx, My, Mz, NMass
        The NF command is used to define nodal (concentrated) loads. All
        defaults are zero. Definition is in the global co-ordinate system.
        Node Node label
        Fx, -- : Concentrated force
        Mx, -- : Concentrated moment (couple)
        NMas   : Concentrated nodal mass
    """
    signature = 'NF, Node, Fx , Fy, Fz, Mx, My, Mz, NMass'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        lcase = self.model.LoadCaseList.get(self.model.ACTLCASE)
        node = int_or_default(args[0], None)
        if node is None:
            raise NoDefault('Node undefined in NF command')
        fx, fy, fz = float_or_default(args[1], 0.0), float_or_default(args[2], 0.0), float_or_default(args[3], 0.0)
        mx, my, mz = float_or_default(args[4], 0.0), float_or_default(args[5], 0.0), float_or_default(args[6], 0.0)
        new_load = LoadNF(self.model, lcase, NODE=node, FX=fx, FY=fy, FZ=fz, MX=mx, MY=my, MZ=mz)
        new_load.commit()


class CommandUDL(Command):
    """
    UDL, Elem, UDX, UDY, UDZ, PROJ
        The UDL command is used to define uniformly distributed element
        loads.
        Elem : Element label
        UDX  : Load intensity in global X
        UDY  : Load intensity in global Y
        UDZ  : Load intensity in global Z
        PROJ : Projection option
               1 = Global
               3 = Projected Global
    """
    signature = 'UDL, Elem, UDX, UDY, UDZ, PROJ'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        lcase = self.model.LoadCaseList.get(self.model.ACTLCASE)
        elem = int_or_default(args[0], None)
        if elem is None:
            raise NoDefault('Element undefined in UDL command')
        udx, udy, udz = float_or_default(args[1], 0.0), float_or_default(args[2], 0.0), float_or_default(args[3], 0.0)
        coord = int_or_default(args[4], 1)
        new_load = LoadUDL(self.model, lcase, ELEM=elem, UDX=udx, UDY=udy, UDZ=udz, COORD=coord)
        new_load.commit()


class CommandPUDL(Command):
    """
    PUDL, Code, Dir, LOAD, Coord
        The PUDL command is used to define global distributed loading on
        beam/pipe elements by geometric property code reference. All default
        are zero.
        Code  : Element Geometric Property Code Number
        Dir   : Load direction (global)
                1 - X Direction
                2 - Y Direction
                3 - Z Direction
        LOAD  : Load magnitude
        COORD : Co-ordinate system (default = global) 1 Global 3 Projected
                Global
    """
    signature = 'PUDL, Code, Dir, LOAD, Coord'

    def __call__(self, *args, **kwargs):
        args = self.fill_args(*args)
        lcase = self.model.LoadCaseList.get(self.model.ACTLCASE)
        code = int_or_default(args[0], None)
        if code is None:
            raise NoDefault('Geometry Code undefined in PUDL command')
        dir_, load, coord = int_or_default(args[1], 1), float_or_default(args[2], 0.0), int_or_default(args[3], 1)
        new_load = LoadPUDL(self.model, lcase, CODE=code, DIR=dir_, LOAD=load, COORD=coord)
        new_load.commit()
