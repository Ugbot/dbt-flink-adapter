import pytest

from dbt.tests.adapter.basic.test_base import BaseSimpleMaterializations
from dbt.tests.adapter.basic.test_singular_tests import BaseSingularTests
from dbt.tests.adapter.basic.test_empty import BaseEmpty
from dbt.tests.adapter.basic.test_generic_tests import BaseGenericTests


@pytest.mark.integration
@pytest.mark.skip(
    reason="Requires INSERT+SELECT capable connector. "
    "Flink in-memory catalog needs external storage (Kafka/JDBC) for seed round-trips."
)
class TestSimpleMaterializationsFlink(BaseSimpleMaterializations):
    pass


@pytest.mark.integration
class TestSingularTestsFlink(BaseSingularTests):
    pass


@pytest.mark.integration
class TestEmptyFlink(BaseEmpty):
    pass


@pytest.mark.integration
@pytest.mark.skip(
    reason="Requires INSERT+SELECT capable connector. "
    "Flink in-memory catalog needs external storage (Kafka/JDBC) for seed round-trips."
)
class TestGenericTestsFlink(BaseGenericTests):
    pass
