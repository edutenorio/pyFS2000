from .load_cases import LoadCase
from .rest import Rest
from .ic import IC
from .rc import RC
from .pparam import PParam
from .element_offset import ElemOffset
from .couple import Couple
from .material import Material
from .ctype import CType
from .geometry import Geometry
from .csys import CSys
from .element import Element
from .node import Node
from .entity_list import EntityList


class ListsMixin:
    def __init__(self, *args, **kwargs):
        self._csys_list = EntityList(CSys)
        self._node_list = EntityList(Node)
        self._element_list = EntityList(Element)
        self._elemoffset_list = EntityList(ElemOffset)
        self._pparam_list = EntityList(PParam)
        self._couple_list = EntityList(Couple)
        self._geometry_list = EntityList(Geometry)
        self._ctype_list = EntityList(CType)
        self._material_list = EntityList(Material)
        self._ic_list = EntityList(IC)
        self._rc_list = EntityList(RC)
        self._rest_list = EntityList(Rest)
        self._loadcase_list = EntityList(LoadCase)
        super().__init__(*args, **kwargs)

    @property
    def CSysList(self):
        """List of coordinate systems"""
        return self._csys_list

    @property
    def NodeList(self):
        """List of nodes"""
        return self._node_list

    @property
    def ElementList(self):
        """List of element"""
        return self._element_list

    @property
    def ElemOffsetList(self):
        """List of element offsets"""
        return self._elemoffset_list

    @property
    def PParamList(self):
        """List of pipework coefficients"""
        return self._pparam_list

    @property
    def CoupleList(self):
        """List of couple elements"""
        return self._couple_list

    @property
    def GeometryList(self):
        """List of geometry properties"""
        return self._geometry_list

    @property
    def CTypeList(self):
        """List of couple types"""
        return self._ctype_list

    @property
    def MaterialList(self):
        """List of material properties"""
        return self._material_list

    @property
    def ICList(self):
        """List of Integer Constants"""
        return self._ic_list

    @property
    def RCList(self):
        """List of Real Constants"""
        return self._rc_list

    @property
    def RestList(self):
        """List of Node Restraints"""
        return self._rest_list

    @property
    def LoadCaseList(self):
        """List of load cases"""
        return self._loadcase_list
