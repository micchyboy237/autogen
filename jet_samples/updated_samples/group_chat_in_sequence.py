from autogen import GroupChatManager
from autogen import GroupChat
from autogen import ConversableAgent
import random

seed = random.randint(0, 1000)
print(f"SEED #: {seed}")
config_list = [
    {
        "model": "llama3",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
        # "temperature": 1.0,
        "top_p": 1.0,
        "seed": seed,
    }
]

# The Number Agent always returns the same numbers.
number_agent = ConversableAgent(
    name="Number_Agent",
    system_message="You return me the number I give you.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

# The Adder Agent adds 1 to the number it receives.
adder_agent = ConversableAgent(
    name="Adder_Agent",
    system_message="You add 1 to the number I give you and return me the new number.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

# The Multiplier Agent multiplies the number it receives by 2.
multiplier_agent = ConversableAgent(
    name="Multiplier_Agent",
    system_message="You multiply the number I give you by 2 and return me the new number.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

# The Subtracter Agent subtracts 1 from the number it receives.
subtracter_agent = ConversableAgent(
    name="Subtracter_Agent",
    system_message="You subtract 1 from the number I give you and return me the new number.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

# The Divider Agent divides the number it receives by 2.
divider_agent = ConversableAgent(
    name="Divider_Agent",
    system_message="You divide the number I give you by 2 and return me the new number.",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
)

# The `description` attribute is a string that describes the agent.
# It can also be set in `ConversableAgent` constructor.
adder_agent.description = "Add 1 to the input number."
multiplier_agent.description = "Multiply the input number by 2."
subtracter_agent.description = "Subtract 1 from the input number."
divider_agent.description = "Divide the input number by 2."
number_agent.description = "Return the numbes given."


group_chat_with_introductions = GroupChat(
    agents=[adder_agent, multiplier_agent,
            subtracter_agent, divider_agent, number_agent],
    messages=[],
    max_round=6,
    send_introductions=True,
    speaker_selection_method="auto",
    select_speaker_message_template="""You are in a role play game. The following roles are available:
                {roles}.
                Read the following conversation.
                Then select the next role from {agentlist} to play. Only return the role.""",
    select_speaker_prompt_template=(
        "Read the above conversation. Then select the next role from {agentlist} to play. Only return the role."
    ),
    select_speaker_auto_multiple_template="""You provided more than one name in your text, please return the name of the speaker that gets the number closer. To determine the speaker use these prioritised rules:
    1. If the context makes the number closer, choose that speaker's name
    2. If it refers to the speaker name that makes the number closer
    3. Do not choose a speaker that makes the number further away from the requested number
    The names are case-sensitive and should not be abbreviated or changed.
    Respond with ONLY the name of the speaker and DO NOT provide a reason.""",
    select_speaker_auto_none_template="""You will choose a speaker. As a reminder, to determine the speaker use these prioritised rules:
    1. If the context makes the number closer, choose that speaker's name
    2. If it refers to the speaker name that makes the number closer
    3. Do not choose a speaker that makes the number further away from the requested number
    The names are case-sensitive and should not be abbreviated or changed.
    The only names that are accepted are {agentlist}.
    Respond with ONLY the name of the speaker and DO NOT provide a reason.""",
)


group_chat_manager_with_intros = GroupChatManager(
    groupchat=group_chat_with_introductions,
    llm_config={"config_list": config_list},
    # system_message="On each sequence, pass to agents until it returns the corect number. Each agent are required to answer."
)

# Start a sequence of two-agent chats between the number agent and
# the group chat manager.
chat_result = number_agent.initiate_chats(
    [
        {
            "recipient": group_chat_manager_with_intros,
            "message": "My number is 3, I want to turn it into 13.",
        },
        {
            "recipient": group_chat_manager_with_intros,
            "message": "Turn the last number to 32.",
        },
    ]
)

print(chat_result.summary)
