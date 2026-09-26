import os
import certifi
import asyncio
import sys
from pathlib import Path
from urllib.parse import urlencode
from dotenv import load_dotenv
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_groq import ChatGroq

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

load_dotenv()

def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"{name} is missing from the deployment environment")
    return value

TAVILY_API_KEY = require_env("TAVILY_API_KEY")
AVIATIONSTACK_API_KEY = require_env("AVIATIONSTACK_API_KEY")
OPENWEATHER_API_KEY = require_env("OPENWEATHER_API_KEY")
GROQ_API_KEY = require_env("GROQ_API_KEY")
BASE_DIR = Path(__file__).resolve().parent

llm = ChatGroq (
    model = "openai/gpt-oss-20b",
    api_key = GROQ_API_KEY
)

client = MultiServerMCPClient(
    {
        "tavily": {
            "transport": "streamable_http",
            "url": "https://mcp.tavily.com/mcp/?" + urlencode(
                {"tavilyApiKey": TAVILY_API_KEY}
            )
        },

        "aviationstack": {
            "transport": "stdio",
            "command": "uvx",
            "args": [
                "aviationstack-mcp"
            ],
            "env": {
                "AVIATION_STACK_API_KEY": AVIATIONSTACK_API_KEY
            }
        },

        "weather": {
            "transport": "stdio",
            "command": sys.executable,
            "args": [
                str(BASE_DIR / "custom_weather_mcp_server.py")
            ],
            "env": {
                "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY
            }
        }
    }
)

# Check if the client is connected to all the servers
async def get_all_tools():
    tools = await client.get_tools()

    print("Available MCP Tools:")
    for tool in tools:
        print(tool)


# =======================================
# TAVILY & AVIATION TOOLS
# =======================================

search_tool = None
aviation_tools = {}

async def initialize_mcp():

    global search_tool
    global aviation_tools

    tools = await client.get_tools(server_name="tavily")

    print("Available MCP Tools:")
    for tool in tools:
        print(tool.name)

    search_tool = next(
        tool
        for tool in tools
        if tool.name == "tavily_search"
    )

    aviation_tools = {
        tool.name: tool
        for tool in tools
        if tool.name != "tavily_search"
    }


async def tavily_mcp_search(query: str):
    await initialize_mcp()
    result = await search_tool.ainvoke(
        {
            "query": query
        }
    )

    return result


async def aviation_mcp_call(
        tool_name: str,
        tool_args: dict = None
):
    tools = await client.get_tools(server_name="aviationstack")

    tool = next(
        tool
        for tool in tools
        if tool.name == tool_name
    )

    result = await tool.ainvoke(
        tool_args or {}
    )

    return result



# =======================================
# WEATHER TOOLS
# =======================================

weather_tool, forecast_tool = None, None

async def initialize_weather_tools():

    global weather_tool, forecast_tool

    if weather_tool is not None:
        return

    tools = await client.get_tools(server_name="weather")

    weather_tool = next (
        tool for tool in tools if tool.name == "get_current_weather"
    )

    forecast_tool = next (
        tool for tool in tools if tool.name == "get_forecast"
    )


async def weather_mcp_search(city: str):

    await initialize_weather_tools()

    return await weather_tool.ainvoke({
            "city": city
    })


async def forecast_mcp_search(city: str):

    await initialize_weather_tools()

    return await forecast_tool.ainvoke({
        "city": city
    })


# =======================================
# Destination Extractor
# =======================================

def extract_destination(query: str):
    prompt = f"""
    Extract only the destination city or country.

    Query:
    {query}

    Return only destination name.
    """

    response = llm.invoke(prompt)

    return response.content.strip()