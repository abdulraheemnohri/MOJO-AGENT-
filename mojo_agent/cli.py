"""Command-line entry point for MOJO AGENT and optional LiteRT-LM."""
import argparse,os,sys,uvicorn

def _litertlm(args):
    from .litertlm import LiteRTLM,LiteRTLMError
    runner=LiteRTLM(timeout_seconds=args.timeout)
    try:
        if args.action=="status":
            print(runner.status());return 0
        result=runner.run(args.model,args.prompt,args.backend,args.approved) if args.action=="run" else runner.benchmark(args.model,args.approved)
        print(result.get("output",result));return 0
    except (ValueError,PermissionError,LiteRTLMError) as exc:
        print(f"LiteRT-LM: {exc}",file=sys.stderr);return 2

def main():
    parser=argparse.ArgumentParser(description="MOJO AGENT local runtime")
    sub=parser.add_subparsers(dest="command")
    server=sub.add_parser("serve",help="Start the local API")
    server.add_argument("--host",default=os.getenv("MOJO_AGENT_HOST","127.0.0.1"))
    server.add_argument("--port",type=int,default=int(os.getenv("MOJO_AGENT_PORT","8766")))
    lm=sub.add_parser("litertlm",help="Optional LiteRT-LM CLI")
    lm.add_argument("action",choices=["status","run","benchmark"])
    lm.add_argument("--model",default="");lm.add_argument("--prompt",default="")
    lm.add_argument("--backend",choices=["cpu","gpu"],default="cpu")
    lm.add_argument("--timeout",type=int,default=120)
    lm.add_argument("--approved",action="store_true",help="Explicitly approve local inference/benchmark")
    args=parser.parse_args()
    if args.command=="litertlm":return _litertlm(args)
    host=args.host if args.command=="serve" else os.getenv("MOJO_AGENT_HOST","127.0.0.1")
    port=args.port if args.command=="serve" else int(os.getenv("MOJO_AGENT_PORT","8766"))
    if not 1024<=port<=65535:parser.error("port must be between 1024 and 65535")
    if host=="0.0.0.0":print("WARNING: LAN binding enabled; use only a trusted private network.")
    uvicorn.run("mojo_agent.api:app",host=host,port=port,reload=False)
    return 0

if __name__=="__main__":raise SystemExit(main())
