"""Safe GitHub extension installer: declarative JSON manifests only.

No Python modules, shell scripts, binaries, workflow files, or executable hooks are
downloaded or run. A package can only call operations implemented in this project.
"""
from __future__ import annotations
import hashlib
import json
import re
import sqlite3
import urllib.error
import urllib.request
from pathlib import Path

_REPO = re.compile(r"^[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}$")
_REF = re.compile(r"^[A-Za-z0-9._/-]{1,120}$")
_PATH = re.compile(r"^[A-Za-z0-9_./-]{1,180}$")
_NAME = re.compile(r"^[a-z][a-z0-9_-]{1,47}$")
_MAX_MANIFEST = 128 * 1024
_ALLOWED_OPERATIONS = {"text_stats", "uppercase", "lowercase", "word_count", "calculator"}

class ExtensionError(ValueError):
    pass

def _fetch_manifest(repo: str, ref: str, path: str) -> tuple[dict, str]:
    if not _REPO.fullmatch(repo): raise ExtensionError("repository must be owner/name")
    if not _REF.fullmatch(ref) or ".." in ref.split("/"): raise ExtensionError("invalid Git ref")
    if not _PATH.fullmatch(path) or path.startswith("/") or ".." in path.split("/"): raise ExtensionError("invalid manifest path")
    url = f"https://raw.githubusercontent.com/{repo}/{ref}/{path}"
    request = urllib.request.Request(url, headers={"User-Agent":"MOJO-AGENT-extension-manager/1.0","Accept":"application/json"})
    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            if response.status != 200: raise ExtensionError(f"GitHub returned HTTP {response.status}")
            raw = response.read(_MAX_MANIFEST + 1)
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ExtensionError("Could not retrieve public GitHub manifest: " + str(exc)[:160]) from exc
    if len(raw) > _MAX_MANIFEST: raise ExtensionError("manifest exceeds 128 KiB limit")
    try: data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc: raise ExtensionError("manifest must be valid UTF-8 JSON") from exc
    if not isinstance(data, dict): raise ExtensionError("manifest root must be an object")
    return data, hashlib.sha256(raw).hexdigest()

class GitHubExtensionRegistry:
    def __init__(self, db_path="data/mojo_agent.sqlite3"):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        with self.db() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS installed_extensions (
                id TEXT PRIMARY KEY, kind TEXT NOT NULL, name TEXT NOT NULL,
                description TEXT NOT NULL, version TEXT NOT NULL, repo TEXT NOT NULL,
                ref TEXT NOT NULL, manifest_path TEXT NOT NULL, manifest_sha256 TEXT NOT NULL,
                manifest_json TEXT NOT NULL, installed_at REAL NOT NULL DEFAULT (unixepoch()),
                UNIQUE(kind,name))""")

    def db(self): return sqlite3.connect(self.db_path)

    @staticmethod
    def _base(data, expected_kind):
        if data.get("schema") != "mojo.extension.v1": raise ExtensionError("unsupported manifest schema; expected mojo.extension.v1")
        if data.get("kind") != expected_kind: raise ExtensionError(f"manifest kind must be {expected_kind}")
        name = data.get("name")
        if not isinstance(name, str) or not _NAME.fullmatch(name): raise ExtensionError("name must be lowercase letters, digits, _ or -")
        description = data.get("description", "")
        version = data.get("version", "1.0.0")
        if not isinstance(description, str) or len(description) > 300: raise ExtensionError("description must be at most 300 characters")
        if not isinstance(version, str) or len(version) > 32: raise ExtensionError("invalid version")
        return name, description, version

    def preview(self, repo, ref="main", path="mojo-extension.json"):
        data, digest = _fetch_manifest(repo, ref, path)
        kind = data.get("kind")
        if kind not in ("skill", "tool"): raise ExtensionError("kind must be skill or tool")
        name, description, version = self._base(data, kind)
        if kind == "skill":
            instructions = data.get("instructions", "")
            tools = data.get("tools", [])
            if not isinstance(instructions, str) or not instructions.strip() or len(instructions) > 6000:
                raise ExtensionError("skill instructions must contain 1-6000 characters")
            if not isinstance(tools, list) or len(tools) > 12 or any(x not in _ALLOWED_OPERATIONS for x in tools):
                raise ExtensionError("skill references unsupported tool operations")
        else:
            operation = data.get("operation")
            if operation not in _ALLOWED_OPERATIONS: raise ExtensionError("tool operation is not in the built-in safe operation set")
            if not isinstance(data.get("input_schema", {}), dict): raise ExtensionError("input_schema must be an object")
        return {"kind":kind,"name":name,"description":description,"version":version,
                "repository":repo,"ref":ref,"manifest_path":path,"manifest_sha256":digest,
                "manifest":data,"execution":"declarative-only","code_execution":False}

    def install(self, repo, ref="main", path="mojo-extension.json", expected_sha256=None):
        item = self.preview(repo, ref, path)
        if expected_sha256 and not __import__('hmac').compare_digest(item['manifest_sha256'], expected_sha256):
            raise ExtensionError('Manifest changed since preview; preview it again before installation')
        data = item["manifest"]
        ident = f"{item['kind']}:{item['name']}"
        with self.db() as conn:
            conn.execute("""INSERT INTO installed_extensions
                (id,kind,name,description,version,repo,ref,manifest_path,manifest_sha256,manifest_json)
                VALUES(?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(kind,name) DO UPDATE SET description=excluded.description,
                version=excluded.version,repo=excluded.repo,ref=excluded.ref,
                manifest_path=excluded.manifest_path,manifest_sha256=excluded.manifest_sha256,
                manifest_json=excluded.manifest_json,installed_at=unixepoch()""",
                (ident,item["kind"],item["name"],item["description"],item["version"],repo,ref,path,item["manifest_sha256"],json.dumps(data)))
        return {k:v for k,v in item.items() if k != "manifest"}

    def list(self, kind=None):
        with self.db() as conn:
            if kind: rows=conn.execute("SELECT id,kind,name,description,version,repo,ref,manifest_sha256,installed_at FROM installed_extensions WHERE kind=? ORDER BY name",(kind,)).fetchall()
            else: rows=conn.execute("SELECT id,kind,name,description,version,repo,ref,manifest_sha256,installed_at FROM installed_extensions ORDER BY kind,name").fetchall()
        keys=("id","kind","name","description","version","repository","ref","manifest_sha256","installed_at")
        return [dict(zip(keys,row)) for row in rows]

    def uninstall(self, ident):
        with self.db() as conn: cur=conn.execute("DELETE FROM installed_extensions WHERE id=?",(ident,))
        return cur.rowcount > 0

    def get_manifest(self, kind, name):
        with self.db() as conn: row=conn.execute("SELECT manifest_json FROM installed_extensions WHERE kind=? AND name=?",(kind,name)).fetchone()
        if not row: raise KeyError("Extension not installed")
        return json.loads(row[0])

    def execute_tool(self, name, arguments, approved=False):
        if not approved: raise PermissionError("Installed tool execution requires explicit approval")
        manifest=self.get_manifest("tool",name)
        operation=manifest["operation"]
        value=arguments.get("text","")
        if operation == "text_stats":
            if not isinstance(value,str) or len(value)>20000: raise ExtensionError("text must be a string up to 20000 characters")
            return {"characters":len(value),"words":len(value.split()),"lines":len(value.splitlines())}
        if operation == "uppercase": return str(value).upper()[:20000]
        if operation == "lowercase": return str(value).lower()[:20000]
        if operation == "word_count": return {"words":len(str(value).split())}
        if operation == "calculator":
            from .tools import calculator
            return calculator(str(arguments.get("expression","")),approved=True)
        raise ExtensionError("unsupported operation")
