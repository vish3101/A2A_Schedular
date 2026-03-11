from crewai import Agent, Crew, Process, Task
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
import os

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
            goal="Answer questions about Mark's schedule with exact free and busy timings.",
            backstory=(
                "You are a helpful scheduling assistant who checks Mark's calendar "
                "for badminton scheduling. Use the availability tool to answer "
                "questions about dates, free time, busy time, and exact timings."
            ),
            tools=[AvailabilityTool()],
            llm=self.llm,
            verbose=True,
        )

    async def invoke(self, user_question: str) -> str:
        try:
            task = Task(
                description=f"Answer this question about Mark's schedule: {user_question}",
                expected_output="A clear answer about Mark's availability with timings if available.",
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