import re
from typing import List, Optional, Union, Tuple
from mcdoc_types import *

# ============================================================================
# Parser Components
# ============================================================================

class McdocLexer:
    """Tokenizes Mcdoc source code"""
    
    TOKEN_PATTERNS = [
        ('COMMENT', r'//(?!/).*'),
        ('DOC_COMMENT', r'///.*'),
        ('NUMBER', r'-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?[bslfdBSLFD]?'),
        ('STRING', r'"(?:[^"\\]|\\.)*"'),
        ('RESOURCE_LOC', r'[a-z_][a-z0-9_]*:[a-z_][a-z0-9_/]*'),
        ('IDENTIFIER', r'[a-zA-Z_][a-zA-Z0-9_]*'),
        ('PATH_SEP', r'::'),
        ('SPREAD', r'\.\.\.'),
        ('RANGE_EX', r'<\.\.<?'),
        ('RANGE', r'\.\.'),
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
    """Parses tokenized Mcdoc into AST"""
    
    def __init__(self, tokens: List[Tuple[str, str, int]]):
        self.tokens = tokens
        self.pos = 0
        self.current_token = self.tokens[0] if tokens else None
    
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
    
    def match(self, token_type: str) -> bool:
        return self.current_token and self.current_token[0] == token_type
    
    def parse_type(self) -> McdocType:
        """Parse a type expression"""
        return self._parse_union_type()
    
    def _parse_union_type(self) -> McdocType:
        """Parse union type (A | B | C)"""
        types = [self._parse_primary_type()]
        
        while self.match('PIPE'):
            self.advance()  # consume |
            types.append(self._parse_primary_type())
        
        return UnionType(types) if len(types) > 1 else types[0]
    
    def _parse_primary_type(self) -> McdocType:
        """Parse primary type expressions"""
        if self.match('IDENTIFIER'):
            return self._parse_identifier_type()
        elif self.match('STRING'):
            return self._parse_literal_string()
        elif self.match('NUMBER'):
            return self._parse_number_type()
        elif self.match('LBRACKET'):
            return self._parse_list_or_tuple()
        elif self.match('LPAREN'):
            return self._parse_grouped_type()
        else:
            # Handle built-in types
            if self.current_token and self.current_token[1] in ['any', 'boolean', 'string', 'byte', 'short', 'int', 'long', 'float', 'double']:
                type_name = self.current_token[1]
                self.advance()
                
                if type_name == 'any':
                    return AnyType()
                elif type_name == 'boolean':
                    return BooleanType()
                elif type_name == 'string':
                    return StringType()
                else:
                    return NumericType(type_name)
            
            raise SyntaxError(f"Unexpected token: {self.current_token}")
    
    def _parse_identifier_type(self) -> McdocType:
        """Parse identifier-based types (references, etc.)"""
        name = self.expect('IDENTIFIER')
        
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
        # Remove quotes and handle escape sequences
        unquoted = value[1:-1].replace('\\"', '"').replace('\\\\', '\\')
        return LiteralType(unquoted)
    
    def _parse_number_type(self) -> Union[LiteralType, NumericType]:
        """Parse numeric types and literals"""
        number_str = self.expect('NUMBER')
        
        # Check for type suffix
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
        
        # Single element with trailing comma is tuple, otherwise list
        if len(elements) == 1 and self.tokens[self.pos - 2][0] == 'COMMA':
            return TupleType(elements)
        elif len(elements) > 1:
            return TupleType(elements)
        else:
            return ListType(elements[0])
    
    def _parse_grouped_type(self) -> McdocType:
        """Parse parenthesized type"""
        self.expect('LPAREN')
        type_expr = self.parse_type()
        self.expect('RPAREN')
        return type_expr
    
    def parse_struct(self) -> StructType:
        """Parse struct definition"""
        self.expect('LBRACE')
        fields = []
        
        while not self.match('RBRACE') and self.current_token:
            # Handle spread operator
            if self.match('SPREAD'):
                self.advance()
                # TODO: Handle spreads properly
                self._parse_primary_type()  # Skip for now
                if self.match('COMMA'):
                    self.advance()
                continue
            
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