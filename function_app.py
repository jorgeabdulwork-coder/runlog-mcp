import json
import logging

import azure.functions as func

from runlog.runs import VALID_UNITS, RunValidationError, build_run, format_pace
from runlog.store import InMemoryRunStore

app = func.FunctionApp()
store = InMemoryRunStore()
USER_ID = "jorge"  # single user for now; real auth comes in Phase 5


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="ping",
    description="Health check. Confirms the RunLog MCP server is running.",
    tool_properties="[]",
)
def ping(context) -> str:
    logging.info("ping tool called")
    return "RunLog MCP server is up and running."


LOG_RUN_PROPERTIES = json.dumps([
    {"propertyName": "distance", "propertyType": "number",
     "description": "Distance run, in the unit given by 'unit'.", "isRequired": True},
    {"propertyName": "duration", "propertyType": "string",
     "description": "Total time as mm:ss or h:mm:ss, e.g. '42:30' or '1:05:10'.", "isRequired": True},
    {"propertyName": "unit", "propertyType": "string",
     "description": "'mi' or 'km'. Defaults to 'mi'."},
    {"propertyName": "date", "propertyType": "string",
     "description": "Date of the run as YYYY-MM-DD. Defaults to today."},
    {"propertyName": "run_type", "propertyType": "string",
     "description": "One of: easy, tempo, long, race. Defaults to easy."},
    {"propertyName": "effort", "propertyType": "integer",
     "description": "Perceived effort from 1 (very easy) to 10 (all-out)."},
    {"propertyName": "notes", "propertyType": "string",
     "description": "Optional notes about the run, such as weather or how it felt."},
])


@app.mcp_tool_trigger(
    arg_name="context",
    tool_name="log_run",
    description="Log a completed run. Stores it and returns a confirmation including pace.",
    tool_properties=LOG_RUN_PROPERTIES,
)
def log_run(context) -> str:
    args = json.loads(context).get("arguments", {})
    try:
        run = build_run(args, USER_ID)
    except RunValidationError as err:
        logging.warning("log_run rejected: %s", err)
        return f"Could not log run: {err}"

    store.add(run)

    unit = str(args.get("unit") or "mi").lower()
    distance = run["distanceMeters"] / VALID_UNITS[unit]
    pace = format_pace(run["durationSeconds"], run["distanceMeters"], unit)
    logging.info("Logged run %s for %s", run["id"], USER_ID)
    return (
        f"Logged a {distance:.2f} {unit} {run['runType']} run on {run['date']} "
        f"at {pace} pace (id: {run['id']})."
    )