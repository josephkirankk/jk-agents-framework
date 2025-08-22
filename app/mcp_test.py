import aiohttp
import asyncio
import json

SSE_URL = "http://localhost:8080/sse"
BASE_URL = "http://localhost:8080"

async def main():
    async with aiohttp.ClientSession() as session:
        async with session.get(SSE_URL, timeout=None, headers={"Accept": "text/event-stream"}) as resp:
            print(f"Connected to MCP SSE: {SSE_URL}")
            session_endpoint = None

            # Initial handshake: capture session endpoint
            async for line in resp.content:
                decoded = line.decode(errors="ignore").strip()
                print("Handshake SSE:", decoded)
                if decoded.startswith("data:"):
                    data = decoded[len("data:"):].strip()
                    if data.startswith("/"):
                        session_endpoint = data
                        print(f"Captured session endpoint: {session_endpoint}")
                        break

            if not session_endpoint:
                print("Session endpoint not found—cannot proceed.")
                return

            # Send tools/list request
            url = f"{BASE_URL}{session_endpoint}"
            payload = {
                "jsonrpc": "2.0",
                "id": "1",
                "method": "tools/list",
                "params": {}
            }
            print(f"POSTing to {url} with payload:")
            print(json.dumps(payload, indent=2))

            post_resp = await session.post(url, json=payload)
            print(f"POST status: {post_resp.status} {post_resp.reason}")

            # Now listen to SSE for tool info
            print("Awaiting tool list result in SSE stream...")

            async for line in resp.content:
                decoded = line.decode(errors="ignore").strip()
                if not decoded:
                    continue
                print("SSE:", decoded)

                if decoded.startswith("data:"):
                    data = decoded[len("data:"):].strip()
                    if data:
                        try:
                            payload_json = json.loads(data)
                            print("Received payload:", json.dumps(payload_json, indent=2))
                            if "tools" in payload_json:
                                print("\n=== Available Tools ===")
                                for tool in payload_json["tools"]:
                                    print(f" - {tool}")
                                print("========================")
                                return
                        except json.JSONDecodeError:
                            print("Non-JSON data:", data)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupted by user.")
