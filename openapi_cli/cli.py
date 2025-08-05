"""
Main CLI implementation for OpenAPI CLI Tool
"""

import sys
import json
import os
import cmd
import requests
import re
from typing import Dict, List, Any, Optional
from .endpoint import APIEndpoint

try:
    import readline
    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

class OpenAPICLI(cmd.Cmd):
    """Interactive CLI for OpenAPI endpoints"""

    def __init__(self, openapi_spec: Dict[str, Any]):
        super().__init__()
        self.prompt = "> "
        self.intro = "Welcome to OpenAPI CLI! Type 'help' to see available commands or 'q' to quit."

        self.base_url = self._extract_base_url(openapi_spec)
        self.endpoints = self._parse_endpoints(openapi_spec)
        self.command_names = [endpoint.command_name for endpoint in self.endpoints]

        # Set up tab completion if readline is available
        if HAS_READLINE:
            self._setup_completion()

    def _setup_completion(self):
        """Set up tab completion for commands"""
        try:
            readline.set_completer_delims(' \t\n;')
            readline.parse_and_bind("tab: complete")

            # Store original completer
            self.original_completer = readline.get_completer()

            # Override the completer
            def completer(text, state):
                options = [cmd for cmd in self.command_names + ['help', 'quit', 'q'] if cmd.startswith(text)]
                if state < len(options):
                    return options[state]
                return None

            readline.set_completer(completer)
        except Exception:
            # Silently fail if readline setup doesn't work
            pass

    def _extract_base_url(self, spec: Dict[str, Any]) -> str:
        """Extract base URL from OpenAPI spec"""
        servers = spec.get('servers', [])
        if servers and isinstance(servers, list) and len(servers) > 0:
            return servers[0].get('url', '')
        return 'http://localhost'

    def _parse_endpoints(self, spec: Dict[str, Any]) -> List[APIEndpoint]:
        """Parse OpenAPI spec and create APIEndpoint objects"""
        endpoints = []
        paths = spec.get('paths', {})

        for path, path_obj in paths.items():
            if not isinstance(path_obj, dict):
                continue

            for method, operation in path_obj.items():
                if method.upper() not in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS']:
                    continue

                if not isinstance(operation, dict):
                    continue

                operation_id = operation.get('operationId', '')
                summary = operation.get('summary', '')
                description = operation.get('description', '')
                parameters = operation.get('parameters', [])

                endpoint = APIEndpoint(
                    path=path,
                    method=method,
                    operation_id=operation_id,
                    summary=summary,
                    description=description,
                    parameters=parameters,
                    base_url=self.base_url
                )

                endpoints.append(endpoint)

        return endpoints

    def do_help(self, arg):
        """Show help for commands"""
        if not arg:
            # Show all available commands
            print("Available commands:")
            print("  help [command] - Show help for a specific command")
            print("  q, quit       - Exit the CLI")
            print()
            print("API Endpoints:")
            if not self.endpoints:
                print("  No endpoints found in the OpenAPI specification")
            else:
                for endpoint in self.endpoints:
                    print(f"  {endpoint.command_name:<20} - {endpoint.summary or endpoint.description or 'No description'}")
        else:
            # Show help for specific command
            command = arg.strip()
            endpoint = self._find_endpoint(command)
            if endpoint:
                print(endpoint.get_help_text())
            elif command in ['q', 'quit']:
                print("q, quit - Exit the CLI")
            else:
                print(f"Unknown command: {command}")
                print("Type 'help' to see all available commands.")

    def do_q(self, arg):
        """Exit the CLI"""
        print("Goodbye!")
        return True

    def do_quit(self, arg):
        """Exit the CLI"""
        print("Goodbye!")
        return True

    def do_EOF(self, arg):
        """Handle Ctrl+D"""
        print()  # New line for cleaner exit
        print("Goodbye!")
        return True

    def _find_endpoint(self, command_name: str) -> Optional[APIEndpoint]:
        """Find endpoint by command name"""
        for endpoint in self.endpoints:
            if endpoint.command_name == command_name:
                return endpoint
        return None

    def default(self, line):
        """Handle unknown commands - try to match API endpoints"""
        parts = line.split()
        if not parts:
            return

        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []

        endpoint = self._find_endpoint(command)
        if endpoint:
            self._execute_api_call(endpoint, args)
        else:
            print(f"Unknown command: {command}")
            print("Type 'help' to see available commands.")

    def _execute_api_call(self, endpoint: APIEndpoint, args: List[str]):
        """Execute API call for the given endpoint"""
        try:
            # Build URL
            url = self._build_url(endpoint, args)
            if not url:
                return

            # Prepare request parameters
            params = {}
            headers = {'User-Agent': 'OpenAPI-CLI/1.0.0'}

            print(f"Making {endpoint.method} request to: {url}")

            # Make the HTTP request
            response = requests.request(
                method=endpoint.method,
                url=url,
                params=params,
                headers=headers,
                timeout=30
            )

            # Print response
            print(f"Status: {response.status_code} {response.reason}")

            # Try to format JSON response nicely
            try:
                content_type = response.headers.get('content-type', '').lower()
                if 'application/json' in content_type:
                    json_data = response.json()
                    print(json.dumps(json_data, indent=2))
                else:
                    print(response.text)
            except json.JSONDecodeError:
                print(response.text)

        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
        except Exception as e:
            print(f"Error: {e}")

    def _build_url(self, endpoint: APIEndpoint, args: List[str]) -> Optional[str]:
        """Build URL with path parameters substituted"""
        path = endpoint.path
        base_url = endpoint.base_url or "http://localhost"

        # Find path parameters
        path_params = re.findall(r'\{([^}]+)\}', path)

        if len(path_params) > len(args):
            print(f"Error: {endpoint.command_name} requires {len(path_params)} argument(s):")
            for i, param_name in enumerate(path_params):
                param_info = next((p for p in endpoint.parameters if p.get('name') == param_name), {})
                desc = param_info.get('description', 'No description')
                print(f"  {i+1}. {param_name}: {desc}")
            return None

        # Substitute path parameters
        for i, param_name in enumerate(path_params):
            if i < len(args):
                path = path.replace(f'{{{param_name}}}', args[i])

        # Build full URL
        if base_url.endswith('/') and path.startswith('/'):
            full_url = base_url[:-1] + path
        elif not base_url.endswith('/') and not path.startswith('/'):
            full_url = base_url + '/' + path
        else:
            full_url = base_url + path

        return full_url

    def completedefault(self, text, line, begidx, endidx):
        """Provide tab completion for API commands"""
        return [cmd for cmd in self.command_names if cmd.startswith(text)]

def load_openapi_spec(url_or_path: str) -> Dict[str, Any]:
    """Load OpenAPI specification from URL or file path"""
    try:
        # Check if it's a URL
        if url_or_path.startswith(('http://', 'https://')):
            print(f"Fetching OpenAPI spec from URL...")
            response = requests.get(url_or_path, timeout=30)
            response.raise_for_status()

            # Try JSON first, then YAML
            try:
                return response.json()
            except json.JSONDecodeError:
                # Try YAML parsing if available
                try:
                    import yaml
                    return yaml.safe_load(response.text)
                except ImportError:
                    raise ValueError("YAML parsing requires 'pyyaml' package: pip install pyyaml")
        else:
            # Local file
            if not os.path.exists(url_or_path):
                raise FileNotFoundError(f"File not found: {url_or_path}")

            print(f"Loading OpenAPI spec from file...")
            with open(url_or_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Try JSON first
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                # Try YAML
                try:
                    import yaml
                    return yaml.safe_load(content)
                except ImportError:
                    raise ValueError("YAML parsing requires 'pyyaml' package: pip install pyyaml")

    except Exception as e:
        raise RuntimeError(f"Failed to load OpenAPI spec: {e}")

def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("OpenAPI CLI Tool")
        print("Usage: python -m openapi_cli <url/path/to/openapi.json>")
        print()
        print("Examples:")
        print("  python -m openapi_cli https://petstore.swagger.io/v2/swagger.json")
        print("  python -m openapi_cli ./api-spec.yaml") 
        sys.exit(1)

    openapi_spec_path = sys.argv[1]

    try:
        # Load OpenAPI specification
        print(f"OpenAPI CLI Tool v1.0.0")
        print(f"Loading OpenAPI specification from: {openapi_spec_path}")
        spec = load_openapi_spec(openapi_spec_path)

        # Validate basic structure
        if not isinstance(spec, dict):
            raise ValueError("Invalid OpenAPI specification: not a valid JSON/YAML object")

        if 'paths' not in spec:
            raise ValueError("Invalid OpenAPI specification: missing 'paths' section")

        # Show API info
        info = spec.get('info', {})
        print(f"API: {info.get('title', 'Unknown')} v{info.get('version', 'Unknown')}")
        if info.get('description'):
            print(f"Description: {info.get('description')}")

        # Create and start CLI
        cli = OpenAPICLI(spec)
        print(f"Loaded {len(cli.endpoints)} API endpoint(s)")
        print()
        cli.cmdloop()

    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

