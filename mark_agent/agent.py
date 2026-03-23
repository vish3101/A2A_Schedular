from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os
from datetime import datetime

from tools import AvailabilityTool

load_dotenv()


class MarkAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")

        self.llm = ChatOpenAI(
            model="gpt-3.5-turbo",
            temperature=0.2
        )

        self.agent = Agent(
            role="Scheduling Assistant",
            goal=(
                "Answer questions about Mark's calendar with EXACT free and busy timings. "
                "Always call the availability tool. "
                "Return answers in this EXACT format:\n"
                "AVAILABLE: <comma-separated time ranges or 'None'>\n"
                "BUSY: <comma-separated time ranges or 'None'>\n"
                "Do NOT add extra commentary."
            ),
            backstory=(
                "You are Mark's scheduling assistant. You ONLY answer calendar questions. "
                "When asked about 'today', resolve today's date as YYYY-MM-DD and pass it to the tool. "
                "If the question is unrelated to scheduling, reply: 'I only handle Mark's schedule.' "
                "Always use the AvailabilityTool before answering — never guess."
            ),
            tools=[AvailabilityTool()],
            llm=self.llm,
            verbose=True,
        )

    async def invoke(self, user_question: str) -> str:
        try:
            task = Task(
                description=(
                    f"Answer this scheduling question: {user_question}\n"
                    f"Today's date is {datetime.now().strftime('%Y-%m-%d')}.\n"
                    "Use the availability tool and return results in the format:\n"
                    "AVAILABLE: <time ranges>\nBUSY: <time ranges>"
                ),
                expected_output=(
                    "Two lines exactly:\n"
                    "AVAILABLE: <comma-separated time ranges or 'None'>\n"
                    "BUSY: <comma-separated time ranges or 'None'>"
                ),
                agent=self.agent,
            )

            crew = Crew(
                agents=[self.agent],
                tasks=[task],
                process=Process.sequential,
                verbose=True,
            )

            result = crew.kickoff()
            return str(result) if result else "No response available"

        except Exception as e:
            print(f"[ERROR] mark_agent.invoke: {e}")
            return f"Sorry, I encountered an error: {str(e)}"