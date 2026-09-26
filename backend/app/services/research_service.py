from app.services.tools import search_web


def research_topic(topic: str):
    from app.services.llm_service import ask_llm

    search_result = search_web(topic)

    sources = [
        {
            "title": result["title"],
            "url": result["url"],
            "content": result["content"],
        }
        for result in search_result["results"]
    ]

    context = "\n\n---\n\n".join(
        f"Title: {source['title']}\n"
        f"URL: {source['url']}\n"
        f"Content: {source['content']}"
        for source in sources
    )

    prompt = f"""
Create a research report about the following topic:

{topic}

Use only the information provided in the sources below.

Organize the report with:

1. Overview
2. Key Points
3. Common Use Cases
4. Conclusion

Sources:
{context}
"""

    report = ask_llm([
        {
            "role": "system",
            "content": "You are a research assistant that creates clear and factual research reports."
        },
        {
            "role": "user",
            "content": prompt
        }
    ])

    return {
        "topic": topic,
        "report": report,
        "sources": sources
    }