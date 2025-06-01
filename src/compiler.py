from typing import Dict, List, Optional

from mcdoc_types import *
from parser import McdocLexer, McdocParser
from form_generator import HTMLFormGenerator

# ============================================================================
# Enhanced Compiler Class with Advanced Features
# ============================================================================

class McdocCompiler:
    """Enhanced compiler class that orchestrates parsing and form generation with advanced features"""
    
    def __init__(self):
        self.type_registry: Dict[str, McdocType] = {}
        self.module_registry: Dict[str, ModuleType] = {}
        self.enum_registry: Dict[str, EnumType] = {}
        self.form_generator = HTMLFormGenerator()
        self.current_version = "1.0.0"
    
    def compile_file(self, file_path: str) -> str:
        """Compile a single Mcdoc file to HTML form"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.compile_string(content)
    
    def compile_string(self, mcdoc_content: str) -> str:
        """Compile Mcdoc string content to HTML form with enhanced features"""
        # Tokenize
        lexer = McdocLexer(mcdoc_content)
        
        # Parse
        parser = McdocParser(lexer.tokens)
        parser.type_registry = self.type_registry
        parser.current_version = self.current_version
        
        # Enhanced parsing - look for multiple definition types
        struct_types = []
        enum_types = []
        module_types = []
        
        while parser.current_token:
            # Skip doc comments at top level
            while parser.match('DOC_COMMENT'):
                parser.advance()
            
            if parser.match('KEYWORD'):
                keyword = parser.current_token[1]
                
                if keyword == 'struct':
                    struct_data = self._parse_struct_definition(parser)
                    if struct_data:
                        struct_types.append(struct_data)
                        
                elif keyword == 'enum':
                    enum_data = self._parse_enum_definition(parser)
                    if enum_data:
                        enum_types.append(enum_data)
                        
                elif keyword == 'module':
                    module_data = self._parse_module_definition(parser)
                    if module_data:
                        module_types.append(module_data)
                        
                elif keyword == 'type':
                    type_alias = self._parse_type_alias(parser)
                    if type_alias:
                        name, type_def = type_alias
                        self.type_registry[name] = type_def
                        
                else:
                    parser.advance()
                    
            elif parser.match('IDENTIFIER') and parser.current_token[1] == 'struct':
                # Legacy struct parsing for backwards compatibility
                parser.advance()  # consume 'struct'
                if not parser.current_token:
                    break
                struct_name = parser.expect('IDENTIFIER')
                struct_type = parser.parse_struct()
                struct_types.append((struct_name, struct_type))
                self.type_registry[struct_name] = struct_type
            else:
                if parser.current_token:
                    parser.advance()
        
        # Store all parsed types in registries
        for name, struct_type in struct_types:
            self.type_registry[name] = struct_type
        
        for name, enum_type in enum_types:
            self.enum_registry[name] = enum_type
            self.type_registry[name] = enum_type
        
        for name, module_type in module_types:
            self.module_registry[name] = module_type
            self.type_registry[name] = module_type
        
        # Update form generator with registries
        self.form_generator.type_registry = self.type_registry
        self.form_generator.enum_registry = self.enum_registry
        
        # Generate form for the first struct found
        if struct_types:
            struct_name, struct_type = struct_types[0]
            return self.form_generator.generate(struct_type, struct_name)
        elif enum_types:
            enum_name, enum_type = enum_types[0]
            return self.form_generator.generate(enum_type, enum_name)
        else:
            return self._generate_empty_form()
    
    def _parse_struct_definition(self, parser: McdocParser) -> Optional[tuple]:
        """Parse struct definition with enhanced features"""
        try:
            parser.advance()  # consume 'struct'
            if not parser.current_token:
                return None
                
            struct_name = parser.expect('IDENTIFIER')
            
            # Handle generic type parameters
            type_params = []
            if parser.match('LANGLE'):
                parser.advance()  # consume <
                type_params.append(parser.expect('IDENTIFIER'))
                
                while parser.match('COMMA'):
                    parser.advance()  # consume ,
                    type_params.append(parser.expect('IDENTIFIER'))
                
                parser.expect('RANGLE')
            
            # Handle inheritance
            extends = []
            if parser.match('KEYWORD', 'extends'):
                parser.advance()  # consume 'extends'
                extends.append(parser.expect('IDENTIFIER'))
                
                while parser.match('COMMA'):
                    parser.advance()  # consume ,
                    extends.append(parser.expect('IDENTIFIER'))
            
            # Handle interfaces
            implements = []
            if parser.match('KEYWORD', 'implements'):
                parser.advance()  # consume 'implements'
                implements.append(parser.expect('IDENTIFIER'))
                
                while parser.match('COMMA'):
                    parser.advance()  # consume ,
                    implements.append(parser.expect('IDENTIFIER'))
            
            struct_type = parser.parse_struct()
            
            # Create enhanced struct type if needed
            if type_params or extends or implements:
                enhanced_struct = NestedStructType(
                    base_struct=struct_type,
                    extends=extends,
                    implements=implements,
                    fields=struct_type.fields
                )
                return (struct_name, enhanced_struct)
            else:
                return (struct_name, struct_type)
                
        except Exception as e:
            print(f"Error parsing struct: {e}")
            return None
    
    def _parse_enum_definition(self, parser: McdocParser) -> Optional[tuple]:
        """Parse enum definition"""
        try:
            parser.advance()  # consume 'enum'
            if not parser.current_token:
                return None
                
            enum_name = parser.expect('IDENTIFIER')
            parser.expect('LBRACE')
            
            values = []
            doc_comments = {}
            
            while not parser.match('RBRACE') and parser.current_token:
                # Parse doc comment
                doc_comment = None
                if parser.match('DOC_COMMENT'):
                    doc_comment = parser.current_token[1][3:].strip()
                    parser.advance()
                
                if parser.match('IDENTIFIER'):
                    value_name = parser.expect('IDENTIFIER')
                    values.append(value_name)
                    
                    if doc_comment:
                        doc_comments[value_name] = doc_comment
                    
                    if parser.match('COMMA'):
                        parser.advance()
                else:
                    break
            
            parser.expect('RBRACE')
            
            enum_type = EnumType(enum_name, values, doc_comments)
            return (enum_name, enum_type)
            
        except Exception as e:
            print(f"Error parsing enum: {e}")
            return None
    
    def _parse_module_definition(self, parser: McdocParser) -> Optional[tuple]:
        """Parse module definition"""
        try:
            parser.advance()  # consume 'module'
            if not parser.current_token:
                return None
                
            module_name = parser.expect('IDENTIFIER')
            parser.expect('LBRACE')
            
            module_types = {}
            exports = []
            
            while not parser.match('RBRACE') and parser.current_token:
                if parser.match('KEYWORD', 'export'):
                    parser.advance()  # consume 'export'
                    export_name = parser.expect('IDENTIFIER')
                    exports.append(export_name)
                    
                    if parser.match('COMMA'):
                        parser.advance()
                elif parser.match('KEYWORD', 'struct'):
                    struct_data = self._parse_struct_definition(parser)
                    if struct_data:
                        name, struct_type = struct_data
                        module_types[name] = struct_type
                elif parser.match('KEYWORD', 'enum'):
                    enum_data = self._parse_enum_definition(parser)
                    if enum_data:
                        name, enum_type = enum_data
                        module_types[name] = enum_type
                else:
                    parser.advance()
            
            parser.expect('RBRACE')
            
            module_type = ModuleType(module_name, module_types, exports)
            return (module_name, module_type)
            
        except Exception as e:
            print(f"Error parsing module: {e}")
            return None
    
    def _parse_type_alias(self, parser: McdocParser) -> Optional[tuple]:
        """Parse type alias definition"""
        try:
            parser.advance()  # consume 'type'
            if not parser.current_token:
                return None
                
            alias_name = parser.expect('IDENTIFIER')
            parser.expect('EQUALS')
            alias_type = parser.parse_type()
            
            return (alias_name, alias_type)
            
        except Exception as e:
            print(f"Error parsing type alias: {e}")
            return None
    
    def set_version(self, version: str):
        """Set the current version for version-aware parsing"""
        self.current_version = version
    
    def resolve_reference(self, ref: ReferenceType) -> Optional[McdocType]:
        """Resolve a reference type to its actual type"""
        if ref.path in self.type_registry:
            return self.type_registry[ref.path]
        
        # Handle module references (module::type)
        if '::' in ref.path:
            module_name, type_name = ref.path.split('::', 1)
            if module_name in self.module_registry:
                module = self.module_registry[module_name]
                if type_name in module.types:
                    return module.types[type_name]
        
        return None
    
    def _generate_empty_form(self) -> str:
        """Generate a basic form when no structures are found"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mcdoc Form</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .error { color: #d63384; background: #f8d7da; padding: 15px; border-radius: 5px; border: 1px solid #f5c2c7; }
    </style>
</head>
<body>
    <div class="container">
        <h1>No Valid Mcdoc Structures Found</h1>
        <div class="error">
            <strong>Error:</strong> Please provide a valid Mcdoc file with struct, enum, or module definitions.
            <br><br>
            <strong>Supported structures:</strong>
            <ul>
                <li><code>struct MyStruct { ... }</code></li>
                <li><code>enum MyEnum { ... }</code></li>
                <li><code>module MyModule { ... }</code></li>
                <li><code>type MyType = ...</code></li>
            </ul>
        </div>
    </div>
</body>
</html>"""