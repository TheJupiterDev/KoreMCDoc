from abc import ABC, abstractmethod
import html
from mcdoc_types import *

# ============================================================================
# HTML Form Generator
# ============================================================================

ADDITIONAL_CSS = """
        .map-container { border: 1px solid #eee; padding: 10px; margin: 5px 0; }
        .map-entry { background: #f9f9f9; padding: 10px; margin: 5px 0; border-radius: 3px; }
        .map-key-value { display: flex; gap: 10px; margin-bottom: 10px; }
        .conditional-field { border-left: 3px solid #007bff; padding-left: 10px; }
        .switch-selector { width: 100%; padding: 8px; margin-bottom: 10px; }
        .index-container { background: #f8f9fa; padding: 10px; border-radius: 5px; }
        .versioned-field { position: relative; }
        .version-info { color: #6c757d; font-weight: normal; }
        .nested-struct-container { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #28a745; }
        .inheritance-info { color: #6c757d; font-style: italic; display: block; margin-bottom: 10px; }
        .constraint-field { border-left: 3px solid #ffc107; padding-left: 10px; }
        .constraints-info { color: #856404; font-weight: bold; }
        .module-container { background: #e9ecef; padding: 15px; margin: 10px 0; border-radius: 5px; border: 2px solid #6c757d; }
        .module-exports { margin-bottom: 15px; padding: 5px; background: #fff; border-radius: 3px; }
        .module-type-field { margin: 10px 0; padding: 10px; background: #fff; border-radius: 5px; }
"""

class FormGenerator(ABC):
    """Abstract base class for form generators"""
    
    @abstractmethod
    def generate(self, mcdoc_type: McdocType, name: str = "root") -> str:
        pass


class HTMLFormGenerator(FormGenerator):
    """Generates HTML forms from Mcdoc types"""
    
    def __init__(self):
        self.form_id_counter = 0
        self.type_registry = {}
        self.enum_registry = {}
    
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
        .help-text {{ color: #666; font-style: italic; display: block; margin-top: 3px; }}
        {ADDITIONAL_CSS}
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
        elif isinstance(mcdoc_type, AttributeType):
            return self._generate_attribute_field(name, field_id, mcdoc_type)
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
            field_html = self._generate_field(field.type, field.name, f"{field_id}_{field.name}")
            optional_text = " <span class='optional'>(optional)</span>" if field.optional else ""
            doc_text = f' title="{html.escape(field.doc_comment)}"' if field.doc_comment else ""
            
            # Add doc comment as a tooltip and help text
            help_text = ""
            if field.doc_comment:
                help_text = f'<small class="help-text">{html.escape(field.doc_comment)}</small>'
            
            field_with_label = field_html.replace(
                f'<label class="field-label"',
                f'<label class="field-label"{doc_text}'
            ).replace(field.name, field.name + optional_text)
            
            fields_html += f'<div class="field-group">{field_with_label}{help_text}</div>'
        
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
                const containers = document.querySelectorAll(`[id^="${fieldId}_option_"][id$="_container"]`);
                containers.forEach(c => c.style.display = 'none');
                
                if (select.value !== '') {{
                    document.getElementById(`${fieldId}_option_${select.value}_container`).style.display = 'block';
                }}
            }}
        </script>'''
    
    def _generate_reference_field(self, name: str, field_id: str, ref_type: ReferenceType) -> str:
        return f'''<div class="field-group">
            <label class="field-label">{html.escape(name)} (reference to {ref_type.path})</label>
            <input type="text" id="{field_id}" name="{name}" class="field-input" placeholder="Reference: {ref_type.path}">
        </div>'''
    
    def _generate_attribute_field(self, name: str, field_id: str, attr_type: AttributeType) -> str:
        # Generate the base field with attribute info
        base_field = self._generate_field(attr_type.base_type, name, field_id)
        
        # Add attribute information as a data attribute and placeholder
        attr_info = ", ".join(attr_type.attributes)
        placeholder_addition = f" (with attributes: {attr_info})"
        
        # Modify the base field to include attribute info
        if 'placeholder="' in base_field:
            base_field = base_field.replace('placeholder="', f'placeholder="{placeholder_addition} ')
        else:
            base_field = base_field.replace('class="field-input"', f'class="field-input" placeholder="{placeholder_addition}"')
        
        return base_field

    def _generate_field(self, mcdoc_type: McdocType, name: str, field_id: str) -> str:
        """Generate HTML for a specific field type - ENHANCED VERSION"""
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
        elif isinstance(mcdoc_type, AttributeType):
            return self._generate_attribute_field(name, field_id, mcdoc_type)
        # NEW ADVANCED TYPE HANDLERS
        elif isinstance(mcdoc_type, EnumType):
            return self._generate_enum_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, MapType):
            return self._generate_map_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, ConditionalType):
            return self._generate_conditional_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, SwitchType):
            return self._generate_switch_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, IndexType):
            return self._generate_index_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, VersionedType):
            return self._generate_versioned_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, NestedStructType):
            return self._generate_nested_struct_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, GenericType):
            return self._generate_generic_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, ConstraintType):
            return self._generate_constraint_field(name, field_id, mcdoc_type)
        elif isinstance(mcdoc_type, ModuleType):
            return self._generate_module_field(name, field_id, mcdoc_type)
        else:
            return f'<div class="field-group">Unsupported type: {type(mcdoc_type).__name__}</div>'
    
    def _generate_enum_field(self, name: str, field_id: str, enum_type: EnumType) -> str:
        """Generate HTML for enum type"""
        options_html = ""
        for value in enum_type.values:
            doc_comment = enum_type.doc_comments.get(value, "")
            title_attr = f' title="{html.escape(doc_comment)}"' if doc_comment else ""
            options_html += f'<option value="{html.escape(value)}"{title_attr}>{html.escape(value)}</option>'
        
        help_text = ""
        if enum_type.doc_comments:
            help_items = [f"{k}: {v}" for k, v in enum_type.doc_comments.items()]
            help_text = f'<small class="help-text">Options: {"; ".join(help_items)}</small>'
        
        return f'''<div class="field-group">
            <label class="field-label" for="{field_id}">{html.escape(name)} (enum: {enum_type.name})</label>
            <select id="{field_id}" name="{name}" class="field-input">
                <option value="">Select {enum_type.name}...</option>
                {options_html}
            </select>
            {help_text}
        </div>'''
    
    def _generate_map_field(self, name: str, field_id: str, map_type: MapType) -> str:
        """Generate HTML for map/dictionary type"""
        key_field = self._generate_field(map_type.key_type, f"{name}_key", f"{field_id}_key")
        value_field = self._generate_field(map_type.value_type, f"{name}_value", f"{field_id}_value")
        
        return f'''<div class="field-group">
            <label class="field-label">{html.escape(name)} (map)</label>
            <div class="map-container" id="{field_id}_container">
                <div class="map-entry">
                    <div class="map-key-value">
                        <div style="display: inline-block; width: 45%;">
                            <label>Key:</label>
                            {key_field}
                        </div>
                        <div style="display: inline-block; width: 45%; margin-left: 5%;">
                            <label>Value:</label>
                            {value_field}
                        </div>
                    </div>
                    <button type="button" class="remove-button" onclick="removeMapEntry(this)">Remove</button>
                </div>
            </div>
            <button type="button" class="add-button" onclick="addMapEntry('{field_id}_container', `{html.escape(key_field + value_field)}`)">Add Entry</button>
        </div>
        <script>
            function addMapEntry(containerId, template) {{
                const container = document.getElementById(containerId);
                const newEntry = document.createElement('div');
                newEntry.className = 'map-entry';
                newEntry.innerHTML = template + '<button type="button" class="remove-button" onclick="removeMapEntry(this)">Remove</button>';
                container.appendChild(newEntry);
            }}
            
            function removeMapEntry(button) {{
                button.parentElement.remove();
            }}
        </script>'''
    
    def _generate_conditional_field(self, name: str, field_id: str, conditional_type: ConditionalType) -> str:
        """Generate HTML for conditional type"""
        base_field = self._generate_field(conditional_type.base_type, name, field_id)
        
        conditions_info = []
        for condition in conditional_type.conditions:
            if condition.type == ConditionType.IF:
                conditions_info.append(f"If: {condition.expression}")
        
        condition_text = "; ".join(conditions_info)
        help_text = f'<small class="help-text">Conditions: {html.escape(condition_text)}</small>' if conditions_info else ""
        
        return f'''<div class="conditional-field" data-conditions="{html.escape(condition_text)}">
            {base_field}
            {help_text}
        </div>'''
    
    def _generate_switch_field(self, name: str, field_id: str, switch_type: SwitchType) -> str:
        """Generate HTML for switch type"""
        # Generate discriminator selector
        discriminator_html = f'''<div class="field-group">
            <label class="field-label">Switch on {switch_type.discriminator}:</label>
            <select class="switch-selector" onchange="showSwitchCase(this, '{field_id}')">
                <option value="">Select case...</option>'''
        
        cases_html = ""
        for case_value, case_type in switch_type.cases.items():
            discriminator_html += f'<option value="{html.escape(case_value)}">{html.escape(case_value)}</option>'
            case_field = self._generate_field(case_type, name, f"{field_id}_case_{case_value}")
            cases_html += f'<div id="{field_id}_case_{case_value}_container" style="display: none;">{case_field}</div>'
        
        discriminator_html += '</select></div>'
        
        if switch_type.default_type:
            default_field = self._generate_field(switch_type.default_type, name, f"{field_id}_default")
            cases_html += f'<div id="{field_id}_default_container" style="display: none;">{default_field}</div>'
            discriminator_html = discriminator_html.replace('</select>', '<option value="default">Default</option></select>')
        
        return f'''<div class="field-group">
            <label class="field-label">{html.escape(name)} (switch)</label>
            {discriminator_html}
            {cases_html}
        </div>
        <script>
            function showSwitchCase(select, fieldId) {{
                const containers = document.querySelectorAll(`[id^="${fieldId}_case_"], [id^="${fieldId}_default_"]`);
                containers.forEach(c => c.style.display = 'none');
                
                if (select.value !== '') {{
                    const containerId = select.value === 'default' ? 
                        `${fieldId}_default_container` : 
                        `${fieldId}_case_${select.value}_container`;
                    const container = document.getElementById(containerId);
                    if (container) container.style.display = 'block';
                }}
            }}
        </script>'''
    
    def _generate_index_field(self, name: str, field_id: str, index_type: IndexType) -> str:
        """Generate HTML for index type"""
        base_field = self._generate_field(index_type.base_type, f"{name}_base", f"{field_id}_base")
        index_field = self._generate_field(index_type.index_type, f"{name}_index", f"{field_id}_index")
        
        return f'''<div class="field-group">
            <label class="field-label">{html.escape(name)} (indexed access)</label>
            <div class="index-container">
                <div style="margin-bottom: 10px;">
                    <label>Base:</label>
                    {base_field}
                </div>
                <div>
                    <label>Index:</label>
                    {index_field}
                </div>
            </div>
        </div>'''
    
    def _generate_versioned_field(self, name: str, field_id: str, versioned_type: VersionedType) -> str:
        """Generate HTML for versioned type"""
        base_field = self._generate_field(versioned_type.base_type, name, field_id)
        
        version_info = []
        if versioned_type.since:
            version_info.append(f"Since: {versioned_type.since.version}")
        if versioned_type.until:
            version_info.append(f"Until: {versioned_type.until.version}")
        
        version_text = " | ".join(version_info)
        help_text = f'<small class="help-text version-info">Version: {html.escape(version_text)}</small>' if version_info else ""
        
        return f'''<div class="versioned-field" data-version-info="{html.escape(version_text)}">
            {base_field}
            {help_text}
        </div>'''
    
    def _generate_nested_struct_field(self, name: str, field_id: str, nested_type: NestedStructType) -> str:
        """Generate HTML for nested struct type"""
        fields_html = ""
        
        # Handle inheritance info
        inheritance_info = ""
        if nested_type.extends:
            inheritance_info += f"Extends: {', '.join(nested_type.extends)} "
        if nested_type.implements:
            inheritance_info += f"Implements: {', '.join(nested_type.implements)}"
        
        # Generate fields from base struct if available
        all_fields = nested_type.fields.copy()
        if nested_type.base_struct:
            all_fields.extend(nested_type.base_struct.fields)
        
        for field in all_fields:
            field_html = self._generate_field(field.type, field.name, f"{field_id}_{field.name}")
            optional_text = " <span class='optional'>(optional)</span>" if field.optional else ""
            
            version_info = ""
            if field.since:
                version_info += f" Since: {field.since}"
            if field.until:
                version_info += f" Until: {field.until}"
            
            help_text = ""
            if field.doc_comment:
                help_text += f'<small class="help-text">{html.escape(field.doc_comment)}</small>'
            if version_info:
                help_text += f'<small class="help-text version-info">{html.escape(version_info)}</small>'
            
            field_with_label = field_html.replace(field.name, field.name + optional_text)
            fields_html += f'<div class="field-group">{field_with_label}{help_text}</div>'
        
        # Handle nested structs
        for nested_name, nested_struct in nested_type.nested_structs.items():
            nested_html = self._generate_nested_struct_field(nested_name, f"{field_id}_{nested_name}", nested_struct)
            fields_html += nested_html
        
        inheritance_html = f'<small class="help-text inheritance-info">{html.escape(inheritance_info)}</small>' if inheritance_info else ""
        
        return f'''<div class="nested-struct-container">
            <h3>{html.escape(name)}</h3>
            {inheritance_html}
            {fields_html}
        </div>'''
    
    def _generate_generic_field(self, name: str, field_id: str, generic_type: GenericType) -> str:
        """Generate HTML for generic type"""
        type_params_info = f"<{', '.join(generic_type.type_params)}>" if generic_type.type_params else ""
        bounds_info = ""
        if generic_type.bounds:
            bounds_list = [f"{k}: {type(v).__name__}" for k, v in generic_type.bounds.items()]
            bounds_info = f" where {', '.join(bounds_list)}"
        
        return f'''<div class="field-group">
            <label class="field-label" for="{field_id}">{html.escape(name)} (generic: {generic_type.name}{type_params_info})</label>
            <textarea id="{field_id}" name="{name}" class="field-input" placeholder="Generic type value (JSON format)"></textarea>
            <small class="help-text">Generic type: {html.escape(generic_type.name + type_params_info + bounds_info)}</small>
        </div>'''
    
    def _generate_constraint_field(self, name: str, field_id: str, constraint_type: ConstraintType) -> str:
        """Generate HTML for constraint type"""
        base_field = self._generate_field(constraint_type.base_type, name, field_id)
        
        constraints_text = "; ".join(constraint_type.constraints)
        help_text = f'<small class="help-text constraints-info">Constraints: {html.escape(constraints_text)}</small>'
        
        return f'''<div class="constraint-field" data-constraints="{html.escape(constraints_text)}">
            {base_field}
            {help_text}
        </div>'''
    
    def _generate_module_field(self, name: str, field_id: str, module_type: ModuleType) -> str:
        """Generate HTML for module type"""
        fields_html = ""
        
        # Show exported types
        if module_type.exports:
            exports_info = f"Exports: {', '.join(module_type.exports)}"
            fields_html += f'<div class="module-exports"><small class="help-text">{html.escape(exports_info)}</small></div>'
        
        # Generate fields for each type in the module
        for type_name, type_def in module_type.types.items():
            if type_name in module_type.exports or not module_type.exports:  # Show if exported or no export list
                type_field = self._generate_field(type_def, type_name, f"{field_id}_{type_name}")
                fields_html += f'<div class="module-type-field">{type_field}</div>'
        
        return f'''<div class="module-container">
            <h3>{html.escape(name)} (module: {module_type.name})</h3>
            {fields_html}
        </div>'''