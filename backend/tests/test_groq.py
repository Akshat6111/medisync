from app.ai.llm import get_llm

client = get_llm()

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {
            "role": "user",
            "content": "Say hello."
        }
    ]
)

print(response.choices[0].message.content)