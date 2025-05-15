[![MseeP.ai Security Assessment Badge](https://mseep.net/pr/danedens-omnispindle-badge.png)](https://mseep.ai/app/danedens-omnispindle)

# FastMCP Todo Server

A FastMCP-based Todo Server for the [Swarmonomicon](https://github.com/DanEdens/madness_interactive/tree/main/projects/common/Swarmonomicon) project. This server receives todo requests via FastMCP and stores them in MongoDB for processing by the Swarmonomicon todo worker.

## Features

- FastMCP server for receiving todo requests
- MongoDB integration for todo storage
- Compatible with Swarmonomicon todo worker
- Python-based implementation

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/DanEdens/Omnispindle.git
   cd Omnispindle
   ```

2. Install uv (if not already installed):
   ```bash
   curl -LsSf https://astral.sh/uv/install.sh | sh
   ```

3. Create and activate a virtual environment with uv:
   ```bash
   uv venv
   source .venv/bin/activate  # On Unix/macOS
   # or
   .venv\Scripts\activate  # On Windows
   ```

4. Install dependencies with uv:
   ```bash
   uv pip install -r requirements.txt
   ```

5. For development, install additional dependencies:
   ```bash
   uv pip install -r requirements-dev.txt
   ```

6. Create a `.env` file with your configuration:
   ```bash
   MONGODB_URI=mongodb://localhost:27017
   MONGODB_DB=swarmonomicon
   MONGODB_COLLECTION=todos
   ```

## Usage

### Starting the Server

1. Start the FastMCP server:
   ```bash
   python -m src.Omnispindle
   ```

### Adding Todos

You can add todos using FastMCP in several ways:

1. Using FastMCP Python client:
   ```python
   from fastmcp import FastMCPClient
   
   client = FastMCPClient()
   response = await client.call_tool("add_todo", {
       "description": "Example todo",
       "priority": "high",  # optional, defaults to "medium"
       "target_agent": "user"  # optional, defaults to "user"
   })
   ```

2. Using MQTT directly:
   ```bash
   mosquitto_pub -t "mcp/todo/new" -m '{
       "description": "Example todo",
       "priority": "high",
       "target_agent": "user"
   }'
   ```

### Development

1. Run tests:
   ```bash
   pytest tests/
   ```

2. Run tests with coverage:
   ```bash
   pytest --cov=src tests/
   ```

3. Run specific test file:
   ```bash
   pytest tests/test_todo_handler.py -v
   ```

## Integration with Swarmonomicon

This server is part of the larger [Swarmonomicon](https://github.com/DanEdens/madness_interactive/tree/main/projects/common/Swarmonomicon) project, which provides:

- Task management and distribution
- Agent-based task processing
- Real-time updates via MQTT
- Integration with various AI models

For more information about the Swarmonomicon project and its features, check out the [main project documentation](https://github.com/DanEdens/madness_interactive/tree/main/projects/common/Swarmonomicon/README.md).

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

For more information about contributing to the Swarmonomicon project, see the [main project's contributing guidelines](https://github.com/DanEdens/madness_interactive/tree/main/projects/common/Swarmonomicon/CONTRIBUTING.md).
