import importlib
from revolve.db.adapter import DatabaseAdapter

def get_adapter(db_type: str = "postgres") -> DatabaseAdapter:
    module_name = f"revolve.db.{db_type}_adapter"
    class_name = f"{db_type.capitalize()}Adapter"

    try:
        module = importlib.import_module(module_name)
        adapter_class = getattr(module, class_name)
        return adapter_class()
    except (ModuleNotFoundError, AttributeError) as e:
        raise ImportError(f"Could not load adapter for '{db_type}': {e}")