from autogen import ConversableAgent, UserProxyAgent
from autogen import AssistantAgent, UserProxyAgent
from autogen.io.base import IOStream
import random

seed = random.randint(0, 1000)
config_list = [
    {
        "model": "llama3",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        "temperature": 0,
        # "top_p": 1.0,
        "seed": seed,
    }
]
print(f"\nSEED #: {seed}\n")

# Create the agent that uses the LLM.
assistant = ConversableAgent(
    name="story_agent",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
    system_message="""
Create an interactive story that unfolds based on my choices. Here’s how it works:

1. **Initiate**: I provide a genre, such as romance, adventure, or mystery, and you begin the story.
2. **Interact**: You narrate a part of the story, stopping with ellipses just before a potential verb or noun that serves as a choice for me to select. This setup ensures that the choices are integral to the continuation and development of the story.
3. **Choose and Continue**: After I make a selection, you seamlessly incorporate my choice as the first word in the continuation of the narrative. 
4. **Loop**: This cycle of narrating parts of the story and presenting choices repeats, evolving into a complete story with a beginning, middle, and end.

Example interaction:

Me: Genre - Romance
You: Under the soft moonlight, Anna and Jose walked along the...
Me: beach
You: beach, hand in hand. They had been friends for a long time, but on that night, both felt a new emotion bubbling up in their hearts. 'Jose, do you...
Me: think
You: think there's a chance for us?' Anna asked quietly, yet hopefully. Jose didn't answer immediately. He...
Me: """.lstrip(),
    description="""Continue text generation based on 'Me'. End it with '...'"""
)

# Create the agent that represents the user in the conversation.
user_proxy = UserProxyAgent(
    "user",
    code_execution_config=False,
    llm_config={"config_list": config_list},
    human_input_mode="ALWAYS"
)


def get_human_input(self, prompt: str) -> str:
    """Get human input.

    Override this method to customize the way to get human input.

    Args:
        prompt (str): prompt for the human input.

    Returns:
        str: human input.
    """
    iostream = IOStream.get_default()

    prompt = ""
    reply = iostream.input(prompt)
    reply = format_user_reply(reply)
    self._human_input.append(reply)
    return reply


def format_user_initial(prompt: str) -> str:
    message = f"Me: {prompt}\nYou:"
    return message


def format_user_reply(prompt: str) -> str:
    message = f"...{prompt}"
    return message


ConversableAgent.get_human_input = get_human_input

# Let the assistant start the conversation.  It will end when the user types exit.
user_proxy.initiate_chat(
    recipient=assistant,
    message=format_user_initial("Genre - Romance"),
    clear_history=True,
)
