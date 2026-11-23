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
    parser.add_argument("--host",default=os.getenv("MOJO_AGENT_HOST","127.0.0.1"),
                        help="API bind address (default loopback; use 0.0.0.0 only on a trusted LAN)")
    parser.add_argument("--port",type=int,default=int(os.getenv("MOJO_AGENT_PORT","8766")))
    sub=parser.add_subparsers(dest="command")
    sub.add_parser("serve",help="Start the local API (default action)")
    lm=sub.add_parser("litertlm",help="Optional LiteRT-LM CLI")
    lm.add_argument("action",choices=["status","run","benchmark"])
    lm.add_argument("--model",default="");lm.add_argument("--prompt",default="")
    lm.add_argument("--backend",choices=["cpu","gpu"],default="cpu")
    lm.add_argument("--timeout",type=int,default=120)
    lm.add_argument("--approved",action="store_true",help="Explicitly approve local inference/benchmark")
    args=parser.parse_args()
    if args.command=="litertlm":return _litertlm(args)
    if not 1024<=args.port<=65535:parser.error("port must be between 1024 and 65535")
    if args.host=="0.0.0.0":print("WARNING: LAN binding enabled; use only a trusted private network.")
    uvicorn.run("mojo_agent.api:app",host=args.host,port=args.port,reload=False)
    return 0

if __name__=="__main__":raise SystemExit(main())
