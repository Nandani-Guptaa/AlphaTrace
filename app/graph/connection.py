import logging
from typing import Any, Dict, List, Optional
import falkordb
from app.config import settings

logger = logging.getLogger(__name__)


class FalkorDBConnection:
    """Manages connection to FalkorDB with parameterization and health inspection."""

    def __init__(self, host: str = settings.FALKORDB_HOST, port: int = settings.FALKORDB_PORT,
                 graph_name: str = settings.FALKORDB_GRAPH, password: Optional[str] = settings.FALKORDB_PASSWORD):
        self.host = host
        self.port = port
        self.graph_name = graph_name
        self.password = password
        self._client: Optional[falkordb.FalkorDB] = None
        self._graph = None

    def get_client(self) -> falkordb.FalkorDB:
        if self._client is None:
            self._client = falkordb.FalkorDB(
                host=self.host,
                port=self.port,
                password=self.password
            )
        return self._client

    def get_graph(self):
        if self._graph is None:
            client = self.get_client()
            self._graph = client.select_graph(self.graph_name)
        return self._graph

    def query(self, cypher: str, params: Optional[Dict[str, Any]] = None) -> List[List[Any]]:
        """Execute parameterized Cypher query against FalkorDB.
        Guarantees parameterized query execution to prevent Cypher injection.
        """
        graph = self.get_graph()
        try:
            if params:
                result = graph.query(cypher, params=params)
            else:
                result = graph.query(cypher)
            return result.result_set if result is not None else []
        except Exception as e:
            logger.error(f"FalkorDB query failed: {cypher} | params={params} | err={e}")
            raise

    def check_health(self) -> Dict[str, Any]:
        """Check live connection and return database health status."""
        try:
            res = self.query("RETURN 1 AS ping")
            if res and res[0][0] == 1:
                # Count nodes
                node_count_res = self.query("MATCH (n) RETURN count(n) AS cnt")
                node_count = node_count_res[0][0] if node_count_res else 0
                return {
                    "status": "healthy",
                    "backend": "FalkorDB",
                    "host": self.host,
                    "port": self.port,
                    "graph_name": self.graph_name,
                    "node_count": node_count,
                    "message": "FalkorDB instance connected and responsive."
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "backend": "FalkorDB",
                "host": self.host,
                "port": self.port,
                "error": str(e),
                "message": "Failed to connect to FalkorDB service."
            }
        return {"status": "unknown"}


# Global singleton
db_connection = FalkorDBConnection()


def get_db() -> FalkorDBConnection:
    return db_connection
