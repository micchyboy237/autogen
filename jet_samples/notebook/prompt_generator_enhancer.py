from autogen import ConversableAgent, UserProxyAgent
from autogen import AssistantAgent, UserProxyAgent

config_list = [
    {
        "model": "llama3",
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",
    }
]

# Create the agent that uses the LLM.
assistant = ConversableAgent(
    name="agent",
    llm_config={"config_list": config_list},
    human_input_mode="NEVER",
    system_message="""
You are an AI language model designed to generate and enhance highly detailed and verbose system prompts for other AI language models and chatbots. Your primary goal is to create comprehensive, well-structured, and effective prompts that guide the behavior and responses of AI assistants like ChatGPT, Claude, Anthropic's Constitutional AI, Google's Gemini, and Meta's LLaMA.

When generating prompts, focus on the following key elements and provide in-depth explanations for each:

1. Purpose: Clearly define the primary purpose, role, and objectives of the AI assistant. Elaborate on the specific tasks, interactions, and outcomes the AI should aim to achieve. Provide examples and use cases to illustrate the desired functionality.

2. Tone and Personality: Specify the desired tone, communication style, and personality traits the AI should exhibit. Describe in detail how the AI should interact with users, adapt to different contexts, and maintain a consistent persona throughout conversations. Discuss the importance of tone and personality in creating engaging and relatable AI experiences.

3. Knowledge Domains: Identify the specific knowledge domains, areas of expertise, or topics the AI should focus on. Provide a comprehensive list of subjects, concepts, and skills the AI should be well-versed in. Explain how the AI should acquire, organize, and apply this knowledge to provide accurate and relevant responses.

4. Capabilities: Outline any specific features, functionalities, or capabilities the AI should possess. Describe in detail how these capabilities should be implemented, their potential applications, and any limitations or considerations. Discuss the technical aspects of integrating these capabilities into the AI's architecture.


When enhancing existing prompts, thoroughly analyze the provided prompt and offer comprehensive suggestions for improvement. Provide detailed explanations for each proposed change, discussing the reasoning behind them and their potential impact on the AI's performance. Offer in-depth insights and recommendations based on your extensive knowledge of best practices in prompt engineering for language models like ChatGPT, Claude, Gemini, and LLaMA.

Your responses should be highly technical and detailed, delving into the intricacies of prompt design and the inner workings of language models. Use your expertise to provide comprehensive explanations, examples, and justifications for your prompt suggestions. Aim to educate and empower AI developers and users by sharing your knowledge and insights.

Remember, your role is to enable the creation of high-quality, efficient, and ethically sound system prompts through your detailed and informative guidance. Continuously update your knowledge based on the latest advancements in language models and prompt engineering techniques, and incorporate this information into your verbose and comprehensive responses.
""".strip()
)

# Create the agent that represents the user in the conversation.
user_proxy = UserProxyAgent(
    "user",
    code_execution_config=False,
    llm_config={"config_list": config_list},
    human_input_mode="ALWAYS"
)

# Let the assistant start the conversation.  It will end when the user types exit.
message = """
Create an interactive story that unfolds based on my choices. Here’s how it works:

Initiate: I provide a genre, like romance, adventure, or mystery, and you begin the story.
Interact: You narrate a part of the story and end with ellipses before presenting me with a couple of options to choose from. These options should be verbs or nouns that will naturally lead into the next part of the story.
Choose and Continue: After I make a selection, you incorporate my choice as the first word in the continuation of the narrative.
Loop: This cycle of narrating parts of the story and presenting choices repeats, forming a coherent story with a beginning, middle, and end.

Example interaction:

Me: genre: romance
You: Under the soft moonlight, Anna and Jose walked along the...
Choices: road, beach

Me: next word: beach
You: beach, hand in hand. They had been friends for a long time, but on that night, both felt a new emotion bubbling up in their hearts. "Jose, do you...
Choices: think, hate

Me: next word: think
You: think there's a chance for us?" Anna asked quietly, yet hopefully. Jose didn't answer immediately. He...
Choices: looked, frowned

This format ensures a clear and engaging narrative experience, driven by my choices, with each new segment beginning with the choice I selected. Each choice option is either a verb or a noun, seamlessly leading into the subsequent narrative portion.
"""
user_proxy.initiate_chat(
    recipient=assistant,
    message=message.strip(),
    clear_history=True,
)
