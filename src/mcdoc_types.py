from typing import Dict, List, Optional, Union, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

# ============================================================================
# Core Type System with Advanced Features
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
    conditions: List['Condition'] = field(default_factory=list)
    since: Optional[str] = None
    until: Optional[str] = None


@dataclass
class StructType(McdocType):
    """Struct type definition"""
    fields: List[StructField]
    spreads: List[str] = field(default_factory=list)  # Other structs to spread
    conditions: List['Condition'] = field(default_factory=list)
    since: Optional[str] = None
    until: Optional[str] = None


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


@dataclass
class AttributeType(McdocType):
    """Attribute-decorated type"""
    base_type: McdocType
    attributes: List[str] = field(default_factory=list)


# ============================================================================
# Advanced Features
# ============================================================================

class ConditionType(Enum):
    """Types of conditions"""
    IF = "if"
    SWITCH = "switch"
    CASE = "case"


@dataclass
class Condition:
    """Conditional logic for fields/types"""
    type: ConditionType
    expression: str
    target_field: Optional[str] = None
    expected_value: Optional[Any] = None


@dataclass
class ConditionalType(McdocType):
    """Type that depends on conditions"""
    base_type: McdocType
    conditions: List[Condition]


@dataclass
class SwitchType(McdocType):
    """Switch-based type selection"""
    discriminator: str  # Field name to switch on
    cases: Dict[str, McdocType]  # value -> type mapping
    default_type: Optional[McdocType] = None


@dataclass
class IndexType(McdocType):
    """Index-based type (for accessing array/object elements)"""
    base_type: McdocType
    index_type: McdocType


@dataclass
class MapType(McdocType):
    """Map/dictionary type"""
    key_type: McdocType
    value_type: McdocType


@dataclass
class VersionConstraint:
    """Version constraint for since/until"""
    version: str
    inclusive: bool = True


@dataclass
class VersionedType(McdocType):
    """Type with version constraints"""
    base_type: McdocType
    since: Optional[VersionConstraint] = None
    until: Optional[VersionConstraint] = None


@dataclass
class NestedStructType(McdocType):
    """Nested structure with inheritance and composition"""
    base_struct: Optional[StructType] = None
    extends: List[str] = field(default_factory=list)
    implements: List[str] = field(default_factory=list)
    fields: List[StructField] = field(default_factory=list)
    nested_structs: Dict[str, 'NestedStructType'] = field(default_factory=dict)


@dataclass
class GenericType(McdocType):
    """Generic type with type parameters"""
    name: str
    type_params: List[str] = field(default_factory=list)
    bounds: Dict[str, McdocType] = field(default_factory=dict)


@dataclass
class ConstraintType(McdocType):
    """Type with additional constraints"""
    base_type: McdocType
    constraints: List[str] = field(default_factory=list)  # Custom validation rules


@dataclass
class ModuleType(McdocType):
    """Module/namespace type"""
    name: str
    types: Dict[str, McdocType] = field(default_factory=dict)
    exports: List[str] = field(default_factory=list)