from typing import Dict

from mcdoc_types import McdocType
from parser import McdocLexer, McdocParser
from form_generator import HTMLFormGenerator

# ============================================================================
# Main Compiler Class
# ============================================================================

class McdocCompiler:
    """Main compiler class that orchestrates parsing and form generation"""
    
    def __init__(self):
        self.type_registry: Dict[str, McdocType] = {}
        self.form_generator = HTMLFormGenerator()
    
    def compile_file(self, file_path: str) -> str:
        """Compile a single Mcdoc file to HTML form"""
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        return self.compile_string(content)
    
    def compile_string(self, mcdoc_content: str) -> str:
        """Compile Mcdoc string content to HTML form"""
        # Tokenize
        lexer = McdocLexer(mcdoc_content)
        
        # Parse
        parser = McdocParser(lexer.tokens)
        
        # Simple parsing - look for struct definitions
        struct_types = []
        
        while parser.current_token:
            # Skip doc comments at top level
            while parser.match('DOC_COMMENT'):
                parser.advance()
            
            if parser.match('IDENTIFIER') and parser.current_token[1] == 'struct':
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
        
        # Generate form for the first struct found
        if struct_types:
            struct_name, struct_type = struct_types[0]
            return self.form_generator.generate(struct_type, struct_name)
        else:
            return self._generate_empty_form()
    
    def _generate_empty_form(self) -> str:
        """Generate a basic form when no structs are found"""
        return """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mcdoc Form</title>
</head>
<body>
    <div style="padding: 20px;">
        <h1>No Valid Mcdoc Structures Found</h1>
        <p>Please provide a valid Mcdoc file with struct definitions.</p>
    </div>
</body>
</html>"""