
import asyncio
import uuid
import httpx
from dotenv import load_dotenv
from google.adk import Agent
from google.adk.tools.tool_context import ToolContext
from google.adk.models.lite_llm import LiteLlm
from a2a.client import A2ACardResolver, A2AClient
from a2a.types import (
    AgentCard,
    MessageSendParams,
    SendMessageRequest,
    SendMessageResponse,
)
import datetime

from .tools import book_badminton_court, list_court_availabilities

load_dotenv()

class RemoteAgentConnection:
    """
    Represents a single connection between the Host Agent and one remote friend agent.

    Each connection wraps the A2AClient, which knows how to send messages
    to that agent over HTTP.
    """

    def __init__(self, agent_card: AgentCard, agent_url: str):
        self.agent_card = agent_card
        self.agent_url = agent_url
        self.http_client = httpx.AsyncClient(timeout=30)
        self.client = A2AClient(self.http_client, agent_card, url=agent_url)

    async def send_message(self, message_request: SendMessageRequest) -> SendMessageResponse:
        """Send a message to this remote agent."""
        return await self.client.send_message(message_request)
    
import nest_asyncio
nest_asyncio.apply()

class ElonAgent:

    def __init__(self, remote_agent_urls):
        self.remote_agent_urls = remote_agent_urls or []
        self.remote_connections = {}
        self.cards = {}
        self.agent = None

    async def create_agent(self):
        
        await self._load_remote_agents()

        self.agent = Agent(
            model=LiteLlm(model="openai/gpt-4o"),
            name="elon_agent",
            description="Helps coordinate badminton games with friends",
            instruction=self._get_instruction(),
            tools=[
                self.send_message,
                book_badminton_court,
                list_court_availabilities,
            ],
        )

        return self.agent
    
    def _get_instruction(self):
        """Describes what our Host Agent should do."""
        friends = "\n".join([card.name for card in self.cards.values()]) or "No friends yet"

        return f"""
            You are the Host Agent — a helpful coordinator who loves Badminton.
            Your mission: organize a game with your friends.

            - Ask friends for availability from today.
            - Find a common time.
            - Check court availability.
            - Book a court when confirmed.

            **Friends:**
            {friends}

            **Today's date**
            {datetime.datetime.now()}
            """
    
    async def _load_remote_agents(self):
        async with httpx.AsyncClient(timeout=30) as client:
            for url in self.remote_agent_urls:
                resolver = A2ACardResolver(client, url)
                card = await resolver.get_agent_card()
                self.remote_connections[card.name] = RemoteAgentConnection(card, url)
                self.cards[card.name] = card


    async def send_message(self, agent_name: str, task: str, tool_context: ToolContext):
        """Sends a message to a friend agent."""
        connection = self.remote_connections.get(agent_name)
        if not connection:
            raise ValueError(f"No such agent: {agent_name}")

        message_id = str(uuid.uuid4())
        payload = {
            "message": {
                "role": "user",
                "parts": [{"type": "text", "text": task}],
                "messageId": message_id,
            }
        }

        request = SendMessageRequest(id=message_id, params=MessageSendParams.model_validate(payload))
        response = await connection.send_message(request)
        print(f"[INFO] Sent message to {agent_name}")
        return response


async def setup():
    # Step 1: Define the friend agents our host should connect to.
    friend_urls = ["http://localhost:10004", "http://localhost:10005"]

    print("🌟 Starting up the Host Agent...")
    host = ElonAgent(remote_agent_urls=friend_urls)

    # Step 2: Actually create the AI agent (this does async setup under the hood)
    agent = await host.create_agent()
    print("✅ Host Agent is ready to coordinate badminton games!")
    return agent


root_agent = asyncio.run(setup())