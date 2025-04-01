import json
import inspect
import os
import sys
from filip.models.ngsi_v2.context import ContextEntityKeyValues
import data_models  # this is the module containing your defined data models


def main():
    # Get all classes defined in models.py
    for name, cls in inspect.getmembers(data_models, inspect.isclass):
        # Filter out classes that inherit from ContextEntityKeyValues,
        # but skip the base class itself.
        if issubclass(cls, ContextEntityKeyValues) and cls is not ContextEntityKeyValues:
            try:
                schema = cls.model_json_schema()
                # create schemas folder if it doesn't exist
                os.makedirs("schemas", exist_ok=True)
                filename = f"./schemas/{cls.__name__}.json"
                with open(filename, "w") as f:
                    json.dump(schema, f, indent=4)
                print(f"Saved JSON schema for {name} to {filename}")
            except Exception as e:
                print(f"Error generating schema for {name}: {e}", file=sys.stderr)


if __name__ == '__main__':
    main()
