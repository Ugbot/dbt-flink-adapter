"""
Jinja macro rendering helpers for unit testing dbt-flink-adapter macros.

Renders Jinja templates using the adapter's macro files WITHOUT requiring
a running Flink cluster or dbt project. This enables fast, isolated unit
tests for macro logic, validation, and output verification.

Usage:
    from tests.macro_test_helpers import render_macro, render_template

    # Render a specific macro with arguments
    result = render_macro("iceberg.iceberg_table_properties", format_version=2)
    props = ast.literal_eval(result)

    # Render arbitrary Jinja template using adapter macros
    result = render_template(
        "{% import 'catalogs/iceberg.sql' as ice %}"
        "{{ ice.iceberg_table_properties(format_version=2) }}"
    )
"""

import os
from typing import Any

from jinja2 import Environment, FileSystemLoader


# Path to the adapter's macro directory
_MACRO_DIR = os.path.join(
    os.path.dirname(__file__),
    "..",
    "dbt",
    "include",
    "flink",
    "macros",
)
_MACRO_DIR = os.path.normpath(_MACRO_DIR)


class _FakeExceptions:
    """Mimics dbt's exceptions object for macro validation."""

    @staticmethod
    def raise_compiler_error(msg: str) -> None:
        raise Exception(msg)


def _log(msg: str, info: bool = False) -> str:
    """No-op log function matching dbt's Jinja log()."""
    return ""


def _return(value: Any) -> Any:
    """Mimics dbt's {{ return(value) }} Jinja extension.

    In dbt, return() sets the macro's return value. In our test
    environment, we just pass through the value so it gets rendered.
    """
    return value


def _statement(name: str = "", auto_begin: bool = True, **kwargs: Any) -> str:
    """No-op callable mimicking dbt's {% call statement() %} block.

    In Jinja2, {% call statement() %}...{% endcall %} calls
    statement(caller=<fn>) where caller() returns the block content.
    The return value replaces the entire call block in the output.

    We invoke caller() to capture the SQL block content and return it
    so it appears in the rendered output for test assertions.
    """
    caller = kwargs.get("caller")
    if caller:
        return caller()
    return ""


def _make_env() -> Environment:
    """Create a Jinja2 environment matching dbt's macro rendering context."""
    env = Environment(
        loader=FileSystemLoader(_MACRO_DIR),
        extensions=["jinja2.ext.do"],
    )

    # Provide dbt-like globals that macros depend on
    env.globals["exceptions"] = _FakeExceptions()
    env.globals["log"] = _log
    env.globals["return"] = _return
    env.globals["statement"] = _statement

    # Pre-load all macro files so cross-imports resolve
    for root, _dirs, files in os.walk(_MACRO_DIR):
        for fname in files:
            if fname.endswith(".sql"):
                rel = os.path.relpath(os.path.join(root, fname), _MACRO_DIR)
                try:
                    env.get_template(rel)
                except Exception:
                    pass  # Some templates may have dbt-only constructs

    return env


# Module-level singleton
_ENV = _make_env()


def render_template(template_str: str) -> str:
    """Render an arbitrary Jinja template string using the adapter's macros.

    Args:
        template_str: Jinja template string. Use {% import %} to access macros.

    Returns:
        Rendered string with whitespace stripped.

    Example:
        result = render_template(
            "{% import 'catalogs/iceberg.sql' as ice %}"
            "{{ ice.iceberg_table_properties(format_version=2) }}"
        )
    """
    template = _ENV.from_string(template_str)
    return template.render().strip()


def render_macro(macro_path: str, **kwargs: Any) -> str:
    """Render a specific macro by dotted path with keyword arguments.

    The macro_path format is: '<import_alias>.<macro_name>'
    where the import alias maps to a file in the catalogs/ directory.

    Supported aliases:
        iceberg -> catalogs/iceberg.sql
        iceberg_tt -> catalogs/iceberg_time_travel.sql
        snowflake -> catalogs/snowflake.sql
        delta -> catalogs/delta.sql
        hudi -> catalogs/hudi.sql
        paimon -> catalogs/paimon.sql
        fluss -> catalogs/fluss.sql

    Args:
        macro_path: Dotted path like 'iceberg.iceberg_table_properties'
        **kwargs: Keyword arguments to pass to the macro

    Returns:
        Rendered string with whitespace stripped.
    """
    alias_map = {
        "iceberg": "catalogs/iceberg.sql",
        "iceberg_tt": "catalogs/iceberg_time_travel.sql",
        "snowflake": "catalogs/snowflake.sql",
        "delta": "catalogs/delta.sql",
        "hudi": "catalogs/hudi.sql",
        "paimon": "catalogs/paimon.sql",
        "fluss": "catalogs/fluss.sql",
    }

    parts = macro_path.split(".", 1)
    if len(parts) != 2:
        raise ValueError(
            f"macro_path must be 'alias.macro_name', got: {macro_path}"
        )

    alias, macro_name = parts

    if alias not in alias_map:
        raise ValueError(
            f"Unknown macro alias: '{alias}'. "
            f"Available: {', '.join(sorted(alias_map))}"
        )

    template_file = alias_map[alias]

    # Build kwargs string for Jinja call
    kwarg_parts = []
    for key, value in kwargs.items():
        if isinstance(value, bool):
            kwarg_parts.append(f"{key}={'true' if value else 'false'}")
        elif isinstance(value, str):
            kwarg_parts.append(f"{key}='{value}'")
        elif isinstance(value, dict):
            # Convert Python dict to Jinja dict literal
            dict_items = []
            for dk, dv in value.items():
                dict_items.append(f"'{dk}': '{dv}'")
            kwarg_parts.append(f"{key}={{{', '.join(dict_items)}}}")
        elif value is None:
            kwarg_parts.append(f"{key}=none")
        else:
            kwarg_parts.append(f"{key}={value}")

    kwargs_str = ", ".join(kwarg_parts)

    template_str = (
        f"{{% import '{template_file}' as _mod %}}"
        f"{{{{ _mod.{macro_name}({kwargs_str}) }}}}"
    )

    return render_template(template_str)
