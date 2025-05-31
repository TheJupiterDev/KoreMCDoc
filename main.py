#!/usr/bin/env python3
"""
Mcdoc to PySide6 Form Generator

A comprehensive parser and form generator that converts mcdoc schema files
into interactive PySide6 forms for data input and validation.
"""

import sys
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum as PyEnum

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QFormLayout, QLabel, QLineEdit, QSpinBox, QDoubleSpinBox,
        QCheckBox, QComboBox, QPushButton, QScrollArea, QGroupBox,
        QTabWidget, QTextEdit, QMessageBox, QFileDialog, QListWidget,
        QListWidgetItem, QSplitter, QTreeWidget, QTreeWidgetItem
    )
    from PySide6.QtCore import Qt, Signal, QObject
    from PySide6.QtGui import QFont, QPalette
except ImportError:
    print("Error: PySide6 is required. Install with: pip install PySide6")
    sys.exit(1)


class TokenType(PyEnum):
    """Token types for mcdoc lexer"""
    # Literals
    INTEGER = "INTEGER"
    FLOAT = "FLOAT"
    TYPED_NUMBER = "TYPED_NUMBER"
    STRING = "STRING"
    BOOLEAN = "BOOLEAN"
    
    # Keywords
    STRUCT = "struct"
    ENUM = "enum"
    TYPE = "type"
    USE = "use"
    DISPATCH = "dispatch"
    INJECT = "inject"
    ANY = "any"
    BOOLEAN_KW = "boolean"
    STRING_KW = "string"
    BYTE = "byte"
    SHORT = "short"
    INT = "int"
    LONG = "long"
    FLOAT_KW = "float"
    DOUBLE = "double"
    TRUE = "true"
    FALSE = "false"
    SUPER = "super"
    AS = "as"
    TO = "to"
    
    # Symbols
    LBRACE = "{"
    RBRACE = "}"
    LBRACKET = "["
    RBRACKET = "]"
    LPAREN = "("
    RPAREN = ")"
    LANGLE = "<"
    RANGLE = ">"
    COMMA = ","
    COLON = ":"
    SEMICOLON = ";"
    EQUALS = "="
    QUESTION = "?"
    PIPE = "|"
    DOT = "."
    SPREAD = "..."
    RANGE = ".."
    RANGE_EXCL_END = "..<"
    RANGE_EXCL_START = "<.."
    RANGE_EXCL_BOTH = "<..<"
    AT = "@"
    HASH = "#"
    PATH_SEP = "::"
    
    # Identifiers and paths
    IDENTIFIER = "IDENTIFIER"
    RESOURCE_LOCATION = "RESOURCE_LOCATION"
    PATH = "PATH"
    
    # Special
    COMMENT = "COMMENT"
    DOC_COMMENT = "DOC_COMMENT"
    NEWLINE = "NEWLINE"
    EOF = "EOF"


@dataclass
class Token:
    """Represents a token in the mcdoc source"""
    type: TokenType
    value: str
    line: int
    column: int


class McdocLexer:
    """Lexer for mcdoc files"""
    
    KEYWORDS = {
        'struct', 'enum', 'type', 'use', 'dispatch', 'inject',
        'any', 'boolean', 'string', 'byte', 'short', 'int', 'long',
        'float', 'double', 'true', 'false', 'super', 'as', 'to'
    }
    
    def __init__(self, source: str):
        self.source = source
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
    
    def error(self, message: str):
        raise SyntaxError(f"Line {self.line}, Column {self.column}: {message}")
    
    def peek(self, offset: int = 0) -> str:
        pos = self.pos + offset
        return self.source[pos] if pos < len(self.source) else '\0'
    
    def advance(self) -> str:
        if self.pos >= len(self.source):
            return '\0'
        
        char = self.source[self.pos]
        self.pos += 1
        
        if char == '\n':
            self.line += 1
            self.column = 1
        else:
            self.column += 1
        
        return char
    
    def skip_whitespace(self):
        while self.peek() in ' \t\r':
            self.advance()
    
    def read_string(self) -> str:
        value = ""
        self.advance()  # Skip opening quote
        
        while self.peek() != '"' and self.peek() != '\0':
            char = self.advance()
            if char == '\\':
                next_char = self.advance()
                escape_map = {
                    '"': '"', '\\': '\\', 'b': '\b', 'f': '\f',
                    'n': '\n', 'r': '\r', 't': '\t'
                }
                value += escape_map.get(next_char, next_char)
            else:
                value += char
        
        if self.peek() == '\0':
            self.error("Unterminated string literal")
        
        self.advance()  # Skip closing quote
        return value
    
    def read_number(self) -> Tuple[str, TokenType]:
        value = ""
        token_type = TokenType.INTEGER
        
        # Handle sign
        if self.peek() in '+-':
            value += self.advance()
        
        # Read digits
        while self.peek().isdigit():
            value += self.advance()
        
        # Check for decimal point
        if self.peek() == '.' and self.peek(1).isdigit():
            token_type = TokenType.FLOAT
            value += self.advance()  # dot
            while self.peek().isdigit():
                value += self.advance()
        
        # Check for scientific notation
        if self.peek().lower() == 'e':
            token_type = TokenType.FLOAT
            value += self.advance()
            if self.peek() in '+-':
                value += self.advance()
            while self.peek().isdigit():
                value += self.advance()
        
        # Check for type suffix
        if self.peek().lower() in 'bslfd':
            value += self.advance()
            token_type = TokenType.TYPED_NUMBER
        
        return value, token_type
    
    def read_identifier(self) -> str:
        value = ""
        if self.peek() == '%':
            value += self.advance()

        while self.peek().isalnum() or self.peek() in '_':
            value += self.advance()
        return value
    
    def read_comment(self) -> Tuple[str, TokenType]:
        value = ""
        self.advance()  # Skip first /
        self.advance()  # Skip second /
        
        # Check for doc comment
        if self.peek() == '/':
            self.advance()  # Skip third /
            token_type = TokenType.DOC_COMMENT
        else:
            token_type = TokenType.COMMENT
        
        # Read until end of line
        while self.peek() not in '\n\0':
            value += self.advance()
        
        return value, token_type
    
    def tokenize(self) -> List[Token]:
        self.tokens = []
        
        while self.pos < len(self.source):
            self.skip_whitespace()
            
            if self.pos >= len(self.source):
                break
            
            start_line = self.line
            start_column = self.column
            char = self.peek()
            
            # Handle newlines
            if char == '\n':
                self.advance()
                self.tokens.append(Token(TokenType.NEWLINE, '\n', start_line, start_column))
                continue
            
            # Handle comments
            if char == '/' and self.peek(1) == '/':
                value, token_type = self.read_comment()
                self.tokens.append(Token(token_type, value, start_line, start_column))
                continue
            
            # Handle strings
            if char == '"':
                value = self.read_string()
                self.tokens.append(Token(TokenType.STRING, value, start_line, start_column))
                continue
            
            # Handle numbers
            if char.isdigit() or (char in '+-' and self.peek(1).isdigit()):
                value, token_type = self.read_number()
                self.tokens.append(Token(token_type, value, start_line, start_column))
                continue
            
            # Handle identifiers and keywords (including special keys like %key)
            if char.isalpha() or char == '_' or char == '%':
                value = self.read_identifier()
                if value in self.KEYWORDS:
                    token_type = TokenType(value)
                else:
                    token_type = TokenType.IDENTIFIER
                self.tokens.append(Token(token_type, value, start_line, start_column))
                continue
            
            # Handle multi-character operators
            if char == ':' and self.peek(1) == ':':
                self.advance()
                self.advance()
                self.tokens.append(Token(TokenType.PATH_SEP, '::', start_line, start_column))
                continue
            
            if char == '.' and self.peek(1) == '.':
                self.advance()
                self.advance()
                if self.peek() == '.':
                    self.advance()
                    self.tokens.append(Token(TokenType.SPREAD, '...', start_line, start_column))
                    continue
                elif self.peek() == '<':
                    self.advance()
                    self.tokens.append(Token(TokenType.RANGE_EXCL_END, '..<', start_line, start_column))
                    continue
                else:
                    self.tokens.append(Token(TokenType.RANGE, '..', start_line, start_column))
                    continue
            
            if char == '<' and self.peek(1) == '.' and self.peek(2) == '.':
                self.advance()
                self.advance()
                self.advance()
                if self.peek() == '<':
                    self.advance()
                    self.tokens.append(Token(TokenType.RANGE_EXCL_BOTH, '<..<', start_line, start_column))
                    continue
                else:
                    self.tokens.append(Token(TokenType.RANGE_EXCL_START, '<..', start_line, start_column))
                    continue
            
            # Handle single-character tokens
            single_chars = {
                '{': TokenType.LBRACE, '}': TokenType.RBRACE,
                '[': TokenType.LBRACKET, ']': TokenType.RBRACKET,
                '(': TokenType.LPAREN, ')': TokenType.RPAREN,
                '<': TokenType.LANGLE, '>': TokenType.RANGLE,
                ',': TokenType.COMMA, ':': TokenType.COLON,
                ';': TokenType.SEMICOLON, '=': TokenType.EQUALS,
                '?': TokenType.QUESTION, '|': TokenType.PIPE,
                '.': TokenType.DOT, '@': TokenType.AT, '#': TokenType.HASH
            }
            
            if char in single_chars:
                self.advance()
                self.tokens.append(Token(single_chars[char], char, start_line, start_column))
                continue
            
            # Unknown character
            self.error(f"Unexpected character: {char}")
        
        self.tokens.append(Token(TokenType.EOF, '', self.line, self.column))
        return self.tokens


@dataclass
class McdocType:
    """Base class for mcdoc types"""
    pass


@dataclass
class PrimitiveType(McdocType):
    """Primitive types like int, string, boolean"""
    name: str
    range_constraint: Optional[str] = None


@dataclass
class LiteralType(McdocType):
    """Literal values like "foo", 42, true"""
    value: Any


@dataclass
class ArrayType(McdocType):
    """Array type like [string] or int[]"""
    element_type: McdocType
    size_constraint: Optional[str] = None


@dataclass
class TupleType(McdocType):
    """Tuple type like [string, int]"""
    element_types: List[McdocType]


@dataclass
class StructField:
    """Field in a struct"""
    name: str
    type: McdocType
    optional: bool = False
    doc_comment: Optional[str] = None


@dataclass
class StructType(McdocType):
    """Struct type definition"""
    name: Optional[str]
    fields: List[StructField] = field(default_factory=list)
    doc_comment: Optional[str] = None


@dataclass
class EnumField:
    """Field in an enum"""
    name: str
    value: Any
    doc_comment: Optional[str] = None


@dataclass
class EnumType(McdocType):
    """Enum type definition"""
    name: Optional[str]
    base_type: str
    fields: List[EnumField] = field(default_factory=list)
    doc_comment: Optional[str] = None


@dataclass
class UnionType(McdocType):
    """Union type like (string | int)"""
    types: List[McdocType]


@dataclass
class ReferenceType(McdocType):
    """Reference to another type"""
    path: str
    attributes: List[str] = field(default_factory=list)


@dataclass
class TypeAlias:
    """Type alias definition"""
    name: str
    type: McdocType
    type_params: List[str] = field(default_factory=list)
    doc_comment: Optional[str] = None


class McdocParser:
    """Parser for mcdoc files"""
    
    def __init__(self, tokens: List[Token], file_path: str = ""):
        self.tokens = tokens
        self.pos = 0
        self.file_path = file_path
        self.structs: Dict[str, StructType] = {}
        self.enums: Dict[str, EnumType] = {}
        self.type_aliases: Dict[str, TypeAlias] = {}
        self.imports: List[str] = []
    
    def error(self, message: str):
        token = self.current_token()
        raise SyntaxError(f"File {self.file_path}, Line {token.line}: {message}")
    
    def current_token(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]
    
    def peek_token(self, offset: int = 0) -> Token:
        pos = self.pos + offset
        return self.tokens[pos] if pos < len(self.tokens) else self.tokens[-1]
    
    def advance(self) -> Token:
        token = self.current_token()
        if token.type != TokenType.EOF:
            self.pos += 1
        return token
    
    def match(self, *token_types: TokenType) -> bool:
        return self.current_token().type in token_types
    
    def consume(self, token_type: TokenType, message: str = "") -> Token:
        if not self.match(token_type):
            expected = token_type.value
            actual = self.current_token().value
            self.error(message or f"Expected {expected}, got {actual}")
        return self.advance()
    
    def skip_newlines(self):
        while self.match(TokenType.NEWLINE, TokenType.COMMENT, TokenType.DOC_COMMENT):
            self.advance()
    
    def parse_doc_comment(self) -> Optional[str]:
        """Parse doc comments that precede declarations"""
        comments = []
        while self.match(TokenType.DOC_COMMENT):
            comments.append(self.advance().value)
        return '\n'.join(comments) if comments else None
    
    def parse_type(self) -> McdocType:
        """Parse a type expression"""
        self.skip_newlines()
        
        # Handle attributes with #[...]
        attributes = []
        while self.match(TokenType.HASH):
            self.advance()  # consume #
            self.consume(TokenType.LBRACKET)
            
            # Parse attribute contents
            attr_content = []
            while not self.match(TokenType.RBRACKET, TokenType.EOF):
                if self.match(TokenType.IDENTIFIER):
                    id_name = self.advance().value
                    attr_part = id_name
                    
                    if self.match(TokenType.LPAREN):
                        self.advance()  # consume (
                        params = []
                        
                        while not self.match(TokenType.RPAREN, TokenType.EOF):
                            if self.match(TokenType.IDENTIFIER):
                                key = self.advance().value
                                if self.match(TokenType.EQUALS):
                                    self.advance()
                                    if self.match(TokenType.STRING):
                                        value = self.advance().value
                                        params.append(f'{key}="{value}"')
                                else:
                                    params.append(key)
                            
                            if self.match(TokenType.COMMA):
                                self.advance()
                                self.skip_newlines()
                        
                        self.consume(TokenType.RPAREN)
                        if params:
                            attr_part += f"({', '.join(params)})"
                    
                    attr_content.append(attr_part)
                
                if self.match(TokenType.COMMA):
                    self.advance()
                    self.skip_newlines()
            
            self.consume(TokenType.RBRACKET)
            if attr_content:
                attributes.append(f"#[{', '.join(attr_content)}]")

        # Parse the base type
        if self.match(TokenType.STRING_KW):
            base_type = PrimitiveType(self.advance().value)
        elif self.match(TokenType.LBRACKET):
            self.advance()  # consume [
            element_type = self.parse_type()  # This will handle nested attributes
            self.consume(TokenType.RBRACKET)
            base_type = ArrayType(element_type)
        elif self.match(TokenType.LPAREN):
            self.advance()  # consume (
            self.skip_newlines()
            
            types = []
            while not self.match(TokenType.RPAREN, TokenType.EOF):
                types.append(self.parse_type())
                self.skip_newlines()
                if self.match(TokenType.PIPE):
                    self.advance()  # consume |
                    self.skip_newlines()
                else:
                    break
            
            self.consume(TokenType.RPAREN)
            base_type = UnionType(types) if len(types) > 1 else types[0]
        elif self.match(TokenType.IDENTIFIER):
            path = self.advance().value
            while self.match(TokenType.PATH_SEP):
                self.advance()  # consume ::
                path += "::" + self.consume(TokenType.IDENTIFIER).value
            base_type = ReferenceType(path)
        else:
            self.error(f"Unexpected token in type: {self.current_token().value}")

        # Attach attributes to the type
        if attributes:
            if isinstance(base_type, ReferenceType):
                base_type.attributes = attributes
            elif isinstance(base_type, ArrayType):
                base_type.element_type.attributes = attributes
            elif isinstance(base_type, UnionType):
                # For union types, attach attributes to each member type
                for type_member in base_type.types:
                    if isinstance(type_member, ReferenceType):
                        type_member.attributes = attributes.copy()

        return base_type

    def parse_range(self) -> str:
        """Parse a range constraint like 1..10 or ..5"""
        range_str = ""
        
        # Handle exclusive start
        if self.match(TokenType.RANGE_EXCL_START, TokenType.RANGE_EXCL_BOTH):
            range_str += self.advance().value
        elif self.match(TokenType.RANGE, TokenType.RANGE_EXCL_END):
            range_str += self.advance().value
        else:
            # Start value
            if self.match(TokenType.INTEGER, TokenType.FLOAT):
                range_str += self.advance().value
            
            # Range operator
            if self.match(TokenType.RANGE, TokenType.RANGE_EXCL_END, 
                         TokenType.RANGE_EXCL_START, TokenType.RANGE_EXCL_BOTH):
                range_str += self.advance().value
                
                # End value
                if self.match(TokenType.INTEGER, TokenType.FLOAT):
                    range_str += self.advance().value
        
        return range_str if range_str else "0.."
    
    def parse_struct_type(self) -> StructType:
        """Parse struct type definition"""
        doc_comment = self.parse_doc_comment()
        self.consume(TokenType.STRUCT)
        
        # Optional struct name
        name = None
        if self.match(TokenType.IDENTIFIER):
            name = self.advance().value
        
        self.consume(TokenType.LBRACE)
        self.skip_newlines()
        
        fields = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            field_doc = self.parse_doc_comment()
            self.skip_newlines()
            
            if self.match(TokenType.RBRACE):
                break
            
            # Parse field name
            field_name = self.consume(TokenType.IDENTIFIER).value
            
            # Check for optional marker
            optional = False
            if self.match(TokenType.QUESTION):
                self.advance()
                optional = True
            
            self.consume(TokenType.COLON)
            field_type = self.parse_type()
            
            fields.append(StructField(field_name, field_type, optional, field_doc))
            
            self.skip_newlines()
            if self.match(TokenType.COMMA):
                self.advance()
            self.skip_newlines()
        
        self.consume(TokenType.RBRACE)
        return StructType(name, fields, doc_comment)
    
    def parse_enum_type(self) -> EnumType:
        """Parse enum type definition"""
        doc_comment = self.parse_doc_comment()
        self.consume(TokenType.ENUM)
        
        # Parse enum base type
        self.consume(TokenType.LPAREN)
        base_type = self.consume(TokenType.BYTE, TokenType.SHORT, TokenType.INT,
                                TokenType.LONG, TokenType.STRING_KW, TokenType.FLOAT_KW,
                                TokenType.DOUBLE).value
        self.consume(TokenType.RPAREN)
        
        # Optional enum name
        name = None
        if self.match(TokenType.IDENTIFIER):
            name = self.advance().value
        
        self.consume(TokenType.LBRACE)
        self.skip_newlines()
        
        fields = []
        while not self.match(TokenType.RBRACE, TokenType.EOF):
            field_doc = self.parse_doc_comment()
            self.skip_newlines()
            
            if self.match(TokenType.RBRACE):
                break
            
            field_name = self.consume(TokenType.IDENTIFIER).value
            self.consume(TokenType.EQUALS)
            
            # Parse field value
            if self.match(TokenType.STRING):
                field_value = self.advance().value
            elif self.match(TokenType.INTEGER, TokenType.FLOAT, TokenType.TYPED_NUMBER):
                value_str = self.advance().value
                try:
                    field_value = int(value_str.rstrip('bslBSL')) if base_type in ['byte', 'short', 'int', 'long'] else float(value_str.rstrip('fdFD'))
                except ValueError:
                    field_value = value_str
            else:
                self.error("Expected enum field value")
            
            fields.append(EnumField(field_name, field_value, field_doc))
            
            self.skip_newlines()
            if self.match(TokenType.COMMA):
                self.advance()
            self.skip_newlines()
        
        self.consume(TokenType.RBRACE)
        return EnumType(name, base_type, fields, doc_comment)
    
    def parse_struct_definition(self):
        """Parse top-level struct definition"""
        doc_comment = self.parse_doc_comment()
        struct_type = self.parse_struct_type()
        
        if struct_type.name:
            struct_type.doc_comment = doc_comment
            self.structs[struct_type.name] = struct_type
    
    def parse_enum_definition(self):
        """Parse top-level enum definition"""
        doc_comment = self.parse_doc_comment()
        enum_type = self.parse_enum_type()
        
        if enum_type.name:
            enum_type.doc_comment = doc_comment
            self.enums[enum_type.name] = enum_type
    
    def parse_type_alias(self):
        """Parse type alias definition"""
        doc_comment = self.parse_doc_comment()
        self.consume(TokenType.TYPE)
        
        name = self.consume(TokenType.IDENTIFIER).value
        
        # Optional type parameters
        type_params = []
        if self.match(TokenType.LANGLE):
            self.advance()  # consume <
            self.skip_newlines()
            
            if not self.match(TokenType.RANGLE):
                type_params.append(self.consume(TokenType.IDENTIFIER).value)
                
                while self.match(TokenType.COMMA):
                    self.advance()  # consume ,
                    self.skip_newlines()
                    type_params.append(self.consume(TokenType.IDENTIFIER).value)
            
            self.consume(TokenType.RANGLE)
        
        self.consume(TokenType.EQUALS)
        alias_type = self.parse_type()
        
        self.type_aliases[name] = TypeAlias(name, alias_type, type_params, doc_comment)
    
    def parse_use_statement(self):
        """Parse use statement in the format:
        use [::][super::]?path::to::item [as alias]?
        """
        self.consume(TokenType.USE)
        
        segments = []
        
        # Handle optional leading ::
        has_leading_path_sep = self.match(TokenType.PATH_SEP)
        if has_leading_path_sep:
            self.advance()
        
        # Parse first segment
        if self.match(TokenType.SUPER):
            segments.append(self.advance().value)
            self.consume(TokenType.PATH_SEP)
        elif not self.match(TokenType.IDENTIFIER):
            self.error(f"Expected identifier or 'super' in use statement, got {self.current_token().type}")
        
        # Parse identifier segment
        segments.append(self.consume(TokenType.IDENTIFIER).value)
        
        # Parse remaining path segments
        while self.match(TokenType.PATH_SEP):
            self.advance()  # consume ::
            
            # Handle super in middle of path
            if self.match(TokenType.SUPER):
                segments.append(self.advance().value)
                self.consume(TokenType.PATH_SEP)
                segments.append(self.consume(TokenType.IDENTIFIER).value)
            else:
                segments.append(self.consume(TokenType.IDENTIFIER).value)
        
        # Build full path
        path = "::".join(segments)
        if has_leading_path_sep:
            path = "::" + path
        
        # Handle optional alias
        alias = None
        if self.match(TokenType.AS):
            self.advance()  # consume 'as'
            alias = self.consume(TokenType.IDENTIFIER).value
        
        # Store use statement info
        use_info = {
            'path': path,
            'alias': alias
        }
        self.imports.append(use_info)
    
    def parse(self) -> Dict[str, Any]:
        """Parse the entire file"""
        self.pos = 0
        
        while not self.match(TokenType.EOF):
            self.skip_newlines()
            
            if self.match(TokenType.EOF):
                break
            
            if self.match(TokenType.STRUCT):
                self.parse_struct_definition()
            elif self.match(TokenType.ENUM):
                self.parse_enum_definition()
            elif self.match(TokenType.TYPE):
                self.parse_type_alias()
            elif self.match(TokenType.USE):
                self.parse_use_statement()
            else:
                # Skip unknown tokens for now
                self.advance()
        
        return {
            'structs': self.structs,
            'enums': self.enums,
            'type_aliases': self.type_aliases,
            'imports': self.imports
        }


class McdocProject:
    """Manages a collection of mcdoc files and their dependencies"""
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self.files: Dict[str, Dict[str, Any]] = {}
        self.resolved_types: Dict[str, McdocType] = {}
    
    def find_mcdoc_files(self) -> List[Path]:
        """Find all .mcdoc files in the project"""
        mcdoc_files = []
        
        # Check if there's a dedicated mcdoc directory
        mcdoc_dir = self.root_path / "mcdoc"
        search_root = mcdoc_dir if mcdoc_dir.exists() else self.root_path
        
        for file_path in search_root.rglob("*.mcdoc"):
            mcdoc_files.append(file_path)
        
        return mcdoc_files
    
    def load_project(self):
        """Load all mcdoc files in the project"""
        mcdoc_files = self.find_mcdoc_files()
        
        for file_path in mcdoc_files:
            relative_path = str(file_path.relative_to(self.root_path))
            self.files[relative_path] = self.load_file(file_path)
        
        # Resolve type references
        self.resolve_types()
    
    def load_file(self, file_path: Path) -> Dict[str, Any]:
        """Load a single mcdoc file and return its parsed data"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                source = f.read()
            
            # Tokenize
            lexer = McdocLexer(source)
            tokens = lexer.tokenize()
            
            # Parse
            parser = McdocParser(tokens, str(file_path))
            return parser.parse()
            
        except Exception as e:
            raise Exception(f"Failed to load file {file_path}: {str(e)}")
    
    def resolve_types(self):
        """Resolve type references across files"""
        # Build a global type registry
        self.resolved_types.clear()
        
        for file_data in self.files.values():
            for name, struct in file_data['structs'].items():
                self.resolved_types[name] = struct
            for name, enum in file_data['enums'].items():
                self.resolved_types[name] = enum
            for name, alias in file_data['type_aliases'].items():
                self.resolved_types[name] = alias.type
    
    def get_struct_types(self) -> Dict[str, StructType]:
        """Get all struct types from the project"""
        structs = {}
        for file_data in self.files.values():
            structs.update(file_data['structs'])
        return structs
    
    def get_enum_types(self) -> Dict[str, EnumType]:
        """Get all enum types from the project"""
        enums = {}
        for file_data in self.files.values():
            enums.update(file_data['enums'])
        return enums


class FormFieldWidget(QWidget):
    """Base class for form field widgets"""
    
    valueChanged = Signal()
    
    def __init__(self, field: StructField, parent=None):
        super().__init__(parent)
        self.field = field
        self.setup_ui()
    
    def setup_ui(self):
        """Setup the widget UI - to be implemented by subclasses"""
        raise NotImplementedError
    
    def get_value(self):
        """Get the current value - to be implemented by subclasses"""
        raise NotImplementedError
    
    def set_value(self, value):
        """Set the current value - to be implemented by subclasses"""
        raise NotImplementedError
    
    def is_valid(self) -> bool:
        """Check if the current value is valid"""
        return True
    
    def get_validation_error(self) -> str:
        """Get validation error message"""
        return ""


class StringFieldWidget(FormFieldWidget):
    """Widget for string fields"""
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Label
        self.label = QLabel(self.field.name)
        if self.field.doc_comment:
            self.label.setToolTip(self.field.doc_comment)
        layout.addWidget(self.label)
        
        # Input
        self.line_edit = QLineEdit()
        self.line_edit.textChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.line_edit)
        
        # Optional indicator
        if self.field.optional:
            self.label.setText(f"{self.field.name} (optional)")
    
    def get_value(self):
        return self.line_edit.text() if self.line_edit.text() else None
    
    def set_value(self, value):
        self.line_edit.setText(str(value) if value is not None else "")
    
    def is_valid(self) -> bool:
        if not self.field.optional and not self.line_edit.text():
            return False
        return True
    
    def get_validation_error(self) -> str:
        if not self.is_valid():
            return f"{self.field.name} is required"
        return ""


class NumberFieldWidget(FormFieldWidget):
    """Widget for numeric fields"""
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Label
        self.label = QLabel(self.field.name)
        if self.field.doc_comment:
            self.label.setToolTip(self.field.doc_comment)
        layout.addWidget(self.label)
        
        # Determine number type
        if isinstance(self.field.type, PrimitiveType):
            type_name = self.field.type.name
            if type_name in ['float', 'double']:
                self.spin_box = QDoubleSpinBox()
                self.spin_box.setRange(-999999.999999, 999999.999999)
                self.spin_box.setDecimals(6)
            else:
                self.spin_box = QSpinBox()
                if type_name == 'byte':
                    self.spin_box.setRange(-128, 127)
                elif type_name == 'short':
                    self.spin_box.setRange(-32768, 32767)
                elif type_name == 'int':
                    self.spin_box.setRange(-2147483648, 2147483647)
                elif type_name == 'long':
                    self.spin_box.setRange(-9223372036854775808, 9223372036854775807)
                else:
                    self.spin_box.setRange(-999999, 999999)
            
            # Apply range constraint if present
            if self.field.type.range_constraint:
                self.apply_range_constraint(self.field.type.range_constraint)
        else:
            self.spin_box = QSpinBox()
            self.spin_box.setRange(-999999, 999999)
        
        self.spin_box.valueChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.spin_box)
        
        # Optional indicator
        if self.field.optional:
            self.label.setText(f"{self.field.name} (optional)")
    
    def apply_range_constraint(self, constraint: str):
        """Apply range constraint to the spin box"""
        try:
            # Parse simple range constraints like "1..10" or "0.."
            if '..' in constraint:
                parts = constraint.split('..')
                if len(parts) == 2:
                    min_val = float(parts[0]) if parts[0] else self.spin_box.minimum()
                    max_val = float(parts[1]) if parts[1] else self.spin_box.maximum()
                    
                    if isinstance(self.spin_box, QDoubleSpinBox):
                        self.spin_box.setRange(min_val, max_val)
                    else:
                        self.spin_box.setRange(int(min_val), int(max_val))
        except (ValueError, IndexError):
            pass  # Ignore invalid constraints
    
    def get_value(self):
        return self.spin_box.value()
    
    def set_value(self, value):
        if value is not None:
            self.spin_box.setValue(float(value) if isinstance(self.spin_box, QDoubleSpinBox) else int(value))
    
    def is_valid(self) -> bool:
        return True  # SpinBox handles validation internally


class BooleanFieldWidget(FormFieldWidget):
    """Widget for boolean fields"""
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Checkbox with label
        self.checkbox = QCheckBox(self.field.name)
        if self.field.doc_comment:
            self.checkbox.setToolTip(self.field.doc_comment)
        if self.field.optional:
            self.checkbox.setText(f"{self.field.name} (optional)")
        
        self.checkbox.stateChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.checkbox)
    
    def get_value(self):
        return self.checkbox.isChecked()
    
    def set_value(self, value):
        self.checkbox.setChecked(bool(value) if value is not None else False)
    
    def is_valid(self) -> bool:
        return True


class EnumFieldWidget(FormFieldWidget):
    """Widget for enum fields"""
    
    def __init__(self, field: StructField, enum_type: EnumType, parent=None):
        self.enum_type = enum_type
        super().__init__(field, parent)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Label
        self.label = QLabel(self.field.name)
        if self.field.doc_comment:
            self.label.setToolTip(self.field.doc_comment)
        layout.addWidget(self.label)
        
        # ComboBox
        self.combo_box = QComboBox()
        
        # Add enum options
        if self.field.optional:
            self.combo_box.addItem("(none)", None)
        
        for enum_field in self.enum_type.fields:
            display_text = enum_field.name
            if enum_field.doc_comment:
                display_text += f" - {enum_field.doc_comment}"
            self.combo_box.addItem(display_text, enum_field.value)
        
        self.combo_box.currentIndexChanged.connect(self.valueChanged.emit)
        layout.addWidget(self.combo_box)
        
        # Optional indicator
        if self.field.optional:
            self.label.setText(f"{self.field.name} (optional)")
    
    def get_value(self):
        return self.combo_box.currentData()
    
    def set_value(self, value):
        for i in range(self.combo_box.count()):
            if self.combo_box.itemData(i) == value:
                self.combo_box.setCurrentIndex(i)
                break
    
    def is_valid(self) -> bool:
        if not self.field.optional and self.combo_box.currentData() is None:
            return False
        return True
    
    def get_validation_error(self) -> str:
        if not self.is_valid():
            return f"{self.field.name} is required"
        return ""


class ArrayFieldWidget(FormFieldWidget):
    """Widget for array fields"""
    
    def __init__(self, field: StructField, project: McdocProject, parent=None):
        self.project = project
        self.items = []
        super().__init__(field, parent)
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Label
        self.label = QLabel(self.field.name)
        if self.field.doc_comment:
            self.label.setToolTip(self.field.doc_comment)
        layout.addWidget(self.label)
        
        # Controls
        controls_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Item")
        self.add_button.clicked.connect(self.add_item)
        controls_layout.addWidget(self.add_button)
        
        self.remove_button = QPushButton("Remove Selected")
        self.remove_button.clicked.connect(self.remove_item)
        controls_layout.addWidget(self.remove_button)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        # List widget
        self.list_widget = QListWidget()
        self.list_widget.itemSelectionChanged.connect(self.update_remove_button)
        layout.addWidget(self.list_widget)
        
        # Optional indicator
        if self.field.optional:
            self.label.setText(f"{self.field.name} (optional)")
        
        self.update_remove_button()
    
    def add_item(self):
        """Add a new item to the array"""
        if isinstance(self.field.type, ArrayType):
            element_type = self.field.type.element_type
            
            # Create a simple input dialog for now
            if isinstance(element_type, PrimitiveType):
                if element_type.name == 'string':
                    from PySide6.QtWidgets import QInputDialog
                    text, ok = QInputDialog.getText(self, "Add Item", "Enter string value:")
                    if ok:
                        self.items.append(text)
                        self.list_widget.addItem(text)
                        self.valueChanged.emit()
                elif element_type.name in ['int', 'byte', 'short', 'long']:
                    from PySide6.QtWidgets import QInputDialog
                    value, ok = QInputDialog.getInt(self, "Add Item", "Enter integer value:")
                    if ok:
                        self.items.append(value)
                        self.list_widget.addItem(str(value))
                        self.valueChanged.emit()
                elif element_type.name in ['float', 'double']:
                    from PySide6.QtWidgets import QInputDialog
                    value, ok = QInputDialog.getDouble(self, "Add Item", "Enter decimal value:")
                    if ok:
                        self.items.append(value)
                        self.list_widget.addItem(str(value))
                        self.valueChanged.emit()
    
    def remove_item(self):
        """Remove selected item from the array"""
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            self.items.pop(current_row)
            self.list_widget.takeItem(current_row)
            self.valueChanged.emit()
            self.update_remove_button()
    
    def update_remove_button(self):
        """Update remove button state"""
        self.remove_button.setEnabled(self.list_widget.currentRow() >= 0)
    
    def get_value(self):
        return self.items if self.items else None
    
    def set_value(self, value):
        self.items = list(value) if value else []
        self.list_widget.clear()
        for item in self.items:
            self.list_widget.addItem(str(item))
    
    def is_valid(self) -> bool:
        if not self.field.optional and not self.items:
            return False
        return True
    
    def get_validation_error(self) -> str:
        if not self.is_valid():
            return f"{self.field.name} is required"
        return ""


class StructFormWidget(QWidget):
    """Widget for editing a struct"""
    
    valueChanged = Signal()
    
    def __init__(self, struct_type: StructType, project: McdocProject, parent=None):
        super().__init__(parent)
        self.struct_type = struct_type
        self.project = project
        self.field_widgets = {}
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Create scroll area for large forms
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QFormLayout(scroll_widget)
        
        # Create field widgets
        for field in self.struct_type.fields:
            widget = self.create_field_widget(field)
            if widget:
                widget.valueChanged.connect(self.valueChanged.emit)
                self.field_widgets[field.name] = widget
                form_layout.addRow(widget)
        
        scroll_area.setWidget(scroll_widget)
        layout.addWidget(scroll_area)
    
    def create_field_widget(self, field: StructField) -> Optional[FormFieldWidget]:
        """Create appropriate widget for field type"""
        field_type = field.type
        
        # Handle primitive types
        if isinstance(field_type, PrimitiveType):
            if field_type.name == 'string':
                return StringFieldWidget(field)
            elif field_type.name == 'boolean':
                return BooleanFieldWidget(field)
            elif field_type.name in ['byte', 'short', 'int', 'long', 'float', 'double']:
                return NumberFieldWidget(field)
        
        # Handle literal types
        elif isinstance(field_type, LiteralType):
            if isinstance(field_type.value, str):
                return StringFieldWidget(field)
            elif isinstance(field_type.value, bool):
                return BooleanFieldWidget(field)
            elif isinstance(field_type.value, (int, float)):
                return NumberFieldWidget(field)
        
        # Handle array types
        elif isinstance(field_type, ArrayType):
            return ArrayFieldWidget(field, self.project)
        
        # Handle reference types (including enums)
        elif isinstance(field_type, ReferenceType):
            # Try to resolve as enum first
            enums = self.project.get_enum_types()
            if field_type.path in enums:
                return EnumFieldWidget(field, enums[field_type.path])
            
            # Try to resolve as struct (for nested structs)
            structs = self.project.get_struct_types()
            if field_type.path in structs:
                # For now, create a simple label - nested structs need more complex handling
                widget = QWidget()
                layout = QVBoxLayout(widget)
                label = QLabel(f"{field.name}: {field_type.path} (nested struct)")
                layout.addWidget(label)
                return None  # Skip for now
        
        # Handle union types
        elif isinstance(field_type, UnionType):
            # Create a combo box to select the type, then show appropriate widget
            # This is complex - for now, skip
            return None
        
        # Fallback to string input
        return StringFieldWidget(field)
    
    def get_data(self) -> Dict[str, Any]:
        """Get form data as dictionary"""
        data = {}
        for field_name, widget in self.field_widgets.items():
            value = widget.get_value()
            if value is not None:
                data[field_name] = value
        return data
    
    def set_data(self, data: Dict[str, Any]):
        """Set form data from dictionary"""
        for field_name, widget in self.field_widgets.items():
            if field_name in data:
                widget.set_value(data[field_name])
    
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate all fields"""
        errors = []
        for widget in self.field_widgets.values():
            if not widget.is_valid():
                error = widget.get_validation_error()
                if error:
                    errors.append(error)
        return len(errors) == 0, errors


class McdocFormGenerator(QMainWindow):
    """Main application window"""
    
    def __init__(self):
        super().__init__()
        self.project = None
        self.current_struct = None
        self.current_form = None
        self.setup_ui()
    
    def setup_ui(self):
        self.setWindowTitle("Mcdoc Form Generator")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget with splitter
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(splitter)
        
        # Left panel - project structure
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel - form area
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        # Set splitter proportions
        splitter.setSizes([300, 900])
    
    def _create_left_panel(self) -> QWidget:
        """Create the left panel with project controls and structure tree"""
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        
        # Project controls
        project_controls = QHBoxLayout()
        
        self.load_project_button = QPushButton("Load Project")
        self.load_project_button.clicked.connect(self.load_project)
        project_controls.addWidget(self.load_project_button)
        
        self.load_file_button = QPushButton("Load File")
        self.load_file_button.clicked.connect(self.load_file)
        project_controls.addWidget(self.load_file_button)
        
        left_layout.addLayout(project_controls)
        
        # Structure tree
        self.structure_tree = QTreeWidget()
        self.structure_tree.setHeaderLabel("Project Structure")
        self.structure_tree.itemClicked.connect(self.on_item_clicked)
        left_layout.addWidget(self.structure_tree)
        
        return left_panel
    
    def _create_right_panel(self) -> QWidget:
        """Create the right panel with form controls and form area"""
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        
        # Form controls
        form_controls = self._create_form_controls()
        right_layout.addLayout(form_controls)
        
        # Form area
        self.form_area = QScrollArea()
        self.form_area.setWidgetResizable(True)
        right_layout.addWidget(self.form_area)
        
        return right_panel
    
    def _create_form_controls(self) -> QHBoxLayout:
        """Create form control buttons"""
        form_controls = QHBoxLayout()
        
        self.export_json_button = QPushButton("Export JSON")
        self.export_json_button.clicked.connect(self.export_json)
        self.export_json_button.setEnabled(False)
        form_controls.addWidget(self.export_json_button)
        
        self.import_json_button = QPushButton("Import JSON")
        self.import_json_button.clicked.connect(self.import_json)
        self.import_json_button.setEnabled(False)
        form_controls.addWidget(self.import_json_button)
        
        self.validate_button = QPushButton("Validate")
        self.validate_button.clicked.connect(self.validate_form)
        self.validate_button.setEnabled(False)
        form_controls.addWidget(self.validate_button)
        
        form_controls.addStretch()
        return form_controls
    
    def load_project(self):
        """Load a project directory"""
        directory = QFileDialog.getExistingDirectory(self, "Select Project Directory")
        if not directory:
            return
        
        try:
            self.project = McdocProject(directory)
            self.project.load_project()
            self._update_ui_after_load(f"Mcdoc Form Generator - {directory}")
        except Exception as e:
            self._show_error("Failed to load project", str(e))
    
    def load_file(self):
        """Load a single mcdoc file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Mcdoc File", "", "Mcdoc Files (*.mcdoc)"
        )
        if not file_path:
            return
        
        try:
            # Create a project with just this file
            file_path_obj = Path(file_path)
            self.project = McdocProject(str(file_path_obj.parent))
            
            # Load the single file
            file_data = self.project.load_file(file_path_obj)
            self.project.files[file_path_obj.name] = file_data
            self.project.resolve_types()
            
            self._update_ui_after_load(f"Mcdoc Form Generator - {file_path}")
        except Exception as e:
            self._show_error("Failed to load file", str(e))
    
    def _update_ui_after_load(self, window_title: str):
        """Update UI after successfully loading project or file"""
        self.populate_structure_tree()
        self.setWindowTitle(window_title)
    
    def _show_error(self, title: str, message: str):
        """Show error message dialog"""
        QMessageBox.critical(self, "Error", f"{title}: {message}")
    
    def _show_success(self, message: str):
        """Show success message dialog"""
        QMessageBox.information(self, "Success", message)
    
    def populate_structure_tree(self):
        """Populate the structure tree with project data"""
        self.structure_tree.clear()
        
        if not self.project:
            return
        
        # Add struct types
        self._add_tree_section("Structs", self.project.get_struct_types(), "struct")
        
        # Add enum types
        self._add_tree_section("Enums", self.project.get_enum_types(), "enum")
        
        self.structure_tree.expandAll()
    
    def _add_tree_section(self, section_name: str, items: Dict[str, Any], item_type: str):
        """Add a section to the structure tree"""
        if not items:
            return
        
        section_root = QTreeWidgetItem(self.structure_tree, [section_name])
        for name, item_data in items.items():
            item = QTreeWidgetItem(section_root, [name])
            item.setData(0, Qt.UserRole, (item_type, name, item_data))
    
    def on_item_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle item click in structure tree"""
        data = item.data(0, Qt.UserRole)
        if data and data[0] == "struct":
            self.show_struct_form(data[2])
    
    def show_struct_form(self, struct_type: StructType):
        """Show form for editing a struct"""
        self.current_struct = struct_type
        self.current_form = StructFormWidget(struct_type, self.project)
        self.form_area.setWidget(self.current_form)
        
        # Enable form controls
        self._set_form_controls_enabled(True)
    
    def _set_form_controls_enabled(self, enabled: bool):
        """Enable or disable form control buttons"""
        self.export_json_button.setEnabled(enabled)
        self.import_json_button.setEnabled(enabled)
        self.validate_button.setEnabled(enabled)
    
    def export_json(self):
        """Export current form data as JSON"""
        if not self.current_form:
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export JSON", "", "JSON Files (*.json)"
        )
        if not file_path:
            return
        
        try:
            data = self.current_form.get_data()
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            self._show_success("Data exported successfully!")
        except Exception as e:
            self._show_error("Failed to export JSON", str(e))
    
    def import_json(self):
        """Import JSON data into current form"""
        if not self.current_form:
            return
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import JSON", "", "JSON Files (*.json)"
        )
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.current_form.set_data(data)
            self._show_success("Data imported successfully!")
        except Exception as e:
            self._show_error("Failed to import JSON", str(e))
    
    def validate_form(self):
        """Validate current form"""
        if not self.current_form:
            return
        
        is_valid, errors = self.current_form.validate()
        if is_valid:
            self._show_success("Form is valid!")
        else:
            error_message = "Validation errors:\n\n" + "\n".join(errors)
            QMessageBox.warning(self, "Validation Errors", error_message)

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    
    # Set application properties
    app.setApplicationName("Mcdoc Form Generator")
    app.setApplicationVersion("1.0.0")
    
    # Create and show main window
    window = McdocFormGenerator()
    window.show()
    
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())