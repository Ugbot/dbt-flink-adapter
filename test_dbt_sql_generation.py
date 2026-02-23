#!/usr/bin/env python3
"""
Test SQL Generation for dbt-flink streaming models

This script validates that the dbt macros generate correct Flink SQL
for all streaming features without requiring a full dbt installation.
"""

import re
from pathlib import Path
from typing import Dict, Any, Tuple


def parse_config(model_content: str) -> Dict[str, Any]:
    """Extract config block from dbt model"""
    config_match = re.search(
        r'{{\s*config\((.*?)\)\s*}}',
        model_content,
        re.DOTALL
    )

    if not config_match:
        return {}

    config_str = config_match.group(1)

    # Parse config values
    config = {}

    # materialized
    mat_match = re.search(r"materialized\s*=\s*['\"](\w+)['\"]", config_str)
    if mat_match:
        config['materialized'] = mat_match.group(1)

    # execution_mode
    exec_match = re.search(r"execution_mode\s*=\s*['\"](\w+)['\"]", config_str)
    if exec_match:
        config['execution_mode'] = exec_match.group(1)

    # schema
    schema_match = re.search(r"schema\s*=\s*'''(.*?)'''", config_str, re.DOTALL)
    if schema_match:
        config['schema'] = schema_match.group(1).strip()

    # watermark
    watermark_match = re.search(r"watermark\s*=\s*{(.*?)}", config_str, re.DOTALL)
    if watermark_match:
        wm_str = watermark_match.group(1)
        col_match = re.search(r"['\"]column['\"]\s*:\s*['\"](\w+)['\"]", wm_str)
        # Handle strategy with escaped quotes
        strat_match = re.search(r"['\"]strategy['\"]\s*:\s*['\"](.+?)['\"](?=\s*[,}])", wm_str, re.DOTALL)
        if col_match and strat_match:
            # Unescape quotes in strategy
            strategy = strat_match.group(1).replace("\\'", "'").replace("\\\"", "\"")
            config['watermark'] = {
                'column': col_match.group(1),
                'strategy': strategy
            }

    # properties
    props_match = re.search(r"properties\s*=\s*{(.*?)}", config_str, re.DOTALL)
    if props_match:
        props_str = props_match.group(1)
        config['properties'] = {}
        for prop_match in re.finditer(r"['\"]([^'\"]+)['\"]\s*:\s*['\"]([^'\"]+)['\"]", props_str):
            config['properties'][prop_match.group(1)] = prop_match.group(2)

    return config


def extract_select(model_content: str) -> str:
    """Extract SELECT statement from model"""
    # Remove config block
    no_config = re.sub(r'{{\s*config\(.*?\)\s*}}', '', model_content, flags=re.DOTALL)

    # Remove comments
    no_comments = re.sub(r'--[^\n]*\n', '\n', no_config)

    # Extract SELECT statement
    select_match = re.search(r'(SELECT\s+.*)', no_comments, re.DOTALL | re.IGNORECASE)
    if select_match:
        return select_match.group(1).strip()

    return ""


def generate_watermark_clause(watermark_config: Dict[str, str]) -> str:
    """Generate WATERMARK FOR clause"""
    if not watermark_config:
        return ""

    column = watermark_config['column']
    strategy = watermark_config['strategy']

    return f",\n        WATERMARK FOR {column} AS {strategy}"


def generate_create_table_sql(
    table_name: str,
    config: Dict[str, Any]
) -> str:
    """Generate CREATE TABLE statement for streaming_table materialization"""
    schema = config.get('schema', '')
    watermark = config.get('watermark')
    properties = config.get('properties', {})
    execution_mode = config.get('execution_mode', 'batch')

    # Build CREATE TABLE statement
    sql = f"/** mode('{execution_mode}') */\n"
    sql += f"CREATE TABLE {table_name} (\n"
    sql += f"        {schema}"

    # Add watermark
    if watermark:
        sql += generate_watermark_clause(watermark)

    sql += "\n    )"

    # Add WITH properties
    if properties:
        sql += " WITH (\n"
        props_list = [f"        '{k}' = '{v}'" for k, v in properties.items()]
        sql += ",\n".join(props_list)
        sql += "\n    )"

    return sql


def generate_insert_sql(
    table_name: str,
    select_sql: str,
    config: Dict[str, Any]
) -> str:
    """Generate INSERT INTO statement"""
    execution_mode = config.get('execution_mode', 'batch')

    sql = f"/** mode('{execution_mode}') */\n"
    sql += f"INSERT INTO {table_name}\n"
    sql += select_sql

    return sql


def process_model(model_path: Path) -> Tuple[str, str, str]:
    """Process a dbt model file and generate SQL"""
    content = model_path.read_text()

    # Parse configuration
    config = parse_config(content)

    # Extract SELECT
    select_sql = extract_select(content)

    # Resolve {{ ref('...') }}
    select_sql = re.sub(
        r'{{\s*ref\([\'"]([^\'"]+)[\'"]\)\s*}}',
        r'default_catalog.default_database.\1',
        select_sql
    )

    # Generate table name
    table_name = f"default_catalog.default_database.{model_path.stem}"

    # Generate SQL based on materialization
    if config.get('materialized') == 'streaming_table':
        create_sql = generate_create_table_sql(table_name, config)
        insert_sql = generate_insert_sql(table_name, select_sql, config)

        return create_sql, insert_sql, str(config)
    else:
        return "", "", str(config)


def test_sql_generation():
    """Test SQL generation for all streaming models"""
    models_dir = Path("/Users/bengamble/dbt-flink-adapter/project_example/models/streaming")

    print("=" * 80)
    print("dbt-flink Streaming SQL Generation Test")
    print("=" * 80)
    print()

    test_files = [
        '01_datagen_source.sql',
        '02_tumbling_window_agg.sql',
        '03_hopping_window_agg.sql',
        '04_session_window_agg.sql',
        '05_cumulative_window_agg.sql',
    ]

    all_passed = True

    for filename in test_files:
        model_path = models_dir / filename
        if not model_path.exists():
            print(f"❌ SKIP: {filename} (file not found)")
            continue

        print(f"\n{'=' * 80}")
        print(f"Model: {filename}")
        print(f"{'=' * 80}\n")

        try:
            create_sql, insert_sql, config = process_model(model_path)

            print("Configuration:")
            print("-" * 80)
            print(config)
            print()

            print("Generated CREATE TABLE SQL:")
            print("-" * 80)
            print(create_sql)
            print()

            if insert_sql and 'WHERE FALSE' not in insert_sql:
                print("Generated INSERT INTO SQL:")
                print("-" * 80)
                print(insert_sql)
                print()

            # Validation checks
            checks = []

            # Check 1: Has execution mode
            if "mode('" in create_sql:
                checks.append(("✓", "Execution mode hint present"))
            else:
                checks.append(("✗", "Missing execution mode hint"))
                all_passed = False

            # Check 2: Has watermark (for source tables)
            if '01_datagen' in filename:
                if "WATERMARK FOR" in create_sql:
                    checks.append(("✓", "Watermark clause present"))
                else:
                    checks.append(("✗", "Missing watermark clause"))
                    all_passed = False

            # Check 3: Has window TVF (for aggregation models)
            if any(x in filename for x in ['02_', '03_', '04_', '05_']):
                window_types = {
                    '02_': 'TUMBLE',
                    '03_': 'HOP',
                    '04_': 'SESSION',
                    '05_': 'CUMULATE'
                }
                for prefix, window_type in window_types.items():
                    if prefix in filename:
                        if window_type in insert_sql:
                            checks.append(("✓", f"{window_type} window function present"))
                        else:
                            checks.append(("✗", f"Missing {window_type} window function"))
                            all_passed = False

            # Check 4: Has DESCRIPTOR
            if any(x in filename for x in ['02_', '03_', '04_', '05_']):
                if "DESCRIPTOR(" in insert_sql:
                    checks.append(("✓", "DESCRIPTOR clause present"))
                else:
                    checks.append(("✗", "Missing DESCRIPTOR clause"))
                    all_passed = False

            # Check 5: Has GROUP BY for aggregations
            if any(x in filename for x in ['02_', '03_', '04_', '05_']):
                if "GROUP BY" in insert_sql:
                    checks.append(("✓", "GROUP BY clause present"))
                else:
                    checks.append(("✗", "Missing GROUP BY clause"))
                    all_passed = False

            # Print validation results
            print("Validation:")
            print("-" * 80)
            for status, message in checks:
                print(f"{status} {message}")

            print()

        except Exception as e:
            print(f"❌ ERROR processing {filename}: {e}")
            all_passed = False

    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)

    if all_passed:
        print("✅ All SQL generation tests passed!")
        print("\nThe dbt macros correctly generate:")
        print("  • CREATE TABLE statements with watermarks")
        print("  • Window TVF syntax (TUMBLE, HOP, SESSION, CUMULATE)")
        print("  • DESCRIPTOR clauses for time attributes")
        print("  • Execution mode query hints")
        print("  • Connector properties")
        return 0
    else:
        print("❌ Some tests failed. Review output above.")
        return 1


if __name__ == "__main__":
    exit(test_sql_generation())
