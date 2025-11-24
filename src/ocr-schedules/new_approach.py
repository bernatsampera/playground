import base64

from langchain.chat_models import init_chat_model
from pydantic import BaseModel, Field


# Define your schedule structure
class ScheduleEvent(BaseModel):
    time: str = Field(description="Event time (e.g., 09:00 AM)")
    activity: str = Field(description="Activity name")
    location: str = Field(description="Location/room")


class Schedule(BaseModel):
    events: list[ScheduleEvent] = Field(description="List of scheduled events")


# Initialize Ollama model via init_chat_model
# Make sure Ollama is running locally (default: http://localhost:11434)
model = init_chat_model(
    "gpt-oss:20b",  # Ollama model identifier
    model_provider="ollama",
    base_url="http://localhost:11434",  # Ollama API endpoint
)

# Bind structured output directly - no extra LLM calls
structured_model = model.with_structured_output(Schedule)

# Load and encode your image
with open("/Users/bsampera/Documents/test/playground/Stundenplan-Muc.png", "rb") as f:
    image_data = base64.b64encode(f.read()).decode("utf-8")

# Single call - get JSON directly
message = structured_model.invoke(
    [
        {
            "role": "user",
            "content": [
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/jpeg;base64,{image_data}"},
                },
                {
                    "type": "text",
                    "text": "Extract all schedule events from this image. Return as structured JSON with time, activity, and location for each event.",
                },
            ],
        }
    ]
)

# Access the structured response
schedule = message  # Already validated Pydantic model
print(schedule)
# Output: Schedule(events=[ScheduleEvent(time='09:00 AM', activity='Team Meeting', location='Room A'), ...])

# Convert to JSON if needed
import json

print(json.dumps(schedule.model_dump(), indent=2))
