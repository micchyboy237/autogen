from IPython.display import Image, display

import autogen
from autogen.coding import LocalCommandLineCodeExecutor
from autogen.agentchat import AssistantAgent

import os
import random


DEFAULT_SYSTEM_MESSAGE = """You are a helpful AI assistant providing Node.js code or shell scripts for user tasks. Ensure the code is executable and complete. Clearly explain your plans and use 'console.log' for output. Include types and write separate tests for each API route. Add // filename: <filename> at the beginning of the code block to indicate the file name where the code should be saved. Provide only one code block.
""".strip()

RAG_CONTENT = """
## Sign-Up User Stories & Acceptance Criteria
1. **Email and Password Sign-Up**
   - **User Story:** As a new user, I want to sign up using my email and password, so that I can create an account and access the app's features.
   - **Acceptance Criteria:** The sign-up screen includes fields for entering email and password. User can submit the form to create an account. User receives a confirmation message indicating that an account has been created.

2. **Social Login Options**
   - **User Story:** As a new user, I want to sign up using my Google, Apple, or Facebook account, so that I can quickly create an account without entering my email and password manually.
   - **Acceptance Criteria:** The sign-up screen includes buttons for signing up with Google, Apple, and Facebook. User can authenticate using their selected social account. An account is created, and the user is redirected to the app's dashboard upon successful authentication.

3. **Password Validation**
   - **User Story:** As a new user, I want to see validation messages for passwords that do not meet security criteria, so that I can create a secure password.
   - **Acceptance Criteria:** If the password is too short or lacks complexity, a validation message is displayed. The validation message specifies the password requirements (e.g., minimum length, inclusion of special characters).

4. **Email Validation**
   - **User Story:** As a new user, I want to see validation messages for invalid email addresses, so that I can correct any mistakes before submitting the form.
   - **Acceptance Criteria:** If the email format is incorrect, a validation message is displayed. The validation message specifies the correct format for an email address.

5. **Email Confirmation**
   - **User Story:** As a new user, I want to receive an email verification link after signing up, so that I can verify my email address and activate my account.
   - **Acceptance Criteria:** Upon successful sign-up, the user receives an email with a verification link. The email includes instructions on how to verify the email address.

6. **Password Confirmation**
   - **User Story:** As a new user, I want to confirm my password by entering it twice, so that I can ensure I did not make any typing errors.
   - **Acceptance Criteria:** The sign-up screen includes a field for confirming the password. If the passwords do not match, a validation message is displayed.

7. **Terms and Conditions**
   - **User Story:** As a new user, I want to view the terms and conditions and privacy policy before signing up, so that I can understand the app's policies.
   - **Acceptance Criteria:** The sign-up screen includes links to the terms and conditions and privacy policy. Users can click the links to view the documents in a new screen or modal.

8. **Duplicate Email Check**
   - **User Story:** As a new user, I want to receive feedback if my email is already registered, so that I can avoid creating duplicate accounts.
   - **Acceptance Criteria:** If the entered email is already registered, a message is displayed indicating that the email is in use. The message provides options to log in or reset the password if the user already has an account.
""".strip()
RAG_CONTENT = RAG_CONTENT.strip()

cache_seed = random.randint(0, 1000)

# Print current working directory
print(f"Current working directory: {os.getcwd()}")
# Print work_dir
print(f"Work directory: {os.path.abspath('./coding')}")
# Create the work directory if it does not exist
os.makedirs("./coding", exist_ok=True)

# config_list = autogen.config_list_from_json(
#     "OAI_CONFIG_LIST",
#     filter_dict={"tags": ["gpt-4"]},  # comment out to get all
# )
# When using a single openai endpoint, you can use the following:
# config_list = [{"model": "gpt-4", "api_key": os.getenv("OPENAI_API_KEY")}]
config_list = [
    {
        "model": "codellama",
        # "base_url": "http://localhost:11434/v1",
        "base_url": "http://0.0.0.0:4279",
        "api_key": "ollama",
        "stream": True,
        "temperature": 0,
    }
]

# Example Task: Check Stock Price Change

# create an AssistantAgent named "assistant"
assistant = autogen.AssistantAgent(
    name="assistant",
    system_message=f"{DEFAULT_SYSTEM_MESSAGE}\n\nDigital Garage context:\n{RAG_CONTENT}",
    llm_config={
        # seed for caching and reproducibility
        "cache_seed": cache_seed,
        "config_list": config_list,  # a list of OpenAI API configurations
    },  # configuration for autogen's enhanced inference API which is compatible with OpenAI API
)

# create a UserProxyAgent instance named "user_proxy"
user_proxy = autogen.UserProxyAgent(
    name="user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
    is_termination_msg=lambda x: x.get(
        "content", "").rstrip().endswith("TERMINATE"),
    code_execution_config={
        # the executor to run the generated code
        "executor": LocalCommandLineCodeExecutor(
            work_dir="./coding",
            execution_policies={
                "bash": False,
                "shell": False,
                "sh": False,
                "pwsh": False,
                "powershell": False,
                "ps1": False,
                "python": False,
                "javascript": True,
                "html": False,
                "css": False,
            }
        )
    },
)
# the assistant receives a message from the user_proxy, which contains the task description
# chat_res = user_proxy.initiate_chat(
#     assistant,
#     message="""Write the date today using Python code then save as date_today.py.""",
#     summary_method="reflection_with_llm",
# )
chat_res = user_proxy.initiate_chat(
    assistant,
    message=f"""Write all api routes for Digital Garage sign up feature Node.js code then save as one single file sign-up-router.js. No need to execute the code.""".strip(),
    summary_method="reflection_with_llm",
)

# print("Chat history:", chat_res.chat_history)
# print("Summary:", chat_res.summary)
print("Cost info:", chat_res.cost)
