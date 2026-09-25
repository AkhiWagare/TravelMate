from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights
from backend import run_travel_agent
# from mcp_client_test import get_all_tools, tavily_mcp_search
from mcp_client import get_all_tools
import asyncio

# res = tavily_search("Best hotels in India")

# res = search_flights("Plan a 7 days Singapore trip from India")

# user_input = input("Enter travel request: ")

# response = run_travel_agent(
#     user_input=user_input,
#     thread_id="test_user"
# )

# print("\nFinal Response:\n")
# print(response["answer"])

if __name__ == "__main__":
    asyncio.run(get_all_tools())
    # query = "latest news about AI"
    # asyncio.run(tavily_mcp_search(query))