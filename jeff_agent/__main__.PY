# Step3: Agent Card
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)

from agent import JeffAgent
#import httpx
from a2a.server.request_handlers import DefaultRequestHandler
from agent_executor import JeffAgentExecutor
from a2a.server.tasks import InMemoryTaskStore
from a2a.server.apps import A2AStarletteApplication
import uvicorn


def main(host = "localhost", port = 10004):

    skill = AgentSkill(
        id="schedule_badminton",
        name="Badminton Scheduling Tool",
        description="Helps with finding Jeff's availability for Badminton",
        tags=["scheduling", "badminton"],
        examples=["Are you free to play badminton on 2025-11-05?"]
    )

    agent_card = AgentCard(
        name="Jeff's Agent",
        description="Helps with scheduling badminton games",
        url=f"http://{host}:{port}/",
        version="1.0.0",
        defaultInputModes=JeffAgent.SUPPORTED_CONTENT_TYPES,
        defaultOutputModes=JeffAgent.SUPPORTED_CONTENT_TYPES,
        capabilities=AgentCapabilities(),
        skills=[skill]
    )
    
    # Step4: Host the Agent
    # request handler
    #httpx_client = httpx.AsyncClient()
    request_handler = DefaultRequestHandler(
        agent_executor=JeffAgentExecutor(),
        task_store=InMemoryTaskStore(),
        #push_notifier=InMemoryPushNotifier(httpx_client),

    )

    # host the app
    server = A2AStarletteApplication(
        agent_card=agent_card, http_handler=request_handler
    )       

    uvicorn.run(server.build(), host=host, port=port)


if __name__ == "__main__":
    main()