import json
import logging
from typing import Optional
from google import genai
from google.genai.types import GenerateContentConfig

from config.settings import settings
from services.timezone_helper import current_time_context, now_eat

logger = logging.getLogger(__name__)


class TaskExtractionResult:
    def __init__(
        self,
        intent: str = "general_query",
        title: Optional[str] = None,
        description: Optional[str] = None,
        due_datetime_iso: Optional[str] = None,
        reminder_datetime_iso: Optional[str] = None,
        target_task_id: Optional[str] = None,
        conversational_reply: str = "",
    ):
        self.intent = intent
        self.title = title
        self.description = description
        self.due_datetime_iso = due_datetime_iso
        self.reminder_datetime_iso = reminder_datetime_iso
        self.target_task_id = target_task_id
        self.conversational_reply = conversational_reply


_client: genai.Client | None = None


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        _client = genai.Client(api_key=settings.gemini_api_key)
    return _client


def _build_system_prompt() -> str:
    time_ctx = current_time_context()

    return (
        "You are a smart task and reminder assistant. "
        "You understand natural language and help users manage tasks and deadlines.\n\n"
        f"CURRENT TIME CONTEXT:\n"
        f"Current time: {time_ctx}\n"
        f"Timezone: Africa/Addis_Ababa (UTC+3)\n"
        f"Use this to compute relative times like 'tomorrow at 6 PM', 'in 2 hours', 'next Monday at 9 AM'. "
        f"All datetime values you return MUST be in Africa/Addis_Ababa timezone (UTC+3, offset +03:00).\n\n"
        "INTENT DETECTION:\n"
        "- create_task: User wants to create a new task or reminder\n"
        "- list_tasks: User wants to see their tasks\n"
        "- complete_task: User marks a task as done\n"
        "- delete_task: User wants to remove a task\n"
        "- general_query: Anything else\n\n"
        "DATETIME RULES:\n"
        "- 'tomorrow at 6 PM' = tomorrow at 18:00 in Addis Ababa time\n"
        "- Always return ISO 8601 with +03:00 offset\n"
        "- If user says 'remind me 30 mins before X', set reminder_datetime 30 mins before due\n"
        "- Default reminder: 15 mins before due if not specified\n\n"
        "REPLY STYLE:\n"
        "- Use AM/PM format (e.g., '6:30 PM')\n"
        "- Be concise and friendly\n\n"
        "Return ONLY a JSON object with these keys:\n"
        '{"intent": "create_task|list_tasks|complete_task|delete_task|general_query", '
        '"title": "string or null", '
        '"description": "string or null", '
        '"due_datetime_iso": "ISO8601 string or null", '
        '"reminder_datetime_iso": "ISO8601 string or null", '
        '"target_task_id": "string or null", '
        '"conversational_reply": "string"}'
    )


def extract_task(user_input: str) -> TaskExtractionResult:
    client = _get_client()
    system_prompt = _build_system_prompt()

    response = client.models.generate_content(
        model="gemini-2.5-flash-lite",
        contents=user_input,
        config=GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.3,
        ),
    )

    text = response.text.strip()
    logger.info("Gemini raw response: %s", text)

    # Strip markdown code fences if present
    if text.startswith("```json"):
        text = text[7:]
    if text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    text = text.strip()

    data = json.loads(text)
    return TaskExtractionResult(
        intent=data.get("intent", "general_query"),
        title=data.get("title"),
        description=data.get("description"),
        due_datetime_iso=data.get("due_datetime_iso"),
        reminder_datetime_iso=data.get("reminder_datetime_iso"),
        target_task_id=data.get("target_task_id"),
        conversational_reply=data.get("conversational_reply", ""),
    )
