"""Basic chat example using Synapse API"""
import os
from openai import OpenAI

# Configure client to use Synapse
client = OpenAI(
    base_url="http://localhost:8000/v1",
    api_key=os.getenv("API_KEY", "your-api-key")
)

# Simple chat
response = client.chat.completions.create(
    model="synapse",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is Synapse?"}
    ]
)

print("Response:", response.choices[0].message.content)

# Streaming example
print("\nStreaming response:")
stream = client.chat.completions.create(
    model="synapse",
    messages=[
        {"role": "user", "content": "Tell me a short story"}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
print()

# With user context (for memory)
response = client.chat.completions.create(
    model="synapse",
    messages=[
        {"role": "user", "content": "Remember that my favorite color is blue"}
    ],
    user="user123"  # This enables user-specific memory
)

print("\nMemory stored:", response.choices[0].message.content)