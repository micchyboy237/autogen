from IPython.display import Image, display

import autogen
from autogen.coding import LocalCommandLineCodeExecutor

import os
import random

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
        "model": "llama3",
        # "base_url": "http://localhost:11434/v1",
        "base_url": "http://0.0.0.0:4279",
        "api_key": "ollama",
        "stream": True,
        # "temperature": 1.0,
        # "top_p": 1.0,
    }
]

# Example Task: Check Stock Price Change

# create an AssistantAgent named "assistant"
assistant = autogen.AssistantAgent(
    name="assistant",
    llm_config={
        # seed for caching and reproducibility
        "cache_seed": cache_seed,
        "config_list": config_list,  # a list of OpenAI API configurations
        "temperature": 0,  # temperature for sampling
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
                "python": True,
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
    message="""
This is my salary cutoff from Aug. 1 - 14.

```
DESCRIPTION
HRS
RATE
AMOUNT
August 1, 2024
7
15
105
August 5, 2024
6.5
15
97.5
August 6, 2024
6.5
15
97.5
August 8, 2024
7
15
105
August 12, 2024
6.5
15
97.5
August 13, 2024
6.5
15
97.5

TOTAL:
£600
```

Cutoffs are 1 - 14 and 15 - end of the month.
Weekly schedule: Working days / hrs are Mon / 6.5, Tue / 6.5 and Thurs / 7

Now write a Python code that accepts a number of salary cutoffs, then calculates the total salary for each cutoff and the total salary for all cutoffs. It starts with the cutoff that contains current date. It follows the weekly schedule, hourly rate and cutoffs provided above.
Save the code as salary_calculator.py.

Sample input: 3
Sample output:
```
Cutoff: August 15 - 31
Total Salary: £705
Cutoff: September 1 - 14
Total Salary: £600
Cutoff: September 15 - 30
Total Salary: £697.5
```
""",
    summary_method="reflection_with_llm",
)

# print("Chat history:", chat_res.chat_history)
# print("Summary:", chat_res.summary)
print("Cost info:", chat_res.cost)
