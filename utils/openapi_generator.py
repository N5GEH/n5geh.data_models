#!/usr/bin/env python3
import os
import re
import json
import glob
import yaml


def camel_to_spaces(name: str) -> str:
    """
    Konvertiert einen CamelCase-Bezeichner in einen lesbaren Namen mit Leerzeichen.
    Beispiel: "TemperatureSensor" -> "Temperature Sensor"
    """
    return re.sub(r'(?<!^)(?=[A-Z])', ' ', name)


def generate_example_body(model_name: str) -> dict:
    """
    Erzeugt ein Beispiel-Request-Body-Dictionary, das im POST-Request genutzt wird.
    Je nach Modellname (z. B. TemperatureSensor, CO2Sensor etc.) wird ein Beispielwert hinzugefügt.
    """
    example = {
        "id": f"{model_name.lower()}001",
        "type": model_name
    }
    if "Temperature" in model_name:
        example["temperature"] = {"value": 22.5}
    elif "CO2" in model_name:
        example["co2"] = {"value": 400}
    elif "Presence" in model_name:
        example["pir"] = 1.0
    elif "Hotel" in model_name:
        example["name"] = "Hotel Example"
    # Weitere Sonderfälle können nach Bedarf ergänzt werden.
    return example


def generate_get_response(model_name: str, json_schema: dict) -> dict:
    """
    Generiert die GET-Antwort, die sich – je nach Modell (wie z. B. Sensoren) – unterscheiden kann.
    Bei Sensortypen wird per Default ein number-Wert (im Textformat) als Beispiel angehängt,
    bei anderen Entitäten wird als Alternative das Schema per $ref eingebunden.
    """
    if any(x in model_name for x in ["Temperature", "CO2", "Presence"]):
        if "Temperature" in model_name:
            example_value = 22.5
            description_get = "Successful operation. Returns the temperature measurement."
        elif "CO2" in model_name:
            example_value = 400
            description_get = "Successful operation. Returns the CO2 measurement."
        elif "Presence" in model_name:
            example_value = 1.0
            description_get = "Successful operation. Returns the presence measurement."
        get_response = {
            "description": description_get,
            "content": {
                "text/plain": {
                    "schema": {"type": "number", "format": "float"},
                    "example": example_value
                }
            }
        }
    else:
        # Für andere Entitäten (z. B. Hotels) wird der GET-Response als JSON-Objekt
        # zurückgegeben.
        get_response = {
            "description": "Successful operation. Returns the entity.",
            "content": {
                "application/json": {
                    "schema": {"$ref": f"#/components/schemas/{model_name}"}
                }
            }
        }
    return get_response


def generate_openapi(model_name: str, json_schema: dict) -> dict:
    """
    Erzeugt ein OpenAPI-Dokument (als Dict) für ein gegebenes JSON Schema.
    Dabei werden per Default zwei Requests (GET und POST) definiert.
    """
    # Für eine bessere Lesbarkeit der Tags wandeln wir den CamelCase-Namen um.
    model_display = camel_to_spaces(model_name)
    # Plural (sehr einfach) – hier wird einfach ein "s" angehängt.
    model_display_plural = model_display + "s"

    example_body = generate_example_body(model_name)
    get_response = generate_get_response(model_name, json_schema)

    openapi_spec = {
        "openapi": "3.0.1",
        "info": {
            "title": model_name,
            "description": f"API specification for IoT platform including {model_display_plural}",
            "version": "1.0"
        },
        "servers": [
            {"url": "http://fiware.rwth-aachen.de/"}
        ],
        "paths": {
            "/v2/entities": {
                "get": {
                    "tags": [model_display],
                    "summary": f"Get {model_display_plural}",
                    "description": f"Retrieves available {model_display_plural.lower()}",
                    "operationId": f"get{model_name}s",
                    "parameters": [
                        {
                            "name": "type",
                            "in": "query",
                            "description": (
                                "Entity type, to avoid ambiguity in case there are several "
                                "entities with the same entity id."
                            ),
                            "schema": {"type": "string", "default": model_name}
                        },
                        {
                            "name": "Fiware-Service",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string", "default": "semantic_iot"}
                        },
                        {
                            "name": "Fiware-ServicePath",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string", "default": "/"}
                        }
                    ],
                    "responses": {
                        "200": get_response,
                        "404": {
                            "description": f"{model_display} not found.",
                            "content": {}
                        },
                        "500": {
                            "description": "Internal server error.",
                            "content": {}
                        }
                    }
                },
                "post": {
                    "tags": [model_display],
                    "summary": f"Create {model_display}",
                    "description": f"Creates a new {model_display} entity in the system.",
                    "operationId": f"create{model_name}",
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": f"#/components/schemas/{model_name}"},
                                "example": example_body
                            }
                        }
                    },
                    "parameters": [
                        {
                            "name": "Fiware-Service",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string", "default": "semantic_iot"}
                        },
                        {
                            "name": "Fiware-ServicePath",
                            "in": "header",
                            "required": True,
                            "schema": {"type": "string", "default": "/"}
                        }
                    ],
                    "responses": {
                        "201": {
                            "description": f"{model_display} successfully created.",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": f"#/components/schemas/{model_name}"}
                                }
                            }
                        },
                        "400": {
                            "description": "Invalid input data.",
                            "content": {}
                        },
                        "500": {
                            "description": "Internal server error.",
                            "content": {}
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                model_name: json_schema
            }
        }
    }
    return openapi_spec


def main():
    # Hole alle .json-Dateien im aktuellen Verzeichnis, die (vermutlich) die JSON Schemas enthalten.
    json_files = glob.glob("./schemas/*.json")
    for json_file in json_files:
        try:
            with open(json_file, "r") as f:
                json_schema = json.load(f)
        except Exception as e:
            print(f"Fehler beim Laden der JSON-Datei {json_file}: {e}")
            continue

        # Bestimme den Modellnamen anhand des Dateinamens (ohne .json)
        model_name = os.path.splitext(os.path.basename(json_file))[0]
        openapi_doc = generate_openapi(model_name, json_schema)

        # Speichere das OpenAPI-Dokument als YAML (z. B. TemperatureSensor_openapi.yaml)
        os.makedirs("./api_docs", exist_ok=True)
        openapi_filename = f"./api_docs/{model_name}.yaml"
        try:
            with open(openapi_filename, "w") as f:
                yaml.dump(openapi_doc, f, sort_keys=False, default_flow_style=False,
                          allow_unicode=True)
            print(f"save OpenAPI-specification for {model_name} in {openapi_filename} ")
        except Exception as e:
            print(f"error when saving OpenAPI-specification for {model_name}: {e}")


if __name__ == "__main__":
    main()
