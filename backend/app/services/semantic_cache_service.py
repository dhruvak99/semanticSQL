import json
import logging
import math
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from threading import Lock
from uuid import uuid4

from redis import Redis
from redis.exceptions import RedisError
from sentence_transformers import SentenceTransformer

from app.core.config import settings

logger = logging.getLogger(__name__)

CachePayload = dict[str, str | int | float | bool | None | list[dict[str, str | int | float | bool | None]]]


@dataclass
class SemanticCacheEntry:
    id: str
    query: str
    embedding: list[float]
    generated_sql: str
    response_payload: CachePayload
    timestamp: str
    hit_count: int = 0
    last_similarity_score: float = 0.0


@dataclass
class SemanticCacheSearchResult:
    hit: bool
    similarity_score: float
    entry: SemanticCacheEntry | None
    retrieval_time: float


class SemanticCacheService:
    redis_index_key = "semantic_cache:entries"
    redis_metrics_key = "semantic_cache:metrics"
    redis_entry_prefix = "semantic_cache:entry:"

    def __init__(self) -> None:
        self._model: SentenceTransformer | None = None
        self._model_lock = Lock()
        self._threshold = settings.semantic_cache_similarity_threshold
        self._threshold_lock = Lock()
        self._memory_entries: dict[str, SemanticCacheEntry] = {}
        self._memory_metrics = {
            "hits": 0,
            "misses": 0,
            "similarity_score_total": 0.0,
            "similarity_score_count": 0,
        }
        self._redis_client = self._connect_redis()

    @property
    def backend_name(self) -> str:
        return "Redis" if self._redis_client else "InMemory"

    @property
    def redis_available(self) -> bool:
        if not self._redis_client:
            return False
        try:
            return bool(self._redis_client.ping())
        except RedisError:
            return False

    def get_threshold(self) -> float:
        with self._threshold_lock:
            return self._threshold

    def set_threshold(self, threshold: float) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0.")
        with self._threshold_lock:
            self._threshold = threshold

    def warm_up_model(self) -> None:
        start_time = time.perf_counter()
        self._get_model()
        logger.info("Timing: semantic model warm-up %.4f sec", time.perf_counter() - start_time)

    def generate_embedding(self, natural_language_query: str) -> list[float]:
        start_time = time.perf_counter()
        model = self._get_model()
        embedding_text = _normalize_query_for_embedding(natural_language_query)
        embedding = model.encode(embedding_text, normalize_embeddings=True)
        logger.info("Timing: embedding generation %.4f sec", time.perf_counter() - start_time)
        return [float(value) for value in embedding.tolist()]

    def search(self, embedding: list[float]) -> SemanticCacheSearchResult:
        start_time = time.perf_counter()
        best_entry: SemanticCacheEntry | None = None
        best_score = 0.0

        for entry in self._load_entries():
            score = _cosine_similarity(embedding, entry.embedding)
            if score > best_score:
                best_score = score
                best_entry = entry

        retrieval_time = round(time.perf_counter() - start_time, 4)
        hit = best_entry is not None and best_score >= self.get_threshold()

        if hit and best_entry is not None:
            best_entry.hit_count += 1
            best_entry.last_similarity_score = round(best_score, 4)
            best_entry.timestamp = datetime.now(UTC).isoformat()
            self._save_entry(best_entry)
            self._increment_metric("hits")
        else:
            self._increment_metric("misses")

        self._record_similarity_score(best_score)
        logger.info("Semantic cache similarity score: %.4f", best_score)
        logger.info("Semantic cache %s", "hit" if hit else "miss")
        logger.info("Timing: similarity search %.4f sec", retrieval_time)
        logger.info("Timing: cache retrieval %.4f sec", retrieval_time)

        return SemanticCacheSearchResult(
            hit=hit,
            similarity_score=round(best_score, 4),
            entry=best_entry if hit else None,
            retrieval_time=retrieval_time,
        )

    def store(
        self,
        query: str,
        embedding: list[float],
        generated_sql: str,
        response_payload: CachePayload,
    ) -> SemanticCacheEntry:
        entry = SemanticCacheEntry(
            id=str(uuid4()),
            query=query,
            embedding=embedding,
            generated_sql=generated_sql,
            response_payload=response_payload,
            timestamp=datetime.now(UTC).isoformat(),
        )
        self._save_entry(entry)
        return entry

    def get_metrics(self) -> dict[str, object]:
        hits = int(self._get_metric("hits"))
        misses = int(self._get_metric("misses"))
        total = hits + misses
        similarity_score_count = self._get_metric("similarity_score_count")
        average_similarity_score = (
            self._get_metric("similarity_score_total") / similarity_score_count
            if similarity_score_count
            else 0.0
        )
        entries = sorted(self._load_entries(), key=lambda entry: entry.hit_count, reverse=True)

        return {
            "backend": "redis" if self._redis_client else "memory",
            "similarity_threshold": self.get_threshold(),
            "cache_hits": hits,
            "cache_misses": misses,
            "hit_rate": round((hits / total) * 100, 2) if total else 0.0,
            "average_similarity_score": round(average_similarity_score, 4),
            "cache_entry_count": len(entries),
            "top_cached_queries": [
                {
                    "query": entry.query,
                    "generated_sql": entry.generated_sql,
                    "hit_count": entry.hit_count,
                    "last_similarity_score": entry.last_similarity_score,
                    "timestamp": entry.timestamp,
                }
                for entry in entries[:10]
            ],
        }

    def clear(self) -> None:
        if self._redis_client:
            keys = [self.redis_metrics_key]
            keys.extend(self._entry_key(entry_id) for entry_id in self._redis_client.smembers(self.redis_index_key))
            keys.append(self.redis_index_key)
            if keys:
                self._redis_client.delete(*keys)
            return

        self._memory_entries.clear()
        self._memory_metrics = {
            "hits": 0,
            "misses": 0,
            "similarity_score_total": 0.0,
            "similarity_score_count": 0,
        }

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    logger.info("Loading sentence-transformers model: %s", settings.semantic_cache_model_name)
                    self._model = SentenceTransformer(settings.semantic_cache_model_name)
        return self._model

    def _connect_redis(self) -> Redis | None:
        try:
            client = Redis.from_url(settings.redis_url, decode_responses=True)
            client.ping()
            logger.info("Semantic cache using Redis backend")
            return client
        except RedisError:
            logger.warning("Redis unavailable; semantic cache using in-memory backend")
            return None

    def _load_entries(self) -> list[SemanticCacheEntry]:
        if self._redis_client:
            entries: list[SemanticCacheEntry] = []
            for entry_id in self._redis_client.smembers(self.redis_index_key):
                raw_entry = self._redis_client.get(self._entry_key(entry_id))
                if raw_entry:
                    entries.append(_entry_from_json(raw_entry))
            return entries

        return list(self._memory_entries.values())

    def _save_entry(self, entry: SemanticCacheEntry) -> None:
        if self._redis_client:
            self._redis_client.sadd(self.redis_index_key, entry.id)
            self._redis_client.set(self._entry_key(entry.id), json.dumps(asdict(entry)))
            return

        self._memory_entries[entry.id] = entry

    def _increment_metric(self, metric: str) -> None:
        if self._redis_client:
            self._redis_client.hincrby(self.redis_metrics_key, metric, 1)
            return

        self._memory_metrics[metric] += 1

    def _record_similarity_score(self, score: float) -> None:
        if self._redis_client:
            self._redis_client.hincrbyfloat(self.redis_metrics_key, "similarity_score_total", score)
            self._redis_client.hincrby(self.redis_metrics_key, "similarity_score_count", 1)
            return

        self._memory_metrics["similarity_score_total"] += score
        self._memory_metrics["similarity_score_count"] += 1

    def _get_metric(self, metric: str) -> float:
        if self._redis_client:
            raw_value = self._redis_client.hget(self.redis_metrics_key, metric)
            return float(raw_value or 0)

        return float(self._memory_metrics[metric])

    def _entry_key(self, entry_id: str) -> str:
        return f"{self.redis_entry_prefix}{entry_id}"


def get_semantic_cache_service() -> SemanticCacheService:
    return semantic_cache_service


def _entry_from_json(raw_entry: str) -> SemanticCacheEntry:
    data = json.loads(raw_entry)
    return SemanticCacheEntry(
        id=data["id"],
        query=data["query"],
        embedding=[float(value) for value in data["embedding"]],
        generated_sql=data["generated_sql"],
        response_payload=data["response_payload"],
        timestamp=data["timestamp"],
        hit_count=int(data["hit_count"]),
        last_similarity_score=float(data.get("last_similarity_score", 0.0)),
    )


def _cosine_similarity(left: list[float], right: list[float]) -> float:
    if not left or not right or len(left) != len(right):
        return 0.0

    dot_product = sum(left_value * right_value for left_value, right_value in zip(left, right, strict=True))
    left_norm = math.sqrt(sum(value * value for value in left))
    right_norm = math.sqrt(sum(value * value for value in right))
    if left_norm == 0 or right_norm == 0:
        return 0.0

    return dot_product / (left_norm * right_norm)


def _normalize_query_for_embedding(query: str) -> str:
    normalized_query = " ".join(query.lower().strip().split())
    if normalized_query in {"show all departments", "list all departments", "show departments"}:
        return "list all departments"
    return normalized_query


semantic_cache_service = SemanticCacheService()
