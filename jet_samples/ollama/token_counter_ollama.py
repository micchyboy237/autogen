from langchain_community.llms.ollama import Ollama
from langchain_core.callbacks import CallbackManager, StreamingStdOutCallbackHandler
import json

# Initialize the model
llm = Ollama(
    model="llama3",
    callback_manager=CallbackManager([StreamingStdOutCallbackHandler()])
)

# Define the prompt
prompt = "Tell me a 10 word joke"

# Generate a response
response = llm.generate(prompts=[prompt])

# Approximate token count for the prompt
generation = response.generations[0][0]
llm_output = response.llm_output

# generated_text = generation.text
context = generation.generation_info['context']
token_count = len(context)

print(f"\nRESPONSE: {response.json()}")
print(f"\nTOKEN COUNT: {token_count}")
