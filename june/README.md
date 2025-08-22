# AI Career Copilot - Python Implementation

This directory contains the Python implementation of the AI Career Copilot system, built on the A2A protocol using Google ADK framework.

## Project Structure

* [**Common**](/june/common)  
Shared utilities, A2A server implementation, MongoDB persistence, and Azure service integrations.

* [**Agents**](/june/agents/README.md)  
All AI Career Copilot agents built on Google ADK framework, each exposing an A2A server endpoint.

* [**Demo UI**](/ui/)  
Web-based demonstration interface built with Mesop for testing and showcasing the system.

## Prerequisites

- Python 3.12 or higher
- UV package manager
- MongoDB Cloud Atlas
- Google AI Platform API key

## Quick Start

1. Navigate to the june directory:
    ```bash
    cd june
    ```

2. Configure environment variables:
    ```bash
    cp ../env.example ../.env
    # Edit .env with your actual values
    ```

3. Install dependencies:
    ```bash
    pip install -r ../requirements-azure.txt
    ```

4. Start the demo UI:
    ```bash
    cd ../ui
    uv run main.py
    ```

## Running Individual Agents

Each agent can be run independently for development and testing:

```bash
cd june/agents/[agent_name]
uv run __main__.py
```

## Architecture

The system follows a modular agent architecture where each agent:
- Exposes an A2A server endpoint
- Implements Google ADK agent logic
- Persists data to MongoDB
- Integrates with Azure services (optional)
- Provides streaming responses via SSE

## Development

- All agents follow a consistent pattern for easy development
- Common utilities are shared across all agents
- MongoDB persistence is handled automatically
- Azure integrations are optional and gracefully degraded

---
**Note:** This is a production-ready implementation of the AI Career Copilot system.
---
