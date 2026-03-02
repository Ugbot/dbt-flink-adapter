{#
    Redis Connector Macros

    Convenience macros that return validated connector property dicts for
    Redis sink and dimension (lookup join) configurations.

    Redis supports two roles in Flink:
      - Sink (result table): Write data to Redis data structures
      - Dimension table: Lookup joins against Redis for enrichment

    Redis reference:
    https://docs.ververica.com/managed-service/reference/connectors/redis/

    Requirements:
      - Redis connector JAR on Flink classpath
      - Redis server accessible from Flink cluster
#}


{% macro redis_sink_properties(
    host,
    mode,
    port=6379,
    password=none,
    db_num=0,
    cluster_mode=false,
    ignore_delete=false,
    expiration=0,
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for a Redis sink.

    Writes Flink data into Redis data structures. The 'mode' parameter
    determines which Redis data structure is used.

    Args:
        host: Redis server connection address
        mode: Redis data structure mode — determines how data maps to Redis.
            Common modes: 'string', 'hashmap', 'list', 'set', 'sortedset'
        port: Redis server port (default: 6379)
        password: Authentication password (optional)
        db_num: Redis database number (default: 0)
        cluster_mode: Whether Redis is in cluster mode (default: false)
        ignore_delete: Whether to ignore retraction/DELETE messages (default: false)
        expiration: TTL in seconds for written keys (default: 0 = no expiration)
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Example:
        {{ config(
            materialized='streaming_table',
            connector_properties=redis_sink_properties(
                host='redis.example.com',
                mode='hashmap',
                password=env_var('REDIS_PASSWORD')
            )
        ) }}
    #}

    {% if not host %}
        {% do exceptions.raise_compiler_error(
            'redis_sink_properties requires "host" parameter'
        ) %}
    {% endif %}
    {% if not mode %}
        {% do exceptions.raise_compiler_error(
            'redis_sink_properties requires "mode" parameter. '
            ~ 'Specifies the Redis data structure (e.g., "string", "hashmap", "list", "set", "sortedset").'
        ) %}
    {% endif %}
    {% set valid_modes = ['string', 'hashmap', 'list', 'set', 'sortedset'] %}
    {% if mode not in valid_modes %}
        {% do exceptions.raise_compiler_error(
            'Invalid Redis mode: "' ~ mode ~ '". '
            ~ 'Valid values: ' ~ valid_modes | join(', ')
        ) %}
    {% endif %}

    {% set props = {
        'connector': 'redis',
        'host': host,
        'port': port | string,
        'dbNum': db_num | string,
        'clusterMode': cluster_mode | string | lower,
        'mode': mode,
        'ignoreDelete': ignore_delete | string | lower,
        'expiration': expiration | string
    } %}

    {% if password is not none %}
        {% set _dummy = props.update({'password': password}) %}
    {% endif %}

    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}


{% macro redis_dimension_properties(
    host,
    port=6379,
    password=none,
    db_num=0,
    cluster_mode=false,
    hash_name=none,
    cache='None',
    cache_size=10000,
    cache_ttl_ms=none,
    cache_empty=true,
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for a Redis dimension table.

    Redis dimension tables support lookup joins for real-time enrichment.
    The table must declare exactly one primary key column.

    Args:
        host: Redis server connection address
        port: Redis server port (default: 6379)
        password: Authentication password (optional)
        db_num: Redis database number (default: 0)
        cluster_mode: Whether Redis is in cluster mode (default: false)
        hash_name: Hash key name when using hash mode (optional)
        cache: Caching strategy — 'None' (default) or 'LRU'
        cache_size: Max cached rows when cache='LRU' (default: 10000)
        cache_ttl_ms: Cache entry timeout in milliseconds (optional)
        cache_empty: Whether to cache empty/miss results (default: true)
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Example:
        Define as a source with primary_key for lookup joins:

        sources:
          - name: enrichment
            tables:
              - name: user_cache
                config:
                  primary_key: [user_id]
                  connector_properties: {{ redis_dimension_properties(
                      host='redis.example.com',
                      cache='LRU',
                      cache_size=50000,
                      cache_ttl_ms=60000
                  ) }}
    #}

    {% if not host %}
        {% do exceptions.raise_compiler_error(
            'redis_dimension_properties requires "host" parameter'
        ) %}
    {% endif %}

    {% set valid_cache = ['None', 'LRU'] %}
    {% if cache not in valid_cache %}
        {% do exceptions.raise_compiler_error(
            'Invalid Redis cache strategy: "' ~ cache ~ '". '
            ~ 'Valid values: ' ~ valid_cache | join(', ')
        ) %}
    {% endif %}

    {% set props = {
        'connector': 'redis',
        'host': host,
        'port': port | string,
        'dbNum': db_num | string,
        'clusterMode': cluster_mode | string | lower,
        'cache': cache,
        'cacheSize': cache_size | string,
        'cacheEmpty': cache_empty | string | lower
    } %}

    {% if password is not none %}
        {% set _dummy = props.update({'password': password}) %}
    {% endif %}
    {% if hash_name is not none %}
        {% set _dummy = props.update({'hashName': hash_name}) %}
    {% endif %}
    {% if cache_ttl_ms is not none %}
        {% set _dummy = props.update({'cacheTTLMs': cache_ttl_ms | string}) %}
    {% endif %}

    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}
