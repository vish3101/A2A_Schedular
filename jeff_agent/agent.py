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
            "You are Jeff's scheduling assistant. You ONLY handle calendar availability queries.\n\n"
            "RULES:\n"
            "1. ANY message containing a date, the word 'today', 'available', 'free', 'busy', or 'schedule' "
            "MUST trigger a call to get_availability. No exceptions.\n"
            "2. When the message contains 'today', extract today's date as YYYY-MM-DD yourself and pass it to the tool.\n"
            "3. ALWAYS call get_availability FIRST before forming any response.\n"
            "4. Return your answer in this EXACT format:\n"
            "   AVAILABLE: <comma-separated time ranges or 'None'>\n"
            "   BUSY: <comma-separated time ranges or 'None'>\n"
            "5. Do NOT add greetings, apologies, or extra commentary.\n"
            "6. ONLY if the message has zero relation to dates or scheduling, reply: "
            "'I only handle Jeff's schedule.'\n"
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