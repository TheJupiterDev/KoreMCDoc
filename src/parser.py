import re
from typing import List, Optional, Union, Tuple, Dict, Any
from mcdoc_types import *

# ============================================================================
# Enhanced Parser Components
# ============================================================================

class McdocLexer:
    """Tokenizes Mcdoc source code with enhanced features"""
    
    TOKEN_PATTERNS = [
        ('COMMENT', r'//(?!/).*'),
        ('DOC_COMMENT', r'///.*'),
        ('NUMBER', r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?[bslfdBSLFD]?'),
        ('STRING', r'"(?:[^"\\]|\\.)*"'),
        ('RESOURCE_LOC', r'[a-z_][a-z0-9_]*:[a-z_][a-z0-9_/]*'),
        ('KEYWORD', r'\b(struct|enum|if|switch|case|default|since|until|extends|implements|module|export|import|type|interface)\b'),
        ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('VERSION', r'\d+\.\d+(?:\.\d+)?(?:-[a-zA-Z0-9_.-]+)?'),
        ('PATH_SEP', r'::'),
        ('SPREAD', r'\.\.\.'),
        ('RANGE_EX', r'<\.\.<?'),
        ('RANGE', r'\.\.'),
        ('ARROW', r'=>'),
        ('OPTIONAL', r'\?'),
        ('LBRACE', r'\{'),
        ('RBRACE', r'\}'),
        ('LBRACKET', r'\['),
        ('RBRACKET', r'\]'),
        ('LPAREN', r'\('),
        ('RPAREN', r'\)'),
        ('LANGLE', r'<'),
        ('RANGLE', r'>'),
        ('COMMA', r','),
        ('COLON', r':'),
        ('SEMICOLON', r';'),
        ('PIPE', r'\|'),
        ('EQUALS', r'='),
        ('AT', r'@'),
        ('HASH', r'#'),
        ('AMPERSAND', r'&'),
        ('EXCLAMATION', r'!'),
        ('WHITESPACE', r'\s+'),
    ]
    
    def __init__(self, text: str):
        self.text = text
        self.pos = 0
        self.tokens = []
        self._tokenize()
    
    def _tokenize(self):
        while self.pos < len(self.text):
            matched = False
            for token_type, pattern in self.TOKEN_PATTERNS:
                regex = re.compile(pattern)
                match = regex.match(self.text, self.pos)
                if match:
                    value = match.group(0)
                    if token_type not in ['WHITESPACE', 'COMMENT']:
                        self.tokens.append((token_type, value, self.pos))
                    self.pos = match.end()
                    matched = True
                    break
            
            if not matched:
                self.pos += 1  # Skip unknown characters


class McdocParser:
    """Enhanced parser with support for advanced features"""
    
    def __init__(self, tokens: List[Tuple[str, str, int]]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else None
        self.type_registry: Dict[str, McdocType] = {}
        self.current_version = "1.0.0"
    
    def advance(self):
        self.pos += 1
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
        else:
            self.current_token = None
    
    def peek(self, offset: int = 1) -> Optional[Tuple[str, str, int]]:
        peek_pos = self.pos + offset
        return self.tokens[peek_pos] if peek_pos < len(self.tokens) else None
    
    def expect(self, token_type: str) -> str:
        if not self.current_token or self.current_token[0] != token_type:
            raise SyntaxError(f"Expected {token_type}, got {self.current_token}")
        value = self.current_token[1]
        self.advance()
        return value
    
    def match(self, token_type: str, value: str = None) -> bool:
        if not self.current_token or self.current_token[0] != token_type:
            return False
        return value is None or self.current_token[1] == value
    
    def parse_type(self) -> McdocType:
        """Parse a type expression with enhanced features"""
        return self._parse_union_type()
    
    def _parse_union_type(self) -> McdocType:
        """Parse union type (A | B | C)"""
        types = [self._parse_intersection_type()]
        
        while self.match('PIPE'):
            self.advance()  # consume |
            types.append(self._parse_intersection_type())
        
        return UnionType(types) if len(types) > 1 else types[0]
    
    def _parse_intersection_type(self) -> McdocType:
        """Parse intersection type (A & B & C) - for future use"""
        return self._parse_conditional_type()
    
    def _parse_conditional_type(self) -> McdocType:
        """Parse conditional types"""
        base_type = self._parse_primary_type()
        
        # Handle if conditions
        if self.match('KEYWORD', 'if'):
            self.advance()  # consume 'if'
            condition_expr = self._parse_condition_expression()
            conditions = [Condition(ConditionType.IF, condition_expr)]
            return ConditionalType(base_type, conditions)
        
        return base_type
    
    def _parse_condition_expression(self) -> str:
        """Parse condition expression - simplified for now"""
        expr = ""
        depth = 0
        while self.current_token and (depth > 0 or self.current_token[0] not in ['COMMA', 'RBRACE', 'RBRACKET']):
            if self.current_token[0] in ['LPAREN', 'LBRACE', 'LBRACKET']:
                depth += 1
            elif self.current_token[0] in ['RPAREN', 'RBRACE', 'RBRACKET']:
                depth -= 1
                if depth < 0:
                    break
            expr += self.current_token[1] + " "
            self.advance()
        return expr.strip()
    
    def _parse_primary_type(self) -> McdocType:
        """Parse primary type expressions with enhanced features"""
        # Handle attributes first
        attributes = []
        while self.match('HASH'):
            self.advance()  # consume #
            if self.match('LBRACKET'):
                self.advance()  # consume [
                attr_content = ""
                while self.current_token and not self.match('RBRACKET'):
                    attr_content += self.current_token[1]
                    self.advance()
                self.expect('RBRACKET')
                attributes.append(attr_content)
        
        base_type = None
        
        # Handle keywords
        if self.match('KEYWORD', 'switch'):
            base_type = self._parse_switch_type()
        elif self.match('IDENTIFIER'):
            base_type = self._parse_identifier_type()
        elif self.match('STRING'):
            base_type = self._parse_literal_string()
        elif self.match('NUMBER'):
            base_type = self._parse_number_type()
        elif self.match('LBRACKET'):
            base_type = self._parse_list_or_tuple()
        elif self.match('LPAREN'):
            base_type = self._parse_grouped_type()
        elif self.match('LBRACE'):
            base_type = self._parse_map_or_object_type()
        else:
            raise SyntaxError(f"Unexpected token: {self.current_token}")
        
        # Handle version constraints
        base_type = self._parse_version_constraints(base_type)
        
        # Handle range constraints (@1..10)
        if self.match('AT'):
            self.advance()  # consume @
            constraints = []
            while self.current_token and self.current_token[0] not in ['COMMA', 'RBRACE', 'RBRACKET', 'RPAREN']:
                constraints.append(self.current_token[1])
                self.advance()
            if constraints and isinstance(base_type, NumericType):
                # Parse range constraint
                constraint_str = "".join(constraints)
                if ".." in constraint_str:
                    parts = constraint_str.split("..")
                    try:
                        min_val = float(parts[0]) if parts[0] else None
                        max_val = float(parts[1]) if len(parts) > 1 and parts[1] else None
                        base_type.range = (min_val, max_val)
                    except ValueError:
                        pass
        
        if attributes and base_type:
            return AttributeType(base_type, attributes)
        elif base_type:
            return base_type
        else:
            raise SyntaxError(f"Failed to parse type at: {self.current_token}")
    
    def _parse_switch_type(self) -> SwitchType:
        """Parse switch type"""
        self.advance()  # consume 'switch'
        self.expect('LPAREN')
        discriminator = self.expect('IDENTIFIER')
        self.expect('RPAREN')
        self.expect('LBRACE')
        
        cases = {}
        default_type = None
        
        while not self.match('RBRACE') and self.current_token:
            if self.match('KEYWORD', 'case'):
                self.advance()  # consume 'case'
                case_value = self._parse_literal_value()
                self.expect('COLON')
                case_type = self.parse_type()
                cases[str(case_value)] = case_type
            elif self.match('KEYWORD', 'default'):
                self.advance()  # consume 'default'
                self.expect('COLON')
                default_type = self.parse_type()
            else:
                self.advance()  # Skip unknown tokens
            
            if self.match('COMMA'):
                self.advance()
        
        self.expect('RBRACE')
        return SwitchType(discriminator, cases, default_type)
    
    def _parse_literal_value(self) -> Any:
        """Parse a literal value"""
        if self.match('STRING'):
            value = self.current_token[1][1:-1]  # Remove quotes
            self.advance()
            return value
        elif self.match('NUMBER'):
            value_str = self.current_token[1]
            self.advance()
            try:
                return int(value_str) if '.' not in value_str else float(value_str)
            except ValueError:
                return value_str
        elif self.match('IDENTIFIER'):
            if self.current_token[1] in ['true', 'false']:
                value = self.current_token[1] == 'true'
                self.advance()
                return value
            else:
                value = self.current_token[1]
                self.advance()
                return value
        else:
            raise SyntaxError(f"Expected literal value, got {self.current_token}")
    
    def _parse_version_constraints(self, base_type: McdocType) -> McdocType:
        """Parse since/until version constraints"""
        since = None
        until = None
        
        if self.match('AT') and self.peek() and self.peek()[1] == 'since':
            self.advance()  # consume @
            self.advance()  # consume 'since'
            since_version = self.expect('VERSION')
            since = VersionConstraint(since_version)
        
        if self.match('AT') and self.peek() and self.peek()[1] == 'until':
            self.advance()  # consume @
            self.advance()  # consume 'until'
            until_version = self.expect('VERSION')
            until = VersionConstraint(until_version)
        
        if since or until:
            return VersionedType(base_type, since, until)
        
        return base_type
    
    def _parse_map_or_object_type(self) -> McdocType:
        """Parse map type {K: V} or inline object type"""
        self.expect('LBRACE')
        
        if self.match('RBRACE'):
            self.advance()
            return MapType(StringType(), AnyType())  # Empty map
        
        # Try to parse as map first
        if self._looks_like_map():
            key_type = self.parse_type()
            self.expect('COLON')
            value_type = self.parse_type()
            self.expect('RBRACE')
            return MapType(key_type, value_type)
        else:
            # Parse as inline struct
            return self._parse_inline_struct()
    
    def _looks_like_map(self) -> bool:
        """Check if the current position looks like a map type"""
        # Simple heuristic: if we see Type: Type pattern, it's likely a map
        saved_pos = self.pos
        try:
            # Try to parse a type
            self.parse_type()
            if self.match('COLON'):
                return True
        except:
            pass
        finally:
            # Restore position
            self.pos = saved_pos
            self.current_token = self.tokens[self.pos] if self.pos < len(self.tokens) else None
        return False
    
    def _parse_inline_struct(self) -> StructType:
        """Parse inline struct definition"""
        fields = []
        
        while not self.match('RBRACE') and self.current_token:
            # Parse field
            field_name = self.expect('IDENTIFIER')
            
            optional = False
            if self.match('OPTIONAL'):
                self.advance()
                optional = True
            
            self.expect('COLON')
            field_type = self.parse_type()
            
            fields.append(StructField(field_name, field_type, optional))
            
            if self.match('COMMA'):
                self.advance()
        
        self.expect('RBRACE')
        return StructType(fields)
    
    def _parse_identifier_type(self) -> McdocType:
        """Parse identifier-based types (references, etc.)"""
        name = self.expect('IDENTIFIER')
        
        # Check if this is a built-in type first
        if name in ['any', 'boolean', 'string', 'byte', 'short', 'int', 'long', 'float', 'double']:
            if name == 'any':
                return AnyType()
            elif name == 'boolean':
                return BooleanType()
            elif name == 'string':
                return StringType()
            else:
                return NumericType(name)
        
        # Handle type parameters
        type_params = []
        if self.match('LANGLE'):
            self.advance()  # consume <
            type_params.append(self.parse_type())
            
            while self.match('COMMA'):
                self.advance()  # consume ,
                type_params.append(self.parse_type())
            
            self.expect('RANGLE')
        
        return ReferenceType(name, type_params)
    
    def _parse_literal_string(self) -> LiteralType:
        """Parse string literal"""
        value = self.expect('STRING')
        unquoted = value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
        return LiteralType(unquoted)
    
    def _parse_number_type(self) -> Union[LiteralType, NumericType]:
        """Parse numeric types and literals"""
        number_str = self.expect('NUMBER')
        
        suffix_map = {
            'b': 'byte', 's': 'short', 'l': 'long',
            'f': 'float', 'd': 'double'
        }
        
        suffix = None
        if number_str[-1].lower() in suffix_map:
            suffix = suffix_map[number_str[-1].lower()]
            number_str = number_str[:-1]
        
        try:
            if '.' in number_str or 'e' in number_str.lower():
                value = float(number_str)
                return LiteralType(value, suffix or 'double')
            else:
                value = int(number_str)
                return LiteralType(value, suffix or 'int')
        except ValueError:
            raise SyntaxError(f"Invalid number: {number_str}")
    
    def _parse_list_or_tuple(self) -> Union[ListType, TupleType]:
        """Parse list [T] or tuple [T, U, V]"""
        self.expect('LBRACKET')
        
        if self.match('RBRACKET'):
            self.advance()
            raise SyntaxError("Empty list/tuple not allowed")
        
        elements = [self.parse_type()]
        
        while self.match('COMMA'):
            self.advance()  # consume ,
            if self.match('RBRACKET'):  # trailing comma
                break
            elements.append(self.parse_type())
        
        self.expect('RBRACKET')
        
        if len(elements) == 1:
            return ListType(elements[0])
        else:
            return TupleType(elements)
    
    def _parse_grouped_type(self) -> McdocType:
        """Parse parenthesized type"""
        self.expect('LPAREN')
        type_expr = self.parse_type()
        self.expect('RPAREN')
        return type_expr
    
    def parse_struct(self) -> StructType:
        """Parse struct definition with enhanced features"""
        self.expect('LBRACE')
        fields = []
        
        while not self.match('RBRACE') and self.current_token:
            # Skip doc comments and collect them
            doc_comment = None
            while self.match('DOC_COMMENT'):
                if doc_comment is None:
                    doc_comment = self.current_token[1][3:].strip()
                else:
                    doc_comment += "\n" + self.current_token[1][3:].strip()
                self.advance()
            
            # Handle spread operator
            if self.match('SPREAD'):
                self.advance()
                self._parse_primary_type()  # Skip for now
                if self.match('COMMA'):
                    self.advance()
                continue
            
            # Parse field with conditions
            if not self.match('IDENTIFIER'):
                break
                
            field_name = self.expect('IDENTIFIER')
            
            optional = False
            if self.match('OPTIONAL'):
                self.advance()
                optional = True
            
            self.expect('COLON')
            field_type = self.parse_type()
            
            # Parse field-level conditions
            conditions = []
            since = None
            until = None
            
            if self.match('KEYWORD', 'if'):
                self.advance()
                condition_expr = self._parse_condition_expression()
                conditions.append(Condition(ConditionType.IF, condition_expr))
            
            # Parse since/until for fields
            if self.match('AT') and self.peek() and self.peek()[1] == 'since':
                self.advance()
                self.advance()
                since = self.expect('VERSION')
            
            if self.match('AT') and self.peek() and self.peek()[1] == 'until':
                self.advance()
                self.advance()
                until = self.expect('VERSION')
            
            fields.append(StructField(field_name, field_type, optional, doc_comment, conditions, since, until))
            
            if self.match('COMMA'):
                self.advance()
        
        self.expect('RBRACE')
        return StructType(fields)