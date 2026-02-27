"""Minimal Jinja rendering harness for CDC source macro testing.

Provides _CompilerError and _render_source_sql for use by CDC test modules.
Does NOT depend on dbt or a running Flink cluster.
"""

import pathlib
from typing import Optional

from jinja2 import DictLoader, Environment


class _CompilerError(Exception):
    """Simulates dbt's compilation error in our test harness."""


class _ExceptionNamespace:
    """Namespace that mimics dbt's ``exceptions`` module in Jinja."""

    @staticmethod
    def raise_compiler_error(msg: str) -> None:
        raise _CompilerError(msg)


def _load_macros() -> str:
    """Load the source and CDC validation macros as raw Jinja text."""
    macro_dir = (
        pathlib.Path(__file__).resolve().parents[3]
        / "dbt"
        / "include"
        / "flink"
        / "macros"
        / "materializations"
        / "sources"
    )
    source_macro = (macro_dir / "source.sql").read_text()
    cdc_validation = (macro_dir / "cdc_validation.sql").read_text()
    cdc_helpers = (macro_dir / "cdc_helpers.sql").read_text()
    return source_macro + "\n" + cdc_validation + "\n" + cdc_helpers


class _RunQueryCapture:
    """Captures the SQL passed to run_query() during macro rendering."""

    def __init__(self) -> None:
        self.captured_sql: list[str] = []

    def __call__(self, sql: str) -> str:
        self.captured_sql.append(sql)
        return ""


def _render_source_sql(
    columns: list[dict],
    connector_properties: dict,
    primary_key: Optional[list[str]] = None,
    watermark: Optional[dict] = None,
    identifier: str = "test_table",
    catalog_managed: bool = False,
) -> str:
    """Render the source macro for a single source and return the generated SQL.

    This builds a minimal Jinja environment with the macros loaded and
    a fake ``graph.sources`` dict matching the macro's expectations.

    Returns the SQL that would be passed to ``run_query()`` — i.e., the
    CREATE TABLE DDL statement — not the template output (which is mostly
    whitespace and log messages).
    """
    macro_text = _load_macros()

    # Build a columns dict keyed by column name (matching dbt's structure)
    columns_dict = {}
    for col in columns:
        name = col["name"]
        columns_dict[name] = {
            "name": name,
            "data_type": col.get("data_type", "STRING"),
            "column_type": col.get("column_type", "physical"),
            "expression": col.get("expression"),
        }

    node = {
        "identifier": identifier,
        "config": {
            "connector_properties": connector_properties,
            "default_connector_properties": {},
            "catalog_managed": catalog_managed,
            "type": "streaming",
            "primary_key": primary_key or [],
            "watermark": watermark,
        },
        "columns": columns_dict,
    }

    template_str = macro_text + "\n" + "{{ create_sources() }}"

    env = Environment(
        loader=DictLoader({"tpl": template_str}),
        extensions=["jinja2.ext.do"],
    )
    template = env.get_template("tpl")

    # Capture the SQL that create_sources passes to run_query
    capture = _RunQueryCapture()

    template.render(
        execute=True,
        graph={"sources": {"src_0": node}},
        exceptions=_ExceptionNamespace(),
        log=lambda *a, **kw: "",
        run_query=capture,
    )

    # Return the captured SQL (first call, since we have one source)
    if capture.captured_sql:
        return capture.captured_sql[0].strip()
    return ""
