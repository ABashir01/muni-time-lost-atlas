{% test unique_column_combination(model, columns) %}
with validation_errors as (
    select
        {% for column in columns %}
        {{ column }}{% if not loop.last %}, {% endif %}
        {% endfor %},
        count(*) as row_count
    from {{ model }}
    group by
        {% for column in columns %}
        {{ column }}{% if not loop.last %}, {% endif %}
        {% endfor %}
    having count(*) > 1
)
select *
from validation_errors
{% endtest %}
