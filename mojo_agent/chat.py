"""Persistent local chat conversations and attachment metadata for MOJO AGENT."""
from __future__ import annotations
import json
import os
import re
import sqlite3
import time
import uuid
from pathlib import Path

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._ -]")
MAX_ATTACHMENT_BYTES = 10 * 1024 * 1024
ALLOWED_EXTENSIONS = {
    ".txt", ".md", ".json", ".csv", ".log", ".pdf", ".docx", ".xlsx",
    ".pptx", ".png", ".jpg", ".jpeg", ".webp", ".mp3", ".wav", ".m4a", ".mp4"
}
TEXT_EXTENSIONS = {".txt", ".md", ".json", ".csv", ".log"}

class ChatStore:
    def __init__(self, db_path="data/mojo_agent.sqlite3"):
        self.path = str(db_path)
        Path(self.path).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as conn:
            conn.execute("""CREATE TABLE IF NOT EXISTS chat_conversations(
                id TEXT PRIMARY KEY, title TEXT NOT NULL, mode TEXT NOT NULL DEFAULT 'algorithms',
                model TEXT NOT NULL DEFAULT '', system_prompt TEXT NOT NULL DEFAULT '',
                created_at REAL NOT NULL, updated_at REAL NOT NULL, archived INTEGER NOT NULL DEFAULT 0)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS chat_messages(
                id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
                role TEXT NOT NULL, content TEXT NOT NULL, metadata TEXT NOT NULL DEFAULT '{}',
                created_at REAL NOT NULL)""")
            conn.execute("""CREATE TABLE IF NOT EXISTS chat_attachments(
                id TEXT PRIMARY KEY, conversation_id TEXT NOT NULL REFERENCES chat_conversations(id) ON DELETE CASCADE,
                message_id TEXT, filename TEXT NOT NULL, extension TEXT NOT NULL, content_type TEXT NOT NULL,
                size_bytes INTEGER NOT NULL, content BLOB NOT NULL, created_at REAL NOT NULL)""")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(conversation_id,created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_chat_conversations_updated ON chat_conversations(updated_at DESC)")
            conn.execute("""CREATE TABLE IF NOT EXISTS chat_models(
                id TEXT PRIMARY KEY, label TEXT NOT NULL, model_id TEXT NOT NULL UNIQUE,
                backend TEXT NOT NULL DEFAULT 'cpu', added_at REAL NOT NULL)""")
            conn.execute("PRAGMA foreign_keys=ON")

    def connect(self):
        conn = sqlite3.connect(self.path, timeout=15)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    @staticmethod
    def _message(row):
        if not row: return None
        item = dict(row)
        try: item["metadata"] = json.loads(item.get("metadata") or "{}")
        except json.JSONDecodeError: item["metadata"] = {}
        return item


    def add_model(self, label, model_id, backend="cpu"):
        label=(label or "").strip()[:100]
        model_id=(model_id or "").strip()
        if not label or not model_id or len(model_id)>512: raise ValueError("label and valid model identifier are required")
        if backend not in {"cpu","gpu"}: raise ValueError("backend must be cpu or gpu")
        ident=uuid.uuid4().hex
        with self.connect() as conn:
            try: conn.execute("INSERT INTO chat_models(id,label,model_id,backend,added_at) VALUES(?,?,?,?,?)",(ident,label,model_id,backend,time.time()))
            except sqlite3.IntegrityError as exc: raise ValueError("this model is already in the catalog") from exc
        return self.get_model(ident)

    def list_models(self):
        with self.connect() as conn: rows=conn.execute("SELECT * FROM chat_models ORDER BY added_at DESC").fetchall()
        return [dict(row) for row in rows]

    def get_model(self, model_id):
        with self.connect() as conn: row=conn.execute("SELECT * FROM chat_models WHERE id=?",(model_id,)).fetchone()
        return dict(row) if row else None

    def delete_model(self, model_id):
        with self.connect() as conn: cur=conn.execute("DELETE FROM chat_models WHERE id=?",(model_id,))
        return cur.rowcount>0

    def create(self, title="New chat", mode="algorithms", model=""):
        if mode not in {"algorithms", "litertlm"}: raise ValueError("mode must be algorithms or litertlm")
        title = (title or "New chat").strip()[:120] or "New chat"
        now = time.time(); ident = uuid.uuid4().hex
        with self.connect() as conn:
            conn.execute("INSERT INTO chat_conversations(id,title,mode,model,created_at,updated_at) VALUES(?,?,?,?,?,?)",
                         (ident,title,mode,(model or "")[:512],now,now))
        return self.get(ident)

    def get(self, conversation_id):
        with self.connect() as conn:
            row = conn.execute("SELECT * FROM chat_conversations WHERE id=?", (conversation_id,)).fetchone()
        return dict(row) if row else None

    def list(self, limit=50, include_archived=False):
        limit = max(1, min(int(limit), 100))
        query = """SELECT c.*,COUNT(m.id) AS message_count,
                   (SELECT content FROM chat_messages mm WHERE mm.conversation_id=c.id AND mm.role='user' ORDER BY mm.created_at DESC LIMIT 1) AS last_message
                   FROM chat_conversations c LEFT JOIN chat_messages m ON m.conversation_id=c.id"""
        if not include_archived: query += " WHERE c.archived=0"
        query += " GROUP BY c.id ORDER BY c.updated_at DESC LIMIT ?"
        with self.connect() as conn: rows = conn.execute(query,(limit,)).fetchall()
        return [dict(row) for row in rows]

    def update(self, conversation_id, **values):
        allowed = {"title","mode","model","system_prompt","archived"}
        if set(values)-allowed: raise ValueError("unsupported conversation field")
        if "title" in values:
            values["title"]=(values["title"] or "").strip()[:120]
            if not values["title"]: raise ValueError("title cannot be empty")
        if "mode" in values and values["mode"] not in {"algorithms","litertlm"}: raise ValueError("invalid chat mode")
        if "model" in values and len(values["model"])>512: raise ValueError("model identifier too long")
        if "system_prompt" in values and len(values["system_prompt"])>2000: raise ValueError("system prompt exceeds 2000 characters")
        if "archived" in values: values["archived"]=1 if values["archived"] else 0
        if not values: return self.get(conversation_id)
        assignments=", ".join(f"{key}=?" for key in values)
        with self.connect() as conn:
            cur=conn.execute(f"UPDATE chat_conversations SET {assignments},updated_at=? WHERE id=?",
                             (*values.values(),time.time(),conversation_id))
        return self.get(conversation_id) if cur.rowcount else None

    def delete(self, conversation_id):
        with self.connect() as conn:
            cur=conn.execute("DELETE FROM chat_conversations WHERE id=?",(conversation_id,))
        return cur.rowcount > 0

    def add_message(self, conversation_id, role, content, metadata=None):
        if role not in {"system","user","assistant","tool"}: raise ValueError("invalid message role")
        if not isinstance(content,str) or not content.strip() or len(content)>20000: raise ValueError("message content must contain 1 to 20000 characters")
        now=time.time(); ident=uuid.uuid4().hex
        with self.connect() as conn:
            exists=conn.execute("SELECT id,title FROM chat_conversations WHERE id=?",(conversation_id,)).fetchone()
            if not exists: raise KeyError("conversation not found")
            conn.execute("INSERT INTO chat_messages(id,conversation_id,role,content,metadata,created_at) VALUES(?,?,?,?,?,?)",
                         (ident,conversation_id,role,content,json.dumps(metadata or {},ensure_ascii=False),now))
            if role=="user" and exists["title"]=="New chat":
                title=" ".join(content.split())[:72]
                conn.execute("UPDATE chat_conversations SET title=?,updated_at=? WHERE id=?",(title,now,conversation_id))
            else: conn.execute("UPDATE chat_conversations SET updated_at=? WHERE id=?",(now,conversation_id))
            row=conn.execute("SELECT * FROM chat_messages WHERE id=?",(ident,)).fetchone()
        return self._message(row)

    def messages(self, conversation_id, limit=100, before=None):
        limit=max(1,min(int(limit),200))
        with self.connect() as conn:
            if not conn.execute("SELECT 1 FROM chat_conversations WHERE id=?",(conversation_id,)).fetchone(): return None
            if before:
                rows=conn.execute("SELECT * FROM chat_messages WHERE conversation_id=? AND created_at<? ORDER BY created_at DESC LIMIT ?",
                                  (conversation_id,float(before),limit)).fetchall()
            else:
                rows=conn.execute("SELECT * FROM chat_messages WHERE conversation_id=? ORDER BY created_at DESC LIMIT ?",
                                  (conversation_id,limit)).fetchall()
        return [self._message(row) for row in reversed(rows)]

    def clear_messages(self, conversation_id):
        with self.connect() as conn:
            if not conn.execute("SELECT 1 FROM chat_conversations WHERE id=?",(conversation_id,)).fetchone(): return None
            cur=conn.execute("DELETE FROM chat_messages WHERE conversation_id=?",(conversation_id,))
            conn.execute("UPDATE chat_conversations SET updated_at=? WHERE id=?",(time.time(),conversation_id))
        return cur.rowcount

    def add_attachment(self, conversation_id, filename, content_type, payload):
        if not self.get(conversation_id): raise KeyError("conversation not found")
        if not isinstance(payload,bytes) or not payload: raise ValueError("attachment is empty")
        if len(payload)>MAX_ATTACHMENT_BYTES: raise ValueError("attachment exceeds 10 MiB")
        clean=Path(str(filename or "attachment")).name
        clean=_SAFE_NAME.sub("_",clean).strip(" .")[:140]
        ext=Path(clean).suffix.lower()
        if not clean or ext not in ALLOWED_EXTENSIONS: raise ValueError("unsupported attachment type")
        ident=uuid.uuid4().hex
        with self.connect() as conn:
            conn.execute("""INSERT INTO chat_attachments(id,conversation_id,filename,extension,content_type,size_bytes,content,created_at)
                            VALUES(?,?,?,?,?,?,?,?)""",
                         (ident,conversation_id,clean,ext,(content_type or "application/octet-stream")[:120],len(payload),payload,time.time()))
        return self.attachment_info(ident)

    def attachment_info(self, attachment_id):
        with self.connect() as conn:
            row=conn.execute("SELECT id,conversation_id,filename,extension,content_type,size_bytes,created_at FROM chat_attachments WHERE id=?",(attachment_id,)).fetchone()
        return dict(row) if row else None

    def attachment_bytes(self, attachment_id):
        with self.connect() as conn:
            row=conn.execute("SELECT filename,content_type,content FROM chat_attachments WHERE id=?",(attachment_id,)).fetchone()
        return dict(row) if row else None

    def list_attachments(self, conversation_id):
        with self.connect() as conn:
            rows=conn.execute("SELECT id,filename,extension,content_type,size_bytes,created_at FROM chat_attachments WHERE conversation_id=? ORDER BY created_at",(conversation_id,)).fetchall()
        return [dict(row) for row in rows]

    def text_for_attachments(self, conversation_id, attachment_ids):
        if not attachment_ids: return []
        if len(attachment_ids)>10: raise ValueError("a message can reference at most 10 attachments")
        placeholders=",".join("?" for _ in attachment_ids)
        with self.connect() as conn:
            rows=conn.execute(f"SELECT id,filename,extension,content FROM chat_attachments WHERE conversation_id=? AND id IN ({placeholders})",
                              (conversation_id,*attachment_ids)).fetchall()
        if len(rows)!=len(set(attachment_ids)): raise ValueError("one or more attachments do not belong to this conversation")
        result=[]
        for row in rows:
            extracted=""
            if row["extension"] in TEXT_EXTENSIONS:
                try: extracted=bytes(row["content"]).decode("utf-8")[:12000]
                except UnicodeDecodeError: extracted="[Text extraction unavailable: file is not UTF-8]"
            result.append({"id":row["id"],"filename":row["filename"],"extracted_text":extracted})
        return result
