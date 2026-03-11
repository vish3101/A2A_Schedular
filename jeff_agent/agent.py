from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from langchain_core.messages.ai import AIMessage
from tools import get_availability

load_dotenv()

memory = MemorySaver()


class JeffAgent:
    SUPPORTED_CONTENT_TYPES = ["text", "text/plain"]

    def __init__(self):
        self.model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.2)
        self.tools = [get_availability]
        self.system_prompt = (
            "You are Jeff Bezos's scheduling assistant.\n"
            "Your only job is to answer questions about Jeff's badminton availability.\n"
            "Always use the get_availability tool when the user asks about dates, schedule, availability, free time, busy time, or timings.\n"
            "If the tool returns free slots or busy slots, report them clearly.\n"
            "If the question is unrelated to scheduling, politely say you cannot help."
        )

        self.graph = create_agent(
            self.model,
            tools=self.tools,
            system_prompt=self.system_prompt,
            checkpointer=memory
        )

    async def get_response(self, query, context_id):
        inputs = {"messages": [("user", query)]}
        config = {"configurable": {"thread_id": context_id}}
        raw_response = self.graph.invoke(inputs, config)

        messages = raw_response.get("messages", [])
        ai_messages = [message.content for message in messages if isinstance(message, AIMessage)]

        if not ai_messages:
            return {"content": "No response"}

        content = ai_messages[-1]
        if isinstance(content, list):
            text_parts = [part.get("text", "") if isinstance(part, dict) else str(part) for part in content]
            response = " ".join(text_parts)
        else:
            response = str(content)

        return {"content": response}