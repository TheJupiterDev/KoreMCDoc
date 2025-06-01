from typing import Dict, List, Optional, Union, Tuple
from dataclasses import dataclass, field

# ============================================================================
# Core Type System
# ============================================================================

@dataclass
class McdocType:
    """Base class for all Mcdoc types"""
    pass


@dataclass
class AnyType(McdocType):
    """The 'any' type - accepts any value"""
    pass


@dataclass
class BooleanType(McdocType):
    """Boolean type"""
    pass


@dataclass
class StringType(McdocType):
    """String type with optional length range"""
    length_range: Optional[Tuple[Optional[int], Optional[int]]] = None


@dataclass
class NumericType(McdocType):
    """Numeric types (byte, short, int, long, float, double)"""
    type_name: str  # byte, short, int, long, float, double
    range: Optional[Tuple[Optional[float], Optional[float]]] = None


@dataclass
class LiteralType(McdocType):
    """Literal value types"""
    value: Union[str, int, float, bool]
    type_hint: Optional[str] = None


@dataclass
class ListType(McdocType):
    """List/array type"""
    element_type: McdocType
    size_range: Optional[Tuple[Optional[int], Optional[int]]] = None


@dataclass
class TupleType(McdocType):
    """Tuple type with specific ordered elements"""
    elements: List[McdocType]


@dataclass
class StructField:
    """A field in a struct"""
    name: str
    type: McdocType
    optional: bool = False
    doc_comment: Optional[str] = None


@dataclass
class StructType(McdocType):
    """Struct type definition"""
    fields: List[StructField]
    spreads: List[str] = field(default_factory=list)  # Other structs to spread


@dataclass
class UnionType(McdocType):
    """Union type (A | B | C)"""
    types: List[McdocType]


@dataclass
class ReferenceType(McdocType):
    """Reference to another type"""
    path: str
    type_params: List[McdocType] = field(default_factory=list)


@dataclass
class EnumType(McdocType):
    """Enum type definition"""
    name: str
    values: List[str]
    doc_comments: Dict[str, str] = field(default_factory=dict)