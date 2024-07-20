import json
import random
import redis
from typing import Any, Dict, List, Tuple
from autogen import ConversableAgent, UserProxyAgent
from autogen.io.base import IOStream
from autogen.oai.client import OpenAIWrapper

# default generated redis url w/o password, and db index '0'
DEFAULT_REDIS_URL = "redis://localhost:6379/0"

BOLD = "\u001b[1m"
RESET = "\u001b[0m"
PINK = BOLD + "\u001b[38;5;201m"
CYAN = BOLD + "\u001b[38;5;45m"
YELLOW = BOLD + "\u001b[38;5;220m"
RED = BOLD + "\u001b[38;5;196m"
GREEN = BOLD + "\u001b[38;5;40m"

DEFAULT_SYSTEM_MESSAGE = """
Create a Tagalog interactive story that unfolds based on my choices. Here’s how it works:

1. **Initiate**: I provide a genre, such as romance, adventure, or mystery, and you begin the story.
2. **Interact**: You narrate a part of the story, stopping with ellipses just before a potential verb, noun, adjective or phrase that serves as a choice for me to select. This setup ensures that the choices are integral to the continuation and development of the story.
3. **Choose and Continue**: After I make a selection, you seamlessly incorporate my choice as the first word in the continuation of the narrative.
4. **Structure**: Continue text generation based starting with '...' concatened with my last message. Avoid repeating previous words, phrases and events. Do not show choices at the end unless asked to. Selecting choices should evolve into a complete story with a beginning, middle, and end.

Example interactions:

1.)
Genre: Pag-ibig
You: Si Elena ay isang...

2.)
User: magandang guro
You: ...magandang guro na nakatira sa Maynila. Kahit siya ay maganda, hindi pa niya nararanasan ang tunay na pag-ibig. Si Marco naman ay isang binata na...

2.)
User: doktor
You: ...doktor mula sa Maynila, upang maglingkod sa komunidad. Sa lokal na kapistahan, nagkatagpo ang kanilang mga landas.\n\nUnti-unting nagkakalapit sina Elena at Marco. Ibinahagi nila ang kanilang mga...

3.)
User: pangarap
You: ...pangarap. Habang si Elena ay nagtuturo kay Marco ng kagandahan ng panitikan, ipinakilala naman ni Marco kay Elena ang mundo ng medisina. Ngunit, nagkaroon ng mga...

4.)
User: View - Choices
You: pagsubok, paghihirap

5.)
User: pagsubok
You: ...pagsubok: ang pagtutol ng mga magulang ni Elena at ang alok kay Marco para sa trabaho sa ibang bansa. Sa huli, pinili ni Marco ang...

6.)
User: manatili
You: ...manatili at ipagpatuloy ang kanyang serbisyo sa bayan kasama si Elena. Nagtapos ang kuwento sa isang romantikong tagpo sa lokal na kapistahan, kung saan inialay ni Marco ang kanyang sarili para kay Elena—simbolo ng kanilang pagmamahalan at pinagsamang mga pangarap.
""".lstrip()


class InteractiveStoryTL:
    def __init__(self, initial_message: str = None, system_message: str = DEFAULT_SYSTEM_MESSAGE, redis_url: str = DEFAULT_REDIS_URL, new_chat: bool = False, stream_callback: callable = None, redis_key='shared_key') -> None:
        self.seed = random.randint(0, 1000)
        self.config_list = [
            {
                "model": "llama3",
                "base_url": "http://localhost:11434/v1",
                "api_key": "ollama",
                "temperature": 1.0,
                "top_p": 1.0,
                "seed": self.seed,
                "stream": True,
            }
        ]
        self.iostream = IOStream.get_default()

        # Establish a connection to Redis
        self.redis = redis.from_url(redis_url)
        self.redis_key = redis_key
        self.cached_data = self.get_cache()
        if new_chat or not self.cached_data:
            self.set_cache({
                "user": [],
                "assistant": [],
            })
            self.cached_data = self.get_cache()

        self.max_chat_messages = None
        self.max_context_length = None
        self.initial_message = initial_message
        self.system_message = system_message
        self.out_stream_callback = stream_callback

        self.chat_messages = None

        # Initialize autogen agents
        self.init_agents()

    # def _update_redis(self, recipient: Any, messages: List[str] = [], sender: Any = None, config: Dict[str, Any] = None) -> Tuple[bool, None]:
    #     if len(messages) > 1:
    #         message_dict = {
    #             "user": [],
    #             "assistant": [],
    #         }
    #         for message in messages:
    #             role = None
    #             if message['role'] == "assistant":
    #                 role = "user"
    #             else:
    #                 role = "assistant"

    #             message_dict[role].append(message['content'])

    #         self.iostream.print(CYAN + "_update_redis:\n" + RESET +
    #                             json.dumps(message_dict, indent=2) + "\nUser choice: ", flush=True, end="")
    #     return False, None

    def init_agents(self) -> None:
        self.user_proxy = UserProxyAgent(
            "user",
            code_execution_config=False,
            llm_config={"config_list": self.config_list},
            human_input_mode="ALWAYS",
            # stream_callback=self._stream_callback,
            # stream_response_callback=self._stream_response_callback,
            # system_message=self.system_message,
        )
        self.prev_story_agent = ConversableAgent(
            name="story_agent",
            llm_config={"config_list": self.config_list},
            human_input_mode="NEVER",
        )

        cached_chat_messages = self.cached_data
        current_prompt_len = len(json.dumps(
            [{"content": self.system_message, "role": "system"}, *cached_chat_messages.values()]))
        current_messages_count = sum(
            len(messages) for messages in cached_chat_messages.values())
        self.iostream.print("Current Messages Count: " +
                            GREEN + str(current_messages_count) + RESET)
        self.iostream.print("Current Prompt Length: " +
                            GREEN + str(current_prompt_len) + RESET)

        has_previous_messages = any(
            messages for messages in cached_chat_messages.values())

        if has_previous_messages and self.max_chat_messages:
            while current_messages_count > self.max_chat_messages:
                cached_chat_messages['user'] = cached_chat_messages['user'][1:]
                cached_chat_messages['assistant'] = cached_chat_messages['assistant'][1:]
                current_messages_count = sum(
                    len(messages) for messages in cached_chat_messages.values())
                self.iostream.print("Reduced Messages Count: " +
                                    GREEN + str(current_messages_count) + RESET)

        if has_previous_messages and self.max_context_length:
            while current_prompt_len > self.max_context_length:
                cached_chat_messages['user'] = cached_chat_messages['user'][1:]
                cached_chat_messages['assistant'] = cached_chat_messages['assistant'][1:]
                current_prompt_len = len(json.dumps(
                    [{"content": self.system_message, "role": "system"}, *cached_chat_messages.values()]))
                self.iostream.print("Reduced Prompt Length: " +
                                    GREEN + str(current_prompt_len) + RESET)

        chat_messages = None
        if has_previous_messages:
            self.iostream.print(BOLD + f"\nPrevious Chat Messages:\n" +
                                RESET + json.dumps(cached_chat_messages, indent=2) + "\n")
            chat_messages = {}
            for role, messages in cached_chat_messages.items():
                if role == 'user':
                    chat_messages[self.user_proxy] = messages
                if role == 'assistant':
                    chat_messages[self.prev_story_agent] = messages
        self.chat_messages = chat_messages

        self.story_agent = ConversableAgent(
            name="story_agent",
            llm_config={"config_list": self.config_list},
            human_input_mode="NEVER",
            stream_callback=self._stream_callback,
            stream_response_callback=self._stream_response_callback,
            chat_messages=self.chat_messages,
            system_message=self.system_message,
        )

        # Register the reply function for each agent
        # agents_list = [self.user_proxy, self.story_agent]
        # for agent in agents_list:
        #     agent.register_reply(
        #         [ConversableAgent, None],
        #         reply_func=self._update_redis,
        #         config={"callback": None},
        #     )

    def _stream_callback(self, prompt: str) -> None:
        msg = prompt
        self.iostream.print(GREEN + msg + RESET, flush=True, end="")
        if self.out_stream_callback:
            self.out_stream_callback(prompt)

    def _stream_response_callback(self, messages: List[str]) -> None:
        message_dict = self.cached_data or {
            "user": [],
            "assistant": []
        }
        for message in messages:
            if message['role'] in message_dict:
                new_message = {
                    "role": message['role'],
                    "content": message['content'],
                }

                # Check if new_message is already in the list
                if new_message not in message_dict[message['role']]:
                    message_dict[message['role']].append(new_message)

        self.iostream.print(BOLD + "\nAll Messages:\n" + RESET +
                            json.dumps(message_dict, indent=2))

        total_messages_count = len(messages)
        total_prompt_len = len(json.dumps(
            [{"content": self.system_message, "role": "system"}, *message_dict.values()]))
        self.iostream.print("Total Messages Count: " +
                            GREEN + str(total_messages_count) + RESET)
        self.iostream.print("Total Prompt Length: " +
                            GREEN + str(total_prompt_len) + RESET)
        self.set_cache(message_dict)

    def run(self) -> None:
        if self.cached_data.get('assistant'):

            message = self.cached_data['assistant'][-1]['content']
            self.story_agent.initiate_chat(
                recipient=self.user_proxy,
                message=message,
                clear_history=False,
            )

            # if self.initial_message:
            #     print(
            #         f"GENERATE REPLY MANUALLY:\n{format_user_reply(self.initial_message, initial=False)}")
            #     self.user_proxy.generate_oai_reply(
            #         messages=[{
            #             "content": format_user_reply(self.initial_message, initial=False),
            #             "role": "user"
            #         }],
            #         sender=self.user_proxy,
            #         config=OpenAIWrapper(**{"config_list": self.config_list})
            #     )
            # else:
            #     message = self.cached_data['assistant'][-1]['content']
            #     self.story_agent.initiate_chat(
            #         recipient=self.user_proxy,
            #         message=message,
            #         clear_history=False,
            #     )
        elif self.cached_data.get('user'):
            message = self.cached_data['user'][-1]['content']
            self.user_proxy.initiate_chat(
                recipient=self.story_agent,
                message=message,
                clear_history=False,
            )
        else:
            self.user_proxy.initiate_chat(
                recipient=self.story_agent,
                message=format_user_reply(
                    self.initial_message, initial=True),
                clear_history=False,
            )

    def set_cache(self, data: any):
        self.redis.set(self.redis_key, json.dumps(data))

    def get_cache(self) -> any:
        # Retrieve the JSON string from Redis
        retrieved_json_data = self.redis.get(self.redis_key)

        # Deserialize the JSON string back to a Python dictionary
        if retrieved_json_data:
            cached_data = json.loads(retrieved_json_data)
            return cached_data
        else:
            self.iostream.print(RED + "\nNo redis cached data." + RESET + "\n")
            return None


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
    # all_messages = self.get_chat_results()
    # print(f"self._oai_messages.values():\n{all_messages}")
    # reply = f"Chat history:\n{self._oai_messages.values()}\n\n{reply}"
    self._human_input.append(reply)
    return reply


def format_user_reply(prompt: str, initial: bool = False) -> str:
    if initial:
        message = f"Genre: {prompt}"
    else:
        message = f"User: {prompt}\nYou: ...{prompt}" if prompt and "choices" not in prompt.lower(
        ) else "User: View - Choices"
    return message


def generate_hash(item, max_length=24):
    """Generate a consistent, truncated hash for a given item."""
    import hashlib
    item_str = json.dumps(
        item, sort_keys=True)  # Convert item to a string with sorted keys
    hash_key = hashlib.sha256(item_str.encode()).hexdigest()
    return hash_key[:max_length]


ConversableAgent.get_human_input = get_human_input

if __name__ == "__main__":
    story_id = "6"
    story_app = InteractiveStoryTL(
        redis_key=story_id,
        initial_message="Pag-ibig",
        new_chat=True,
    )
    # story_app = InteractiveStoryTL(
    #     redis_key=story_id,
    #     initial_message="reyna",
    #     new_chat=False,
    # )
    story_app.run()
