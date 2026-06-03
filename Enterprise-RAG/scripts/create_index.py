import json
import os
import logging
logger = logging.getLogger(__name__)

def create_index(db_client):

    #check if index already exists
    index_name = os.getenv("INDEX_NAME", "enterprise-rag-index")
    index_exists = db_client.indices.exists(index=index_name)

    if index_exists:
        logger.info(f"Index={index_name} already exists.")
        return
    
    logger.info(f"Creating index={index_name}")
    # ===== INDEX DEFINITION =====
    index_body = {
        "settings": {
            "index": {
                "knn": True
            }
        },
        "mappings": {
            "properties": {
                "doc_id": {
                    "type": "keyword"
                },
                "text": {
                    "type": "text"
                },
                "source": {
                    "type": "keyword"
                },
                "embedding": {
                    "type": "knn_vector",
                    "dimension": 512,
                    "method": {
                    "name": "hnsw",
                    "space_type": "cosinesimil",
                    "engine": "nmslib"
                    }
                }
            }
        }
    }

    # ===== CREATE INDEX =====
    try:

        response = db_client.indices.create(
            index=index_name,
            body=index_body
        )
        logger.info(f"✅Index: {index_name} created successfully.")
        logger.info(json.dumps(response, indent=2))
    
    except Exception as e:
        logger.critical(f"❌ Creating index failed. Error -> {e}")
        raise
