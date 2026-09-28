import os
import logging

from dotenv import load_dotenv
from openai import OpenAI, APIConnectionError, APIStatusError
import json
from app.services.research_service import research_topic
from app.services.tools import (
    search_web,
    send_email,
)


def get_client() -> OpenAI:
    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is missing.")

    return OpenAI(
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        api_key=api_key,
        timeout=30.0,
        max_retries=2,
    )


def create_completion(client, **kwargs):
    """Retry via the SDK, then optionally try another configured model.

    Only retry model generation, never the entire tool workflow: replaying
    that workflow could send an email twice.
    """
    primary = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-lite").strip()
    fallback = os.getenv("GEMINI_FALLBACK_MODEL", "").strip()
    try:
        return client.chat.completions.create(model=primary, **kwargs)
    except (APIConnectionError, APIStatusError) as exc:
        transient = isinstance(exc, APIConnectionError) or exc.status_code >= 500
        if not transient or not fallback or fallback == primary:
            raise
        logging.getLogger(__name__).warning(
            "Primary Gemini model unavailable; trying configured fallback."
        )
        return client.chat.completions.create(model=fallback, **kwargs)


def ask_llm(messages: str | list[dict[str, str]]) -> str:
    client = get_client()

    if isinstance(messages, str):
        messages = [{"role": "user", "content": messages}]

    response = create_completion(
        client,
        messages=messages,
    )

    return response.choices[0].message.content or ""


def ask_llm_with_tools(message: str, history: list[dict] | None = None):
    client = get_client()

    messages = [
        {
            "role": "system",
            "content": """
                    You are an AI Knowledge and Research Assistant.

                    Always use tools when external information is required.

                    When a tool returns information,
                    use it to generate a final answer.

                    Do not invent sources.
                    """
        }
    ]
    messages.extend(history or [])
    messages.append(
        {
            "role": "user",
            "content": message
        }
    )
    search_sources = []
    logger = logging.getLogger(__name__)
    email_status = None

    def get_unique_sources():
        unique_sources = []
        seen_urls = set()

        for source in search_sources:
            url = source.get("url")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_sources.append(source)

        return unique_sources

    MAX_TOOL_ITERATIONS = 5

    for _ in range(MAX_TOOL_ITERATIONS):

        response = create_completion(
            client,
            messages=messages,
            tools=get_tools(),
        )

        assistant_message = response.choices[0].message
        if not assistant_message.tool_calls:
            return {
                "answer": assistant_message.content or "The model returned no text response.",
                "sources": get_unique_sources(),
                "email_status": email_status,
            }

        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.content,
                "tool_calls": assistant_message.tool_calls,
            }
)

        for tool_call in assistant_message.tool_calls:
            logger.info("Tool Called: %s", tool_call.function.name)
            try:
                tool_result = execute_tool(tool_call)
            except Exception as exc:
                tool_result = {
                    "success": False,
                    "error": str(exc),
                }

            logger.info("Tool Result: %s", tool_result)

            if tool_call.function.name == "send_email":
                email_status = tool_result


            if not isinstance(tool_result, dict):
                tool_result = {
                    "success": True,
                    "tool": tool_call.function.name,
                    "result": tool_result,
                }

            if tool_call.function.name == "search_web":
                search_sources.extend(tool_result.get("results", []))

            if tool_call.function.name == "research_topic":
                search_sources.extend(tool_result.get("sources", []))

            if not isinstance(tool_result, str):
                tool_result = json.dumps(
                    tool_result,
                    ensure_ascii=False,
                    default=str
                )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_result
                }
            )

    return {
        "answer": "The model exceeded the maximum number of tool calls.",
        "sources": get_unique_sources(),
        "email_status": email_status,
    }

def get_tools():
    return [
        get_search_tool(),
        get_research_tool(),
        get_email_tool()
    ]

def execute_tool(tool_call):
    tool_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)

    if tool_name == "search_web":
        search_result = search_web(**arguments)

        return {
            "query": search_result["query"],
            "results": [
                {
                    "title": result["title"],
                    "url": result["url"],
                    "content": result["content"],
                }
                for result in search_result["results"]
            ]
        }

    if tool_name == "research_topic":
        return research_topic(**arguments)

    if tool_name == "send_email":
        return send_email(**arguments)

    return "Unknown tool."

def get_search_tool():
    return {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web for current or external information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The search query to use on the web."
                    }
                },
                "required": ["query"]
            }
        }
    }


def get_research_tool():
    return {
        "type": "function",
        "function": {
            "name": "research_topic",
            "description": "Research a topic using web search and create a structured research report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "topic": {
                        "type": "string",
                        "description": "The topic that should be researched."
                    }
                },
                "required": ["topic"]
            }
        }
    }

def get_email_tool():
    return {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Send an email when the user explicitly asks to email or share "
                "the answer/report. Use the recipient, subject, and body requested "
                "by the user; do not invent recipient addresses."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "The recipient's complete email address."
                    },
                    "subject": {
                        "type": "string",
                        "description": "The email subject line."
                    },
                    "body": {
                        "type": "string",
                        "description": "The email body to send."
                    }
                },
                "required": ["to", "subject", "body"]
            }
        }
    }
