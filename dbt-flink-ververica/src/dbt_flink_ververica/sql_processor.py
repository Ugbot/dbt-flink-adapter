"""SQL processing and transformation for dbt-flink models.

This module handles:
1. Extracting compiled SQL from dbt artifacts
2. Parsing dbt-flink query hints
3. Transforming hints to SET statements
4. Cleaning SQL for Ververica Cloud deployment
"""

import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pydantic import BaseModel, Field


logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

class QueryHint(BaseModel):
    """Represents a parsed dbt-flink query hint.

    Attributes:
        name: Hint name (e.g., 'mode', 'drop_statement')
        value: Hint value (e.g., 'streaming', 'DROP TABLE ...')
        raw: Original raw hint string
    """

    name: str = Field(description="Hint name")
    value: str = Field(description="Hint value")
    raw: str = Field(description="Original raw hint string")


class ProcessedSql(BaseModel):
    """Result of SQL processing.

    Attributes:
        original_sql: Original SQL with hints
        clean_sql: SQL with hints removed
        set_statements: SET statements generated from hints
        drop_statements: DROP statements extracted from hints
        hints: Parsed query hints
        final_sql: Complete SQL ready for deployment
    """

    original_sql: str = Field(description="Original SQL with hints")
    clean_sql: str = Field(description="SQL with hints removed")
    set_statements: List[str] = Field(
        default_factory=list,
        description="SET statements from hints"
    )
    drop_statements: List[str] = Field(
        default_factory=list,
        description="DROP statements from hints"
    )
    hints: List[QueryHint] = Field(
        default_factory=list,
        description="Parsed query hints"
    )
    final_sql: str = Field(description="Complete SQL for deployment")


class CompiledModel(BaseModel):
    """Represents a compiled dbt model.

    Attributes:
        name: Model name
        path: Path to compiled SQL file
        sql: Raw compiled SQL
        processed: Processed SQL (after transformation)
    """

    name: str = Field(description="Model name")
    path: Path = Field(description="Path to compiled SQL file")
    sql: str = Field(description="Raw compiled SQL")
    processed: Optional[ProcessedSql] = Field(
        default=None,
        description="Processed SQL"
    )


# ============================================================================
# SQL Hint Parser
# ============================================================================

class SqlHintParser:
    """Parser for dbt-flink query hints.

    Parses hints in the format: /** hint_name('value') */
    """

    # Regex for matching query hints
    HINT_PATTERN = re.compile(
        r'/\*\*\s*(\w+)\s*\(\s*[\'"]([^\'"]*)[\'"\s]*\)\s*\*/',
        re.IGNORECASE
    )

    @classmethod
    def parse_hints(cls, sql: str) -> List[QueryHint]:
        """Parse all query hints from SQL.

        Args:
            sql: SQL statement with hints

        Returns:
            List of parsed QueryHint objects

        Example:
            >>> sql = "/** mode('streaming') */ SELECT * FROM t"
            >>> hints = SqlHintParser.parse_hints(sql)
            >>> hints[0].name
            'mode'
            >>> hints[0].value
            'streaming'
        """
        hints = []

        for match in cls.HINT_PATTERN.finditer(sql):
            hint_name = match.group(1)
            hint_value = match.group(2)
            hint_raw = match.group(0)

            hints.append(QueryHint(
                name=hint_name,
                value=hint_value,
                raw=hint_raw
            ))

            logger.debug(f"Parsed hint: {hint_name}='{hint_value}'")

        return hints

    @classmethod
    def strip_hints(cls, sql: str) -> str:
        """Remove all query hints from SQL.

        Args:
            sql: SQL statement with hints

        Returns:
            SQL with hints removed
        """
        clean_sql = cls.HINT_PATTERN.sub('', sql)

        # Clean up extra whitespace
        clean_sql = re.sub(r'\n\s*\n', '\n\n', clean_sql)  # Remove extra blank lines
        clean_sql = clean_sql.strip()

        return clean_sql


# ============================================================================
# SQL Transformer
# ============================================================================

class SqlTransformer:
    """Transforms dbt-flink SQL for Ververica Cloud deployment.

    This class handles:
    - Converting query hints to SET statements
    - Extracting DROP statements
    - Cleaning SQL syntax
    """

    # Mapping of hint names to Flink configuration keys
    HINT_TO_CONFIG = {
        'mode': 'execution.runtime-mode',
        'execution_mode': 'execution.runtime-mode',
        'job_state': None,  # Not a Flink config, used by dbt-flink
        'fetch_timeout_ms': 'table.exec.resource.default-parallelism',  # Example mapping
    }

    @classmethod
    def hint_to_set_statement(cls, hint: QueryHint) -> Optional[str]:
        """Convert a query hint to a SET statement.

        Args:
            hint: Parsed query hint

        Returns:
            SET statement or None if hint doesn't map to config

        Example:
            >>> hint = QueryHint(name='mode', value='streaming', raw='...')
            >>> SqlTransformer.hint_to_set_statement(hint)
            "SET 'execution.runtime-mode' = 'streaming';"
        """
        # Special handling for specific hints
        if hint.name == 'mode':
            return f"SET 'execution.runtime-mode' = '{hint.value}';"

        elif hint.name == 'execution_mode':
            return f"SET 'execution.runtime-mode' = '{hint.value}';"

        elif hint.name == 'job_state':
            # job_state is metadata for dbt-flink, not a Flink config
            logger.debug(f"Skipping non-config hint: {hint.name}")
            return None

        elif hint.name == 'drop_statement':
            # drop_statement is handled separately
            return None

        # Check mapping table
        config_key = cls.HINT_TO_CONFIG.get(hint.name)
        if config_key:
            return f"SET '{config_key}' = '{hint.value}';"

        # Unknown hint - log warning but don't fail
        logger.warning(f"Unknown hint '{hint.name}' - skipping SET statement generation")
        return None

    # Pattern to validate DROP statements (prevent SQL injection)
    DROP_PATTERN = re.compile(
        r'^\s*DROP\s+(TABLE|VIEW|DATABASE|CATALOG)\s+(?:IF\s+EXISTS\s+)?'
        r'[\w.`]+\s*(?:CASCADE|RESTRICT)?\s*;?\s*$',
        re.IGNORECASE
    )

    @classmethod
    def extract_drop_statements(cls, hints: List[QueryHint]) -> List[str]:
        """Extract DROP statements from hints.

        Validates DROP statements to prevent SQL injection attacks.

        Args:
            hints: List of parsed hints

        Returns:
            List of validated DROP statements

        Raises:
            ValueError: If DROP statement fails validation
        """
        drop_statements = []

        for hint in hints:
            if hint.name == 'drop_statement':
                # Value contains the DROP statement
                drop_sql = hint.value.strip()

                # Validate it's a safe DROP statement
                if not cls.DROP_PATTERN.match(drop_sql):
                    logger.error(f"Invalid DROP statement format: {drop_sql[:100]}")
                    raise ValueError(
                        f"DROP statement failed security validation. "
                        f"Expected format: DROP [TABLE|VIEW|DATABASE|CATALOG] [IF EXISTS] name [CASCADE|RESTRICT]. "
                        f"Got: {drop_sql[:100]}"
                    )

                # Ensure statement ends with semicolon
                if not drop_sql.endswith(';'):
                    drop_sql += ';'

                drop_statements.append(drop_sql)
                logger.debug(f"Extracted DROP statement: {drop_sql[:50]}...")

        return drop_statements

    @classmethod
    def generate_set_statements(cls, hints: List[QueryHint]) -> List[str]:
        """Generate SET statements from all hints.

        Args:
            hints: List of parsed hints

        Returns:
            List of SET statements
        """
        set_statements = []

        for hint in hints:
            set_stmt = cls.hint_to_set_statement(hint)
            if set_stmt:
                set_statements.append(set_stmt)

        return set_statements


# ============================================================================
# SQL Processor
# ============================================================================

class SqlProcessor:
    """Main SQL processing orchestrator.

    Coordinates parsing, transformation, and assembly of final SQL.
    """

    def __init__(
        self,
        strip_hints: bool = True,
        generate_set_statements: bool = True,
        include_drop_statements: bool = True,
        wrap_in_statement_set: bool = False,
    ):
        """Initialize SQL processor.

        Args:
            strip_hints: Whether to strip query hints
            generate_set_statements: Whether to generate SET statements from hints
            include_drop_statements: Whether to include DROP statements
            wrap_in_statement_set: Whether to wrap in STATEMENT SET
        """
        self.strip_hints = strip_hints
        self.generate_set_statements = generate_set_statements
        self.include_drop_statements = include_drop_statements
        self.wrap_in_statement_set = wrap_in_statement_set

    def process_sql(self, sql: str) -> ProcessedSql:
        """Process SQL statement.

        Args:
            sql: Original SQL with hints

        Returns:
            ProcessedSql with all transformations applied
        """
        # Parse hints
        hints = SqlHintParser.parse_hints(sql)
        logger.info(f"Parsed {len(hints)} query hints")

        # Strip hints if configured
        if self.strip_hints:
            clean_sql = SqlHintParser.strip_hints(sql)
        else:
            clean_sql = sql

        # Generate SET statements if configured
        set_statements = []
        if self.generate_set_statements:
            set_statements = SqlTransformer.generate_set_statements(hints)
            logger.info(f"Generated {len(set_statements)} SET statements")

        # Extract DROP statements if configured
        drop_statements = []
        if self.include_drop_statements:
            drop_statements = SqlTransformer.extract_drop_statements(hints)
            logger.info(f"Extracted {len(drop_statements)} DROP statements")

        # Assemble final SQL
        final_sql = self._assemble_final_sql(
            clean_sql,
            set_statements,
            drop_statements
        )

        return ProcessedSql(
            original_sql=sql,
            clean_sql=clean_sql,
            set_statements=set_statements,
            drop_statements=drop_statements,
            hints=hints,
            final_sql=final_sql
        )

    def _assemble_final_sql(
        self,
        clean_sql: str,
        set_statements: List[str],
        drop_statements: List[str]
    ) -> str:
        """Assemble final SQL from components.

        Args:
            clean_sql: SQL with hints removed
            set_statements: SET statements
            drop_statements: DROP statements

        Returns:
            Complete SQL ready for deployment
        """
        parts = []

        # Add header comment
        parts.append("-- SQL generated by dbt-flink-ververica")
        parts.append("")

        # Add SET statements
        if set_statements:
            parts.append("-- Configuration")
            parts.extend(set_statements)
            parts.append("")

        # Add DROP statements
        if drop_statements:
            parts.append("-- Drop existing objects")
            parts.extend(drop_statements)
            parts.append("")

        # Add main SQL
        parts.append("-- Main SQL")

        if self.wrap_in_statement_set:
            parts.append("BEGIN STATEMENT SET;")
            parts.append("")
            parts.append(clean_sql)
            parts.append("")
            parts.append("END;")
        else:
            parts.append(clean_sql)

        return "\n".join(parts)


# ============================================================================
# dbt Artifact Reader
# ============================================================================

class DbtArtifactReader:
    """Reads compiled SQL from dbt artifacts.

    Extracts compiled models from dbt's target/compiled directory.
    """

    def __init__(self, project_dir: Path, target: str = "dev"):
        """Initialize artifact reader.

        Args:
            project_dir: Path to dbt project root
            target: dbt target name
        """
        self.project_dir = project_dir
        self.target = target
        self.compiled_dir = project_dir / "target" / "compiled"

    def find_compiled_models(
        self,
        models: Optional[List[str]] = None
    ) -> List[CompiledModel]:
        """Find compiled SQL files.

        Args:
            models: Optional list of specific model names to find

        Returns:
            List of CompiledModel objects

        Raises:
            FileNotFoundError: If target/compiled directory doesn't exist
        """
        if not self.compiled_dir.exists():
            raise FileNotFoundError(
                f"dbt compiled directory not found: {self.compiled_dir}\n"
                f"Run 'dbt compile' first to generate compiled artifacts."
            )

        compiled_models = []

        # Find all .sql files in target/compiled
        for sql_file in self.compiled_dir.rglob("*.sql"):
            model_name = sql_file.stem

            # Filter by model names if specified
            if models and model_name not in models:
                continue

            # Read SQL content
            try:
                sql_content = sql_file.read_text(encoding='utf-8')

                compiled_models.append(CompiledModel(
                    name=model_name,
                    path=sql_file,
                    sql=sql_content
                ))

                logger.debug(f"Found compiled model: {model_name} ({sql_file})")

            except Exception as e:
                logger.error(f"Failed to read {sql_file}: {e}")
                continue

        logger.info(f"Found {len(compiled_models)} compiled models")
        return compiled_models

    def process_models(
        self,
        models: List[CompiledModel],
        processor: SqlProcessor
    ) -> List[CompiledModel]:
        """Process multiple models with SQL processor.

        Args:
            models: List of compiled models
            processor: SQL processor instance

        Returns:
            Models with processed SQL attached
        """
        for model in models:
            logger.info(f"Processing model: {model.name}")

            try:
                processed = processor.process_sql(model.sql)
                model.processed = processed

            except Exception as e:
                logger.error(f"Failed to process model {model.name}: {e}")
                raise

        return models

    def write_processed_sql(
        self,
        model: CompiledModel,
        output_dir: Path
    ) -> Path:
        """Write processed SQL to output file.

        Args:
            model: Compiled model with processed SQL
            output_dir: Directory to write output

        Returns:
            Path to written file

        Raises:
            ValueError: If model hasn't been processed yet
        """
        if model.processed is None:
            raise ValueError(f"Model {model.name} has not been processed yet")

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Write file
        output_file = output_dir / f"{model.name}.sql"
        output_file.write_text(model.processed.final_sql, encoding='utf-8')

        logger.info(f"Wrote processed SQL: {output_file}")
        return output_file
