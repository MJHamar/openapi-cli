"""
Parameter Parser for OpenAPI CLI Tool - Handles complex schema parsing and input collection
"""

from typing import Dict, List, Any, Optional, Union, Tuple
import json
import re


class ParameterParser:
    """Handles parsing of OpenAPI parameters and schemas into a structured format"""
    
    def __init__(self, openapi_version: str = "3.0.0", spec: Optional[Dict[str, Any]] = None):
        self.openapi_version = openapi_version
        self.spec = spec or {}
    
    def parse_parameter(self, param: Dict[str, Any]) -> List['ParsedParameter']:
        """
        Parse a parameter definition into a list of ParsedParameter objects.
        
        Args:
            param: Parameter definition from OpenAPI spec
            
        Returns:
            List of ParsedParameter objects (can be multiple for complex objects)
        """
        param_name = param.get('name', 'unknown')
        param_in = param.get('in', 'query')
        required = param.get('required', False)
        description = param.get('description', 'No description')
        
        # Get schema - different locations in OpenAPI 2.0 vs 3.x
        schema = self._get_parameter_schema(param)
        
        if not schema:
            # Simple parameter without schema
            param_type = param.get('type', 'string')
            return [ParsedParameter(
                name=param_name,
                location=param_in,
                required=required,
                param_type=param_type,
                description=description,
                schema=schema
            )]
        
        # Parse schema recursively
        return self._parse_schema(param_name, schema, param_in, required, description)
    
    def _resolve_ref(self, ref: str) -> Optional[Dict[str, Any]]:
        """Resolve a $ref reference in the OpenAPI specification"""
        if not ref.startswith('#/'):
            return None
        
        # Remove the '#/' prefix and split by '/'
        path_parts = ref[2:].split('/')
        
        # Navigate through the spec
        current = self.spec
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return None
        
        return current if isinstance(current, dict) else None
    
    def _get_parameter_schema(self, param: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract schema from parameter definition"""
        if 'schema' in param:
            # OpenAPI 3.x
            return param['schema']
        elif param.get('type'):
            # OpenAPI 2.0 - create schema from type info
            schema = {'type': param['type']}
            if 'format' in param:
                schema['format'] = param['format']
            if 'items' in param:
                schema['items'] = param['items']
            if 'properties' in param:
                schema['properties'] = param['properties']
            return schema
        return None
    
    def _parse_schema(self, base_name: str, schema: Dict[str, Any], location: str, 
                     required: bool, description: str, path: str = "") -> List['ParsedParameter']:
        """
        Recursively parse a JSON schema into ParsedParameter objects.
        
        Args:
            base_name: Base parameter name
            schema: JSON schema to parse
            location: Parameter location (query, path, header, body)
            required: Whether the parameter is required
            description: Parameter description
            path: Current path in nested structure (e.g., "user.address.street")
            
        Returns:
            List of ParsedParameter objects
        """
        # Resolve $ref if present
        if '$ref' in schema:
            resolved_schema = self._resolve_ref(schema['$ref'])
            if resolved_schema:
                schema = resolved_schema
            else:
                # If we can't resolve the ref, treat it as a generic object
                current_name = f"{base_name}.{path}" if path else base_name
                return [ParsedParameter(
                    name=current_name,
                    location=location,
                    required=required,
                    param_type='object',
                    description=f"{description} (unresolved reference: {schema['$ref']})",
                    schema=schema
                )]
        
        param_type = schema.get('type', 'string')
        current_name = f"{base_name}.{path}" if path else base_name
        
        if param_type == 'object':
            return self._parse_object_schema(base_name, schema, location, required, description, path)
        elif param_type == 'array':
            return self._parse_array_schema(base_name, schema, location, required, description, path)
        else:
            # Primitive type
            return [ParsedParameter(
                name=current_name,
                location=location,
                required=required,
                param_type=param_type,
                description=description,
                schema=schema,
                format=schema.get('format'),
                enum=schema.get('enum')
            )]
    
    def _parse_object_schema(self, base_name: str, schema: Dict[str, Any], location: str,
                           required: bool, description: str, path: str = "") -> List['ParsedParameter']:
        """Parse object schema recursively"""
        parsed_params = []
        properties = schema.get('properties', {})
        required_props = schema.get('required', [])
        
        for prop_name, prop_schema in properties.items():
            prop_path = f"{path}.{prop_name}" if path else prop_name
            prop_required = prop_name in required_props
            prop_description = prop_schema.get('description', f'Property of {base_name}')
            
            parsed_params.extend(
                self._parse_schema(base_name, prop_schema, location, prop_required, prop_description, prop_path)
            )
        
        return parsed_params
    
    def _parse_array_schema(self, base_name: str, schema: Dict[str, Any], location: str,
                          required: bool, description: str, path: str = "") -> List['ParsedParameter']:
        """Parse array schema"""
        current_name = f"{base_name}.{path}" if path else base_name
        items_schema = schema.get('items', {'type': 'string'})
        
        # Resolve $ref in items if present
        if '$ref' in items_schema:
            resolved_items = self._resolve_ref(items_schema['$ref'])
            if resolved_items:
                items_schema = resolved_items
        
        items_type = items_schema.get('type', 'unknown')
        description_with_type = f"{description} (array of {items_type})"
        
        # For arrays, we create a special parameter that indicates it's an array
        return [ParsedParameter(
            name=current_name,
            location=location,
            required=required,
            param_type='array',
            description=description_with_type,
            schema=schema,
            items_schema=items_schema
        )]


class ParsedParameter:
    """Represents a parsed parameter with all necessary information"""
    
    def __init__(self, name: str, location: str, required: bool, param_type: str,
                 description: str, schema: Optional[Dict[str, Any]] = None,
                 format: Optional[str] = None, enum: Optional[List[Any]] = None,
                 items_schema: Optional[Dict[str, Any]] = None):
        self.name = name
        self.location = location
        self.required = required
        self.param_type = param_type
        self.description = description
        self.schema = schema
        self.format = format
        self.enum = enum
        self.items_schema = items_schema
        
        # For nested parameters, extract the final field name
        self.display_name = name.split('.')[-1] if '.' in name else name
        self.is_nested = '.' in name
    
    def get_type_display(self) -> str:
        """Get a human-readable type display"""
        if self.enum:
            return f"{self.param_type} (enum: {', '.join(map(str, self.enum))})"
        elif self.format:
            return f"{self.param_type}({self.format})"
        elif self.param_type == 'array' and self.items_schema:
            items_type = self.items_schema.get('type', 'unknown')
            return f"array<{items_type}>"
        else:
            return self.param_type
    
    def collect_input(self) -> Any:
        """
        Collect input for this parameter from the user.
        
        Returns:
            The collected value, properly typed
        """
        if self.param_type == 'array':
            return self._collect_array_input()
        else:
            return self._collect_simple_input()
    
    def _collect_simple_input(self) -> Any:
        """Collect input for a simple (non-array) parameter"""
        prompt = f"Enter {self.display_name} ({self.get_type_display()})"
        if not self.required:
            prompt += " [optional]"
        prompt += ": "
        
        value = input(prompt).strip()
        
        if not value and not self.required:
            return None
        
        # Type conversion
        return self._convert_value(value)
    
    def _collect_array_input(self) -> List[Any]:
        """Collect input for an array parameter"""
        print(f"Enter values for {self.display_name} (array). Press Enter on empty line to finish:")
        values = []
        index = 0
        
        while True:
            try:
                value = input(f"  [{index}]: ").strip()
                if not value:
                    break
                
                converted_value = self._convert_array_item(value)
                values.append(converted_value)
                index += 1
                
            except KeyboardInterrupt:
                print("\nArray input cancelled.")
                break
            except EOFError:
                break
        
        return values
    
    def _convert_value(self, value: str) -> Any:
        """Convert string input to appropriate type"""
        if not value:
            return None
            
        if self.param_type == 'boolean':
            return value.lower() in ('true', '1', 'yes', 'y', 'on')
        elif self.param_type == 'integer':
            try:
                return int(value)
            except ValueError:
                print(f"Warning: '{value}' is not a valid integer, using as string")
                return value
        elif self.param_type == 'number':
            try:
                return float(value)
            except ValueError:
                print(f"Warning: '{value}' is not a valid number, using as string")
                return value
        else:
            return value
    
    def _convert_array_item(self, value: str) -> Any:
        """Convert array item based on items schema"""
        if not self.items_schema:
            return value
        
        item_type = self.items_schema.get('type', 'string')
        
        if item_type == 'boolean':
            return value.lower() in ('true', '1', 'yes', 'y', 'on')
        elif item_type == 'integer':
            try:
                return int(value)
            except ValueError:
                print(f"Warning: '{value}' is not a valid integer, using as string")
                return value
        elif item_type == 'number':
            try:
                return float(value)
            except ValueError:
                print(f"Warning: '{value}' is not a valid number, using as string")
                return value
        else:
            return value
    
    def __str__(self) -> str:
        status = "required" if self.required else "optional"
        return f"{self.name} ({self.get_type_display()}) - {status}: {self.description}"


class ParameterCollector:
    """Handles the collection and organization of parameter values"""
    
    def __init__(self):
        self.values: Dict[str, Any] = {}
    
    def collect_parameters(self, parsed_params: List[ParsedParameter], 
                         existing_values: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Collect values for all parameters interactively.
        
        Args:
            parsed_params: List of parsed parameters
            existing_values: Pre-existing parameter values
            
        Returns:
            Dictionary of collected parameter values
        """
        if existing_values:
            self.values.update(existing_values)
        
        # Group parameters by location and requirement
        required_params = [p for p in parsed_params if p.required and p.name not in self.values]
        optional_params = [p for p in parsed_params if not p.required and p.name not in self.values]
        
        # Collect required parameters
        if required_params:
            print("Required parameters:")
            for param in required_params:
                try:
                    value = param.collect_input()
                    if value is not None:
                        self.values[param.name] = value
                except (KeyboardInterrupt, EOFError):
                    print(f"\nSkipping parameter {param.name}")
                    break
        
        # Ask about optional parameters
        if optional_params:
            response = input(f"\nThere are {len(optional_params)} optional parameters. Collect them? (y/N): ").strip()
            if response.lower().startswith('y'):
                print("Optional parameters:")
                for param in optional_params:
                    try:
                        value = param.collect_input()
                        if value is not None:
                            self.values[param.name] = value
                    except (KeyboardInterrupt, EOFError):
                        print(f"\nSkipping parameter {param.name}")
                        break
        
        return self.values.copy()
    
    def build_request_data(self, parsed_params: List[ParsedParameter]) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, str], Any]:
        """
        Build request components from collected values.
        
        Returns:
            Tuple of (path_params, query_params, headers, body)
        """
        path_params = {}
        query_params = {}
        headers = {}
        body_parts = {}
        
        for param in parsed_params:
            if param.name not in self.values:
                continue
                
            value = self.values[param.name]
            
            if param.location == 'path':
                # For nested parameters, use the base name for path substitution
                base_name = param.name.split('.')[0]
                path_params[base_name] = value
            elif param.location == 'query':
                # For nested parameters, flatten or use dot notation
                query_params[param.name] = value
            elif param.location == 'header':
                headers[param.name] = str(value)
            elif param.location == 'body':
                # Build nested body structure
                self._set_nested_value(body_parts, param.name, value)
        
        # If we have body parts, construct the body
        body = body_parts if body_parts else None
        
        return path_params, query_params, headers, body
    
    def _set_nested_value(self, target: Dict[str, Any], path: str, value: Any):
        """Set a nested value in a dictionary using dot notation"""
        parts = path.split('.')
        current = target
        
        # Navigate to the parent of the final key
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        
        # Set the final value
        current[parts[-1]] = value
