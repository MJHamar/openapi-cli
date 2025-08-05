#!/usr/bin/env python3
"""
OpenAPI CLI Tool - Main CLI functionality
"""

import sys
import json
import yaml
import argparse
import requests
import cmd
import shlex
from urllib.parse import urlparse, urljoin
from typing import Dict, List, Any, Optional, Union
from .endpoint import APIEndpoint


class OpenAPICLI(cmd.Cmd):
    """Main CLI class for OpenAPI specification parsing and endpoint management"""
    
    def __init__(self):
        super().__init__()
        self.base_url: str = ""
        self.spec: Dict[str, Any] = {}
        self.endpoints: List[APIEndpoint] = []
        self.openapi_version: str = ""
        self._current_endpoint: Optional[APIEndpoint] = None
        self._endpoint_map: Dict[str, APIEndpoint] = {}
        self.intro = "OpenAPI CLI loaded successfully! Type 'help' for available commands."
        self.prompt = "() > "
    
    def parse_url(self, url: str) -> str:
        """
        Parse the OpenAPI specification URL and extract the base path.
        
        Args:
            url: URL pointing to the OpenAPI specification
            
        Returns:
            Base URL in the format <scheme>://<host>:<port>
        """
        try:
            parsed = urlparse(url)
            
            # Construct base URL
            scheme = parsed.scheme if parsed.scheme else "https"
            hostname = parsed.hostname if parsed.hostname else ""
            port = parsed.port
            
            if port:
                base_url = f"{scheme}://{hostname}:{port}"
            else:
                base_url = f"{scheme}://{hostname}"
                
            return base_url
            
        except Exception as e:
            raise ValueError(f"Invalid URL format: {url}. Error: {str(e)}")
    
    def fetch_openapi_spec(self, url: str) -> Dict[str, Any]:
        """
        Fetch and parse the OpenAPI specification from the given URL.
        
        Args:
            url: URL pointing to the OpenAPI specification
            
        Returns:
            Parsed OpenAPI specification as a dictionary
        """
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            
            # Try to parse as JSON first, then YAML
            try:
                if 'json' in content_type:
                    spec = response.json()
                else:
                    # Try YAML parsing
                    spec = yaml.safe_load(response.text)
            except (json.JSONDecodeError, yaml.YAMLError):
                # If parsing fails, try the other format
                try:
                    spec = yaml.safe_load(response.text)
                except yaml.YAMLError:
                    spec = response.json()
                    
            return spec
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch OpenAPI specification from {url}: {str(e)}")
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Failed to parse OpenAPI specification: {str(e)}")
    
    def determine_openapi_version(self, spec: Dict[str, Any]) -> str:
        """
        Determine the OpenAPI version from the specification.
        
        Args:
            spec: Parsed OpenAPI specification
            
        Returns:
            OpenAPI version string (e.g., "2.0", "3.0.0", "3.1.0")
        """
        if 'openapi' in spec:
            # OpenAPI 3.x
            return spec['openapi']
        elif 'swagger' in spec:
            # OpenAPI 2.0 (Swagger)
            return spec['swagger']
        else:
            raise ValueError("Invalid OpenAPI specification: missing 'openapi' or 'swagger' field")
    
    def get_server_base_urls(self, spec: Dict[str, Any]) -> List[str]:
        """
        Extract server base URLs from the OpenAPI specification.
        
        Args:
            spec: Parsed OpenAPI specification
            
        Returns:
            List of server base URLs
        """
        base_urls = []
        
        if self.openapi_version.startswith('3'):
            # OpenAPI 3.x uses 'servers' array
            servers = spec.get('servers', [])
            for server in servers:
                url = server.get('url', '')
                if url:
                    base_urls.append(url)
        else:
            # OpenAPI 2.0 uses host, basePath, and schemes
            host = spec.get('host', '')
            base_path = spec.get('basePath', '')
            schemes = spec.get('schemes', ['https'])
            
            if host:
                for scheme in schemes:
                    url = f"{scheme}://{host}{base_path}"
                    base_urls.append(url)
        
        return base_urls
    
    def resolve_base_url(self, spec_url: str, spec: Dict[str, Any]) -> str:
        """
        Resolve the final base URL for API calls.
        
        Args:
            spec_url: URL where the specification was fetched from
            spec: Parsed OpenAPI specification
            
        Returns:
            Resolved base URL for API calls
        """
        server_urls = self.get_server_base_urls(spec)
        
        if server_urls:
            # Use the first server URL
            server_url = server_urls[0]
            
            # If server URL is relative, resolve it against the spec URL
            if server_url.startswith('/'):
                spec_base = self.parse_url(spec_url)
                return urljoin(spec_base, server_url)
            elif not server_url.startswith(('http://', 'https://')):
                spec_base = self.parse_url(spec_url)
                return urljoin(spec_base + '/', server_url)
            else:
                return server_url
        else:
            # Fallback: use the spec URL's base
            return self.parse_url(spec_url)
    
    def parse_paths(self, spec: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse all paths and operations from the OpenAPI specification.
        
        Args:
            spec: Parsed OpenAPI specification
            
        Returns:
            List of endpoint definitions
        """
        endpoints = []
        paths = spec.get('paths', {})
        
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
                
            # Handle common parameters at path level
            path_parameters = path_item.get('parameters', [])
            
            # Iterate through HTTP methods
            http_methods = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options', 'trace']
            
            for method in http_methods:
                if method in path_item:
                    operation = path_item[method]
                    if isinstance(operation, dict):
                        endpoint_def = {
                            'path': path,
                            'method': method.upper(),
                            'operation': operation,
                            'path_parameters': path_parameters
                        }
                        endpoints.append(endpoint_def)
        
        return endpoints
    
    def _update_prompt(self):
        """Update the prompt based on current endpoint state"""
        if self._current_endpoint:
            self.prompt = f"({self._current_endpoint.command_name}) > "
        else:
            self.prompt = "() > "
    
    def do_help(self, line):
        """Help command - shows available commands or endpoint help"""
        line = line.strip()
        
        if not line:
            # No arguments - show general help
            if self._current_endpoint is None:
                # No current endpoint - show available endpoints
                self._list_endpoints_for_help()
            else:
                # Current endpoint active - show its help
                self._current_endpoint.help_()
        else:
            # Specific command requested
            if line in self._endpoint_map:
                self._endpoint_map[line].help_()
            else:
                print(f"Unknown command: {line}")
                print(f"Available commands: {list(self._endpoint_map.keys())}")
    
    def do_quit(self, line):
        """Exit the application"""
        return True
    
    def do_q(self, line):
        """Exit the application"""
        return True
    
    def do_EOF(self, line):
        """Exit the application on EOF"""
        print()
        return True
    
    def do_list(self, line):
        """List all available endpoints"""
        if not self.endpoints:
            print("No endpoints available. Load a specification first.")
            return
        
        print(f"\nAvailable endpoints ({len(self.endpoints)} total):")
        print("-" * 60)
        
        for endpoint in self.endpoints:
            summary = endpoint.operation.get('summary', 'No description')
            print(f"{endpoint.command_name:25} {endpoint.method:7} {endpoint.path}")
            print(f"{'':25} {summary}")
            print()
    
    def do_info(self, line):
        """Show current endpoint info"""
        if not self._current_endpoint:
            print("No endpoint currently selected.")
            return
        self._current_endpoint.help_()
    
    def _list_endpoints_for_help(self):
        """List available commands for help when no current endpoint"""
        print("Available commands:")
        print("  help [command] - Show help for command or general help")
        print("  list           - Show all available endpoints")
        print("  info           - Show current endpoint information")
        print("  quit, q        - Exit the application")
        
        if self.endpoints:
            print(f"\nAvailable API endpoints ({len(self.endpoints)} total):")
            for endpoint in self.endpoints:
                summary = endpoint.operation.get('summary', 'No description')
                print(f"  {endpoint.command_name:20} - {summary}")
    
    def default(self, line):
        """Handle endpoint commands and parameter passing"""
        # Parse command and parameters
        command_name, params = self._extract_command_and_params(line)
        
        # Case 1: Command name provided
        if command_name:
            # Check if there's already a current endpoint active
            if self._current_endpoint is not None:
                print(f"Error: Endpoint '{self._current_endpoint.command_name}' is currently active.")
                print("Complete the current endpoint operation or start a new session.")
                return
            
            # Select new endpoint
            if command_name in self._endpoint_map:
                self._current_endpoint = self._endpoint_map[command_name]
                
                # call do_() with - possibly empty - parameters
                self._current_endpoint = self._current_endpoint.do_(**params)
                self._update_prompt()
            else:
                print(f"Unknown command: {command_name}")
                print(f"Available commands: {list(self._endpoint_map.keys())}")
                return
        else:
            # Case 2: No command name, just parameters or empty line
            if self._current_endpoint is None:
                print("No endpoint selected. Please specify an endpoint name.")
                return
            
            # Call endpoint's do_() method with parameters (or empty params)
            result = self._current_endpoint.do_(**params)
            if result is None:
                # Endpoint completed, clear current endpoint
                self._current_endpoint = None
                self._update_prompt()
    
    def emptyline(self):
        """Handle empty line - don't repeat last command"""
        pass
    
    def create_endpoints(self, endpoint_definitions: List[Dict[str, Any]]) -> List[APIEndpoint]:
        """
        Create APIEndpoint objects from endpoint definitions.
        
        Args:
            endpoint_definitions: List of endpoint definitions
            
        Returns:
            List of APIEndpoint objects
        """
        endpoints = []
        
        for endpoint_def in endpoint_definitions:
            try:
                # Combine path-level and operation-level parameters
                operation = endpoint_def['operation'].copy()
                path_params = endpoint_def.get('path_parameters', [])
                
                if path_params:
                    operation_params = operation.get('parameters', [])
                    operation['parameters'] = path_params + operation_params
                
                endpoint = APIEndpoint(
                    base_url=self.base_url,
                    path=endpoint_def['path'],
                    method=endpoint_def['method'],
                    operation=operation,
                    openapi_version=self.openapi_version
                )
                endpoints.append(endpoint)
                
                # Add to endpoint map for quick lookup
                self._endpoint_map[endpoint.command_name] = endpoint
                
            except Exception as e:
                print(f"Warning: Failed to create endpoint for {endpoint_def['method']} {endpoint_def['path']}: {str(e)}")
                continue
        
        return endpoints
    
    def _extract_command_and_params(self, line: str) -> tuple[Optional[str], Dict[str, str]]:
        """
        Extract command name and parameters from a line.
        
        Args:
            line: Full command line
            
        Returns:
            Tuple of (command_name, parameters_dict)
        """
        line = line.strip()
        if not line:
            return None, {}
        
        # Split by spaces but preserve values with spaces in quotes
        try:
            tokens = shlex.split(line)
        except ValueError:
            # If shlex fails, fall back to simple split
            tokens = line.split()
        
        if not tokens:
            return None, {}
        
        command_name = None
        param_tokens = []
        
        # First token might be command name or parameter
        first_token = tokens[0]
        if '=' in first_token:
            # First token is a parameter
            param_tokens = tokens
        else:
            # First token is command name
            command_name = first_token
            param_tokens = tokens[1:]
        
        # Parse parameters from remaining tokens
        params = {}
        for token in param_tokens:
            if '=' in token:
                key, value = token.split('=', 1)
                params[key.strip()] = value.strip()
        
        return command_name, params
    
    def load_specification(self, url: str) -> None:
        """
        Load and parse the OpenAPI specification from the given URL.
        
        Args:
            url: URL pointing to the OpenAPI specification
        """
        print(f"Fetching OpenAPI specification from: {url}")
        
        # Fetch the specification
        self.spec = self.fetch_openapi_spec(url)
        
        # Determine OpenAPI version
        self.openapi_version = self.determine_openapi_version(self.spec)
        print(f"Detected OpenAPI version: {self.openapi_version}")
        
        # Resolve base URL
        self.base_url = self.resolve_base_url(url, self.spec)
        print(f"Resolved base URL: {self.base_url}")
        
        # Parse endpoints
        endpoint_definitions = self.parse_paths(self.spec)
        print(f"Found {len(endpoint_definitions)} endpoints")
        
        # Create endpoint objects
        self.endpoints = self.create_endpoints(endpoint_definitions)
        print(f"Successfully created {len(self.endpoints)} endpoint objects")
    

def create_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser"""
    parser = argparse.ArgumentParser(
        description="OpenAPI CLI Tool - Work with any OpenAPI documented API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s https://petstore.swagger.io/v2/swagger.json
  %(prog)s https://api.github.com/openapi.yaml
        """
    )
    
    parser.add_argument(
        'url',
        help='URL pointing to the OpenAPI specification (JSON or YAML)'
    )
    
    return parser


def main():
    """Main entry point for the CLI tool"""
    parser = create_parser()
    args = parser.parse_args()
    
    cli = OpenAPICLI()
    
    try:
        cli.load_specification(args.url)
        
        # Start the interactive CLI
        cli.cmdloop()
                
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)



if __name__ == "__main__":
    main()