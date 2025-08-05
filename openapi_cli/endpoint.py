"""
API Endpoint representation for OpenAPI CLI Tool
"""

from typing import Dict, List, Any, Optional, Union
import re
import requests
import json
from .parameter_parser import ParameterParser, ParsedParameter, ParameterCollector


class APIEndpoint:
    """Represents a single API endpoint from an OpenAPI specification"""
    
    def __init__(self, base_url: str, path: str, method: str, operation: Dict[str, Any], 
                 openapi_version: str = "3.0.0", spec: Optional[Dict[str, Any]] = None):
        """
        Initialize an API endpoint.
        
        Args:
            base_url: Base URL of the API
            path: Endpoint path (e.g., "/pets/{id}")
            method: HTTP method (GET, POST, etc.)
            operation: OpenAPI operation object
            openapi_version: OpenAPI specification version
            spec: Full OpenAPI specification for resolving references
        """
        self.base_url = base_url.rstrip('/')
        self.path = path
        self.method = method.upper()
        self.operation = operation
        self.openapi_version = openapi_version
        
        # Generate command name
        self.command_name = self._generate_command_name()
        
        # Initialize parameter parser
        self.parameter_parser = ParameterParser(openapi_version, spec)
        
        # Parse parameters using the new parser
        self.parameters = self._parse_parameters()
        self.parsed_parameters = self._parse_all_parameters()
        self.required_params = [p for p in self.parsed_parameters if p.required]
        self.optional_params = [p for p in self.parsed_parameters if not p.required]
        
        # Store user-provided parameter values
        self.param_values: Dict[str, Any] = {}
        self.parameter_collector = ParameterCollector()
    
    def _generate_command_name(self) -> str:
        """Generate command name using operationId or method_path fallback"""
        operation_id = self.operation.get('operationId')
        if operation_id:
            return operation_id
        
        # Fallback: method_path (sanitized)
        path_clean = re.sub(r'[{}]', '', self.path)  # Remove path parameter braces
        path_clean = re.sub(r'[^a-zA-Z0-9_]', '_', path_clean)  # Replace special chars with underscore
        path_clean = re.sub(r'_+', '_', path_clean)  # Collapse multiple underscores
        path_clean = path_clean.strip('_')  # Remove leading/trailing underscores
        
        return f"{self.method.lower()}_{path_clean}"
    
    def _parse_parameters(self) -> List[Dict[str, Any]]:
        """Parse parameters from the operation"""
        params = []
        
        # Get parameters from operation
        operation_params = self.operation.get('parameters', [])
        params.extend(operation_params)
        
        # For OpenAPI 3.x, also check requestBody
        if self.openapi_version.startswith('3') and 'requestBody' in self.operation:
            request_body = self.operation['requestBody']
            # Treat request body as a special "body" parameter
            body_param = {
                'name': 'body',
                'in': 'body',
                'required': request_body.get('required', False),
                'schema': request_body.get('content', {})
            }
            params.append(body_param)
        
        return params
    
    def _parse_all_parameters(self) -> List[ParsedParameter]:
        """Parse all parameters using the new parameter parser"""
        parsed_params = []
        
        for param in self.parameters:
            parsed_params.extend(self.parameter_parser.parse_parameter(param))
        
        return parsed_params
    
    def _get_required_parameters(self) -> List[Dict[str, Any]]:
        """Get list of required parameters"""
        return [p for p in self.parameters if p.get('required', False)]

    def _get_optional_parameters(self) -> List[Dict[str, Any]]:
        """Get list of optional parameters"""
        return [p for p in self.parameters if not p.get('required', False)]
    
    def _get_parameter_by_name(self, name: str) -> Optional[ParsedParameter]:
        """Get parameter definition by name"""
        for param in self.parsed_parameters:
            if param.name == name:
                return param
        return None
    
    def _are_all_required_params_supplied(self) -> bool:
        """Check if all required parameters have been supplied"""
        for param in self.required_params:
            if param.name not in self.param_values:
                return False
        return True
    
    def _are_all_optional_params_supplied(self) -> bool:
        """Check if all optional parameters have been supplied"""
        for param in self.optional_params:
            if param.name not in self.param_values:
                return False
        return True
    
    def _prompt_for_optional_params(self) -> bool:
        """Prompt user if they want to supply additional optional parameters"""
        if not self.optional_params:
            return False
            
        missing_optional = [p for p in self.optional_params 
                           if p.name not in self.param_values]
        
        if not missing_optional:
            return False
        
        print(f"Optional parameters available: {[p.name for p in missing_optional]}")
        response = input("Would you like to supply additional parameters? (Y/n): ").strip()
        
        # Default to Yes if empty or starts with Y/y
        return response == '' or response.lower().startswith('y')
    
    def _build_request_components(self) -> tuple[str, Dict[str, Any], Dict[str, str], Any]:
        """Build all request components using the parameter collector"""
        path_params, query_params, headers, body = self.parameter_collector.build_request_data(self.parsed_parameters)
        
        # Build URL with path parameter substitution
        url = f"{self.base_url}{self.path}"
        for param_name, param_value in path_params.items():
            placeholder = f"{{{param_name}}}"
            url = url.replace(placeholder, str(param_value))
        
        return url, query_params, headers, body
    
    def _execute_request(self) -> None:
        """Execute the HTTP request and pretty-print the response"""
        try:
            # Set parameter values in the collector
            self.parameter_collector.values = self.param_values.copy()
            
            # Build request components
            url, params, headers, body = self._build_request_components()
            
            # Set content-type for body requests
            if body is not None and 'content-type' not in [h.lower() for h in headers.keys()]:
                headers['Content-Type'] = 'application/json'
            
            # Make the request
            response = requests.request(
                method=self.method,
                url=url,
                params=params,
                headers=headers,
                json=body if body is not None else None,
                timeout=30
            )
            
            # Pretty-print the response
            print(f"\n--- {self.method} {url} ---")
            print(f"Status: {response.status_code} {response.reason}")
            
            if response.headers:
                print("Response Headers:")
                for key, value in response.headers.items():
                    print(f"  {key}: {value}")
            
            print("Response Body:")
            try:
                # Try to parse as JSON for pretty printing
                json_data = response.json()
                print(json.dumps(json_data, indent=2))
            except json.JSONDecodeError:
                # If not JSON, print as text
                print(response.text)
            
        except requests.RequestException as e:
            print(f"Request failed: {str(e)}")
        except Exception as e:
            print(f"Error executing request: {str(e)}")
    
    def do_(self, **kwargs) -> Optional['APIEndpoint']:
        """
        Execute the endpoint command.
        
        Args:
            **kwargs: Parameter name-value pairs to set before execution
        
        Returns:
            None if request was executed
            self if more parameters are needed
        """
        # Set provided parameters
        for param_name, param_value in kwargs.items():
            param_def = self._get_parameter_by_name(param_name)
            if param_def:
                self.param_values[param_name] = param_value
                print(f"Set {param_name} = {param_value}")
            else:
                print(f"Warning: Parameter '{param_name}' not found for endpoint {self.command_name}")
        
        # Check if all required parameters are supplied
        if not self._are_all_required_params_supplied():
            missing_required = [p.name for p in self.required_params 
                              if p.name not in self.param_values]
            print(f"Missing required parameters: {missing_required}")
            return self
        
        # Check if all optional parameters are supplied
        if not self._are_all_optional_params_supplied():
            print("Some optional parameters are not supplied.")
            if self._prompt_for_optional_params():
                # Collect missing parameters interactively
                missing_params = [p for p in self.parsed_parameters 
                                if p.name not in self.param_values]
                if missing_params:
                    print("Please provide the missing parameters:")
                    for param in missing_params:
                        if param.required or input(f"Provide {param.name}? (y/N): ").strip().lower().startswith('y'):
                            try:
                                value = param.collect_input()
                                if value is not None:
                                    self.param_values[param.name] = value
                            except (KeyboardInterrupt, EOFError):
                                print(f"\nSkipping parameter {param.name}")
                                continue
                return self
        
        # All required parameters supplied, execute the request
        self._execute_request()
        
        # Clear parameter values after successful execution
        self.param_values.clear()
        
        return None
    
    def help_(self) -> None:
        """Display help information for this endpoint"""
        print(f"\nEndpoint: {self.command_name}")
        print(f"Method: {self.method}")
        print(f"Path: {self.path}")
        print(f"URL: {self.base_url}{self.path}")
        
        summary = self.operation.get('summary')
        if summary:
            print(f"Summary: {summary}")
        
        description = self.operation.get('description')
        if description:
            print(f"Description: {description}")
        
        if self.required_params:
            print(f"\nRequired parameters:")
            for param in self.required_params:
                status = "✓" if param.name in self.param_values else "✗"
                print(f"  {status} {param.name} -- {param.get_type_display()}: {param.description}")
        
        if self.optional_params:
            print(f"\nOptional parameters:")
            for param in self.optional_params:
                status = "✓" if param.name in self.param_values else "✗"
                print(f"  {status} {param.name} -- {param.get_type_display()}: {param.description}")
    
    def complete_(self, text: str, line: str, begidx: int, endidx: int) -> List[str]:
        """
        Handle command completion for this endpoint.
        
        Args:
            text: The text being completed
            line: The entire command line
            begidx: Beginning index of text in line
            endidx: Ending index of text in line
            
        Returns:
            List of completion suggestions
        """
        # TODO: Implement completion logic
        return []
    
    def __repr__(self) -> str:
        """String representation of the endpoint"""
        return f"APIEndpoint(command_name={self.command_name}, method={self.method}, path={self.path})"
    
    def __str__(self) -> str:
        return f"{self.method} {self.path} ({self.command_name})"