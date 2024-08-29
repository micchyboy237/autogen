import os
import autogen
import tempfile
from autogen.coding import LocalCommandLineCodeExecutor


print("")
# Get current directory
current_dir = os.path.dirname(os.path.realpath(__file__))
print(f"Script directory: {current_dir}")
# Set the working directory to the script directory
work_dir = current_dir
coding_dir = "./coding"
os.chdir(work_dir)
print(f"Current working directory: {os.getcwd()}")
print(f"Code directory: {coding_dir}")


# Step 1: Setup Local Command Line Code Executor
os.makedirs(coding_dir, exist_ok=True)
print(f"Coding directory: {coding_dir}")
executor = LocalCommandLineCodeExecutor(
    timeout=10,  # Timeout for each code execution in seconds.
    # Use the temporary directory to store the code files.
    work_dir=coding_dir,
    execution_policies={
        "bash": True,
        "shell": True,
        "sh": True,
        "pwsh": True,
        "powershell": True,
        "ps1": True,
        "python": True,
        "javascript": True,
        "typescript": True,
        "jsx": False,
        "tsx": False,
        "html": False,
        "css": False,
    }
)
code_execution_config = {"executor": executor}

# Step 2: LLM Configuration
# config_list = autogen.config_list_from_json("OAI_CONFIG_LIST")
config_list = [
    {
        "model": "NotRequired",
        "api_key": "NotRequired",
        "base_url": "http://0.0.0.0:4000",
        "stream": True
    }
]

llm_config = {
    # Turns off caching, useful for testing different models
    "cache_seed": None,
    # "config_list": config_list,
    "config_list": config_list,
    "temperature": 0,
    "timeout": 120,
}


# Step 3: Define Agents
initializer = autogen.UserProxyAgent(
    name="Init_1",
    code_execution_config=False,
)

executor_agent = autogen.UserProxyAgent(
    name="Execute_Action_1",
    system_message="Executor. Execute the code written by the Coder and report the result.",
    human_input_mode="NEVER",
    code_execution_config=code_execution_config,
)

coder = autogen.AssistantAgent(
    name="Develop_Action_1",
    llm_config=llm_config,
    system_message="""You are the Coder. Write a React Native component with types for a user login screen with username and password fields, and a login button. The component should use Expo and follow best practices for performance and scalability. Include appropriate styling and state management. Only respond with the code block to keep it brief."""
)

optimizer = autogen.AssistantAgent(
    name="Optimize_Action_1",
    llm_config=llm_config,
    system_message="""You are the Optimizer. Analyze the given React Native code for performance improvements. Suggest and implement optimizations related to state management, rendering efficiency, and any other best practices to ensure the component is optimized for mobile performance."""
)

tester = autogen.AssistantAgent(
    name="Test_Action_1",
    llm_config=llm_config,
    system_message="""You are the Tester. Write and execute tests for the given React Native component to ensure it functions correctly. Include unit tests, integration tests, and performance tests. Ensure that the component handles all edge cases and performs well under various conditions."""
)

# Step 4: Define State Transition Function


def all_tests_passed(test_result_message):
    # Assume the test result message is a string containing test results
    # For simplicity, we consider tests passed if the message contains "All tests passed"
    return "All tests passed" in test_result_message["content"]


def state_transition(last_speaker, groupchat):
    messages = groupchat.messages

    if last_speaker is initializer:
        return coder
    elif last_speaker is coder:
        return executor_agent
    elif last_speaker is executor_agent:
        return optimizer
    elif last_speaker is optimizer:
        return tester
    elif last_speaker is tester:
        if all_tests_passed(messages[-1]):
            return None  # End the workflow
        else:
            return coder  # Return to coder for revisions


groupchat = autogen.GroupChat(
    agents=[initializer, coder, executor_agent, optimizer, tester],
    messages=[],
    max_round=20,
    speaker_selection_method=state_transition,
)
manager = autogen.GroupChatManager(groupchat=groupchat, llm_config=llm_config)

# Step 5: Initiate Workflow
task_description = "Develop a scalable and optimized React Native component for a user login screen."
chat_result = initializer.initiate_chat(manager, message=task_description)

# print(f"\nChat result: {chat_result.summary}")
print(f"\nChat Summary:\n{chat_result.summary}")
