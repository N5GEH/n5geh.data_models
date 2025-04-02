**preliminary version**

# Data Models Automation Utilities 

This repository contains a set of Python utility scripts designed to automatically keep JSON Schemas and OpenAPI documentation in sync with your data models. This automation is especially useful when data models change frequently, as it reduces manual work and the likelihood of inconsistencies.

## Overview

The utilities include two main scripts:

- **`serializer.py`**  
  Dynamically scans for data model classes (which extend from a common base) and serializes them as JSON Schemas. Every time a model is updated, this script can generate or update a corresponding JSON Schema file without hard-coding each model name.

- **`openapi_generator.py`**  
  Converts the generated JSON Schemas into full-featured OpenAPI documents. It creates standardized API definitions by injecting default GET and POST operations for the IoT platform based on the JSON Schema, ensuring that your API documentation always mirrors the current state of your data models.

## Main Functionality

### `serializer.py`

- **Dynamic Model Discovery:**  
  Scans modules for classes that inherit from `ContextEntityKeyValues` (or a similar base class) without requiring any hard-coded configuration.
  
- **JSON Schema Generation:**  
  Uses Pydantic’s built-in method (`model_json_schema`) on each discovered model to create a corresponding JSON Schema.
  
- **Output:**  
  Writes each JSON Schema to a file (e.g., `TemperatureSensor.json`), making it easy to track changes over time or use these schemas in further processing.

- **Workflow Integration:**  
  Designed to be executed within a larger workflow (e.g., a GitHub Actions pipeline) so that when data models are updated, the JSON Schemas are regenerated automatically.

### `openapi_generator.py`

- **Conversion to OpenAPI:**  
  Processes each generated JSON Schema and converts it into an OpenAPI document (in YAML format), integrating the schema as a component.
  
- **Standardized API Endpoints:**  
  Automatically defines two common endpoints for each model:
  - **GET** (to retrieve entities): Incorporates query parameters (like entity type and Fiware-specific info).
  - **POST** (to create new entities): Defines a request body that references the model's JSON Schema.
  
- **Output:**  
  Produces an OpenAPI YAML file (e.g., `TemperatureSensor_openapi.yaml`) for every JSON Schema, providing a ready-to-go API specification that matches the current model.

## Integration into GitHub Actions

The repository also includes a GitHub Actions workflow that leverages these scripts:

- **Detection of Changes:**  
  The workflow scans repository folders (excluding `utils`) for a `data_models.py` file. If such a file is changed or added in a commit, it triggers the generation steps.
  
- **Automated Execution:**  
  The workflow copies `serializer.py` and `openapi_generator.py` temporarily into the respective folders, runs them to update the JSON Schemas and OpenAPI docs, and then cleans up the copied scripts.
  
- **Commit & Push:**  
  Finally, if any changes were made, the workflow automatically commits and pushes these updates back to the branch that triggered the workflow (using commit messages with `[skip ci]` to avoid endless loops).

## Usage

- **Manually:**  
  Run `python serializer.py` in the folder containing your `data_models.py` to generate JSON Schemas, then run `python openapi_generator.py` to create or update the OpenAPI documents.

- **Automated Workflow:**  
  With the GitHub Actions setup, any change in the data model folders will trigger the proper regeneration of schemas and API documentation.

## Summary

These utilities are designed to streamline documentation and validation in projects where data models evolve regularly. By automating the serialization to JSON Schema and conversion to OpenAPI docs, they help maintain consistency and reduce manual errors, enabling developers to focus more on design and functionality over repetitive documentation tasks.