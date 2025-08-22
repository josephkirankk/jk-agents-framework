from fastapi import FastAPI
import uvicorn
import os

app = FastAPI()


@app.get("/weather")
def get_weather(city: str):
    """
    Example: GET /weather?city=Mumbai
    """
    sample_data = {
        "mumbai": {"temp": 30, "condition": "sunny"},
        "delhi": {"temp": 34, "condition": "humid"},
        "bangalore": {"temp": 26, "condition": "cloudy"}
    }
    return sample_data.get(city.lower(), {"error": "City not found"})


if __name__ == "__main__":
    # Allow overriding the port via env var to avoid conflicts
    port = int(os.getenv("WEATHER_PORT", "8002"))
    uvicorn.run(app, host="0.0.0.0", port=port)
