"""Convert nested native tool values to JSON without changing their content."""
def to_json(value):
    if hasattr(value,'model_dump'):return to_json(value.model_dump(mode='json'))
    if isinstance(value,dict):return {k:to_json(v) for k,v in value.items()}
    if isinstance(value,(list,tuple)):return [to_json(v) for v in value]
    return value
