import json
import logging
from typing import Optional, Literal
from pydantic import BaseModel, Field
from google import genai
from google.genai.types import GenerateContentConfig

from config.settings import settings
from services.timezone_helper import current_time_context, now_eat

logger = logging.getLogger(__name__)


class TaskExtractionResult(BaseModel):
    intent: Literal["create_task", "list_tasks", "complete_task", "delete_task", "general_query"] = Field(
        description="The recognized user intent."
    )
    title: Optional[str] = Field(
        None, description="Clear, concise title of the task."
    )
    description: Optional[str] = Field(
        None, description="Optional extra details or notes about the task."
    )
    due_datetime_iso: Optional[str] = Field(
        None, description="ISO 8601 string of the task's due date/time in Africa/Addis_Ababa (UTC+3)."
    )
    reminder_datetime_iso: Optional[str] = Field(
        None, description="ISO 8601 string of when the reminder should trigger in Africa/Addis_Ababa (UTC+3)."
    )
    target_task_id: Optional[str] = Field(
        None, description="UUID or partial title of an existing task if intent is complete_task or delete_task."
    )
    conversational_reply: str = Field(
        ..., description="A friendly, concise reply to show to the user confirming the action or answering their query."
    )


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _build_system_prompt() -> str:
    time_ctx = current_time_context()
    now = now_eat()

    return (
        "You are a smart task and reminder assistant. "
        "You understand natural language and help users manage tasks and deadlines.\n\n"
        f"CURRENT TIME CONTEXT:\n"
        f"Current time: {time_ctx}\n"
        f"Timezone: Africa/Addis_Ababa (UTC+3)\n"
        f"Use this to compute relative times like 'tomorrow at 6 PM', 'in 2 hours', 'next Monday at 9 AM'. "
        f"All datetime values you return MUST be in Africa/Addis_Ababa timezone (UTC+3, offset +03:00).\n\n"
        "INTENT DETECTION:\n"
        "- create_task: User wants to create a new task or reminder (keywords: remind, schedule, create, set up, don't let me forget)\n"
        "- list_tasks: User wants to see their tasks (keywords: show, list, what are, my tasks)\n"
        "- complete_task: User marks a task as done (keywords: done, completed, finished)\n"
        "- delete_task: User wants to remove a task (keywords: delete, remove, cancel task)\n"
        "- general_query: Anything else\n\n"
        "DATETIME RULES:\n"
        "- 'tomorrow at 6 PM' = tomorrow's date at 18:00 in Addis Ababa time\n"
        "- 'in 30 minutes' = current time + 30 minutes\n"
        "- 'next Friday at 10 AM' = next Friday at 10:00 in Addis Ababa time\n"
        "- Always return ISO 8601 with +03:00 offset\n"
        "- If user says 'remind me 30 mins before X', set reminder_datetime 30 minutes before the due_datetime\n"
        "- If user does not specify a reminder time, set it to 15 minutes before the due_datetime\n\n"
        "REPLY STYLE:\n"
        "- Use AM/PM time format (e.g., '6:30 PM' not '18:30')\n"
        "- Be concise and friendly\n"
        "- Confirm what you understood\n"
        "- Use emojis sparingly for warmth\n\n"
        "If the user input is ambiguous or not a task request, set intent to 'general_query' and reply helpfully."
    )


def extract_task(user_input: str) -> TaskExtractionResult:
    client = _get_client()
    system_prompt = _build_system_prompt()

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=user_input,
        config=GenerateContentConfig(
            system_instruction=system_prompt,
            response_mime_type="application/json",
            response_schema=TaskExtractionResult,
            temperature=0.3,
        ),
    )

    text = response.text.strip()
    logger.info("Gemini raw response: %s", text)

    data = json.loads(text)
    return TaskExtractionResult(**data)
