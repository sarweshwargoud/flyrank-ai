from fastapi import FastAPI

app=FastAPI()

@app.get("/tasks")
def read_root():
    return {"Hello": "World"} 
@app.get("/") 
def home():
     return {
        "name": "Task API",
        "version": "1.0",
        "endpoints": ["/tasks"]
    }
@app.get("/health")
def health_check():
     return {"status ": "healthy"}

