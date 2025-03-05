from fastmcp import FastMCP, Context
from pymongo import MongoClient
from datetime import datetime, UTC
import uuid
import os
from dotenv import load_dotenv
import json
# import logging
import asyncio
from aiohttp import web
import paho.mqtt.client as mqtt
from typing import Union
import subprocess
import ssl
import aiohttp
import logging

# Import the tool functions from the tools module
from fastmcp_todo_server.tools import (
    add_todo,
    query_todos,
    update_todo,
    mqtt_publish,
    delete_todo,
    get_todo,
    mark_todo_complete,
    list_todos_by_status,
    add_lesson,
    get_lesson,
    update_lesson,
    delete_lesson,
    list_lessons,
    search_todos,
    search_lessons,
)

# Comment out all logging configuration
# logging.basicConfig(
#     level=logging.DEBUG,
#     format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# )
# logger = logging.getLogger(__name__)

# Also enable debug logging for FastMCP
# logging.getLogger('fastmcp').setLevel(logging.DEBUG)
# logging.getLogger('mcp').setLevel(logging.DEBUG)

# Load environment variables
load_dotenv()

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
MONGODB_DB = os.getenv("MONGODB_DB", "swarmonomicon")
MONGODB_COLLECTION = os.getenv("MONGODB_COLLECTION", "todos")

# MQTT configuration
MQTT_HOST = "3.134.3.199"
MQTT_PORT = 3003
MQTT_KEEPALIVE = 60

# Cursor MCP configuration
# CURSOR_MCP_URL = os.getenv("CURSOR_MCP_URL", "http://localhost:8000")
# CURSOR_MCP_SSE_ENDPOINT = os.getenv("CURSOR_MCP_SSE_ENDPOINT", "/sse")

# Import the server instance from our server module
from fastmcp_todo_server.server import server

# Create MongoDB connection at module level
mongo_client = MongoClient(MONGODB_URI)
db = mongo_client[MONGODB_DB]
collection = db[MONGODB_COLLECTION]
lessons_collection = db["lessons_learned"]

# Register tools using the FastMCP decorator syntax
@server.tool()
async def add_todo_tool(description: str, priority: str = "initial", target_agent: str = "user", ctx: Context = None) -> dict:
    return await add_todo(description, priority, target_agent, ctx)

@server.tool()
async def query_todos_tool(filter: dict = None, projection: dict = None, limit: int = 100) -> dict:
    return await query_todos(filter, projection, limit)

@server.tool()
async def update_todo_tool(todo_id: str, updates: dict, ctx: Context = None) -> str:
    return await update_todo(todo_id, updates, ctx)

@server.tool()
async def mqtt_publish_tool(topic: str, message: str, ctx: Context = None) -> str:
    await server.publish(topic, message)
    return {"topic": topic, "message": message}

@server.tool()
async def update_device_status_tool(agent_name: str, status: bool = True, ctx: Context = None) -> str:
    """
    Updates the status of a device in the MQTT Status Dashboard.
    
    Args:
        agent_name: Name of the device to update
        status: True for online (green), False for offline (red)
        
    Returns:
        Result of the operation
    """
    topic = f"status/{agent_name}/alive"
    message = "1" if status else "0"
    await server.publish(topic, message)
    status_text = "online" if status else "offline"
    return {"device": agent_name, "status": status_text, "topic": topic}

# Remove the existing deploy_nodered_flow_tool function
# Add the tool from the new module
@server.tool()
async def deploy_nodered_flow_tool(flow_json_name: str, ctx: Context = None) -> str:
    return await deploy_nodered_flow(flow_json_name, ctx)

@server.tool()
async def delete_todo_tool(todo_id: str, ctx: Context = None) -> str:
    return await delete_todo(todo_id, ctx)

@server.tool()
async def get_todo_tool(todo_id: str) -> str:
    return await get_todo(todo_id)

@server.tool()
async def mark_todo_complete_tool(todo_id: str, ctx: Context = None) -> str:
    return await mark_todo_complete(todo_id, ctx)

@server.tool()
async def list_todos_by_status_tool(status: str, limit: int = 100) -> str:
    return await list_todos_by_status(status, limit)

@server.tool()
async def add_lesson_tool(language: str, topic: str, lesson_learned: str, tags: list = None, ctx: Context = None) -> str:
    return await add_lesson(language, topic, lesson_learned, tags, ctx)

@server.tool()
async def get_lesson_tool(lesson_id: str) -> str:
    return await get_lesson(lesson_id)

@server.tool()
async def update_lesson_tool(lesson_id: str, updates: dict, ctx: Context = None) -> str:
    return await update_lesson(lesson_id, updates, ctx)

@server.tool()
async def delete_lesson_tool(lesson_id: str, ctx: Context = None) -> str:
    return await delete_lesson(lesson_id, ctx)

@server.tool()
async def list_lessons_tool(limit: int = 100) -> str:
    return await list_lessons(limit)

@server.tool()
async def search_todos_tool(query: str, fields: list = None, limit: int = 100) -> str:
    """Search todos with text search capabilities"""
    return await search_todos(query, fields, limit)

@server.tool()
async def search_lessons_tool(query: str, fields: list = None, limit: int = 100) -> str:
    """Search lessons with text search capabilities"""
    return await search_lessons(query, fields, limit)

# Define the Node-RED deployment function directly
async def deploy_nodered_flow(flow_json_name: str, ctx: Context = None) -> str:
    """
    Deploys a Node-RED flow to a Node-RED instance.
    
    Args:
        flow_json_name: The name of the flow JSON file in the dashboard directory
        
    Returns:
        Result of the deployment operation
    """
    # Set up logging
    logger = logging.getLogger(__name__)

    # Set default Node-RED URL if not provided
    node_red_url = os.getenv("NR_URL", "http://localhost:9191")
    username = os.getenv("NR_USER", None)
    password = os.getenv("NR_PASS", None)

    logger.debug(f"Node-RED URL: {node_red_url}")
    logger.debug(f"Username: {username}")
    logger.debug(f"Password length: {len(password) if password else 'None'}")

    # Add local git pull
    dashboard_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../dashboard"))
    result = ""
    try:
        result = subprocess.run(['git', 'pull'], cwd=dashboard_dir, check=True, capture_output=True, text=True)
        logger.debug(f"Git pull output: {result.stdout}")
    except subprocess.CalledProcessError as e:
        logger.warning(f"Git pull failed: {e}")
        logger.warning(f"Git pull stderr: {e.stderr}")

    flow_json_path = f"../../dashboard/{flow_json_name}"
    flow_path = os.path.abspath(os.path.join(os.path.dirname(__file__), flow_json_path))

    if not os.path.exists(flow_path):
        return {"success": False, "error": f"Flow file not found: {flow_json_name}, {result}"}

    # Read the JSON content from the file
    try:
        with open(flow_path, 'r') as file:
            flow_data = json.load(file)
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON in file {flow_json_name}: {str(e)}"}
    except Exception as e:
        return {"success": False, "error": f"Error reading file {flow_json_name}: {str(e)}"}

    # Validate flow_data is either a list or a dict
    if not isinstance(flow_data, (list, dict)):
        return {"success": False, "error": f"Flow JSON must be a list or dict, got {type(flow_data).__name__}"}

    # If it's a single flow object, wrap it in a list
    if isinstance(flow_data, dict):
        flow_data = [flow_data]

    # Create SSL context to handle potential SSL verification issues
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    async with aiohttp.ClientSession() as session:
        # First, check authentication scheme
        try:
            async with session.get(f"{node_red_url}/auth/login", ssl=ssl_context) as login_response:
                logger.debug(f"Login endpoint response status: {login_response.status}")
                logger.debug(f"Login endpoint response headers: {login_response.headers}")
                try:
                    login_info = await login_response.json()
                    logger.debug(f"Login info: {login_info}")
                except Exception as e:
                    login_text = await login_response.text()
                    logger.debug(f"Login response text: {login_text}")
                    logger.debug(f"Login JSON parsing error: {e}")

            # If authentication is required, get a token
            if username and password:
                token_payload = {
                    "client_id": "node-red-admin",
                    "grant_type": "password",
                    "scope": "*",
                    "username": username,
                    "password": password
                }
                logger.debug(f"Token payload: {token_payload}")

                async with session.post(f"{node_red_url}/auth/token", data=token_payload, ssl=ssl_context) as token_response:
                    logger.debug(f"Token request status: {token_response.status}")
                    logger.debug(f"Token request headers: {token_response.headers}")

                    # Log the full response text for debugging
                    token_text = await token_response.text()
                    logger.debug(f"Token response text: {token_text}")

                    # Try to parse the response as JSON
                    try:
                        token_data = json.loads(token_text)
                        access_token = token_data.get('access_token')

                        # Use the access token for subsequent requests
                        headers = {
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {access_token}"
                        }
                    except json.JSONDecodeError:
                        logger.error(f"Failed to parse token response: {token_text}")
                        return {"success": False, "error": f"Failed to parse token response: {token_text}"}

            # If authentication is not required, proceed without token
            else:
                headers = {
                    "Content-Type": "application/json"
                }

            # Get existing flows
            async with session.get(f"{node_red_url}/flows", headers=headers, ssl=ssl_context) as response:
                logger.debug(f"Flows check response status: {response.status}")

                if response.status == 200:
                    existing_flows = await response.json()
                else:
                    return {"success": False, "error": f"Cannot access flows. HTTP {response.status}"}

                # Determine flow ID and operation
                flow_id = None
                flow_label = None
                for node in flow_data:
                    if node.get("type") == "tab":
                        flow_id = node.get("id")
                        flow_label = node.get("label")
                        break

                # Check if flow exists
                flow_exists = any(f.get("id") == flow_id and f.get("type") == "tab" for f in existing_flows)

                # Determine operation and endpoint
                if flow_exists:
                    operation = "update"
                    endpoint = f"{node_red_url}/flow/{flow_id}"
                    method = session.put
                else:
                    operation = "create"
                    endpoint = f"{node_red_url}/flows"
                    method = session.post

                # Deploy the flow
                async with method(endpoint, headers=headers, json=flow_data, ssl=ssl_context) as deploy_response:
                    logger.debug(f"Deploy response status: {deploy_response.status}")
                    result = await deploy_response.text()
                    logger.debug(f"Deploy response body: {result}")

                    if deploy_response.status not in (200, 201, 204):
                        return {"success": False, "error": f"HTTP {deploy_response.status}: {result}", "operation": operation}

                    return {
                        "success": True,
                        "operation": operation,
                        "flow_id": flow_id,
                        "flow_label": flow_label,
                        "dashboard_url": f"{node_red_url}/ui"
                    }

        except Exception as e:
            logger.exception("Deployment error")
            return {"success": False, "error": str(e)}

async def run_server():
    """Run the FastMCP server"""
    print("Starting FastMCP server")
    try:
        import sys
        import uvicorn

        # Custom exception handler to silence specific SSE-related errors
        original_excepthook = sys.excepthook

        def custom_excepthook(exctype, value, traceback):
            # Only silence the specific 'NoneType' object is not callable errors from Starlette
            if exctype is TypeError and "'NoneType' object is not callable" in str(value) and "starlette/routing.py" in str(traceback.tb_frame):
                # Log minimally instead of full stack trace
                print(f"Suppressed known error in SSE endpoint: {str(value)}")
                return
            # For all other errors, use the original exception handler
            original_excepthook(exctype, value, traceback)

        # Replace the default exception handler
        sys.excepthook = custom_excepthook

        # Configure uvicorn to suppress specific access logs for /messages endpoint
        log_config = uvicorn.config.LOGGING_CONFIG
        if "formatters" in log_config:
            log_config["formatters"]["access"]["fmt"] = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

        await server.run_sse_async()  # Use run_sse_async directly
    except Exception as e:
        print(f"Error in server: {str(e)}")
        raise
