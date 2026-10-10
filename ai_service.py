import os
from openai import OpenAI

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

def generate_ai_recommendation(prompt: str):
    response = client.responses.create(
        model="gpt-5-mini",
        input=prompt

    )

    return response.output_text