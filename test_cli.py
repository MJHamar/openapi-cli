#!/usr/bin/env python3
"""
Test script for OpenAPI CLI Tool
"""

import json
import sys
import os

# Add current directory to path
sys.path.insert(0, '.')

def test_basic_functionality():
    """Test basic functionality of the CLI"""
    print("Testing OpenAPI CLI Tool...")

    try:
        from openapi_cli.cli import load_openapi_spec, OpenAPICLI
        from openapi_cli.endpoint import APIEndpoint

        # Test 1: Load spec from file
        print("✓ Successfully imported modules")

        # Test 2: Load OpenAPI spec
        if os.path.exists('sample-petstore.json'):
            spec = load_openapi_spec('sample-petstore.json')
            print("✓ Successfully loaded OpenAPI spec")

            # Test 3: Create CLI instance
            cli = OpenAPICLI(spec)
            print(f"✓ Successfully created CLI with {len(cli.endpoints)} endpoints")

            # Test 4: Test endpoint creation
            if cli.endpoints:
                endpoint = cli.endpoints[0]
                print(f"✓ First endpoint: {endpoint.command_name} ({endpoint.method} {endpoint.path})")

                # Test help text
                help_text = endpoint.get_help_text()
                print("✓ Successfully generated help text")

            print("\n🎉 All tests passed!")
            print("\nAvailable endpoints:")
            for endpoint in cli.endpoints:
                print(f"  • {endpoint.command_name:<20} - {endpoint.summary}")

        else:
            print("❌ sample-petstore.json not found")

    except ImportError as e:
        print(f"❌ Import error: {e}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_basic_functionality()

