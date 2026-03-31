"""
Database Manager - Supabase primary, JSON fallback with auto-sync
"""
import json
import os
import uuid
from datetime import datetime, date
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

# Try to import supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

# Local fallback paths
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

TABLES = ["trades", "strategies", "prop_accounts", "journal_entries", "goals", "sync_queue"]
LOCAL_FILES = {t: DATA_DIR / f"{t}.json" for t in TABLES}


def _load_local(table: str) -> List[Dict]:
    """Load data from local JSON file."""
    path = LOCAL_FILES[table]
    if path.exists():
        try:
            with open(path, "r") as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def _save_local(table: str, records: List[Dict]) -> None:
    """Save data to local JSON file."""
    path = LOCAL_FILES[table]
    with open(path, "w") as f:
        json.dump(records, f, default=str, indent=2)


def _add_to_sync_queue(table: str, record_id: str, operation: str, payload: Dict) -> None:
    """Track offline changes for later sync."""
    queue = _load_local("sync_queue")
    queue.append({
        "id": str(uuid.uuid4()),
        "created_at": datetime.now().isoformat(),
        "table_name": table,
        "record_id": record_id,
        "operation": operation,
        "payload": payload,
        "synced": False
    })
    _save_local("sync_queue", queue)


def get_supabase_client() -> Optional[Any]:
    """Get Supabase client if configured."""
    if not SUPABASE_AVAILABLE:
        return None
    
    url = os.getenv("SUPABASE_URL", st.secrets.get("SUPABASE_URL", "") if hasattr(st, 'secrets') else "")
    key = os.getenv("SUPABASE_KEY", st.secrets.get("SUPABASE_KEY", "") if hasattr(st, 'secrets') else "")
    
    if not url or not key:
        return None
    
    try:
        client = create_client(url, key)
        return client
    except Exception:
        return None


def is_connected() -> bool:
    """Check if Supabase is available and connected."""
    client = get_supabase_client()
    if not client:
        return False
    try:
        client.table("trades").select("id").limit(1).execute()
        return True
    except Exception:
        return False


# ─── CRUD Operations ────────────────────────────────────────────────────────

def db_insert(table: str, record: Dict) -> Optional[Dict]:
    """Insert a record. Falls back to local JSON if Supabase unavailable."""
    if "id" not in record:
        record["id"] = str(uuid.uuid4())
    if "created_at" not in record:
        record["created_at"] = datetime.now().isoformat()
    record["updated_at"] = datetime.now().isoformat()

    client = get_supabase_client()
    if client:
        try:
            result = client.table(table).insert(record).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            st.warning(f"⚠️ Supabase insert failed, saved locally. Will sync later. ({e})")

    # Local fallback
    records = _load_local(table)
    record["is_synced"] = False
    records.append(record)
    _save_local(table, records)
    _add_to_sync_queue(table, record["id"], "INSERT", record)
    return record


def db_select(table: str, filters: Optional[Dict] = None, order_by: Optional[str] = None, 
              order_desc: bool = True, limit: Optional[int] = None) -> List[Dict]:
    """Select records. Falls back to local JSON if Supabase unavailable."""
    client = get_supabase_client()
    if client:
        try:
            query = client.table(table).select("*")
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        query = query.eq(key, value)
            if order_by:
                query = query.order(order_by, desc=order_desc)
            if limit:
                query = query.limit(limit)
            result = query.execute()
            return result.data or []
        except Exception:
            pass

    # Local fallback
    records = _load_local(table)
    if filters:
        for key, value in filters.items():
            if value is not None:
                records = [r for r in records if r.get(key) == value]
    if order_by:
        try:
            records.sort(key=lambda x: x.get(order_by, ""), reverse=order_desc)
        except Exception:
            pass
    if limit:
        records = records[:limit]
    return records


def db_update(table: str, record_id: str, updates: Dict) -> Optional[Dict]:
    """Update a record."""
    updates["updated_at"] = datetime.now().isoformat()

    client = get_supabase_client()
    if client:
        try:
            result = client.table(table).update(updates).eq("id", record_id).execute()
            if result.data:
                return result.data[0]
        except Exception as e:
            st.warning(f"⚠️ Supabase update failed, saved locally. ({e})")

    # Local fallback
    records = _load_local(table)
    for i, r in enumerate(records):
        if r.get("id") == record_id:
            records[i].update(updates)
            records[i]["is_synced"] = False
            _save_local(table, records)
            _add_to_sync_queue(table, record_id, "UPDATE", updates)
            return records[i]
    return None


def db_delete(table: str, record_id: str) -> bool:
    """Delete a record."""
    client = get_supabase_client()
    if client:
        try:
            client.table(table).delete().eq("id", record_id).execute()
            return True
        except Exception as e:
            st.warning(f"⚠️ Supabase delete failed, queued locally. ({e})")

    # Local fallback
    records = _load_local(table)
    original_len = len(records)
    records = [r for r in records if r.get("id") != record_id]
    _save_local(table, records)
    if len(records) < original_len:
        _add_to_sync_queue(table, record_id, "DELETE", {"id": record_id})
    return True


def sync_offline_changes() -> Dict[str, int]:
    """Attempt to sync all offline changes to Supabase."""
    client = get_supabase_client()
    if not client:
        return {"synced": 0, "failed": 0, "pending": 0}

    queue = _load_local("sync_queue")
    pending = [q for q in queue if not q.get("synced")]
    synced_count = 0
    failed_count = 0

    for item in pending:
        try:
            table = item["table_name"]
            operation = item["operation"]
            payload = item["payload"]
            record_id = item["record_id"]

            if operation == "INSERT":
                payload["is_synced"] = True
                client.table(table).upsert(payload).execute()
            elif operation == "UPDATE":
                payload["is_synced"] = True
                client.table(table).update(payload).eq("id", record_id).execute()
            elif operation == "DELETE":
                client.table(table).delete().eq("id", record_id).execute()

            item["synced"] = True
            synced_count += 1
        except Exception:
            failed_count += 1

    _save_local("sync_queue", queue)
    return {"synced": synced_count, "failed": failed_count, "pending": len(pending)}


def get_sync_status() -> Dict:
    """Get current sync status."""
    queue = _load_local("sync_queue")
    pending = [q for q in queue if not q.get("synced")]
    connected = is_connected()
    return {
        "connected": connected,
        "pending_sync": len(pending),
        "storage": "Supabase" if connected else "Local (JSON)"
    }
