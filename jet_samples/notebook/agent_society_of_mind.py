import autogen  # noqa: E402

import os
import random
from autogen.coding import LocalCommandLineCodeExecutor
from autogen.coding.jet_code_extractor import CodeBlockExtractor, CodeBlockSaver
from autogen.io.jet_base import CapturingIOStream, IOStream

task = "Provide an empty React Native component with types with a file named 'Sample.tsx'."


config_list = autogen.config_list_from_json(
    env_or_file="OAI_CONFIG_LIST",
)

llm_config = {
    "timeout": 600,
    "temperature": 0,
    "cache_seed": 42,  # change the seed for different trials
    "config_list": config_list,
}
developer_llm_config = llm_config
reviewer_llm_config = llm_config
manager_llm_config = llm_config
society_of_mind_llm_config = llm_config


script_dir = os.path.dirname(os.path.realpath(__file__))
coding_dir = f"{script_dir}/coding"
work_dir = f"{coding_dir}/society_of_mind"

# Print current working directory
print(f"Current working directory: {os.getcwd()}")
# Print work_dir
print(
    f"Work directory: {os.path.abspath(work_dir)}")
# Create the work directory if it does not exist
os.makedirs(coding_dir, exist_ok=True)
os.makedirs(work_dir, exist_ok=True)


# Define the flush listener for stream output
flushed_output = ''
final_output = ''


def flush_listener(output: str) -> None:
    # Should print the output to the console without creating a new line
    global flushed_output
    flushed_output = output
    print(flushed_output, end='')
    # Should store the output in a variable for later use
    global final_output
    final_output += output

    code_block_extractor = CodeBlockExtractor()
    extracted_code_blocks = code_block_extractor.extract_code_blocks(
        final_output)

    if extracted_code_blocks:
        save_code_block(final_output)
        final_output = ''


def save_code_block(text_with_code_block):
    # Extract code blocks
    code_block_extractor = CodeBlockExtractor()
    extracted_code_blocks = code_block_extractor.extract_code_blocks(
        text_with_code_block)

    if extracted_code_blocks:
        # Save extracted code blocks
        code_block_saver = CodeBlockSaver(directory=work_dir)

        for code_block in extracted_code_blocks:
            if code_block.filename:
                saved_file_path = code_block_saver.save_code_block(code_block)
                print(f"Code block saved to: {saved_file_path}")
            else:
                print("No filename found for the code block, skipping save.")
    # else:
    #     print("No code blocks found in the text.")


# Set the custom IOStream as the global default
capturing_iostream = CapturingIOStream()
capturing_iostream.set_flush_listener(flush_listener)
IOStream.set_global_default(capturing_iostream)


CODER_SYSTEM_MESSAGE = """You are a helpful AI assistant providing javascript code for user tasks. Ensure the code is executable and complete. Clearly explain your plans and use 'console.log' for output. Include types and write separate tests for each API route. Surround code with code blocks. Add // filename: <filename> at the beginning of the code block to indicate the file name where the code should be saved. Don't include multiple code blocks in one response.
""".strip()

REVIEW_SYSTEM_MESSAGE = """You are a helpful AI assistant reviewing the javascript code provided by the user. Ensure the code is refactored, optimized, and follows best practices. Provide feedback on the code quality, readability, and efficiency. Suggest improvements and corrections. Surround code with code blocks. Include // filename: <filename> at the beginning of the code block to indicate the file name where the code should be saved. Don't include multiple code blocks in one response.
""".strip()

# Define the code agents
coder_agent = autogen.AssistantAgent(
    "coder-agent",
    system_message=CODER_SYSTEM_MESSAGE,
    llm_config=developer_llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
)

reviewer_agent = autogen.AssistantAgent(
    "reviewer-agent",
    system_message=REVIEW_SYSTEM_MESSAGE,
    llm_config=reviewer_llm_config,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    code_execution_config=False,
)

# Set up the group chat
groupchat = autogen.GroupChat(
    agents=[coder_agent, reviewer_agent],
    messages=[],
    # speaker_selection_method="round_robin",
    allow_repeat_speaker=False,
    max_round=3,
    # max_retries_for_selecting_speaker=1,
)

manager = autogen.GroupChatManager(
    groupchat=groupchat,
    is_termination_msg=lambda x: x.get("content", "").find("TERMINATE") >= 0,
    llm_config=manager_llm_config,
)

# Define the SocietyOfMind agent
from autogen.agentchat.contrib.society_of_mind_agent import SocietyOfMindAgent  # noqa: E402


society_of_mind_agent = SocietyOfMindAgent(
    "society_of_mind",
    chat_manager=manager,
    llm_config=society_of_mind_llm_config,
)

user_proxy = autogen.UserProxyAgent(
    "user_proxy",
    human_input_mode="NEVER",
    default_auto_reply="",
    is_termination_msg=lambda x: True,
    code_execution_config=False
)

# Initiate the chat
user_proxy.initiate_chat(society_of_mind_agent, message=task)
