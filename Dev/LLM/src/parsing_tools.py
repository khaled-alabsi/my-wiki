from typing import List, Dict, Any, Optional
import json
import re

def parse_numbered_list(text):
    items = []
    for line in text.split('\n'):
        line = line.strip()
        match = re.match(r'^\d+[\.\)]\s*(.*)', line)
        if match:
            items.append(match.group(1))
    return items


def extract_json_array(text: str) -> Optional[str]:
    # from non‑greedy (.*?) to greedy (.*). This makes the pattern match from the first [ until the very last ] in the text.
    pattern: str = r'\[.*\]'
    match = re.search(pattern, text, flags=re.DOTALL)
    return match.group(0) if match else None


def extract_and_parse_json_array(text: str) -> Optional[Any]:
    json_array_str: Optional[str] = extract_json_array(text)
    if json_array_str is None:
        return None
    return json.loads(json_array_str)


def get_topic_details_by_number(data: List[Dict[str, Any]], number: int) -> str:
    for item in data:
        if item.get("number") == number:
            topic: str = item.get("topic", "")
            description: str = item.get("description", "")
            subtopics: List[str] = item.get("subtopics", [])
            subtopics_str: str = ", ".join(subtopics)
            return f"{topic}: {description}\n{subtopics_str}"
    return ""


def format_topic_as_md(data: List[Dict[str, Any]], topic_name: str) -> str:
    md: str = f"# {topic_name}\n\n"
    for item in data:
        topic: str = item.get("topic", "")
        description: str = item.get("description", "")
        subtopics: List[str] = item.get("subtopics", [])
        number: int = item.get("number", 0)
        md += f"## {number}- {topic}\n\n{description}\n\n"
        if subtopics:
            md += "### Subtopics\n"
            for sub in subtopics:
                md += f"- {sub}\n"
        md += "\n"
    return md


def format_topic(item) -> str:
    topic: str = item.get("topic", "")
    description: str = item.get("description", "")
    subtopics: List[str] = item.get("subtopics", [])
    subtopics_str: str = ", ".join(subtopics)
    return f"{topic}: {description} [{subtopics_str}]"

