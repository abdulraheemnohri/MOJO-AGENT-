"""Safe optional adapter for Google's LiteRT-LM CLI."""
from __future__ import annotations
import os,re,shutil,subprocess
from pathlib import Path

_REPO=re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}/[A-Za-z0-9][A-Za-z0-9_.-]{0,95}$")
MAX_PROMPT=6000
class LiteRTLMError(RuntimeError): pass

class LiteRTLM:
    def __init__(self, executable=None, timeout_seconds=120):
        self.executable=executable or os.getenv("MOJO_LITERTLM_BIN","litert-lm")
        self.timeout_seconds=max(10,min(int(timeout_seconds),180))
    def status(self):
        resolved=shutil.which(self.executable)
        return {"available":resolved is not None,"executable":resolved,"configured_executable":self.executable,
                "timeout_seconds":self.timeout_seconds,"supported_backends":["cpu","gpu"],
                "install_command":"python -m pip install --upgrade litert-lm","enabled_by_default":False}
    @staticmethod
    def validate_model(model):
        value=(model or "").strip()
        if not value or len(value)>512: raise ValueError("model must be a local .litertlm path or Hugging Face repository id")
        if _REPO.fullmatch(value) and not value.lower().endswith(".litertlm"): return value,True
        path=Path(value).expanduser()
        if path.suffix.lower()!=".litertlm": raise ValueError("local model files must use the .litertlm extension")
        if not path.is_file(): raise ValueError("model file does not exist")
        return str(path.resolve()),False
    def _execute(self,command):
        try:
            result=subprocess.run(command,capture_output=True,text=True,timeout=self.timeout_seconds,
                check=False,shell=False,stdin=subprocess.DEVNULL,env={**os.environ,"PYTHONUNBUFFERED":"1"})
        except subprocess.TimeoutExpired as exc: raise LiteRTLMError(f"LiteRT-LM timed out after {self.timeout_seconds} seconds") from exc
        except OSError as exc: raise LiteRTLMError("Could not start LiteRT-LM: "+str(exc)[:180]) from exc
        if result.returncode!=0: raise LiteRTLMError((result.stderr or result.stdout or f"CLI exited {result.returncode}")[-2000:])
        return {"status":"completed","return_code":result.returncode,"output":(result.stdout or "").strip()[-12000:],"stderr":(result.stderr or "").strip()[-2000:]}
    def run(self,model,prompt,backend="cpu",approved=False):
        if not approved: raise PermissionError("LiteRT-LM execution requires explicit operator approval")
        if backend not in {"cpu","gpu"}: raise ValueError("backend must be cpu or gpu")
        prompt=(prompt or "").strip()
        if not prompt or len(prompt)>MAX_PROMPT: raise ValueError(f"prompt must contain 1 to {MAX_PROMPT} characters")
        if not shutil.which(self.executable): raise LiteRTLMError("LiteRT-LM CLI not found. Install with: python -m pip install --upgrade litert-lm")
        value,is_hf=self.validate_model(model)
        command=[self.executable,"run"]
        if is_hf:
            command.append("--from-huggingface-repo="+value)
        else:
            command.append(value)
        command += ["--backend="+backend,"--prompt="+prompt]
        result=self._execute(command)
        return {**result,"model":value,"model_source":"huggingface" if is_hf else "local","backend":backend}
    def benchmark(self,model,approved=False):
        if not approved: raise PermissionError("LiteRT-LM benchmark requires explicit operator approval")
        if not shutil.which(self.executable): raise LiteRTLMError("LiteRT-LM CLI not found. Install with: python -m pip install --upgrade litert-lm")
        value,is_hf=self.validate_model(model)
        command=[self.executable,"benchmark"]
        if is_hf:
            command.append("--from-huggingface-repo="+value)
        else:
            command.append(value)
        result=self._execute(command)
        return {**result,"model":value,"model_source":"huggingface" if is_hf else "local"}
