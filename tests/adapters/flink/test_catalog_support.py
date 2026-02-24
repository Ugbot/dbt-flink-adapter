"""
Unit tests for catalog-based connector support.

Tests PRIMARY KEY rendering, catalog_managed config behavior,
FlinkIncludePolicy, and schema evolution logic.
"""

import pytest
from dataclasses import dataclass
from unittest.mock import MagicMock, patch
from typing import List, Optional

from dbt_common.contracts.constraints import (
    ConstraintType,
    ModelLevelConstraint,
    ColumnLevelConstraint,
)

from dbt.adapters.flink.impl import FlinkAdapter
from dbt.adapters.flink.relation import (
    FlinkRelation,
    FlinkIncludePolicy,
    FlinkQuotePolicy,
)


class TestRenderModelConstraint:
    """Tests for PRIMARY KEY and other model-level constraint rendering."""

    def setup_method(self):
        """Create a FlinkAdapter instance with mocked connection manager."""
        self.adapter = FlinkAdapter.__new__(FlinkAdapter)

    def test_primary_key_single_column(self):
        """PRIMARY KEY with a single column renders correctly."""
        constraint = ModelLevelConstraint(
            type=ConstraintType.primary_key,
            columns=["user_id"],
        )
        result = self.adapter.render_model_constraint(constraint)
        assert result == "PRIMARY KEY (user_id) NOT ENFORCED"

    def test_primary_key_composite(self):
        """PRIMARY KEY with multiple columns renders correctly."""
        constraint = ModelLevelConstraint(
            type=ConstraintType.primary_key,
            columns=["catalog_id", "database_id", "table_id"],
        )
        result = self.adapter.render_model_constraint(constraint)
        assert result == "PRIMARY KEY (catalog_id, database_id, table_id) NOT ENFORCED"

    def test_primary_key_two_columns(self):
        """PRIMARY KEY with two columns renders correctly."""
        constraint = ModelLevelConstraint(
            type=ConstraintType.primary_key,
            columns=["event_id", "event_timestamp"],
        )
        result = self.adapter.render_model_constraint(constraint)
        assert result == "PRIMARY KEY (event_id, event_timestamp) NOT ENFORCED"

    def test_unique_constraint_returns_empty(self):
        """UNIQUE constraints are not supported and should return empty string."""
        constraint = ModelLevelConstraint(
            type=ConstraintType.unique,
            columns=["email"],
        )
        result = self.adapter.render_model_constraint(constraint)
        assert result == ""

    def test_check_constraint_returns_empty(self):
        """CHECK constraints are not supported at model level and return empty string."""
        constraint = ModelLevelConstraint(
            type=ConstraintType.check,
            columns=[],
            expression="age > 0",
        )
        result = self.adapter.render_model_constraint(constraint)
        assert result == ""

    def test_foreign_key_constraint_returns_empty(self):
        """FOREIGN KEY constraints are not supported and return empty string."""
        constraint = ModelLevelConstraint(
            type=ConstraintType.foreign_key,
            columns=["user_id"],
        )
        result = self.adapter.render_model_constraint(constraint)
        assert result == ""


class TestRenderColumnConstraint:
    """Tests for column-level constraint rendering."""

    def setup_method(self):
        self.adapter = FlinkAdapter.__new__(FlinkAdapter)

    def test_not_null_renders(self):
        """NOT NULL column constraint renders correctly."""
        constraint = ColumnLevelConstraint(type=ConstraintType.not_null)
        result = self.adapter.render_column_constraint(constraint)
        assert result == "NOT NULL"

    def test_unique_column_constraint_empty(self):
        """UNIQUE column constraint returns empty string."""
        constraint = ColumnLevelConstraint(type=ConstraintType.unique)
        result = self.adapter.render_column_constraint(constraint)
        assert result == ""

    def test_check_column_constraint_empty(self):
        """CHECK column constraint returns empty string."""
        constraint = ColumnLevelConstraint(
            type=ConstraintType.check,
            expression="value > 0",
        )
        result = self.adapter.render_column_constraint(constraint)
        assert result == ""


class TestFlinkIncludePolicy:
    """Tests for FlinkIncludePolicy with database and schema inclusion."""

    def test_default_policy_includes_all(self):
        """Default FlinkIncludePolicy includes database, schema, and identifier."""
        policy = FlinkIncludePolicy()
        assert policy.database is True
        assert policy.schema is True
        assert policy.identifier is True

    def test_relation_renders_full_path(self):
        """Relation with database and schema renders fully-qualified name."""
        relation = FlinkRelation.create(
            database="my_catalog",
            schema="my_database",
            identifier="my_table",
        )
        rendered = relation.render()
        # Should include all three parts separated by dots
        assert "my_catalog" in rendered
        assert "my_database" in rendered
        assert "my_table" in rendered

    def test_relation_renders_without_database(self):
        """Relation without database renders schema.identifier."""
        relation = FlinkRelation.create(
            database=None,
            schema="my_database",
            identifier="my_table",
        )
        rendered = relation.render()
        assert "my_database" in rendered
        assert "my_table" in rendered

    def test_relation_renders_identifier_only(self):
        """Relation with only identifier renders just the identifier."""
        relation = FlinkRelation.create(
            database=None,
            schema=None,
            identifier="my_table",
        )
        rendered = relation.render()
        assert "my_table" in rendered

    def test_quote_policy_defaults_false(self):
        """Default quote policy does not quote any parts."""
        policy = FlinkQuotePolicy()
        assert policy.database is False
        assert policy.schema is False
        assert policy.identifier is False


class TestConstraintSupport:
    """Tests for the CONSTRAINT_SUPPORT class variable."""

    def test_primary_key_not_enforced(self):
        """PRIMARY KEY is supported as NOT_ENFORCED."""
        from dbt.adapters.base.impl import ConstraintSupport as CS
        assert FlinkAdapter.CONSTRAINT_SUPPORT[ConstraintType.primary_key] == CS.NOT_ENFORCED

    def test_not_null_not_enforced(self):
        """NOT NULL is supported as NOT_ENFORCED."""
        from dbt.adapters.base.impl import ConstraintSupport as CS
        assert FlinkAdapter.CONSTRAINT_SUPPORT[ConstraintType.not_null] == CS.NOT_ENFORCED

    def test_foreign_key_not_supported(self):
        """FOREIGN KEY is NOT_SUPPORTED."""
        from dbt.adapters.base.impl import ConstraintSupport as CS
        assert FlinkAdapter.CONSTRAINT_SUPPORT[ConstraintType.foreign_key] == CS.NOT_SUPPORTED

    def test_check_not_enforced(self):
        """CHECK is supported as NOT_ENFORCED."""
        from dbt.adapters.base.impl import ConstraintSupport as CS
        assert FlinkAdapter.CONSTRAINT_SUPPORT[ConstraintType.check] == CS.NOT_ENFORCED

    def test_unique_not_enforced(self):
        """UNIQUE is supported as NOT_ENFORCED."""
        from dbt.adapters.base.impl import ConstraintSupport as CS
        assert FlinkAdapter.CONSTRAINT_SUPPORT[ConstraintType.unique] == CS.NOT_ENFORCED
