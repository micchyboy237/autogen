from autogen import ConversableAgent, UserProxyAgent
from autogen import AssistantAgent, UserProxyAgent

config_list = [
    {
        "model": "llama3",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]

# assistant = AssistantAgent("assistant", llm_config={
#                            "config_list": config_list})

# user_proxy = UserProxyAgent("user_proxy", code_execution_config={
#                             "work_dir": "coding", "use_docker": False})
# user_proxy.initiate_chat(
#     assistant, message="Plot a chart of NVDA and TESLA stock price change YTD.")


# Create the agent that uses the LLM.
assistant = ConversableAgent(
    "agent", llm_config={"config_list": config_list}, human_input_mode="NEVER")

# Create the agent that represents the user in the conversation.
user_proxy = UserProxyAgent("user", code_execution_config=False, llm_config={
                            "config_list": config_list}, human_input_mode="NEVER")

# Let the assistant start the conversation.  It will end when the user types exit.
assistant.initiate_chat(user_proxy, message="How can I help you today?")
