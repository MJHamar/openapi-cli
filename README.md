# OpenAPI CLI Tool

A generic interactive CLI tool for any OpenAPI documented API.

## 🚀 Features

- **Interactive CLI**: Browse and execute API endpoints interactively
- **Tab Completion**: Auto-complete commands and see available options (bash/zsh style)
- **Help System**: Built-in help for all endpoints and parameters
- **JSON Pretty Printing**: Responses are formatted for easy reading
- **Universal**: Works with any valid OpenAPI 3.x specification
- **URL & File Support**: Load specs from URLs or local files
- **Smart Command Naming**: Converts `operationId` to snake_case commands

## 📦 Installation

```bash
# Install dependencies
pip install requests pyyaml

# Or install from source
git clone <repository>
cd openapi-cli
pip install -e .
```

## 🎯 Usage

```bash
python -m openapi_cli <url/path/to/openapi.json>
```

### Examples

```bash
# From a URL
python -m openapi_cli https://petstore.swagger.io/v2/swagger.json

# From a local file
python -m openapi_cli ./api-spec.yaml

# From a local JSON file
python -m openapi_cli ./openapi.json
```

## 🖥️ Interactive Commands

Once the CLI starts, you can use these commands:

| Command | Description |
|---------|-------------|
| `help` | Show all available commands |
| `help <command>` | Show help for a specific command |
| `<endpoint_command> <args>` | Execute an API endpoint |
| `q` or `quit` | Exit the CLI |

### Tab Completion

Press `TAB` to:
- Auto-complete command names
- See available commands when typing
- Navigate through possible completions

## 📋 Example Session

```
$ python -m openapi_cli https://petstore.swagger.io/v2/swagger.json
OpenAPI CLI Tool v1.0.0
Loading OpenAPI specification from: https://petstore.swagger.io/v2/swagger.json
Fetching OpenAPI spec from URL...
API: Swagger Petstore v1.0.6
Description: This is a sample server Petstore server.
Loaded 20 API endpoint(s)

Welcome to OpenAPI CLI! Type 'help' to see available commands or 'q' to quit.
> help
Available commands:
  help [command] - Show help for a specific command
  q, quit       - Exit the CLI

API Endpoints:
  add_pet              - Add a new pet to the store
  update_pet           - Update an existing pet
  find_pets_by_status  - Finds Pets by status
  find_pets_by_tags    - Finds Pets by tags
  get_pet_by_id        - Find pet by ID
  update_pet_with_form - Updates a pet in the store with form data
  delete_pet           - Deletes a pet

> help get_pet_by_id
get_pet_by_id - Find pet by ID. Returns a single pet.
Method: GET /pet/{petId}
Parameters:
  petId (path) (required): ID of pet to return

> get_pet_by_id 1
Making GET request to: https://petstore.swagger.io/v2/pet/1
Status: 200 OK
{
  "id": 1,
  "category": {
    "id": 2,
    "name": "Cats"
  },
  "name": "Cat 1",
  "photoUrls": [
    "url1",
    "url2"
  ],
  "tags": [
    {
      "id": 1,
      "name": "tag1"
    }
  ],
  "status": "available"
}

> find_pets_by_status available
Making GET request to: https://petstore.swagger.io/v2/pet/findByStatus?status=available
Status: 200 OK
[
  {
    "id": 1,
    "name": "doggie",
    "status": "available"
  }
  // ... more pets
]

> q
Goodbye!
```

## 🔧 How It Works

1. **Parse OpenAPI Spec**: The tool loads and parses the OpenAPI specification from a URL or file
2. **Generate Commands**: Each API endpoint becomes a CLI command following the pattern `<method>_<endpoint>`
3. **Interactive Shell**: Uses Python's `cmd` module for the interactive interface
4. **Tab Completion**: Leverages the `readline` library for command completion
5. **HTTP Requests**: Makes actual HTTP requests using the `requests` library
6. **Response Formatting**: Pretty-prints JSON responses with proper indentation

## 📝 Command Naming

Commands are generated from the OpenAPI `operationId` field, converted to snake_case. If no `operationId` is present, commands are generated from the HTTP method and path.

Examples:
- `operationId: "getPetById"` → `get_pet_by_id`
- `operationId: "findPetsByStatus"` → `find_pets_by_status`
- `GET /pet/{petId}` → `get_pet_petid` (if no operationId)

## 🔧 Requirements

- Python 3.7+
- `requests` library for HTTP requests
- `pyyaml` library for YAML parsing (optional, for YAML specs)
- `readline` library for tab completion (usually built-in)

## ⚠️ Current Limitations

- Basic path parameter substitution only
- Query parameters, headers, and request bodies need manual implementation per endpoint
- Authentication is not yet implemented
- Error handling could be more robust
- No support for request body schemas yet

## 🛠️ Development

```bash
# Clone the repository
git clone <repository>
cd openapi-cli

# Install in development mode
pip install -e .

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black .

# Lint code
flake8 .
```

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 🐛 Issues

If you find any issues or have feature requests, please open an issue on GitHub.

---

**Made with ❤️ for the OpenAPI community**

