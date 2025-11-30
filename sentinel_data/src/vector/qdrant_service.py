# sentinel_data/src/vector/qdrant_service.py
import logging
from qdrant_client import QdrantClient
from qdrant_client.http import models
from src.config import settings

logger = logging.getLogger("data.qdrant")

class QdrantService:
    def __init__(self):
        self.client = QdrantClient(url=settings.QDRANT_URL)
        self.collection_name = "sales_playbook"

    def create_collection_if_not_exists(self):
        """Initializes the vector collection with specific config."""
        try:
            self.client.get_collection(self.collection_name)
            logger.info(f"Collection '{self.collection_name}' exists.")
        except Exception:
            logger.info(f"Creating collection '{self.collection_name}'...")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=384,  # Dimension of all-MiniLM-L6-v2
                    distance=models.Distance.COSINE
                ),
                # OPTIMIZATION 1: HNSW Index Configuration
                hnsw_config=models.HnswConfigDiff(
                    m=16,               # Max edges per node. Higher = more RAM, faster search. (16-64 is standard)
                    ef_construct=100,   # Build precision. Higher = slower build, better recall.
                    full_scan_threshold=10000 # If items < 10k, use Flat Search (it's faster for small data).
                ),
               quantization_config=models.ScalarQuantization(
                    scalar=models.ScalarQuantizationConfig(
                        type=models.ScalarType.INT8,
                        quantile=0.99,
                        always_ram=True
                    )
                )
            )

    def upsert_knowledge(self, kb_items: list[dict], embeddings: list[list[float]]):
        """
        kb_items: List of dicts with 'id', 'text', 'metadata'
        embeddings: List of vectors
        """
        points = []
        for i, item in enumerate(kb_items):
            points.append(models.PointStruct(
                id=i,  # In prod, use UUID hashing
                vector=embeddings[i],
                payload=item
            ))

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} items into Qdrant.")