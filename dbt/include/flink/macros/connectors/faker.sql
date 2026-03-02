{#
    Faker Connector Macros

    Convenience macro that returns a validated connector properties dict for
    the Faker source connector. Generates random test data using Java Faker
    expressions — a more expressive alternative to the built-in datagen connector.

    Faker reference:
    https://docs.ververica.com/managed-service/reference/connectors/faker/

    Java Faker expressions reference:
    https://www.datafaker.net/documentation/expressions/

    Requirements:
      - Faker connector JAR on Flink classpath
#}


{% macro faker_source_properties(
    field_expressions,
    rows_per_second=10000,
    number_of_rows=none,
    null_rates={},
    array_lengths={},
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for a Faker source.

    Generates random test data based on Java Faker expressions. Each column
    maps to a Faker expression that produces realistic data.

    Args:
        field_expressions: Dict mapping column names to Faker expressions.
            Format: {'column_name': "#{ClassName.methodName 'param1','param2'}"}
        rows_per_second: Generation rate per second (default: 10000)
        number_of_rows: Total rows to generate. If set, source is bounded (batch).
            If omitted, source is unbounded (streaming).
        null_rates: Dict mapping column names to null probability (0.0 to 1.0).
            Example: {'email': 0.1} means 10% of email values will be null.
        array_lengths: Dict mapping column names to collection size for ARRAY/MAP/MULTISET types.
            Example: {'tags': 3} generates arrays of length 3.
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Expression syntax:
        #{className.methodName 'parameter1','parameter2'}

        Common expressions:
          - #{Name.fullName}           — "John Smith"
          - #{Internet.emailAddress}   — "john@example.com"
          - #{Address.city}            — "New York"
          - #{PhoneNumber.cellPhone}   — "+1-555-123-4567"
          - #{Lorem.sentence}          — "Lorem ipsum dolor sit amet"
          - #{number.numberBetween '1','1000'} — random int 1-1000
          - #{date.birthday}           — random date
          - #{UUID}                    — random UUID

    Example:
        {{ config(
            materialized='table',
            connector_properties=faker_source_properties(
                field_expressions={
                    'user_id': "#{UUID}",
                    'name': "#{Name.fullName}",
                    'email': "#{Internet.emailAddress}",
                    'age': "#{number.numberBetween '18','99'}",
                    'city': "#{Address.city}"
                },
                rows_per_second=1000,
                number_of_rows=100000,
                null_rates={'email': 0.05}
            )
        ) }}
    #}

    {% if not field_expressions or field_expressions | length == 0 %}
        {% do exceptions.raise_compiler_error(
            'faker_source_properties requires at least one entry in "field_expressions". '
            ~ 'Example: {"name": "#{Name.fullName}", "email": "#{Internet.emailAddress}"}'
        ) %}
    {% endif %}

    {% set props = {
        'connector': 'faker',
        'rows-per-second': rows_per_second | string
    } %}

    {% if number_of_rows is not none %}
        {% set _dummy = props.update({'number-of-rows': number_of_rows | string}) %}
    {% endif %}

    {# Build fields.<name>.expression entries #}
    {% for field_name, expression in field_expressions.items() %}
        {% set _dummy = props.update({'fields.' ~ field_name ~ '.expression': expression}) %}
    {% endfor %}

    {# Build fields.<name>.null-rate entries #}
    {% for field_name, rate in null_rates.items() %}
        {% set _dummy = props.update({'fields.' ~ field_name ~ '.null-rate': rate | string}) %}
    {% endfor %}

    {# Build fields.<name>.length entries for collection types #}
    {% for field_name, length in array_lengths.items() %}
        {% set _dummy = props.update({'fields.' ~ field_name ~ '.length': length | string}) %}
    {% endfor %}

    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}
