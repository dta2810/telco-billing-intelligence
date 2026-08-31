"""DB helpers — uses databricks-sql-connector with OAuth/PAT from WorkspaceClient.

Local dev: requires DATABRICKS_PROFILE=LATAM in env.
Deployed:  uses the App's service principal token automatically.
"""
import os
import logging
from concurrent.futures import ThreadPoolExecutor
from databricks import sql as dbsql
from databricks.sdk import WorkspaceClient

logger = logging.getLogger(__name__)

# Shared executor — sized for typical fan-out (profile = 4 queries).
_QUERY_EXECUTOR = ThreadPoolExecutor(max_workers=8, thread_name_prefix="dbsql")

IS_DATABRICKS_APP = bool(os.environ.get("DATABRICKS_APP_NAME"))

CATALOG = os.environ.get("CATALOG", "acmetel_demo")
SCHEMA = os.environ.get("SCHEMA", "gold")


def _get_workspace_client() -> WorkspaceClient:
    if IS_DATABRICKS_APP:
        return WorkspaceClient()
    profile = os.environ.get("DATABRICKS_PROFILE", "LATAM")
    return WorkspaceClient(profile=profile)


def _get_oauth_token() -> str:
    w = _get_workspace_client()
    if w.config.token:
        return w.config.token
    headers = w.config.authenticate()
    if headers and "Authorization" in headers:
        return headers["Authorization"].replace("Bearer ", "")
    raise RuntimeError("Could not obtain OAuth token")


def _get_host() -> str:
    host = os.environ.get("DATABRICKS_HOST", "")
    if IS_DATABRICKS_APP and host and not host.startswith("http"):
        host = f"https://{host}"
    if not host:
        host = _get_workspace_client().config.host
    return host.rstrip("/")


def _get_http_path() -> str:
    wh_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    path = os.environ.get("DATABRICKS_HTTP_PATH", "")
    if path:
        return path
    return f"/sql/1.0/warehouses/{wh_id}"


def get_connection():
    token = _get_oauth_token()
    host = _get_host().replace("https://", "").replace("http://", "")
    return dbsql.connect(
        server_hostname=host,
        http_path=_get_http_path(),
        access_token=token,
        catalog=CATALOG,
        schema=SCHEMA,
    )


def execute_query(query: str, params: dict | None = None) -> list[dict]:
    """Execute SQL and return list of dicts. Use parameterized queries when input is user-supplied."""
    conn = get_connection()
    try:
        cursor = conn.cursor()
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()


def execute_scalar(query: str, params: dict | None = None):
    """Execute and return first cell of first row, or None."""
    rows = execute_query(query, params)
    if not rows:
        return None
    first = rows[0]
    return next(iter(first.values()))


def execute_queries_parallel(queries: list[str]) -> list[list[dict]]:
    """Run multiple SELECTs concurrently, returning results in input order.

    Each query opens its own connection (auth + connect overhead is ~1.5s today),
    so wall-clock collapses to roughly the slowest single query instead of the sum.
    """
    futures = [_QUERY_EXECUTOR.submit(execute_query, q) for q in queries]
    return [f.result() for f in futures]
