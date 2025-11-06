"""
Template loader utility for loading and rendering HTML email templates.
This keeps the existing mail.py functionality intact while making templates modular.
"""
from pathlib import Path
from typing import Dict, Any

def load_template(template_name: str) -> str:
    """
    Load an HTML template from the templates folder.
    
    Args:
        template_name: Name of the template file (with or without .html extension)
    
    Returns:
        Raw HTML content as string
    """
    # Get the templates directory (same folder as this file)
    templates_dir = Path(__file__).parent
    
    # Add .html extension if not present
    if not template_name.endswith('.html'):
        template_name += '.html'
    
    template_path = templates_dir / template_name
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template {template_name} not found in {templates_dir}")
    
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read()


def render_template(template_name: str, **context: Any) -> str:
    """
    Load a template and substitute variables with provided context.
    
    Args:
        template_name: Name of the template file
        **context: Variables to substitute in the template
    
    Returns:
        Rendered HTML with variables substituted
    """
    html_content = load_template(template_name)
    
    # Simple variable substitution using format()
    try:
        return html_content.format(**context)
    except KeyError as e:
        raise ValueError(f"Missing template variable: {e}")


def get_available_templates() -> list[str]:
    """
    Get list of available template files in the templates folder.
    
    Returns:
        List of template filenames
    """
    templates_dir = Path(__file__).parent
    return [f.name for f in templates_dir.glob('*.html')]