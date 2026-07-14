{% macro generate_schema_name(custom_schema_name, node) -%}

    {%- set default_schema = target.schema -%}
    
    {%- if custom_schema_name is none -%}

        {# If no custom schema is provided, use the default target schema #}
        {{ default_schema }}

    {%- else -%}

        {# If a custom schema IS provided, use ONLY the custom schema #}
        {{ custom_schema_name | trim }}

    {%- endif -%}

{%- endmacro %}