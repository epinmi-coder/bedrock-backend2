"""
Email template utilities for rendering HTML email templates
"""
import os
from pathlib import Path
from typing import Dict, Any


def get_template_path(template_name: str) -> Path:
    """Get the full path to a template file"""
    current_dir = Path(__file__).parent
    template_dir = current_dir / "templates"
    return template_dir / f"{template_name}.html"


def load_template(template_name: str) -> str:
    """Load HTML template from templates directory"""
    template_path = get_template_path(template_name)
    
    if not template_path.exists():
        raise FileNotFoundError(f"Template not found: {template_path}")
    
    with open(template_path, 'r', encoding='utf-8') as file:
        return file.read()


def render_template(template_name: str, **kwargs) -> str:
    """
    Load and render HTML template with provided variables
    
    Args:
        template_name: Name of the template file (without .html extension)
        **kwargs: Variables to substitute in the template
        
    Returns:
        Rendered HTML string
        
    Example:
        html = render_template('email_verification', 
                             verification_link="http://example.com/verify", 
                             email="user@example.com")
    """
    template_content = load_template(template_name)
    
    # Replace template variables
    for key, value in kwargs.items():
        placeholder = f"{{{key}}}"
        template_content = template_content.replace(placeholder, str(value))
    
    return template_content


def get_available_templates() -> list:
    """Get list of available template files"""
    current_dir = Path(__file__).parent
    template_dir = current_dir / "templates"
    
    if not template_dir.exists():
        return []
    
    templates = []
    for file_path in template_dir.glob("*.html"):
        templates.append(file_path.stem)
    
    return templates