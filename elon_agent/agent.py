
# import asyncio
# import uuid
# import httpx
# from dotenv import load_dotenv
# from google.adk.agents import Agent
# from google.adk.tools.tool_context import ToolContext
# from google.adk.models.lite_llm import LiteLlm
# from a2a.client import A2ACardResolver, A2AClient
# from a2a.types import (
#     AgentCard,
#     MessageSendParams,
#     SendMessageRequest,
#     SendMessageResponse,
# )
# import datetime

# from .tools import book_badminton_court, list_court_availabilities

# load_dotenv()

# class RemoteAgentConnection:
#     """
#     Represents a single connection between the Host Agent and one remote friend agent.

#     Each connection wraps the A2AClient, which knows how to send messages
#     to that agent over HTTP.
#     """

#     def __init__(self, agent_card: AgentCard, agent_url: str):
#         self.agent_card = agent_card
#         self.agent_url = agent_url
#         self.http_client = httpx.AsyncClient(timeout=30)
#         self.client = A2AClient(self.http_client, agent_card, url=agent_url)

#     async def send_message(self, message_request: SendMessageRequest) -> SendMessageResponse:
#         """Send a message to this remote agent."""
#         return await self.client.send_message(message_request)
    
# import nest_asyncio
# nest_asyncio.apply()

# class ElonAgent:

#     def __init__(self, remote_agent_urls):
#         self.remote_agent_urls = remote_agent_urls or []
#         self.remote_connections = {}
#         self.cards = {}
#         self.agent = None

#     async def create_agent(self):
        
#         await self._load_remote_agents()

#         self.agent = Agent(
#             model=LiteLlm(model="openai/gpt-4o"),
#             name="elon_agent",
#             description="Helps coordinate badminton games with friends",
#             instruction=self._get_instruction(),
#             tools=[
#                 self.send_message,
#                 book_badminton_court,
#                 list_court_availabilities,
#             ],
#         )

#         return self.agent
    
#     def _get_instruction(self):
#         """Describes what our Host Agent should do."""
#         friends = "\n".join([card.name for card in self.cards.values()]) or "No friends yet"

#         return f"""
#             You are the Host Agent — a helpful coordinator who loves Badminton.
#             Your mission: organize a game with your friends.

#             - Ask friends for availability from today.
#             - Find a common time.
#             - Check court availability.
#             - Book a court when confirmed.

#             **Friends:**
#             {friends}

#             **Today's date**
#             {datetime.datetime.now()}
#             """
    
#     async def _load_remote_agents(self):
#         async with httpx.AsyncClient(timeout=30) as client:
#             for url in self.remote_agent_urls:
#                 resolver = A2ACardResolver(client, url)
#                 card = await resolver.get_agent_card()
#                 self.remote_connections[card.name] = RemoteAgentConnection(card, url)
#                 self.cards[card.name] = card


#     async def send_message(self, agent_name: str, task: str, tool_context: ToolContext):
#         """Sends a message to a friend agent."""
#         connection = self.remote_connections.get(agent_name)
#         if not connection:
#             raise ValueError(f"No such agent: {agent_name}")

#         message_id = str(uuid.uuid4())
#         payload = {
#             "message": {
#                 "role": "user",
#                 "parts": [{"type": "text", "text": task}],
#                 "messageId": message_id,
#             }
#         }

#         request = SendMessageRequest(id=message_id, params=MessageSendParams.model_validate(payload))
#         response = await connection.send_message(request)
#         print(f"[INFO] Sent message to {agent_name}")
#         return response


# async def setup():
#     # Step 1: Define the friend agents our host should connect to.
#     friend_urls = ["http://localhost:10004", "http://localhost:10005"]

#     print("🌟 Starting up the Host Agent...")
#     host = ElonAgent(remote_agent_urls=friend_urls)

#     # Step 2: Actually create the AI agent (this does async setup under the hood)
#     agent = await host.create_agent()
#     print("✅ Host Agent is ready to coordinate badminton games!")
#     return agent


# root_agent = Agent(
#     model=LiteLlm(model="openai/gpt-4o"),
#     name="elon_agent",
#     description="Test agent",
#     instruction="You are a test agent.",
# )

import uuid
import httpx
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from google.adk.models.lite_llm import LiteLlm
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import MessageSendParams, SendMessageRequest
from datetime import datetime
from .tools import book_badminton_court, list_court_availabilities

load_dotenv()

REMOTE_AGENT_URLS = {
    "jeff_agent": "http://localhost:10004",
    "mark_agent": "http://localhost:10005",
}

async def send_message(agent_name: str, task: str, tool_context: ToolContext):
    url = REMOTE_AGENT_URLS.get(agent_name)
    if not url:
        raise ValueError(f"No such agent configured: {agent_name}")

    async with httpx.AsyncClient(timeout=30) as http_client:
        resolver = A2ACardResolver(http_client, url)
        card = await resolver.get_agent_card()

        client = A2AClient(http_client, card, url=url)

        message_id = str(uuid.uuid4())
        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
            }
        }

        request = SendMessageRequest(
            id=message_id,
            params=MessageSendParams.model_validate(payload)
        )

        response = await client.send_message(request)
        return response

root_agent = Agent(
    model=LiteLlm(model="openai/gpt-4o"),
    name="elon_agent",
    description="Coordinates badminton games by checking friends' availability and booking courts.",
    instruction=f"""
You are Elon's personal badminton coordinator. Today's date is {datetime.now().strftime('%Y-%m-%d')}.

YOUR ONLY JOB: Schedule badminton games. Refuse anything unrelated politely.

STRICT RULES:
1. If asked anything NOT about badminton scheduling, reply: "I'm only able to help with badminton scheduling. Let me know if you'd like to set up a game!"
2. NEVER guess availability — always call send_message to check.
3. When the user says "today", use today's date: {datetime.now().strftime('%Y-%m-%d')}.

WORKFLOW (follow this exactly):
Step 1 - Check availability:
  - Call send_message("jeff_agent", "What is Jeff's availability on YYYY-MM-DD? Return free and busy slots.")
  - Call send_message("mark_agent", "What is Mark's availability on YYYY-MM-DD? Return free and busy slots.")

Step 2 - Find overlap:
  - Compare the AVAILABLE slots from both responses.
  - Identify time ranges where BOTH Jeff AND Mark are free.

Step 3 - Check courts:
  - Call list_court_availabilities(date) to see open court slots.
  - Match court slots against the overlapping free time.

Step 4 - Book or report:
  - If a match is found: call book_badminton_court and confirm to the user with date, time, and who's playing.
  - If no match: report the individual schedules and explain there is no common free slot.

OUTPUT FORMAT (always use this):
```
Jeff's schedule on <date>:
  Available: <times>
  Busy: <times>

Mark's schedule on <date>:
  Available: <times>
  Busy: <times>

Common free slots: <times or 'None'>
Court availability: <times or 'None'>
Booking result: <confirmation or 'Could not book — no matching slot'>
```
""",
    tools=[
        send_message,
        book_badminton_court,
        list_court_availabilities,
    ],
)