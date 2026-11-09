"""Shared path helpers for the Learn FASTER CLI."""

from pathlib import Path


def get_templates_dir() -> Path:
    """Get the templates directory from the installed package."""
    return Path(__file__).parent.parent / "templates"


def get_agent_templates_dir(agent_name: str) -> Path:
    """Get templates specialized for a supported coding agent."""
    return get_templates_dir() / "agents" / agent_name


def get_shared_templates_dir() -> Path:
    """Get templates shared by every supported coding agent."""
    return get_templates_dir() / "shared"
