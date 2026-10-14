import json
import inspect
import os
import re
import sys
from filip.models.ngsi_v2.context import ContextEntityKeyValues
import data_models  # this is the module containing your defined data models

SCHEMA_BASE_URI = os.environ.get(
    "SCHEMA_BASE_URI", "https://smartdatamodels.org/dataModel")


def slugify(text: str) -> str:
    """Convert PascalCase, camelCase, or spaced strings to kebab-case."""
    s = re.sub(r"([a-z0-9])([A-Z])", r"\1-\2", text)
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-")
    return s.lower()


def add_schema_id(schema: dict, model_name: str) -> dict:
    """Return a new schema dict with a generated ``$id`` as the first key."""
    identifier = schema.get("title") or model_name
    slug = slugify(identifier)
    base = SCHEMA_BASE_URI.rstrip("/")
    schema_id = f"{base}/{slug}.json"

    updated = {"$id": schema_id}
    for key, value in schema.items():
        if key not in ("$id", "id"):
            updated[key] = value
    return updated


def main():
    # Get all classes defined in models.py
    for name, cls in inspect.getmembers(data_models, inspect.isclass):
        # Filter out classes that inherit from ContextEntityKeyValues,
        # but skip the base class itself.
        if issubclass(cls, ContextEntityKeyValues) and cls is not ContextEntityKeyValues:
            try:
                schema = cls.model_json_schema()
                schema = add_schema_id(schema, cls.__name__)
                # create schemas folder if it doesn't exist
                os.makedirs("schemas", exist_ok=True)
                filename = f"./schemas/{cls.__name__}.json"
                with open(filename, "w", encoding="utf-8") as f:
                    json.dump(schema, f, indent=4, ensure_ascii=False)
                    f.write("\n")
                print(f"Saved JSON schema for {name} to {filename}")
            except Exception as e:
                print(f"Error generating schema for {name}: {e}", file=sys.stderr)


if __name__ == '__main__':
    main()
