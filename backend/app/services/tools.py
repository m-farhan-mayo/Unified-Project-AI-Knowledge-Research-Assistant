import os

from dotenv import load_dotenv
from tavily import TavilyClient


def get_user_info(name: str) -> str:
    return f"The user's name is {name}."


def search_web(query: str):
    load_dotenv()

    client = TavilyClient(
        api_key=os.getenv("TAVILY_API_KEY")
    )

    response = client.search(
        query=query,
        max_results=5,
    )

    return response

def send_slack_message(message: str):
    return f"Slack message sent: {message}"


def send_email(to: str, subject: str, body: str):
    return f"Email sent to {to} with subject: {subject}"