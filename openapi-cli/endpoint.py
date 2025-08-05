"""
API Endpoint representation for OpenAPI CLI Tool
"""

from typing import Dict, List, Any
import re

class APIEndpoint:
    """Represents an API endpoint with its details"""

    def __init__(self, path: str, method: str, operation_id: str, 
                 summary: str = "", description: str = "", 
                 parameters: List[Dict] = None, base_url: str = ""):
        self.path = path
        self.method = method.upper()
        self.operation_id = operation_id
        self.summary = summary
        self.description = description
        self.parameters = parameters or []
        self.base_url = base_url

        # Generate command name from operation_id or method + path
        if operation_id:
            # Convert camelCase to snake_case
            self.command_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', operation_id).lower()
        else:
            # Generate from method and path
            path_clean = path.replace('/', '_').replace('{', '').replace('}', '').strip('_')
            self.command_name = f"{method.lower()}_{path_clean}"

    def get_help_text(self) -> str:
        """Generate help text for this endpoint"""
        help_text = f"{self.command_name} - {self.summary or self.description or 'No description'}\n"
        help_text += f"Method: {self.method} {self.path}\n"

        if self.parameters:
            help_text += "Parameters:\n"
            for param in self.parameters:
                param_name = param.get('name', 'unknown')
                param_in = param.get('in', 'unknown')
                param_required = param.get('required', False)
                param_desc = param.get('description', 'No description')
                required_text = " (required)" if param_required else " (optional)"
                help_text += f"  {param_name} ({param_in}){required_text}: {param_desc}\n"
        else:
            help_text += "No parameters required.\n"

        return help_text

