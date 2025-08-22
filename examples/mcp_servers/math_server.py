from fastapi import FastAPI
import uvicorn

app = FastAPI()

@app.get("/calculate")
def calculate(expression: str):
    """
    Example: GET /calculate?expression=2*3+5
    """
    try:
        result = eval(expression, {"__builtins__": {}})
        return {"result": result}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
