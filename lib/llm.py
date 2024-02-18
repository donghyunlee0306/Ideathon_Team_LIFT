import os
from openai import AzureOpenAI
from dotenv import load_dotenv

load_dotenv(verbose=True)

client = AzureOpenAI(
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT"), 
    api_key=os.getenv("AZURE_OPENAI_KEY"),  
    api_version="2023-07-01-preview"
)

def example(context, question) :
    return client.chat.completions.create(
        model=os.getenv("DEPLOYMENT_NAME"),
        messages=[
            {"role": "system", "content": "너는 정확한 답을 내놓는 assistant야"},
            {"role": "user", "content": context},
            {"role": "assistant", "content": "네, 인지했습니다."},
            {"role": "user", "content": question}
        ],
        temperature=0,
    )

def get_llm_result(context, question) :
    return example(context, question).choices[0].message.content