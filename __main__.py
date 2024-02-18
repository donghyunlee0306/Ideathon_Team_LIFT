from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import uvicorn

from api.business_idea import router as idea_router

app = FastAPI()
app.include_router(idea_router)

load_dotenv(verbose=True)

origins = [
    os.getenv('ORIGIN')
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def main():
    return {"message": "Helloworld, FastAPI"}

if __name__ == '__main__':
    uvicorn.run("__main__:app", host="0.0.0.0", port=8080, reload=True, workers=4)