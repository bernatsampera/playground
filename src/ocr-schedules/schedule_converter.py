from typing import List, Optional

from langchain.chat_models import init_chat_model
from langchain_core.prompts import ChatPromptTemplate
from pydantic import BaseModel, Field


class ClassSession(BaseModel):
    day: str = Field(..., description="Day of week (Montag, Dienstag, etc.)")
    activity: str = Field(..., description="Activity name")
    start_time: Optional[str] = Field(None, description="Start time HH:MM")
    end_time: Optional[str] = Field(None, description="End time HH:MM")


class Schedule(BaseModel):
    sessions: List[ClassSession]


def clean_ocr_data(markdown_text: str) -> str:
    model = init_chat_model("ollama:gpt-oss:20b")

    clean_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
Extract schedule activities from messy OCR markdown table.
Format each activity as: DAY: ACTIVITY | TIME | DETAILS
- Extract times from "10-11 Uhr", "14:30-15:00", etc.
- Use "-" if no time or details specified
- Days in English: Monday, Tuesday, etc.
""",
            ),
            ("human", "{markdown_text}"),
        ]
    )

    clean_chain = clean_prompt | model
    clean_result = clean_chain.invoke({"markdown_text": markdown_text})
    return clean_result.content


def parse_schedule_to_json(clean_text: str) -> str:
    model = init_chat_model("ollama:gpt-oss:20b")

    json_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """
Parse clean schedule format into structured JSON.
Extract: day, activity, start_time, end_time.
Convert times to HH:MM format. Leave null if not specified.
""",
            ),
            ("human", "{clean_text}"),
        ]
    )

    structured_llm = model.with_structured_output(Schedule)
    json_chain = json_prompt | structured_llm

    json_result = json_chain.invoke({"clean_text": clean_text})
    return json_result.model_dump_json(indent=2)


def convert_schedule_to_json(markdown_text: str) -> str:
    clean_text = clean_ocr_data(markdown_text)
    return parse_schedule_to_json(clean_text)


if __name__ == "__main__":
    sample_markdown = """
| Montag       | Dienstag     | Mittwoch    | Donnerstag   | Freitag    | Samstag    | Sonntag    |
|-------------|------------|-------------|-------------|-----------|------------|------------|
| Personal Training | BJJ Intermediate 10 - 11 Uhr | Personal Training | BJJ Intermediate 10 - 11 Uhr | Personal Training | Luta Livre Intermediate 10 - 11 Uhr | Yoga 11 - 12 Uhr |
| Personal Training | Freies Training 11 - 12 Uhr | Personal Training | Freies Training 11 - 12 Uhr | Personal Training | Freies Training 11 - 12 Uhr | Yoga 11 - 12 Uhr |
| BJJ Hero Minis 1 (3 - 6 J.) 14:30 - 15:00 | Personal Training | BJJ Hero Minis 1 (3 - 6 J.) 14:30 - 15:00 | Personal Training | BJJ Heroes Minis 1 (3 - 6 J.) 14:30 - 15:00 | Yoga 12:30 - 13:30 Uhr | |
| BJJ Hero Minis 2 (3 - 6 J.) 15:15 - 15:45 | Capoeira Minis (4 - 6 J.) 15:15 - 15:45 Uhr | BJJ Hero Minis 2 (3 - 6 J.) 15:15 - 15:45 | Capoeira Minis 2 (4 - 6 J.) 15:15 - 15:45 Uhr | BJJ Hero Minis 2 (3 - 3 J.) 15:15 - 15:45 Uhr | |
| BJJ Hero Kids (6 - 8 J.) 16 - 16:45 Uhr | Capoeira Kids (7 - 9 J.) 16 - 16:45 Uhr | BJJ Hero Kids (6 - 8 J.) 16 - 16:45 Uhr | Capoeira Kids (7 - 9) 16 - 16:45 Uhr | BJJ Hero Kids (6 - 8 J.) 16 - 16:45 Uhr | |
| BJJ Hero Teens (9 - 14 J.) 17 - 17:45 Uhr | Capoeira Teens (10 - 14 J.) 17 - 17:45 Uhr | BJJ Hero Teens (9 - 14 J.) 17 - 17:45 Uhr | Capoeira Teens (10 - 14) 17 - 17:45 Uhr | BJJ Hero Teens (9 - 14 J.) 17 - 17:45 Uhr | |
| BJJ Intermediate/ Luta Livre Int. 18 - 19 Uhr | BJJ Intro 18 - 19 Uhr | BJJ Intermediate/ Luta Livre Advanced 18 - 19 Uhr | BJJ Intro 18 - 19 Uhr | Krav Maga/ Kickboxen 18 - 19 Uhr | |
| BJJ Intro 19 - 20 Uhr | Kickboxen 19 - 20 Uhr | BJJ Intro 19 - 20 Uhr | Kickboxen 19 - 20 Uhr | BJJ Intro 19 - 20 Uhr |
| Krav Maga/ Kickboxen 20 - 21 Uhr | BJJ Advanced 20 - 21:30 Uhr | Krav Maga/ Kickboxen 20 - 21 Uhr | BJJ Advanced 20 - 21:30 Uhr | BJJ Intermediate/ Luta Livre Int. 20 - 21 Uhr | |
    """

    print("Converting schedule to JSON:")
    print(convert_schedule_to_json(sample_markdown))
