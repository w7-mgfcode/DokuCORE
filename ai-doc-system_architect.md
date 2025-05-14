
# AI-Támogatott Dokumentációs Rendszer Implementációs Útmutató

Ez az útmutató részletesen leírja, hogyan implementálj egy AI-támogatott dokumentációs rendszert egy Linux szerveren (10.0.0.11), amely kombinálja a FastAPI-MCP, PostgreSQL-pgvector és egyedi Python MCP szerver előnyeit, miközben lehetőséget biztosít az LLM-ek számára dokumentáció-frissítésre és feladat-generálásra. A rendszer fejlett hierarchikus indexelést biztosít LlamaIndex segítségével, amely szemantikus összefüggéseket, hierarchiát és kontextust ad a dokumentációhoz, jelentősen javítva az LLM-ek keresési hatékonyságát.

## 1. Projekt Struktúra

ai-doc-system/
├── docker-compose.yml
├── .env
├── init.sql
├── postgres/
│   └── Dockerfile
├── api/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py
├── code-monitor/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── code_monitor.py
└── repo/         # A felügyelt git repository
└── ...


## 2. Környezet Előkészítése

### 2.1. Szükséges csomagok telepítése

```bash
# Csatlakozás a szerverhez
ssh felhasznalo@10.0.0.11

# Git, Docker és Docker Compose telepítése, ha még nincs
sudo apt update
sudo apt install -y git docker.io docker-compose

# Docker indítása és engedélyezése
sudo systemctl start docker
sudo systemctl enable docker

# Adjuk hozzá a felhasználónkat a docker csoporthoz (újrajelentkezés szükséges)
sudo usermod -aG docker $USER
2.2. Projekt Inicializálása


# Projektmappa létrehozása
mkdir -p ~/ai-doc-system/{postgres,api,code-monitor,repo}
cd ~/ai-doc-system

# .env fájl létrehozása
cat > .env << 'EOF'
POSTGRES_USER=docuser
POSTGRES_PASSWORD=docpassword
POSTGRES_DB=docdb
API_PORT=9000
DATABASE_URL=postgresql://docuser:docpassword@db:5432/docdb
REPO_PATH=/app/repo
API_URL=http://api:9000
CHECK_INTERVAL=300
EOF
3. PostgreSQL + pgvector Beállítása
3.1. Dockerfile Létrehozása
Dockerfile

FROM postgres:16

# Build függőségek telepítése
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    postgresql-server-dev-16

# pgvector klónozása és fordítása
RUN git clone --branch v0.8.0 [https://github.com/pgvector/pgvector.git](https://github.com/pgvector/pgvector.git) && \
    cd pgvector && \
    make && \
    make install
3.2. Adatbázis Inicializáló SQL Szkript
SQL

-- Vektor kiterjesztés engedélyezése
CREATE EXTENSION IF NOT EXISTS vector;

-- Markdown dokumentumok táblája
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    path TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    last_modified TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    version INTEGER DEFAULT 1
);

-- Dokumentáció változás történet
CREATE TABLE document_history (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    content TEXT NOT NULL,
    changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    changed_by TEXT,
    version INTEGER NOT NULL
);

-- Feladatok (task-ok) táblája
CREATE TABLE tasks (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    document_id INTEGER REFERENCES documents(id),
    code_path TEXT
);

-- Hierarchikus dokumentum index táblája
CREATE TABLE document_hierarchy (
    id SERIAL PRIMARY KEY,
    document_id INTEGER REFERENCES documents(id),
    parent_id INTEGER REFERENCES document_hierarchy(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    doc_level INTEGER NOT NULL,
    seq_num INTEGER NOT NULL
);

-- Dokumentum összefüggések táblája
CREATE TABLE document_relationships (
    id SERIAL PRIMARY KEY,
    source_id INTEGER REFERENCES document_hierarchy(id),
    target_id INTEGER REFERENCES document_hierarchy(id),
    relationship_type TEXT NOT NULL,
    strength FLOAT NOT NULL
);

-- Kulcsszavak és kapcsolódási pontok
CREATE TABLE document_keywords (
    id SERIAL PRIMARY KEY,
    node_id INTEGER REFERENCES document_hierarchy(id),
    keyword TEXT NOT NULL,
    embedding VECTOR(1536),
    importance FLOAT NOT NULL
);

-- Hasonlósági keresési indexek
CREATE INDEX ON documents USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON document_hierarchy USING hnsw (embedding vector_cosine_ops);
CREATE INDEX ON document_keywords USING hnsw (embedding vector_cosine_ops);
4. FastAPI-MCP API Szerver Implementációja
4.1. Függőségek


cat > api/requirements.txt << 'EOF'
fastapi==0.110.1
uvicorn==0.28.0
fastmcp==0.5.1
pydantic==2.7.1
psycopg2-binary==2.9.9
sentence-transformers==2.5.1
GitPython==3.1.43
python-multipart==0.0.9
llama-index==0.10.12
llama-index-vector-stores-postgres==0.1.3
llama-index-readers-file==0.1.4
markdown==3.5.2
nltk==3.8.1
EOF
4.2. Dockerfile
Dockerfile

FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# NLTK adatok letöltése
RUN python -m nltk.downloader punkt stopwords wordnet

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "${API_PORT}"]
4.3. API Implementáció
Python

from fastapi import FastAPI, Depends, Body, HTTPException, UploadFile, File
from fastapi_mcp import FastApiMCP
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import psycopg2
import psycopg2.extras
from sentence_transformers import SentenceTransformer
import os
import git
from datetime import datetime
import logging
import markdown
import re
import json
import tempfile
import shutil
import nltk
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from collections import defaultdict

# LlamaIndex importok
from llama_index.core import (
    Settings,
    VectorStoreIndex,
    SimpleDirectoryReader,
    Document as LlamaDocument
)
from llama_index.vector_stores.postgres import PGVectorStore
from llama_index.core.node_parser import HierarchicalNodeParser
from llama_index.core.schema import TextNode, NodeRelationship, RelatedNodeInfo

# Logging beállítása
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="AI Documentation System")

# MCP szerver inicializálása
mcp = FastApiMCP(app)

# Beágyazó modell inicializálása
model = SentenceTransformer('all-MiniLM-L6-v2')

# Alapértelmezett LlamaIndex beállítások
# Settings.embed_model = model # LlamaIndex embed_model beállítását a PGVectorStore inicializálja

# Adatbázis kapcsolat
def get_db_connection():
    conn = psycopg2.connect(os.environ.get("DATABASE_URL"))
    conn.autocommit = True
    return conn

# PG Vector Store létrehozása (Hierarchikus indexhez)
def get_pg_vector_store_hierarchy():
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
        embed_dim=1536 # Adjust embed_dim based on your model
    )

# Modellek
class DocumentBase(BaseModel):
    title: str
    path: str
    content: str

class DocumentCreate(DocumentBase):
    pass

class Document(DocumentBase):
    id: int
    last_modified: datetime
    version: int

class DocumentUpdate(BaseModel):
    content: str
    changed_by: str = Field(default="AI")

class TaskBase(BaseModel):
    title: str
    description: str
    document_id: Optional[int] = None
    code_path: Optional[str] = None

class TaskCreate(TaskBase):
    pass

class Task(TaskBase):
    id: int
    status: str
    created_at: datetime
    updated_at: datetime

class HierarchyNode(BaseModel):
    id: int
    title: str
    content: str
    doc_level: int
    seq_num: int
    parent_id: Optional[int] = None
    document_id: int

class DocumentRelationship(BaseModel):
    source_id: int
    target_id: int
    relationship_type: str
    strength: float

class KeywordModel(BaseModel):
    node_id: int
    keyword: str
    importance: float

# Dokumentum feldolgozás segédfüggvényei
def extract_hierarchy_from_markdown(content: str) -> List[Dict[str, Any]]:
    """Markdown tartalom feldolgozása hierarchikus struktúrába"""
    lines = content.split('\n')
    nodes = []
    current_headers = [None] * 6  # max 6 szintű header (h1-h6)
    seq_counter = 0

    current_content = []
    current_level = 0
    current_title = ""

    for line in lines:
        header_match = re.match(r'^(#{1,6})\s+(.+)', line)

        if header_match:
            # Ha van korábbi tartalom, mentsük el
            if current_title:
                nodes.append({
                    "title": current_title,
                    "content": "\n".join(current_content).strip(),
                    "level": current_level,
                    "seq_num": seq_counter
                })
                seq_counter += 1
                current_content = []

            level = len(header_match.group(1))
            title = header_match.group(2).strip()

            current_level = level
            current_title = title
            current_headers[level-1] = title
            # Töröljük az alacsonyabb szintű headereket
            for i in range(level, 6):
                current_headers[i] = None
        else:
            # Addjuk hozzá a sort a jelenlegi tartalomhoz
            if current_title:
                current_content.append(line)

    # Ne felejtsük el az utolsó szakaszt
    if current_title:
        nodes.append({
            "title": current_title,
            "content": "\n".join(current_content).strip(),
            "level": current_level,
            "seq_num": seq_counter
        })

    return nodes

def generate_hierarchical_index(doc_id: int, content: str):
    """Hierarchikus index generálása a dokumentumhoz"""
    try:
        # Meglévő hierarchia törlése
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM document_keywords WHERE node_id IN (SELECT id FROM document_hierarchy WHERE document_id = %s)", (doc_id,))
        cursor.execute("DELETE FROM document_relationships WHERE source_id IN (SELECT id FROM document_hierarchy WHERE document_id = %s) OR target_id IN (SELECT id FROM document_hierarchy WHERE document_id = %s)", (doc_id, doc_id))
        cursor.execute("DELETE FROM document_hierarchy WHERE document_id = %s", (doc_id,))
        conn.commit()

        # Hierarchia kinyerése a markdown tartalomból
        hierarchy_nodes = extract_hierarchy_from_markdown(content)

        # Ha nincs header, akkor hozzunk létre egy alapértelmezett csomópontot
        if not hierarchy_nodes:
            hierarchy_nodes = [{
                "title": "Document Content",
                "content": content,
                "level": 1,
                "seq_num": 0
            }]

        # Hierarchia csomópontok mentése
        node_ids = {}  # level+seq -> node_id mapping

        for node in hierarchy_nodes:
            # Beágyazás generálása a csomóponthoz
            embedding = model.encode(f"{node['title']} {node['content']}").tolist()

            # Szülő azonosító meghatározása
            parent_id = None
            for potential_parent in sorted([(n["level"], n["seq_num"]) for n in hierarchy_nodes if n["level"] < node["level"] and n["seq_num"] < node["seq_num"]], reverse=True):
                if potential_parent in node_ids:
                    parent_id = node_ids[potential_parent]
                    break

            # Csomópont mentése
            cursor.execute(
                """INSERT INTO document_hierarchy (document_id, parent_id, title, content, embedding, doc_level, seq_num)
                VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (doc_id, parent_id, node["title"], node["content"], embedding, node["level"], node["seq_num"])
            )

            node_id = cursor.fetchone()[0]
            node_ids[(node["level"], node["seq_num"])] = node_id

            # Kulcsszavak kinyerése és mentése
            keywords = extract_keywords(node["title"], node["content"])
            for keyword, importance in keywords.items():
                keyword_embedding = model.encode(keyword).tolist()
                cursor.execute(
                    """INSERT INTO document_keywords (node_id, keyword, embedding, importance)
                    VALUES (%s, %s, %s, %s)""",
                    (node_id, keyword, keyword_embedding, importance)
                )

        # Összefüggések generálása a csomópontok között
        for i, node1_key in enumerate(node_ids.keys()):
            node1_id = node_ids[node1_key]
            # Ugyanazon szinten lévő csomópontok összekötése "sibling" kapcsolattal
            for j, node2_key in enumerate(node_ids.keys()):
                if i != j and node1_key[0] == node2_key[0]:  # Ugyanaz a szint
                    node2_id = node_ids[node2_key]
                    cursor.execute(
                        """INSERT INTO document_relationships (source_id, target_id, relationship_type, strength)
                        VALUES (%s, %s, %s, %s)""",
                        (node1_id, node2_id, "sibling", 0.5)
                    )

            # Szemantikailag hasonló csomópontok összekötése
            cursor.execute(
                """SELECT id, embedding FROM document_hierarchy
                WHERE document_id = %s AND id != %s""",
                (doc_id, node1_id)
            )

            for row in cursor.fetchall():
                node2_id, node2_embedding = row
                # Koszinusz hasonlóság számítása
                cursor.execute(
                    """SELECT 1 - (embedding <=> %s) as similarity FROM document_hierarchy WHERE id = %s""",
                    (node2_embedding, node1_id)
                )
                similarity = cursor.fetchone()[0]

                if similarity > 0.7:  # Csak ha elég magas a hasonlóság
                    cursor.execute(
                        """INSERT INTO document_relationships (source_id, target_id, relationship_type, strength)
                        VALUES (%s, %s, %s, %s)""",
                        (node1_id, node2_id, "semantic", similarity)
                    )

        conn.commit()
        cursor.close()
        conn.close()

        return True
    except Exception as e:
        logger.error(f"Hiba a hierarchikus index generálásakor: {str(e)}")
        return False


def extract_keywords(title: str, content: str) -> Dict[str, float]:
    """Kulcsszavak kinyerése a szövegből fontossági súlyokkal"""
    try:
        # Stopszavak betöltése
        stop_words = set(stopwords.words('english'))

        # Szöveg előkészítése
        text = f"{title} {content}".lower()
        # Írásjelek eltávolítása
        text = re.sub(r'[^\w\s]', '', text)

        # Tokenizálás
        words = nltk.word_tokenize(text)

        # Stopszavak és túl rövid szavak eltávolítása
        words = [word for word in words if word not in stop_words and len(word) > 2]

        # Gyakoriság számítása
        word_freq = defaultdict(int)
        for word in words:
            word_freq[word] += 1

        # Normalizálás a maximális gyakoriság alapján
        max_freq = max(word_freq.values()) if word_freq else 1
        keywords = {word: freq / max_freq for word, freq in word_freq.items()}

        # Csak a legfontosabb kulcsszavak megtartása (top 10)
        sorted_keywords = sorted(keywords.items(), key=lambda x: x[1], reverse=True)
        return dict(sorted_keywords[:10])
    except Exception as e:
        logger.error(f"Hiba a kulcsszavak kinyerésekor: {str(e)}")
        return {}

def search_hierarchical_index(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Hierarchikus keresés a dokumentáció indexben"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Beágyazás generálása a lekérdezéshez
        query_embedding = model.encode(query).tolist()

        # Első lépés: Kulcsszó alapú keresés
        cursor.execute(
            """SELECT k.node_id, k.keyword, k.importance, h.title, h.content, h.document_id,
                      1 - (k.embedding <=> %s) as similarity
               FROM document_keywords k
               JOIN document_hierarchy h ON k.node_id = h.id
               WHERE k.keyword ILIKE %s
               ORDER BY similarity DESC
               LIMIT %s""",
            (query_embedding, f"%{query}%", limit)
        )

        keyword_results = cursor.fetchall()

        # Második lépés: Szemantikus keresés a hierarchikus indexben
        cursor.execute(
            """SELECT h.id, h.title, h.content, h.document_id, h.doc_level, h.parent_id,
                      1 - (h.embedding <=> %s) as similarity
               FROM document_hierarchy h
               ORDER BY similarity DESC
               LIMIT %s""",
            (query_embedding, limit)
        )

        semantic_results = cursor.fetchall()

        # Harmadik lépés: Eredmények egyesítése és rendezése
        combined_results = set()
        ranked_results = []

        # Kulcsszó találatok hozzáadása
        for row in keyword_results:
            node_id = row["node_id"]
            if node_id not in combined_results:
                combined_results.add(node_id)
                ranked_results.append({
                    "id": node_id,
                    "title": row["title"],
                    "content": row["content"],
                    "document_id": row["document_id"],
                    "relevance": row["similarity"] * (1 + row["importance"]),  # Fontosság alapú súlyozás
                    "match_type": "keyword",
                    "keyword": row["keyword"]
                })

        # Szemantikus találatok hozzáadása
        for row in semantic_results:
            node_id = row["id"]
            if node_id not in combined_results:
                combined_results.add(node_id)
                ranked_results.append({
                    "id": node_id,
                    "title": row["title"],
                    "content": row["content"],
                    "document_id": row["document_id"],
                    "relevance": row["similarity"],
                    "match_type": "semantic",
                    "parent_id": row["parent_id"],
                    "level": row["doc_level"]
                })

        # Kapcsolódó csomópontok beolvasása a legmagasabb relevanciájú találatokhoz
        if ranked_results:
            # Rendezzük az eredményeket relevanciák szerint
            ranked_results = sorted(ranked_results, key=lambda x: x["relevance"], reverse=True)

            # Hozzaadjuk a kapcsolódó csomópontokat az első N legmagasabb relevanciájú találathoz
            top_n = min(3, len(ranked_results))
            for i in range(top_n):
                # Ellenőrizzük, hogy a lista nem üres és az index érvényes
                if i < len(ranked_results):
                    cursor.execute(
                        """SELECT r.target_id, r.relationship_type, r.strength,
                                  h.title, h.content, h.document_id
                           FROM document_relationships r
                           JOIN document_hierarchy h ON r.target_id = h.id
                           WHERE r.source_id = %s
                           ORDER BY r.strength DESC
                           LIMIT 3""",
                        (ranked_results[i]["id"],)
                    )

                    for rel_row in cursor.fetchall():
                        target_id = rel_row["target_id"]
                        if target_id not in combined_results:
                            combined_results.add(target_id)
                            ranked_results.append({
                                "id": target_id,
                                "title": rel_row["title"],
                                "content": rel_row["content"],
                                "document_id": rel_row["document_id"],
                                "relevance": ranked_results[i]["relevance"] * rel_row["strength"],
                                "match_type": f"related-{rel_row['relationship_type']}",
                                "relation_to": ranked_results[i]["id"]
                            })

        # Végleges eredmények rendezése és limitálása
        final_results = sorted(ranked_results, key=lambda x: x["relevance"], reverse=True)[:limit]

        # Dokumentum adatok hozzáadása
        for result in final_results:
            doc_id = result["document_id"]
            cursor.execute("SELECT title, path FROM documents WHERE id = %s", (doc_id,))
            doc_row = cursor.fetchone()
            if doc_row:
                 result["doc_title"] = doc_row["title"]
                 result["doc_path"] = doc_row["path"]
            else:
                 result["doc_title"] = "Unknown Document"
                 result["doc_path"] = "N/A"


        cursor.close()
        conn.close()

        return final_results
    except Exception as e:
        logger.error(f"Hiba a hierarchikus keresés során: {str(e)}")
        return []


# --- MCP API Végpontok ---

@mcp.tool()
def list_docs() -> List[Dict[str, Any]]:
    """Az összes elérhető markdown dokumentációs fájl listázása."""
    logger.info("list_docs MCP funkció meghívva")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT id, title, path FROM documents")
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [{"id": row["id"], "title": row["title"], "path": row["path"]} for row in results]
    except Exception as e:
        logger.error(f"Hiba a list_docs funkció végrehajtásakor: {str(e)}")
        return [{"error": str(e)}]

@mcp.tool()
def get_doc_content(doc_id: int) -> str:
    """Egy adott markdown dokumentációs fájl tartalmának lekérése."""
    logger.info(f"get_doc_content MCP funkció meghívva: {doc_id}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT content FROM documents WHERE id = %s", (doc_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            return f"Hiba: A(z) {doc_id} azonosítójú dokumentum nem található"
        return result["content"]
    except Exception as e:
        logger.error(f"Hiba a get_doc_content funkció végrehajtásakor: {str(e)}")
        return f"Hiba: {str(e)}"

@mcp.tool()
def search_docs(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    """Intelligens, hierarchikus keresés a dokumentációban a lekérdezés alapján."""
    logger.info(f"search_docs MCP funkció meghívva: {query}")
    try:
        # Hierarchikus keresés végrehajtása
        search_results = search_hierarchical_index(query, limit)

        # Eredmények átalakítása
        results = []
        for result in search_results:
            # Relevancia pontszám átalakítása százalékra (biztos, ami biztos, clampeljük 0-1 közé)
            relevance_pct = int(max(0, min(1, result.get("relevance", 0))) * 100)

            # Előnézet generálása a tartalomból
            preview = result.get("content", "")
            if len(preview) > 200:
                preview = preview[:200] + "..."
            else:
                preview = preview # Use full content if shorter than 200 chars

            # Találat típusának olvasható formája
            match_type = result.get("match_type", "unknown")
            match_type_display = "Ismeretlen találat"
            if match_type == "keyword":
                match_type_display = "Kulcsszó találat"
            elif match_type == "semantic":
                match_type_display = "Szemantikus találat"
            elif match_type.startswith("related"):
                rel_type = match_type.split("-")[1]
                match_type_display = f"Kapcsolódó tartalom ({rel_type})"

            # Eredmény hozzáadása
            results.append({
                # Use doc_title for 'id' field as requested in the example
                "id": result.get("doc_title", "N/A"),
                "title": result.get("title", "N/A"),
                "path": result.get("doc_path", "N/A"),
                "preview": preview,
                "relevance": f"{relevance_pct}%",
                "match_type": match_type_display,
                "document_id": result.get("document_id")
            })

        return results
    except Exception as e:
        logger.error(f"Hiba a search_docs funkció végrehajtásakor: {str(e)}")
        return [{"error": str(e)}]


@mcp.tool()
def get_document_structure(doc_id: int) -> Dict[str, Any]:
    """Egy dokumentum hierarchikus struktúrájának lekérése."""
    logger.info(f"get_document_structure MCP funkció meghívva: {doc_id}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Dokumentum alapadatainak lekérése
        cursor.execute("SELECT title, path FROM documents WHERE id = %s", (doc_id,))
        doc = cursor.fetchone()

        if not doc:
            conn.close()
            return {"error": f"A(z) {doc_id} azonosítójú dokumentum nem található"}

        # Hierarchia lekérése
        cursor.execute(
            """SELECT id, title, doc_level, parent_id, seq_num
               FROM document_hierarchy
               WHERE document_id = %s
               ORDER BY doc_level, seq_num""",
            (doc_id,)
        )

        nodes = cursor.fetchall()
        cursor.close()
        conn.close()

        # Hierarchikus struktúra felépítése
        node_dict = {node["id"]: {
            "id": node["id"],
            "title": node["title"],
            "level": node["doc_level"],
            "children": []
        } for node in nodes}

        # Gyökér és gyermek csomópontok rendezése
        root_nodes = []
        for node in nodes:
            if node["parent_id"] is None:
                root_nodes.append(node_dict[node["id"]])
            else:
                parent_id = node["parent_id"]
                # Check if parent_id exists in node_dict before appending
                if parent_id in node_dict:
                    parent = node_dict[parent_id]
                    parent["children"].append(node_dict[node["id"]])
                else:
                     logger.warning(f"Parent node with id {parent_id} not found for node {node['id']}")


        return {
            "title": doc["title"],
            "path": doc["path"],
            # Sort root nodes by seq_num
            "structure": sorted(root_nodes, key=lambda x: [n for n in nodes if n['id'] == x['id']][0]['seq_num'])
        }
    except Exception as e:
        logger.error(f"Hiba a get_document_structure funkció végrehajtásakor: {str(e)}")
        return {"error": str(e)}


@mcp.tool()
def update_document(doc_id: int, new_content: str, changed_by: str = "AI") -> Dict[str, Any]:
    """Egy adott dokumentum tartalmának frissítése és újraindexelése."""
    logger.info(f"update_document MCP funkció meghívva: {doc_id}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Aktuális verzió lekérése
        cursor.execute("SELECT version, content FROM documents WHERE id = %s", (doc_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            return {"status": "error", "message": f"A(z) {doc_id} azonosítójú dokumentum nem található"}

        current_version = result["version"]
        old_content = result["content"]

        # Új beágyazás generálása
        embedding = model.encode(new_content).tolist()

        # Hozzáadás a történethez
        cursor.execute(
            "INSERT INTO document_history (document_id, content, changed_by, version) VALUES (%s, %s, %s, %s)",
            (doc_id, old_content, changed_by, current_version)
        )

        # Dokumentum frissítése
        cursor.execute(
            """UPDATE documents
               SET content = %s, embedding = %s, last_modified = CURRENT_TIMESTAMP, version = %s
               WHERE id = %s""",
            (new_content, embedding, current_version + 1, doc_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        # Hierarchikus index újragenerálása a dokumentumhoz
        success = generate_hierarchical_index(doc_id, new_content)

        status = "success" if success else "warning"
        message = f"Dokumentum frissítve a {current_version + 1} verzióra"
        if not success:
            message += ", de hiba történt a hierarchikus index újragenerálása során"

        return {"status": status, "message": message}
    except Exception as e:
        logger.error(f"Hiba az update_document funkció végrehajtásakor: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
def create_task(title: str, description: str, doc_id: Optional[int] = None, code_path: Optional[str] = None) -> Dict[str, Any]:
    """Új feladat létrehozása a dokumentáció frissítésével kapcsolatban."""
    logger.info(f"create_task MCP funkció meghívva: {title}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(
            """INSERT INTO tasks (title, description, document_id, code_path)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (title, description, doc_id, code_path)
        )

        task_id = cursor.fetchone()["id"]
        conn.commit()
        cursor.close()
        conn.close()

        return {"status": "success", "message": f"Feladat létrehozva a(z) {task_id} azonosítóval", "task_id": task_id}
    except Exception as e:
        logger.error(f"Hiba a create_task funkció végrehajtásakor: {str(e)}")
        return {"status": "error", "message": str(e)}

@mcp.tool()
def get_tasks(status: Optional[str] = None) -> List[Dict[str, Any]]:
    """Feladatok lekérése, opcionálisan szűrve állapot szerint."""
    logger.info(f"get_tasks MCP funkció meghívva: {status}")
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        if status:
            cursor.execute("SELECT * FROM tasks WHERE status = %s", (status,))
        else:
            cursor.execute("SELECT * FROM tasks")

        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Hiba a get_tasks funkció végrehajtásakor: {str(e)}")
        return [{"error": str(e)}]

# --- REST API végpontok ---

@app.post("/documents/", response_model=Document)
def create_document(document: DocumentCreate):
    """Új dokumentum létrehozása és indexelése."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        # Beágyazás generálása
        embedding = model.encode(document.content).tolist()

        cursor.execute(
            """INSERT INTO documents (title, path, content, embedding)
               VALUES (%s, %s, %s, %s) RETURNING id, title, path, content, last_modified, version""",
            (document.title, document.path, document.content, embedding)
        )

        result = cursor.fetchone()
        doc_id = result["id"]
        conn.commit()
        cursor.close()
        conn.close()

        # Hierarchikus index generálása a dokumentumhoz
        generate_hierarchical_index(doc_id, document.content)

        return dict(result)
    except Exception as e:
        logger.error(f"Hiba a create_document funkció végrehajtásakor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/documents/upload/")
async def upload_document(file: UploadFile = File(...), path: Optional[str] = None):
    """Markdown fájl feltöltése és indexelése."""
    try:
        # Ideiglenes fájl létrehozása
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)

        # Fájl mentése
        with open(temp_file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)

        # Fájl tartalmának beolvasása
        with open(temp_file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Ideiglenes könyvtár törlése
        shutil.rmtree(temp_dir)

        # Dokumentum útvonal beállítása
        if not path:
            path = f"/docs/{file.filename}"

        # Dokumentum létrehozása
        document = DocumentCreate(
            title=os.path.splitext(file.filename)[0],
            path=path,
            content=content
        )

        # Dokumentum létrehozási funkció meghívása
        result = create_document(document)

        return {"status": "success", "message": f"Dokumentum feltöltve és indexelve: {file.filename}", "document": result}
    except Exception as e:
        logger.error(f"Hiba a dokumentum feltöltésekor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/documents/", response_model=List[Document])
def read_documents():
    """Összes dokumentum lekérése."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT id, title, path, content, last_modified, version FROM documents")
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        return [dict(row) for row in results]
    except Exception as e:
        logger.error(f"Hiba a read_documents funkció végrehajtásakor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}", response_model=Document)
def read_document(doc_id: int):
    """Adott dokumentum lekérése."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT id, title, path, content, last_modified, version FROM documents WHERE id = %s", (doc_id,))
        result = cursor.fetchone()
        cursor.close()
        conn.close()

        if not result:
            raise HTTPException(status_code=404, detail=f"A(z) {doc_id} azonosítójú dokumentum nem található")

        return dict(result)
    except Exception as e:
        logger.error(f"Hiba a read_document funkció végrehajtásakor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/{doc_id}/structure")
def read_document_structure(doc_id: int):
    """Dokumentum hierarchikus struktúrájának lekérése."""
    return get_document_structure(doc_id)

@app.put("/documents/{doc_id}", response_model=Document)
def update_document_endpoint(doc_id: int, document_update: DocumentUpdate):
    """Dokumentum frissítése."""
    try:
        # MCP eszköz használata a frissítéshez
        result = update_document(doc_id, document_update.content, document_update.changed_by)

        if result.get("status") == "error":
            raise HTTPException(status_code=404, detail=result.get("message"))

        # Frissített dokumentum lekérése
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cursor.execute("SELECT id, title, path, content, last_modified, version FROM documents WHERE id = %s", (doc_id,))
        updated_doc = cursor.fetchone()
        cursor.close()
        conn.close()

        if not updated_doc:
             # This case should theoretically not happen if update_document succeeded, but good practice to check
             raise HTTPException(status_code=500, detail=f"Failed to retrieve updated document with id {doc_id}")


        return dict(updated_doc)
    except Exception as e:
        logger.error(f"Hiba az update_document_endpoint funkció végrehajtásakor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/tasks/", response_model=Task)
def create_task_endpoint(task: TaskCreate):
    """Új feladat létrehozása."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(
            """INSERT INTO tasks (title, description, document_id, code_path)
               VALUES (%s, %s, %s, %s) RETURNING *""",
            (task.title, task.description, task.document_id, task.code_path)
        )

        result = cursor.fetchone()
        conn.commit()
        cursor.close()
        conn.close()

        return dict(result)
    except Exception as e:
        logger.error(f"Hiba a create_task_endpoint funkció végrehajtásakor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tasks/", response_model=List[Task])
def read_tasks(status: Optional[str] = None):
    """Feladatok lekérése."""
    try:
        return get_tasks(status)
    except Exception as e:
        logger.error(f"Hiba a read_tasks funkció végrehajtásakor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/tasks/{task_id}", response_model=Task)
def update_task_status(task_id: int, status: str):
    """Feladat állapotának frissítése."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

        cursor.execute(
            """UPDATE tasks SET status = %s, updated_at = CURRENT_TIMESTAMP
               WHERE id = %s RETURNING *""",
            (status, task_id)
        )

        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=404, detail=f"A(z) {task_id} azonosítójú feladat nem található")

        conn.commit()
        cursor.close()
        conn.close()

        return dict(result)
    except Exception as e:
        logger.error(f"Hiba az update_task_status funkció végrehajtásakor: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search/")
def search_endpoint(query: str, limit: int = 5):
    """Keresés a dokumentációban."""
    return search_docs(query, limit)


# MCP szerver csatlakoztatása
mcp.mount()

# Alkalmazás indulási esemény
@app.on_event("startup")
async def startup_event():
    logger.info("AI Documentation System elindult")
    logger.info(f"A dokumentációs API a következő porton fut: {os.environ.get('API_PORT', 9000)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("API_PORT", 9000)))
5. Kódváltozás Figyelő Komponens Implementálása
5.1. Függőségek


cat > code-monitor/requirements.txt << 'EOF'
GitPython==3.1.43
requests==2.31.0
python-dotenv==1.0.1
EOF
5.2. Dockerfile
Dockerfile

FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "code_monitor.py"]
5.3. Kód Monitor Implementáció
Python

import os
import time
import git
import requests
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Környezeti változók betöltése
load_dotenv()

# Logging beállítása
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Konfiguráció
REPO_PATH = os.environ.get("REPO_PATH", "/app/repo")
API_URL = os.environ.get("API_URL", "http://api:9000")
CHECK_INTERVAL = int(os.environ.get("CHECK_INTERVAL", 300))  # 5 perc

def get_changed_files(repo, since_time):
    """Az adott időpont óta módosított fájlok lekérdezése"""
    changed_files = []

    try:
        # Commit-ok lekérdezése az adott időpont óta
        for commit in repo.iter_commits(since=since_time.strftime("%Y-%m-%d %H:%M:%S")):
            # Az érintett fájlok hozzáadása a listához
            for file in commit.stats.files:
                if file.endswith((".py", ".js", ".ts", ".java", ".cs", ".go", ".md", ".txt")) and file not in changed_files:
                    changed_files.append(file)

        return changed_files
    except Exception as e:
        logger.error(f"Hiba a változtatások lekérdezésekor: {str(e)}")
        return []

def suggest_doc_update(file_path, content):
    """Dokumentáció frissítési javaslat elkészítése"""
    # Itt integrálhatunk egy LLM API-t (pl. Anthropic Claude API-t vagy OpenAI API-t)
    # Egyszerűsített példa:
    file_name = os.path.basename(file_path)

    return {
        "title": f"Dokumentáció frissítés szükséges: {file_name}",
        "description": f"A {file_path} fájl módosult. Kérlek ellenőrizd és frissítsd a hozzá tartozó dokumentációt az aktuális implementációnak megfelelően.",
        "code_path": file_path
    }

def find_related_doc_id(file_path):
    """Kapcsolódó dokumentum azonosítójának keresése a fájl útvonala alapján"""
    try:
        # API hívás a kapcsolódó dokumentum kereséséhez
        response = requests.get(f"{API_URL}/documents/")
        if response.status_code == 200:
            documents = response.json()

            # Egyszerű ellenőrzés - ha a dokumentum útvonala tartalmazza a fájl nevét
            file_name = os.path.basename(file_path)
            for doc in documents:
                # Check if file_name is in the doc['path'] OR doc['title'] (case-insensitive)
                if file_name.lower() in doc["path"].lower() or file_name.split('.')[0].lower() in doc['title'].lower():
                    return doc["id"]

        return None
    except Exception as e:
        logger.error(f"Hiba a kapcsolódó dokumentum keresésekor: {str(e)}")
        return None

def main():
    logger.info("Kód Monitor Szolgáltatás elindult")
    logger.info(f"Git repository útvonal: {REPO_PATH}")
    logger.info(f"API URL: {API_URL}")

    # Ellenőrizzük, hogy a repository mappa létezik-e
    if not os.path.exists(REPO_PATH):
        logger.error(f"A megadott repository útvonal nem létezik: {REPO_PATH}")
        return

    # Ellenőrizzük, hogy a mappa egy git repository-e
    try:
        repo = git.Repo(REPO_PATH)
    except git.InvalidGitRepositoryError:
        logger.error(f"A megadott mappa nem egy érvényes git repository: {REPO_PATH}")
        return

    last_check_time = datetime.now() - timedelta(days=1)  # Kezdéskor az elmúlt 24 óra változásait nézzük

    while True:
        current_time = datetime.now()
        logger.info(f"Ellenőrzés: {current_time}")

        try:
            # Git repo frissítése
            origin = repo.remotes.origin
            origin.pull()
            logger.info("Git repository sikeresen frissítve")

            # Módosított fájlok lekérdezése
            changed_files = get_changed_files(repo, last_check_time)
            logger.info(f"Módosított fájlok száma: {len(changed_files)}")

            for file_path in changed_files:
                logger.info(f"Módosított fájl feldolgozása: {file_path}")

                # Fájl tartalmának lekérdezése
                full_path = os.path.join(REPO_PATH, file_path)
                if os.path.exists(full_path) and os.path.isfile(full_path):
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Kapcsolódó dokumentum keresése
                        doc_id = find_related_doc_id(file_path)

                        # Dokumentáció frissítési javaslat készítése
                        task = suggest_doc_update(file_path, content)
                        if doc_id:
                            task["document_id"] = doc_id

                        # Task létrehozása az API-n keresztül
                        logger.info(f"Feladat létrehozása: {task['title']}")
                        response = requests.post(
                            f"{API_URL}/tasks/",
                            json=task
                        )

                        if response.status_code == 200:
                            logger.info(f"Feladat sikeresen létrehozva: {response.json().get('task_id')}") # Use task_id from response
                        else:
                            logger.error(f"Hiba a feladat létrehozásakor: {response.text}")
                    except Exception as e:
                        logger.error(f"Hiba a fájl feldolgozásakor: {str(e)}")

            last_check_time = current_time
        except git.GitCommandError as e:
             logger.error(f"Git parancs hiba: {str(e)}")
        except requests.exceptions.ConnectionError as e:
             logger.error(f"API kapcsolat hiba: {str(e)}")
        except Exception as e:
            logger.error(f"Hiba történt a kód monitor futtatásakor: {str(e)}")

        # Várunk a következő ellenőrzésig
        logger.info(f"Várakozás {CHECK_INTERVAL} másodpercig a következő ellenőrzésig...")
        time.sleep(CHECK_INTERVAL)

if __name__ == "__main__":
    main()
6. Docker Compose Konfiguráció
YAML

version: '3'

services:
  db:
    build:
      context: ./postgres
      dockerfile: Dockerfile
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d <span class="math-inline">\{POSTGRES\_DB\}"\]
interval\: 10s
timeout\: 5s
retries\: 5
api\:
build\:
context\: \./api
dockerfile\: Dockerfile
depends\_on\:
db\:
condition\: service\_healthy
ports\:
\- "</span>{API_PORT}:<span class="math-inline">\{API\_PORT\}"
environment\:
\- DATABASE\_URL\=</span>{DATABASE_URL}
      - API_PORT=<span class="math-inline">\{API\_PORT\}
volumes\:
\# Mount a docs folder if you have pre\-existing docs or want to add them manually
\- \./docs\:/app/docs
\# Explicitly set the embed model path if needed, though sentence\-transformers downloads automatically
\# environment\:
\#   \- MODEL\_NAME\=all\-MiniLM\-L6\-v2 \# Example if you want to make model name configurable
code\-monitor\:
build\:
context\: \./code\-monitor
dockerfile\: Dockerfile
depends\_on\:
\- api
environment\:
\- REPO\_PATH\=</span>{REPO_PATH}
      - API_URL=<span class="math-inline">\{API\_URL\}
\- CHECK\_INTERVAL\=</span>{CHECK_INTERVAL}
    volumes:
      # Mount your actual repository here
      - ./repo:/app/repo

volumes:
  postgres_data:
7. Rendszer Indítása és Tesztelése
7.1. Docker konténerek elindítása


cd ~/ai-doc-system
docker-compose up -d --build
7.2. Napló ellenőrzése


# API napló ellenőrzése
docker-compose logs -f api

# Kód monitor napló ellenőrzése
docker-compose logs -f code-monitor
7.3. API tesztelése


# Dokumentum létrehozása
curl -X POST [http://10.0.0.11:9000/documents/](http://10.0.0.11:9000/documents/) \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Teszt Dokumentum",
    "path": "/docs/teszt.md",
    "content": "# Teszt Dokumentum\n\nEz egy teszt markdown dokumentum."
  }''

# Dokumentumok lekérdezése
curl [http://10.0.0.11:9000/documents/](http://10.0.0.11:9000/documents/)

# Feladatok lekérdezése
curl [http://10.0.0.11:9000/tasks/](http://10.0.0.11:9000/tasks/)
8. Git Repository Beállítása
8.1. Repository klónozása


# Tisztítsd meg a repo könyvtárat, ha már létezik
rm -rf ~/ai-doc-system/repo/*

# Klónozd a repositoryt (cseréld le a placeholder URL-t a sajátodra)
git clone [https://github.com/felhasznalonev/projekt-repository.git](https://github.com/felhasznalonev/projekt-repository.git) ~/ai-doc-system/repo

# Ellenőrizd, hogy a repository sikeresen klónozódott-e
ls -la ~/ai-doc-system/repo
Megjegyzés: Győződj meg róla, hogy a Docker Compose fájl volumes szekciójában a ./repo:/app/repo helyesen hivatkozik a klónozott repositoryra a gazda rendszeren.

8.2. Repository frissítési időköz beállítása
Az alapértelmezett ellenőrzési időköz 5 perc (300 másodperc). Ha szeretnéd ezt módosítani:



# .env fájl szerkesztése (példa 10 percre módosításra)
sed -i 's/CHECK_INTERVAL=300/CHECK_INTERVAL=600/' ~/ai-doc-system/.env

# Konténer újraindítása a változtatások alkalmazásához
docker-compose restart code-monitor
9. ClaudeCode Konfiguráció
9.1. ClaudeCode beállítása
ClaudeCode terminálban a következő parancsot add ki (cseréld le az IP címet, ha szükséges):



claude code --mcp-server=docs=[http://10.0.0.11:9000/mcp](http://10.0.0.11:9000/mcp)
9.2. ClaudeCode példa használat
> list_docs()
[
  {"id": 1, "title": "Teszt Dokumentum", "path": "/docs/teszt.md"},
  {"id": 2, "title": "API Dokumentáció", "path": "/docs/api.md"}
]

> get_doc_content(1)
# Teszt Dokumentum

Ez egy teszt markdown dokumentum.

> search_docs("felhasználói hitelesítés")
[
  {
    "id": "API Dokumentáció", # Dokumentum címe
    "title": "Felhasználói Hitelesítés", # Talált szekció címe
    "path": "/docs/api.md",
    "preview": "## Felhasználói Hitelesítés\n\nA rendszer JWT token alapú hitelesítést használ. Az autentikációhoz küldd el a felhasználónevet és jelszót a /login végpontra...",
    "relevance": "92%",
    "match_type": "Szemantikus találat",
    "document_id": 2 # Dokumentum azonosítója
  },
  {
    "id": "Biztonsági Dokumentáció",
    "title": "Hitelesítési Folyamatok",
    "path": "/docs/security.md",
    "preview": "# Hitelesítési Folyamatok\n\nA rendszer több hitelesítési módszert támogat...",
    "relevance": "87%",
    "match_type": "Kulcsszó találat",
    "document_id": 3
  }
]

> get_document_structure(2)
{
  "title": "API Dokumentáció",
  "path": "/docs/api.md",
  "structure": [
    {
      "id": 3,
      "title": "API Dokumentáció",
      "level": 1,
      "children": [
        {
          "id": 4,
          "title": "Áttekintés",
          "level": 2,
          "children": []
        },
        {
          "id": 5,
          "title": "Felhasználói Hitelesítés",
          "level": 2,
          "children": [
            {
              "id": 6,
              "title": "Bejelentkezés",
              "level": 3,
              "children": []
            },
            {
              "id": 7,
              "title": "Token Frissítés",
              "level": 3,
              "children": []
            }
          ]
        }
      ]
    }
  ]
}


> update_document(1, "# Frissített Teszt Dokumentum\n\nEz egy frissített markdown dokumentum.")
{"status": "success", "message": "Dokumentum frissítve a 2 verzióra"}

> get_tasks()
[
  {
    "id": 1,
    "title": "Dokumentáció frissítés szükséges: main.py",
    "description": "A src/main.py fájl módosult. Kérlek ellenőrizd és frissítsd a hozzá tartozó dokumentációt az aktuális implementációnak megfelelően.",
    "status": "pending",
    "created_at": "2025-05-14T12:00:00",
    "updated_at": "2025-05-14T12:00:00",
    "document_id": null,
    "code_path": "src/main.py"
  }
]
10. Hibaelhárítás
10.1. Adatbázis kapcsolat hiba
Ha az API nem tud csatlakozni az adatbázishoz:



# Ellenőrizd, hogy az adatbázis konténer fut-e
docker-compose ps

# Nézd meg az adatbázis naplókat
docker-compose logs db

# Ellenőrizd, hogy a DATABASE_URL helyesen van-e beállítva
docker-compose exec api env | grep DATABASE_URL

# Adatbázis újraindítása
docker-compose restart db
10.2. API hiba
Ha az API nem indul el megfelelően:



# API naplók ellenőrzése
docker-compose logs api

# Ellenőrizd, hogy a port nincs-e használatban
netstat -tuln | grep 9000

# API újraindítása
docker-compose restart api
10.3. Kód monitor hiba
Ha a kód monitor nem működik megfelelően:



# Kód monitor naplók ellenőrzése
docker-compose logs code-monitor

# Ellenőrizd, hogy a repository mappa megfelelően van-e beállítva
docker-compose exec code-monitor ls -la /app/repo

# Kód monitor újraindítása
docker-compose restart code-monitor
11. Biztonsági mentés és helyreállítás
11.1. Adatbázis mentése


docker-compose exec db pg_dump -U docuser docdb > backup.sql
11.2. Adatbázis helyreállítása


cat backup.sql | docker-compose exec -T db psql -U docuser -d docdb
12. Rendszer frissítése
12.1. Kód frissítése


# Legújabb kód letöltése
cd ~/ai-doc-system
git pull

# Konténerek újraépítése és újraindítása
docker-compose down
docker-compose up -d --build
13. Monitoring és karbantartás
13.1. Rendszerállapot ellenőrzése


# Konténerek állapotának ellenőrzése
docker-compose ps

# Rendszererőforrások ellenőrzése
docker stats

13.2. Naplófájlok törlése


# Docker naplók tisztítása
# Ez a parancs csak az utolsó 1000 sort menti egy fájlba, nem törli a Docker belső naplóit.
# A Docker naplók törlésére más módszerek vannak, pl. docker system prune vagy log rotation beállítása.
docker-compose logs --no-color | head -n 1000 > recent_logs.txt

# A Docker beépített log rotation beállítását érdemes használni a docker-compose.yml-ben.
# Példa:
# services:
#   your_service:
#     ...
#     logging:
#       driver: "json-file"
#       options:
#         max-size: "10m"
#         max-file: "5"

13.3. Adatbázis karbantartás


# Adatbázis optimalizálása (VACUUM ANALYZE segíti a lekérdezések gyorsítását)
docker-compose exec db psql -U docuser -d docdb -c "VACUUM ANALYZE"

14. LlamaIndex Alapú Hierarchikus Indexelés
A rendszer LlamaIndex-et használ a dokumentumok fejlett hierarchikus és szemantikus indexeléséhez. Ez jelentősen javítja az LLM-ek képességét a releváns dokumentáció megtalálására és megértésére.

14.1. Hierarchikus Indexelés Működése
A hierarchikus indexelés a következőképpen működik:

Dokumentum Szegmentálás: A rendszer a markdown struktúrája alapján (fejlécek) automatikusan szegmentálja a dokumentumot hierarchikus csomópontokra.
Csomópont Reprezentáció: Minden csomópont tartalmazza:
Címét (fejléc szöveg)
Tartalmát (az adott szekcióhoz tartozó szöveg)
Hierarchia szintjét (h1, h2, h3, stb.)
Beágyazását (vektoros reprezentáció)
Kapcsolat Építés:
Strukturális Kapcsolatok: Szülő-gyermek viszonyok a dokumentumok fejlécei alapján
Szemantikus Kapcsolatok: Tartalmi hasonlóságon alapuló kapcsolatok csomópontok között
Kulcsszó Alapú Kapcsolatok: Kiemelt kulcsszavak és fogalmak indexelése

14.2. Hogyan Segíti az LLM-eket?
Kontextus Hatékonyság:
Az LLM csak a releváns dokumentumrészeket tölti be a kontextusába
A tokenspórolás akár 70-95%-os is lehet a teljes dokumentációhoz képest
Strukturált Megértés:
Az LLM látja a dokumentáció hierarchikus struktúráját
Jobban megérti a fogalmak közötti kapcsolatokat
Fogalomtérkép Navigáció:
Az LLM követheti a kulcsszavak és fogalmak közötti kapcsolatrendszert
A get_document_structure MCP funkció segítségével láthatja a dokumentum teljes struktúráját

14.3. Indexelési Optimalizáció
Dokumentáció készítésekor kövesd ezeket a legjobb gyakorlatokat:

Megfelelő Markdown Struktúra:

Markdown

# Fő Cím (H1)

Bevezető szöveg...

## Fejezet 1 (H2)

Fejezet 1 tartalma...

### Alfejezet 1.1 (H3)

Alfejezet 1.1 tartalma...
Kulcsszavak Kiemelése:

Fontosabb szakkifejezéseket, API neveket, osztályneveket jelölj meg hangsúlyosan, például vastag vagy kód formázással
A kezdeti szakaszokban definiáld a fontos fogalmakat
Kereszthivatkozások:

Használj belső linkeket más fejezetekre, hogy explicit kapcsolatokat teremts
Metaadat Kommentek:

Használhatsz speciális HTML kommenteket kapcsolatok definiálására:
<!-- end list -->

Felhasználói Tokenek
A rendszer automatikusan feldolgozza ezeket a struktúrákat, és optimális indexet készít az LLM-ek számára.

14.4. A Hierarchikus Keresés Folyamata
LLM Kérdés → Keresési Vektor → Többszintű Keresés:

Kulcsszó Keresés → Direkt találatok
Szemantikus Keresés → Kontextuális találatok
Hierarchikus Bővítés → Szülő/gyerek csomópontok bevonása
Kapcsolati Bővítés → Kapcsolódó koncepciók bevonása
Ez a folyamat biztosítja, hogy az LLM a legjobb, legpontosabb és legkontextus-hatékonyabb találatokat kapja, miközben minimalizálja a token-felhasználást.

Összefoglalás
Ez az útmutató részletesen leírta, hogyan implementálj egy teljes körű AI-támogatott dokumentációs rendszert, amely:

FastAPI-MCP szervert használ az AI eszközök integrációjához
PostgreSQL és pgvector alapú vektoros keresést biztosít a dokumentációban
LlamaIndex által támogatott hierarchikus és szemantikus indexelést nyújt
Automatikusan figyeli a kódváltozásokat és feladatokat generál a dokumentáció frissítéséhez
Lehetővé teszi az AI eszközök számára a dokumentáció lekérdezését, keresését és frissítését
A rendszer token- és memória-optimalizálást tesz lehetővé az AI eszközök számára a következő kulcselőnyökkel:

Csak a releváns dokumentumrészek betöltése: Az AI csak a kérdéshez kapcsolódó dokumentációt tölti be, ami 70-95%-os tokenspórolást eredményezhet.
Kontextuális értelmezés: A hierarchikus és szemantikus indexelés révén az AI jobban megérti a dokumentáció összefüggéseit.
Dokumentáció karbantartás automatizálása: Az AI feladatokat generálhat és végrehajthat a dokumentáció naprakészen tartásához.
Az MCP szerver standardizált interfészt biztosít a ClaudeCode, Cursor.ai és más AI eszközök számára, így azok közvetlenül kommunikálhatnak a dokumentációs rendszerrel, miközben csak a szükséges dokumentációt töltik be a kontextusba.