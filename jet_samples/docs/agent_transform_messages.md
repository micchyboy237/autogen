# Preprocessing Chat History with TransformMessages

## Table of Contents
1. [Introduction](#introduction)
2. [Requirements](#requirements)
3. [Define LLM Configuration](#define-llm-configuration)
4. [Handling Long Contexts](#handling-long-contexts)
    - [Example 1: Limiting Number of Messages](#example-1-limiting-number-of-messages)
    - [Example 2: Limiting Number of Tokens](#example-2-limiting-number-of-tokens)
    - [Example 3: Combining Transformations](#example-3-combining-transformations)
5. [Handling Sensitive Data](#handling-sensitive-data)

## Introduction
This documentation illustrates how to use `TransformMessages` to give any `ConversableAgent` the ability to handle long contexts, sensitive data, and more. By leveraging message transformations, we can limit context length and redact sensitive information effectively.

## Requirements
Install `pyautogen`:
```bash
pip install pyautogen
```
For more information, please refer to the [installation guide](#).

## Define LLM Configuration
```python
import copy
import pprint
import re
from typing import Dict, List, Tuple

import autogen
from autogen.agentchat.contrib.capabilities import transform_messages, transforms

config_list = autogen.config_list_from_json(env_or_file="OAI_CONFIG_LIST")

# Define your LLM config
llm_config = {"config_list": config_list}

# Define your agent; the user proxy and an assistant
assistant = autogen.AssistantAgent("assistant", llm_config=llm_config)
user_proxy = autogen.UserProxyAgent(
    "user_proxy",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
    max_consecutive_auto_reply=10,
)
```

## Handling Long Contexts
Imagine a scenario where the LLM generates an extensive amount of text, surpassing the token limit imposed by your API provider. To address this issue, you can leverage `TransformMessages` along with its constituent transformations, `MessageHistoryLimiter` and `MessageTokenLimiter`.

### Example 1: Limiting Number of Messages
Let's take a look at how these transformations affect the messages. By applying the `MessageHistoryLimiter`, we limit the context history to the 3 most recent messages.

```python
# Limit the message history to the 3 most recent messages
max_msg_transform = transforms.MessageHistoryLimiter(max_messages=3)

messages = [
    {"role": "user", "content": "hello"},
    {"role": "assistant", "content": [{"type": "text", "text": "there"}]},
    {"role": "user", "content": "how"},
    {"role": "assistant", "content": [{"type": "text", "text": "are you doing?"}]},
    {"role": "user", "content": "very very very very very very long string"},
]

processed_messages = max_msg_transform.apply_transform(copy.deepcopy(messages))
pprint.pprint(processed_messages)
```
Output:
```
[{'content': 'how', 'role': 'user'},
 {'content': [{'text': 'are you doing?', 'type': 'text'}], 'role': 'assistant'},
 {'content': 'very very very very very very long string', 'role': 'user'}]
```

### Example 2: Limiting Number of Tokens
Now let's test limiting the number of tokens in messages. We limit the number of tokens to 3, which is equivalent to 3 words in this instance.

```python
# Limit the token limit per message to 10 tokens
token_limit_transform = transforms.MessageTokenLimiter(max_tokens_per_message=3, min_tokens=10)

processed_messages = token_limit_transform.apply_transform(copy.deepcopy(messages))
pprint.pprint(processed_messages)
```
Output:
```
[{'content': 'hello', 'role': 'user'},
 {'content': [{'text': 'there', 'type': 'text'}], 'role': 'assistant'},
 {'content': 'how', 'role': 'user'},
 {'content': [{'text': 'are you doing', 'type': 'text'}], 'role': 'assistant'},
 {'content': 'very very very', 'role': 'user'}]
```

### Example 3: Combining Transformations
Let's test these transforms with agents. The agent without the capability to handle long context will result in an error, while the agent with that capability will have no issues.

```python
assistant_base = autogen.AssistantAgent("assistant", llm_config=llm_config)

assistant_with_context_handling = autogen.AssistantAgent("assistant", llm_config=llm_config)
context_handling = transform_messages.TransformMessages(
    transforms=[
        transforms.MessageHistoryLimiter(max_messages=10),
        transforms.MessageTokenLimiter(max_tokens=1000, max_tokens_per_message=50, min_tokens=500),
    ]
)
context_handling.add_to_agent(assistant_with_context_handling)

user_proxy = autogen.UserProxyAgent(
    "user_proxy",
    human_input_mode="NEVER",
    is_termination_msg=lambda x: "TERMINATE" in x.get("content", ""),
    code_execution_config={"work_dir": "coding", "use_docker": False},
    max_consecutive_auto_reply=2,
)

# Create a very long chat history that is bound to cause a crash for gpt 3.5
for i in range(1000):
    assistant_msg = {"role": "assistant", "content": "test " * 1000}
    user_msg = {"role": "user", "content": ""}

    assistant_base.send(assistant_msg, user_proxy, request_reply=False, silent=True)
    assistant_with_context_handling.send(assistant_msg, user_proxy, request_reply=False, silent=True)
    user_proxy.send(user_msg, assistant_base, request_reply=False, silent=True)
    user_proxy.send(user_msg, assistant_with_context_handling, request_reply=False, silent=True)

try:
    user_proxy.initiate_chat(assistant_base, message="plot and save a graph of x^2 from -10 to 10", clear_history=False)
except Exception as e:
    print("Encountered an error with the base assistant")
    print(e)

try:
    user_proxy.initiate_chat(
        assistant_with_context_handling, message="plot and save a graph of x^2 from -10 to 10", clear_history=False
    )
except Exception as e:
    print(e)
```

## Handling Sensitive Data
You can use the `MessageTransform` protocol to create custom message transformations that redact sensitive data from the chat history. This is particularly useful when you want to ensure that sensitive information, such as API keys, passwords, or personal data, is not exposed in the chat history or logs.

### Example: Redacting API Keys
Now, we will create a custom message transform to detect any OpenAI API key and redact it.

```python
# The transform must adhere to transform_messages.MessageTransform protocol.
class MessageRedact:
    def __init__(self):
        self._openai_key_pattern = r"sk-([a-zA-Z0-9]{48})"
        self._replacement_string = "REDACTED"

    def apply_transform(self, messages: List[Dict]) -> List[Dict]:
        temp_messages = copy.deepcopy(messages)

        for message in temp_messages:
            if isinstance(message["content"], str):
                message["content"] = re.sub(self._openai_key_pattern, self._replacement_string, message["content"])
            elif isinstance(message["content"], list):
                for item in message["content"]:
                    if item["type"] == "text":
                        item["text"] = re.sub(self._openai_key_pattern, self._replacement_string, item["text"])
        return temp_messages

    def get_logs(self, pre_transform_messages: List[Dict], post_transform_messages: List[Dict]) -> Tuple[str, bool]:
        keys_redacted = self._count_redacted(post_transform_messages) - self._count_redacted(pre_transform_messages)
        if keys_redacted > 0:
            return f"Redacted {keys_redacted} OpenAI API keys.", True
        return "", False

    def _count_redacted(self, messages: List[Dict]) -> int:
        # counts occurrences of "REDACTED" in message content
        count = 0
        for message in messages:
            if isinstance(message["content"], str):
                if "REDACTED" in message["content"]:
                    count += 1
            elif isinstance(message["content"], list):
                for item in message["content"]:
                    if isinstance(item, dict) and "text" in item:
                        if "REDACTED" in item["text"]:
                            count += 1
        return count

assistant_with_redact = autogen.AssistantAgent(
    "assistant",
    llm_config=llm_config,
    max_consecutive_auto_reply=1,
)
redact_handling = transform_messages.TransformMessages(transforms=[MessageRedact()])

redact_handling.add_to_agent(assistant_with_redact)

user_proxy = autogen.UserProxyAgent(
    "user_proxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=1,
)

messages = [
    {"content": "api key 1 = sk-7nwt00xv6fuegfu3gnwmhrgxvuc1cyrhxcq1quur9zvf05fy"},  # Don't worry, randomly generated
    {"content": [{"type": "text", "text": "API key 2 = sk-9wi0gf1j2rz6utaqd3ww3o6c1h1

n28wviypk7bd81wlj95an"}]},
]

for message in messages:
    user_proxy.send(message, assistant_with_redact, request_reply=False, silent=True)

result = user_proxy.initiate_chat(
    assistant_with_redact, message="What are the two API keys that I just provided", clear_history=False
)
```
Output:
```
Redacted 2 OpenAI API keys.
```
```python
user_proxy (to assistant):

What are the two API keys that I just provided

--------------------------------------------------------------------------------
Redacted 2 OpenAI API keys.
assistant (to user_proxy):

As an AI, I must inform you that it is not safe to share API keys publicly as they can be used to access your private data or services that can incur costs. Given that you've typed "REDACTED" instead of the actual keys, it seems you are aware of the privacy concerns and are likely testing my response or simulating an exchange without exposing real credentials, which is a good practice for privacy and security reasons.

To respond directly to your direct question: The two API keys you provided are both placeholders indicated by the text "REDACTED", and not actual API keys. If these were real keys, I would have reiterated the importance of keeping them secure and would not display them here.

Remember to keep your actual API keys confidential to prevent unauthorized use. If you've accidentally exposed real API keys, you should revoke or regenerate them as soon as possible through the corresponding service's API management console.
```