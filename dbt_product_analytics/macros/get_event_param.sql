{#
  Macro: get_event_param
  
  Safely extracts a value from the GA4 event_params repeated record.
  GA4 stores event parameters as an ARRAY<STRUCT<key STRING, value STRUCT<...>>>.
  Each parameter value can be stored in one of several typed sub-fields.
  
  Arguments:
    - param_key (string): The event parameter key to extract (e.g., 'ga_session_id')
    - value_type (string): Which sub-field to read. One of:
        'string_value', 'int_value', 'double_value', 'float_value'
  
  Usage:
    {{ get_event_param('ga_session_id', 'int_value') }}
    {{ get_event_param('page_location', 'string_value') }}
  
  Returns NULL if the parameter key is not present or the typed sub-field is NULL.
#}

{% macro get_event_param(param_key, value_type) %}
(
    select event_params.value.{{ value_type }}
    from unnest(event_params) as event_params
    where event_params.key = '{{ param_key }}'
    limit 1
)
{% endmacro %}
