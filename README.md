# Data Models Automation Utilities 

This repository contains a set of Python utility scripts designed to automatically keep **JSON Schemas** and **OpenAPI documentation** in sync with your **[pydantic](https://docs.pydantic.dev/latest/)** based data models for FIWARE-based IoT platform.

This automation reduces manual work and the likelihood of inconsistencies, so that developers can focus on managing the data models, which  will be considered as the single source of truth.

To use these utilities, the provided data models must follow some specific convention. For this, please refer to the [n5geh tutorials](https://github.com/N5GEH/n5geh.tutorials.data_model) or the [example data model](./example_building_automation/data_models.py) in this repository. 

## Main Functionality

### `serializer.py`

- **Dynamic Model Discovery:**  
  Scans modules for classes that inherit from `ContextEntityKeyValues` (or a similar base class) without requiring any hard-coded configuration.
  
- **JSON Schema Generation:**  
  Uses Pydantic’s built-in method (`model_json_schema`) on each discovered model to create a corresponding JSON Schema.
  
- **Output:**  
  Writes each JSON Schema to a file (e.g., `TemperatureSensor.json`), making it easy to track changes over time or use these schemas in further processing.

- **Workflow Integration:**  
  Designed to be executed within a larger workflow (e.g., a GitHub Actions pipeline) so that when data models are updated, the JSON Schemas are regenerated automatically. But manual usage is also possible.

### `openapi_generator.py`

- **Conversion to OpenAPI:**  
  Processes each generated JSON Schema and converts it into an OpenAPI document (in YAML format), integrating the schema as a component.
  
- **Standardized API Endpoints:**  
  Automatically defines two common FIWARE NGSI-v2 endpoints for each data model:
  - **GET** (to retrieve entities): Incorporates query parameters (like entity type and Fiware-specific info).
  - **POST** (to create new entities): Defines a request body that references the model's JSON Schema.
  
- **Output:**  
  Produces an OpenAPI YAML file (e.g., `TemperatureSensor_openapi.yaml`) for every JSON Schema.

### GitHub Pages deployment
- **JSON Schema hosting:**  
    The generated JSON Schemas are hosted on GitHub Pages, for example [TemperatureSensorFiware.json](https://n5geh.github.io/n5geh.data_models/example_building_automation/schemas/TemperatureSensorFiware.json). This will make serialized data models accessible for everyone, accelerating the collaboration and enhancing the transparency of the project. 

- **Swagger UI generation:**  
    The generated OpenAPI YAML files are further used to create Swagger UI documentation, which is visualization of the API documentation, for example [TemperatureSensorFiware](https://n5geh.github.io/n5geh.data_models/example_building_automation/api_docs/swagger-ui/TemperatureSensorFiware/). This provides a user-friendly interface for developers and partners to explore the use of corresponding data models in FIWARE APIs.
  
## Usage (preliminary version)

- **Manually:**  
  Run `python serializer.py` in the folder containing your `data_models.py` to generate JSON Schemas, then run `python openapi_generator.py` to create or update the OpenAPI documents.

- **Automated Workflow:**  
  With the GitHub Actions setup, any change in the data model folders will trigger the proper regeneration of schemas and API documentation.

## Summary

These utilities are designed to streamline documentation and validation in projects where data models evolve regularly. By automating the serialization to JSON Schema and conversion to OpenAPI docs, they help maintain consistency and reduce manual errors, enabling developers to focus more on design and functionality over repetitive documentation tasks.