#!/usr/bin/env python3
"""
MCP Weather Server

A simple MCP server that provides weather information.
Supports both stdio and HTTP transports.
"""

import sys
import os
from typing import Dict, Any

# Try to import MCP SDK
try:
    from mcp.server.fastmcp import FastMCP
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False

# Fallback HTTP server
from fastapi import FastAPI
import uvicorn

# Sample weather data
WEATHER_DATA = {
    "mumbai": {"temp": 30, "condition": "sunny", "humidity": 65},
    "delhi": {"temp": 34, "condition": "humid", "humidity": 80},
    "bangalore": {"temp": 26, "condition": "cloudy", "humidity": 70},
    "london": {"temp": 15, "condition": "rainy", "humidity": 85},
    "new york": {"temp": 22, "condition": "partly cloudy", "humidity": 60},
    "tokyo": {"temp": 28, "condition": "sunny", "humidity": 55},
    "sydney": {"temp": 20, "condition": "windy", "humidity": 50},
    "paris": {"temp": 18, "condition": "overcast", "humidity": 75}
}


def get_weather_info(city: str) -> Dict[str, Any]:
    """Get weather information for a city"""
    city_key = city.lower().strip()

    if city_key in WEATHER_DATA:
        data = WEATHER_DATA[city_key].copy()
        data["city"] = city.title()
        return data
    else:
        return {"error": f"Weather data not available for {city}"}


# MCP Server Implementation
if MCP_AVAILABLE:
    mcp = FastMCP("Weather Server")

    @mcp.tool()
    def get_weather(city: str) -> Dict[str, Any]:
        """Get current weather for a city"""
        return get_weather_info(city)

    @mcp.tool()
    def get_temperature(city: str) -> float:
        """Get temperature for a city"""
        weather = get_weather_info(city)
        if "error" in weather:
            raise ValueError(weather["error"])
        return weather["temp"]

    @mcp.tool()
    def get_condition(city: str) -> str:
        """Get weather condition for a city"""
        weather = get_weather_info(city)
        if "error" in weather:
            raise ValueError(weather["error"])
        return weather["condition"]

    @mcp.tool()
    def list_cities() -> list:
        """List all available cities"""
        return [city.title() for city in WEATHER_DATA.keys()]

    @mcp.resource("weather://{city}")
    def weather_resource(city: str) -> str:
        """Get weather as a resource"""
        weather = get_weather_info(city)
        if "error" in weather:
            return f"Error: {weather['error']}"

        return f"Weather in {weather.get('city', city)}: {weather['temp']}°C, {weather['condition']}, {weather['humidity']}% humidity"


# HTTP Server Implementation (fallback)
app = FastAPI(title="Weather Server", description="Simple weather information server")


@app.get("/weather")
def http_get_weather(city: str):
    """Get weather via HTTP"""
    return get_weather_info(city)


@app.get("/temperature")
def http_get_temperature(city: str):
    """Get temperature via HTTP"""
    weather = get_weather_info(city)
    if "error" in weather:
        return weather
    return {"city": city, "temperature": weather["temp"]}


@app.get("/cities")
def http_list_cities():
    """List available cities via HTTP"""
    return {"cities": [city.title() for city in WEATHER_DATA.keys()]}


@app.get("/health")
def health():
    """Health check endpoint"""
    return {"status": "ok", "server": "weather"}


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == "stdio" and MCP_AVAILABLE:
        # Run as MCP server with stdio transport
        mcp.run(transport="stdio")
    elif len(sys.argv) > 1 and sys.argv[1] == "sse" and MCP_AVAILABLE:
        # Run as MCP server with SSE transport
        port = int(os.getenv("WEATHER_PORT", "8002"))
        mcp.run(transport="sse", port=port)
    else:
        # Run as HTTP server
        port = int(os.getenv("WEATHER_PORT", "8002"))
        uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
