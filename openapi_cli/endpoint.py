"""
API Endpoint representation for OpenAPI CLI Tool
"""

from typing import Dict, List, Any, Optional, Union
import re
import requests
import json


class APIEndpoint:
    """Represents a single API endpoint from an OpenAPI specification"""
    
    def __init__(self, base_url: str, path: str, method: str, operation: Dict[str, Any], 
                 openapi_version: str = "3.0.0"):
        """
        Initialize an API endpoint.
        
        Args:
            base_url: Base URL of the API
            path: Endpoint path (e.g., "/pets/{id}")
            method: HTTP method (GET, POST, etc.)
            operation: OpenAPI operation object
            openapi_version: OpenAPI specification version
        """
        self.base_url = base_url.rstrip('/')
        self.path = path
        self.method = method.upper()
        self.operation = operation
        self.openapi_version = openapi_version
        
        # Generate command name
        self.command_name = self._generate_command_name()
        
        # Parse parameters
        self.parameters = self._parse_parameters()
        self.required_params = self._get_required_parameters()
        self.optional_params = self._get_optional_parameters()
        
        # Store user-provided parameter values
        self.param_values: Dict[str, Any] = {}
    
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
    
    def _get_required_parameters(self) -> List[Dict[str, Any]]:
        """Get list of required parameters"""
        return [p for p in self.parameters if p.get('required', False)]

    def _get_optional_parameters(self) -> List[Dict[str, Any]]:
        """Get list of optional parameters"""
        return [p for p in self.parameters if not p.get('required', False)]
    
    def _get_parameter_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get parameter definition by name"""
        for param in self.parameters:
            if param.get('name') == name:
                return param
        return None
    
    def _are_all_required_params_supplied(self) -> bool:
        """Check if all required parameters have been supplied"""
        for param in self.required_params:
            param_name = param.get('name')
            if param_name not in self.param_values:
                return False
        return True
    
    def _are_all_optional_params_supplied(self) -> bool:
        """Check if all optional parameters have been supplied"""
        for param in self.optional_params:
            param_name = param.get('name')
            if param_name not in self.param_values:
                return False
        return True
    
    def _prompt_for_optional_params(self) -> bool:
        """Prompt user if they want to supply additional optional parameters"""
        if not self.optional_params:
            return False
            
        missing_optional = [p for p in self.optional_params 
                           if p.get('name') not in self.param_values]
        
        if not missing_optional:
            return False
        
        print(f"Optional parameters available: {[p.get('name') for p in missing_optional]}")
        response = input("Would you like to supply additional parameters? (Y/n): ").strip()
        
        # Default to Yes if empty or starts with Y/y
        return response == '' or response.lower().startswith('y')
    
    def _build_request_url(self) -> str:
        """Build the full request URL with path parameters substituted"""
        url = f"{self.base_url}{self.path}"
        
        # Substitute path parameters
        for param in self.parameters:
            if param.get('in') == 'path':
                param_name = param.get('name')
                if param_name in self.param_values:
                    placeholder = f"{{{param_name}}}"
                    url = url.replace(placeholder, str(self.param_values[param_name]))
        
        return url
    
    def _build_request_params(self) -> Dict[str, Any]:
        """Build query parameters for the request"""
        query_params = {}
        
        for param in self.parameters:
            if param.get('in') == 'query':
                param_name = param.get('name')
                if param_name in self.param_values:
                    query_params[param_name] = self.param_values[param_name]
        
        return query_params
    
    def _build_request_headers(self) -> Dict[str, str]:
        """Build headers for the request"""
        headers = {}
        
        for param in self.parameters:
            if param.get('in') == 'header':
                param_name = param.get('name')
                if param_name in self.param_values:
                    headers[param_name] = str(self.param_values[param_name])
        
        return headers
    
    def _build_request_body(self) -> Optional[Any]:
        """Build request body"""
        for param in self.parameters:
            if param.get('in') == 'body':
                param_name = param.get('name')
                if param_name in self.param_values:
                    return self.param_values[param_name]
        
        return None
    
    def _execute_request(self) -> None:
        """Execute the HTTP request and pretty-print the response"""
        try:
            url = self._build_request_url()
            params = self._build_request_params()
            headers = self._build_request_headers()
            body = self._build_request_body()
            
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
            missing_required = [p.get('name') for p in self.required_params 
                              if p.get('name') not in self.param_values]
            print(f"Missing required parameters: {missing_required}")
            return self
        
        # Check if all optional parameters are supplied
        if not self._are_all_optional_params_supplied():
            print("Some optional parameters are not supplied.")
            if self._prompt_for_optional_params():
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
                param_name = param.get('name', 'unknown')
                param_type = param.get('type', 'string')
                param_desc = param.get('description', 'No description')
                status = "✓" if param_name in self.param_values else "✗"
                print(f"  {status} {param_name} ({param_type}): {param_desc}")
        
        if self.optional_params:
            print(f"\nOptional parameters:")
            for param in self.optional_params:
                param_name = param.get('name', 'unknown')
                param_type = param.get('type', 'string')
                param_desc = param.get('description', 'No description')
                status = "✓" if param_name in self.param_values else "✗"
                print(f"  {status} {param_name} ({param_type}): {param_desc}")
    
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