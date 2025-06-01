from abc import ABC, abstractmethod
import html
from mcdoc_types import *

# ============================================================================
# HTML Form Generator
# ============================================================================

class FormGenerator(ABC):
    """Abstract base class for form generators"""
    
    @abstractmethod
    def generate(self, mcdoc_type: McdocType, name: str = "root") -> str:
        pass


class HTMLFormGenerator(FormGenerator):
    """Generates HTML forms from Mcdoc types"""
    
    def __init__(self):
        self.form_id_counter = 0
    
    def _next_id(self) -> str:
        self.form_id_counter += 1
        return f"field_{self.form_id_counter}"
    
    def generate(self, mcdoc_type: McdocType, name: str = "root") -> str:
        """Generate complete HTML form"""
        form_content = self._generate_field(mcdoc_type, name, self._next_id())
        
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mcdoc Form</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .form-container {{ max-width: 800px; margin: 0 auto; }}
        .field-group {{ margin-bottom: 15px; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .field-label {{ font-weight: bold; margin-bottom: 5px; display: block; }}
        .field-input {{ width: 100%; padding: 8px; border: 1px solid #ccc; border-radius: 3px; }}
        .optional {{ color: #666; font-style: italic; }}
        .union-selector {{ margin-bottom: 10px; }}
        .list-container {{ border: 1px solid #eee; padding: 10px; margin: 5px 0; }}
        .list-item {{ background: #f9f9f9; padding: 5px; margin: 5px 0; border-radius: 3px; }}
        .add-button, .remove-button {{ padding: 5px 10px; margin: 2px; border: none; border-radius: 3px; cursor: pointer; }}
        .add-button {{ background: #4CAF50; color: white; }}
        .remove-button {{ background: #f44336; color: white; }}
        .struct-container {{ background: #fafafa; padding: 15px; margin: 10px 0; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="form-container">
        <h1>Generated Form</h1>
        <form id="mcdoc-form">
            {form_content}
            <div style="margin-top: 20px;">
                <button type="button" onclick="generateJSON()">Generate JSON</button>
                <button type="button" onclick="validateForm()">Validate</button>
            </div>
        </form>
        <div id="output" style="margin-top: 20px; padding: 10px; background: #f0f0f0; display: none;">
            <h3>Generated JSON:</h3>
            <pre id="json-output"></pre>
        </div>
    </div>
    
    <script>
        function generateJSON() {{
            const form = document.getElementById('mcdoc-form');
            const formData = new FormData(form);
            const result = {{}};
            
            for (let [key, value] of formData.entries()) {{
                result[key] = value;
            }}
            
            document.getElementById('json-output').textContent = JSON.stringify(result, null, 2);
            document.getElementById('output').style.display = 'block';
        }}
        
        function validateForm() {{
            // TODO: Implement validation logic
            alert('Validation functionality not yet implemented');
        }}
        
        function addListItem(containerId, template) {{
            const container = document.getElementById(containerId);
            const newItem = document.createElement('div');
            newItem.innerHTML = template;
            container.appendChild(newItem);
        }}
        
        function removeListItem(button) {{
            button.parentElement.remove();
        }}
    </script>
</body>
</html>"""
    
    def _generate_field(self, mcdoc_type: McdocType, name: str, field_id: str) -> str:
        """Generate HTML for a specific field type"""
        if isinstance(mcdoc_type, AnyType):
            return self._generate_any_field(name, field_id)
        elif isinstance(mcdoc_type, BooleanType):
            return self._generate_boolean_field(name, field_id)
        elif isinstance(mcdoc_type, StringType):
            return self._generate_string_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, NumericType):
            return self._generate_numeric_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, LiteralType):
            return self._generate_literal_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, ListType):
            return self._generate_list_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, TupleType):
            return self._generate_tuple_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, StructType):
            return self._generate_struct_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, UnionType):
            return self._generate_union_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, ReferenceType):
            return self._generate_reference_field(name, field_id, mcdoc_type)
        else:
            return f'<div class="field-group">Unsupported type: {type(mcdoc_type).__name__}</div>'
    
    def _generate_any_field(self, name: str, field_id: str) -> str:
        return f'''<div class="field-group">
            <label class="field-label" for="{field_id}">{html.escape(name)} (any type)</label>
            <textarea id="{field_id}" name="{name}" class="field-input" placeholder="Enter any value (JSON format)"></textarea>
        </div>'''
    
    def _generate_boolean_field(self, name: str, field_id: str) -> str:
        return f'''<div class="field-group">
            <label class="field-label">{html.escape(name)}</label>
            <label><input type="radio" name="{name}" value="true"> True</label>
            <label><input type="radio" name="{name}" value="false"> False</label>
        </div>'''
    
    def _generate_string_field(self, name: str, field_id: str, string_type: StringType) -> str:
        constraints = ""
        if string_type.length_range:
            min_len, max_len = string_type.length_range
            if min_len is not None:
                constraints += f' minlength="{min_len}"'
            if max_len is not None:
                constraints += f' maxlength="{max_len}"'
        
        return f'''<div class="field-group">
            <label class="field-label" for="{field_id}">{html.escape(name)}</label>
            <input type="text" id="{field_id}" name="{name}" class="field-input"{constraints}>
        </div>'''
    
    def _generate_numeric_field(self, name: str, field_id: str, numeric_type: NumericType) -> str:
        input_type = "number"
        step = "1" if numeric_type.type_name in ['byte', 'short', 'int', 'long'] else "any"
        
        constraints = f' step="{step}"'
        if numeric_type.range:
            min_val, max_val = numeric_type.range
            if min_val is not None:
                constraints += f' min="{min_val}"'
            if max_val is not None:
                constraints += f' max="{max_val}"'
        
        return f'''<div class="field-group">
            <label class="field-label" for="{field_id}">{html.escape(name)} ({numeric_type.type_name})</label>
            <input type="{input_type}" id="{field_id}" name="{name}" class="field-input"{constraints}>
        </div>'''
    
    def _generate_literal_field(self, name: str, field_id: str, literal_type: LiteralType) -> str:
        return f'''<div class="field-group">
            <label class="field-label">{html.escape(name)} (literal)</label>
            <input type="text" value="{html.escape(str(literal_type.value))}" readonly class="field-input">
            <input type="hidden" name="{name}" value="{html.escape(str(literal_type.value))}">
        </div>'''
    
    def _generate_list_field(self, name: str, field_id: str, list_type: ListType) -> str:
        item_template = self._generate_field(list_type.element_type, f"{name}[]", f"{field_id}_item")
        
        return f'''<div class="field-group">
            <label class="field-label">{html.escape(name)} (list)</label>
            <div class="list-container" id="{field_id}_container">
                <div class="list-item">
                    {item_template}
                    <button type="button" class="remove-button" onclick="removeListItem(this)">Remove</button>
                </div>
            </div>
            <button type="button" class="add-button" onclick="addListItem('{field_id}_container', `{html.escape(item_template)}`)">Add Item</button>
        </div>'''
    
    def _generate_tuple_field(self, name: str, field_id: str, tuple_type: TupleType) -> str:
        fields_html = ""
        for i, element_type in enumerate(tuple_type.elements):
            element_html = self._generate_field(element_type, f"{name}[{i}]", f"{field_id}_{i}")
            fields_html += f'<div class="list-item">{element_html}</div>'
        
        return f'''<div class="field-group">
            <label class="field-label">{html.escape(name)} (tuple)</label>
            <div class="list-container">
                {fields_html}
            </div>
        </div>'''
    
    def _generate_struct_field(self, name: str, field_id: str, struct_type: StructType) -> str:
        fields_html = ""
        for field in struct_type.fields:
            field_html = self._generate_field(field.type, f"{name}.{field.name}", f"{field_id}_{field.name}")
            optional_text = " <span class='optional'>(optional)</span>" if field.optional else ""
            fields_html += f'<div class="field-group">{field_html.replace(field.name, field.name + optional_text)}</div>'
        
        return f'''<div class="struct-container">
            <h3>{html.escape(name)}</h3>
            {fields_html}
        </div>'''
    
    def _generate_union_field(self, name: str, field_id: str, union_type: UnionType) -> str:
        options_html = ""
        for i, union_option in enumerate(union_type.types):
            option_html = self._generate_field(union_option, name, f"{field_id}_option_{i}")
            options_html += f'<div id="{field_id}_option_{i}_container" style="display: none;">{option_html}</div>'
        
        selector_html = f'<select class="union-selector" onchange="showUnionOption(this, \'{field_id}\')">'
        selector_html += '<option value="">Select type...</option>'
        for i, union_option in enumerate(union_type.types):
            type_name = type(union_option).__name__.replace('Type', '').lower()
            selector_html += f'<option value="{i}">{type_name}</option>'
        selector_html += '</select>'
        
        return f'''<div class="field-group">
            <label class="field-label">{html.escape(name)} (union)</label>
            {selector_html}
            {options_html}
        </div>
        <script>
            function showUnionOption(select, fieldId) {{
                const containers = document.querySelectorAll(`[id^="${field_id}_option_"][id$="_container"]`);
                containers.forEach(c => c.style.display = 'none');
                
                if (select.value !== '') {{
                    document.getElementById(`${field_id}_option_${select.value}_container`).style.display = 'block';
                }}
            }}
        </script>'''
    
    def _generate_reference_field(self, name: str, field_id: str, ref_type: ReferenceType) -> str:
        return f'''<div class="field-group">
            <label class="field-label">{html.escape(name)} (reference to {ref_type.path})</label>
            <input type="text" id="{field_id}" name="{name}" class="field-input" placeholder="Reference: {ref_type.path}">
        </div>'''