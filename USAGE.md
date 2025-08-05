# OpenAPI CLI Tool - Usage Guide

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install requests pyyaml
   ```

2. **Run the tool:**
   ```bash
   # With a URL
   python -m openapi_cli https://petstore.swagger.io/v2/swagger.json

   # With a local file
   python -m openapi_cli sample-petstore.json
   ```

## Command Structure

The tool automatically generates CLI commands from your OpenAPI specification:

- **operationId present**: `getPetById` → `get_pet_by_id`
- **No operationId**: `GET /pet/{id}` → `get_pet_id`

## Interactive Commands

| Command | Description | Example |
|---------|-------------|---------|
| `help` | Show all commands | `help` |
| `help <cmd>` | Show command details | `help get_pet_by_id` |
| `<endpoint> <args>` | Call API endpoint | `get_pet_by_id 123` |
| `q` or `quit` | Exit CLI | `q` |

## Tab Completion

- Press `TAB` to autocomplete commands
- Press `TAB` twice to see all options
- Works like bash/zsh completion

## Real-World Examples

### Example 1: Pet Store API
```bash
python -m openapi_cli https://petstore.swagger.io/v2/swagger.json

> help
> get_pet_by_id 1
> find_pets_by_status available
> q
```

### Example 2: JSONPlaceholder API
```bash
# First create a simple OpenAPI spec for JSONPlaceholder
python -m openapi_cli https://jsonplaceholder.typicode.com/openapi.json

> get_posts
> get_post 1
> get_users
> q
```

## Tips & Tricks

1. **Use tab completion** - Start typing and press TAB
2. **Check help first** - Use `help <command>` to see required parameters
3. **Path parameters** - Provide them as space-separated arguments
4. **JSON responses** - Automatically formatted for readability
5. **Error handling** - Tool shows clear error messages for missing parameters

## Troubleshooting

**Tab completion not working?**
- Install readline: `pip install readline` (some systems)
- Use arrow keys to navigate command history

**YAML files not loading?**
- Install PyYAML: `pip install pyyaml`

**Connection errors?**
- Check internet connection for URLs
- Verify API server is running
- Check authentication requirements

**No endpoints found?**
- Verify OpenAPI spec has `paths` section
- Check spec format (JSON/YAML)
- Ensure spec is valid OpenAPI 3.x

## Advanced Usage

### Custom Base URLs
The tool automatically detects base URLs from the `servers` section in your OpenAPI spec.

### Parameter Types Supported
- Path parameters: `/pet/{petId}` 
- Query parameters: Coming soon
- Headers: Coming soon
- Request bodies: Coming soon

### Response Formats
- JSON: Automatically pretty-printed
- Text: Displayed as-is
- Other formats: Raw display

---

Happy API exploring! 🚀

