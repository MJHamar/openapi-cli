#!/usr/bin/env python3
"""
Advanced demo showing all features of the OpenAPI CLI Tool
"""

import sys
import json
sys.path.insert(0, '.')

from openapi_cli.cli import OpenAPICLI, load_openapi_spec

def simulate_cli_session():
    """Simulate an interactive CLI session to show features"""

    print("=" * 60)
    print("🚀 OPENAPI CLI TOOL - ADVANCED DEMO")
    print("=" * 60)
    print()

    # Load the sample spec
    print("📂 Loading sample OpenAPI specification...")
    spec = load_openapi_spec('sample-petstore.json')

    # Create CLI instance
    cli = OpenAPICLI(spec)

    print(f"✅ Loaded {len(cli.endpoints)} API endpoints")
    print(f"🌐 Base URL: {cli.base_url}")
    print()

    # Show all endpoints
    print("📋 Available API Endpoints:")
    print("-" * 40)
    for i, endpoint in enumerate(cli.endpoints, 1):
        print(f"{i:2d}. {endpoint.command_name:<18} {endpoint.method:<6} {endpoint.path}")
        print(f"    └─ {endpoint.summary}")
    print()

    # Show command naming examples
    print("🏷️  Command Naming Examples:")
    print("-" * 40)
    for endpoint in cli.endpoints:
        if endpoint.operation_id:
            print(f"operationId: '{endpoint.operation_id}' → command: '{endpoint.command_name}'")
        else:
            print(f"{endpoint.method} {endpoint.path} → command: '{endpoint.command_name}'")
    print()

    # Show help examples
    print("❓ Help System Examples:")
    print("-" * 40)

    # General help
    print("Command: help")
    print("Output:")
    cli.do_help("")
    print()

    # Specific command help
    print("Command: help get_pet_by_id")
    print("Output:")
    cli.do_help("get_pet_by_id")
    print()

    # Show tab completion simulation
    print("⌨️  Tab Completion Simulation:")
    print("-" * 40)
    print("User types: 'get<TAB>'")
    completions = [cmd for cmd in cli.command_names if cmd.startswith('get')]
    print(f"Available completions: {completions}")
    print()

    print("User types: 'get_p<TAB>'")
    completions = [cmd for cmd in cli.command_names if cmd.startswith('get_p')]
    print(f"Available completions: {completions}")
    print()

    # Show parameter handling
    print("🔧 Parameter Handling Examples:")
    print("-" * 40)

    # Find an endpoint with parameters
    param_endpoint = next((e for e in cli.endpoints if e.parameters), None)
    if param_endpoint:
        print(f"Endpoint: {param_endpoint.command_name}")
        print(f"Required parameters:")
        for param in param_endpoint.parameters:
            if param.get('required', False):
                print(f"  • {param['name']} ({param['in']}): {param.get('description', 'No description')}")

        print(f"\nExample usage:")
        if param_endpoint.command_name == 'get_pet_by_id':
            print(f"  {param_endpoint.command_name} 123")
            print(f"  → GET {cli.base_url}/pet/123")
    print()

    # Show URL building examples
    print("🔗 URL Building Examples:")  
    print("-" * 40)
    for endpoint in cli.endpoints[:3]:  # Show first 3
        example_args = []
        # Generate example args for path parameters
        import re
        path_params = re.findall(r'\{([^}]+)\}', endpoint.path)
        for param in path_params:
            if param == 'petId':
                example_args.append('123')
            elif param == 'id':
                example_args.append('456')
            else:
                example_args.append('example')

        if example_args:
            example_url = cli._build_url(endpoint, example_args)
            print(f"{endpoint.command_name} {' '.join(example_args)}")
            print(f"  → {example_url}")
        else:
            example_url = cli._build_url(endpoint, [])
            print(f"{endpoint.command_name}")
            print(f"  → {example_url}")
    print()

    # Show JSON response formatting example
    print("📄 JSON Response Formatting:")
    print("-" * 40)
    sample_response = {
        "id": 123,
        "name": "Fluffy",
        "category": {"id": 1, "name": "Dogs"},
        "tags": [{"id": 1, "name": "friendly"}, {"id": 2, "name": "cute"}],
        "status": "available"
    }
    print("Raw API response would be formatted as:")
    print(json.dumps(sample_response, indent=2))
    print()

    print("🎯 Key Features Summary:")
    print("-" * 40)
    features = [
        "✅ Interactive command-line interface",
        "✅ Tab completion for commands",
        "✅ Built-in help system", 
        "✅ Automatic command generation from OpenAPI",
        "✅ Smart parameter handling",
        "✅ Pretty-printed JSON responses",
        "✅ Support for URLs and local files",
        "✅ Graceful error handling",
        "✅ Multiple exit options (q, quit, Ctrl+D)"
    ]

    for feature in features:
        print(f"  {feature}")

    print()
    print("🚀 Ready to try the real CLI!")
    print("Run: python -m openapi_cli sample-petstore.json")
    print("=" * 60)

if __name__ == "__main__":
    simulate_cli_session()

