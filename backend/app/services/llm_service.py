import os

from dotenv import load_dotenv
from openai import OpenAI
import json

from app.services.tools import get_user_info



def get_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing.")

    return OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=api_key,
    )


def ask_llm(messages: str | list[dict[str, str]]) -> str:
    client = get_client()

    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]

    response = client.chat.completions.create(
        model="gemini-3.5-flash-lite",
        messages=messages,
    )

    return response.choices[0].message.content or ""


def ask_llm_with_tools(message: str):
    client = get_client()

    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant."
        },
        {
            "role": "user",
            "content": message
        }
    ]

    response = client.chat.completions.create(
        model="gemini-3.8-flash",
        messages=messages,
        tools=get_tools(),
    )

    assistant_message = response.choices[0].message

    if not assistant_message.tool_calls:
        return assistant_message.content

    tool_call = assistant_message.tool_calls[0]

    tool_result = execute_tool(tool_call)

    messages.append(assistant_message)

    messages.append(
        {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "content": tool_result
        }
    )

    final_response = client.chat.completions.create(
        model="gemini-3.5-flash-lite", # gemini-3.1-flash-lite
        messages=messages,
        tools=get_tools(),
    )

    return final_response.choices[0].message.content


def get_tools():
    return [
        {
            "type": "function",
            "function": {
                "name": "get_user_info",
                "description": "Get information about a user by their name.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "name": {
                            "type": "string",
                            "description": "The name of the user."
                        }
                    },
                    "required": ["name"]
                }
            }
        }
    ]

def execute_tool(tool_call):
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    if tool_name == "get_user_info":
        return get_user_info(**arguments)

    return "Unknown tool."