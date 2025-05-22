# Revolve

**Revolve** is an agentic Python code generation and editing tool that automates the creation of REST APIs, service logic, and test cases from natural language prompts. 
It uses the generated apps in a modern react UI to enable CRUD operations on tables. See our [Roadmap] for future features.

---
![Revolve](./screenshots/animated.gif)

## Features

- **Prompt-driven API Generation:** Describe your requirements in natural language to generate Falcon-based REST APIs and service files.
- **Automated Test Generation:** Creates comprehensive pytest-based test suites for all generated endpoints and services.
- **Iterative Code Refinement:** Automatically revises code and tests based on test results until all tests pass or a stopping condition is met.
- **UI for Workflow Management:** React-based interface for configuring the database, sending prompts, viewing generated files, and monitoring test results.
- **Version Control Integration:** Optionally auto-commits and pushes changes to a Git repository.
- **Test Reporting:** Tracks test history and generates Markdown and JSON reports for all test runs.

---
## Pre-requisites
- Python 3.11
- OPENAI API Key
- PostgreSQL database with tables

## Quick Start

### 1. Install Dependencies

```sh
brew install uv
uv sync
```

### 2. Start

```sh
python src/revolve/api.py
```


## Roadmap

- Authz and Authn configuration
- Support for other databases
- Support foreign key testing 
- Enhance UI to support lookups for foreign keys and editing json elegantly
- Support for enums while editing via the discovery apis
- Multi-turn conversations 
- Add fine-tuned Qwen 3 support in addition to paid model support.


## License

MIT