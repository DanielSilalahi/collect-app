import datetime
from decimal import Decimal
from typing import Any, Dict
from sqlalchemy.orm import class_mapper

def model_to_dict(obj: Any, include_relationships: bool = False, visited=None) -> Dict[str, Any]:
    """
    Convert a SQLAlchemy model instance to a dictionary.
    Handles Datetime, Date, and Decimal objects for JSON serialization.
    """
    if obj is None:
        return None
    
    if visited is None:
        visited = set()
    
    # Avoid infinite recursion
    obj_id = id(obj)
    if obj_id in visited:
        return {"id": getattr(obj, "id", None)} # Return identifying part
    visited.add(obj_id)

    data = {}
    for column in class_mapper(obj.__class__).columns:
        val = getattr(obj, column.key)
        
        if isinstance(val, (datetime.datetime, datetime.date)):
            data[column.key] = val.isoformat()
        elif isinstance(val, Decimal):
            data[column.key] = float(val)
        else:
            data[column.key] = val
            
    if include_relationships:
        for rel in class_mapper(obj.__class__).relationships:
            # Only include common relationships for archive
            if rel.key in ["loans", "addresses", "contacts", "current_loan", "agent"]:
                val = getattr(obj, rel.key)
                if isinstance(val, list):
                    data[rel.key] = [model_to_dict(item, include_relationships=False, visited=visited) for item in val]
                elif val is not None:
                    data[rel.key] = model_to_dict(val, include_relationships=False, visited=visited)
                    
    return data
