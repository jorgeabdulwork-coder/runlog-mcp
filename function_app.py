import logging
import azure.functions as func

app = func.FunctionApp()


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="ping",
    description="Health check. Confirms the RunLog MCP server is running.",
    tool_properties="[]",
)
def ping(context) -> str:
    logging.info("ping tool called")
    return "RunLog MCP server is up and running."