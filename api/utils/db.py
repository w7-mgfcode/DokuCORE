import os
import logging
import psycopg2
import psycopg2.extras
from llama_index.vector_stores.postgres import PGVectorStore

logger = logging.getLogger(__name__)

def get_db_connection():
    """
    Create a new database connection.
    
    Returns:
        psycopg2.connection: A PostgreSQL database connection.
    """
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = True
    return conn

def get_pg_vector_store_hierarchy():
    """
    Create a PG Vector Store for hierarchical indexing.
    
    Returns:
        PGVectorStore: A configured PostgreSQL vector store.
    """
    try:
        conn_str = os.environ.get("DATABASE_URL")
        # Parse connection string
        db_parts = conn_str.replace("postgresql://", "").split("@")
        user_pass = db_parts[0].split(":")
        host_port_db = db_parts[1].split("/")
        host_port = host_port_db[0].split(":")

        return PGVectorStore.from_params(
            database=host_port_db[1],
            host=host_port[0],
            password=user_pass[1],
            port=int(host_port[1]),
            user=user_pass[0],
            table_name="document_hierarchy",
            embed_dim=1536  # Adjust embed_dim based on your model
        )
    except Exception as e:
        logger.error(f"Error creating PG Vector Store: {str(e)}")
        raise