"""Command-line entry point for the MOJO AGENT API."""
import argparse
import os
import uvicorn

def main():
    parser = argparse.ArgumentParser(description="Run the local MOJO AGENT backend")
    parser.add_argument("--host", default=os.getenv("MOJO_AGENT_HOST", "127.0.0.1"),
                        help="Bind address (default: 127.0.0.1; use 0.0.0.0 only on a trusted LAN)")
    parser.add_argument("--port", type=int, default=int(os.getenv("MOJO_AGENT_PORT", "8766")))
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    if args.host == "0.0.0.0":
        print("WARNING: LAN binding enabled. Use a trusted private network and firewall port 8766.")
    uvicorn.run("mojo_agent.api:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
