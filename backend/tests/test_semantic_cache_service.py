import unittest

from app.services.semantic_cache_service import SemanticCacheService


class FakeEmbedding:
    def __init__(self, values: list[float]) -> None:
        self._values = values

    def tolist(self) -> list[float]:
        return self._values


class FakeModel:
    def encode(self, query: str, normalize_embeddings: bool = True) -> FakeEmbedding:
        if query.lower() in {"list all departments", "show all departments"}:
            return FakeEmbedding([1.0, 0.0])
        return FakeEmbedding([0.0, 1.0])


class SemanticCacheServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.cache = SemanticCacheService()
        self.cache._redis_client = None
        self.cache._model = FakeModel()
        self.cache.clear()

    def test_generates_embedding_and_returns_semantic_hit(self) -> None:
        first_embedding = self.cache.generate_embedding("List all departments")
        first_search = self.cache.search(first_embedding)

        self.assertFalse(first_search.hit)

        self.cache.store(
            query="List all departments",
            embedding=first_embedding,
            generated_sql="SELECT DISTINCT department FROM employees;",
            response_payload={
                "generated_sql": "SELECT DISTINCT department FROM employees;",
                "cache_hit": False,
                "similarity_score": 0.0,
                "validation_status": "valid",
                "execution_time": 0.01,
                "rows_returned": 4,
                "results": [{"department": "Finance"}],
            },
        )

        second_embedding = self.cache.generate_embedding("Show all departments")
        second_search = self.cache.search(second_embedding)

        self.assertTrue(second_search.hit)
        self.assertEqual(second_search.similarity_score, 1.0)
        self.assertIsNotNone(second_search.entry)

    def test_metrics_track_hits_misses_and_entries(self) -> None:
        embedding = self.cache.generate_embedding("List all departments")
        self.cache.search(embedding)
        self.cache.store(
            query="List all departments",
            embedding=embedding,
            generated_sql="SELECT DISTINCT department FROM employees;",
            response_payload={
                "generated_sql": "SELECT DISTINCT department FROM employees;",
                "cache_hit": False,
                "similarity_score": 0.0,
                "validation_status": "valid",
                "execution_time": 0.01,
                "rows_returned": 4,
                "results": [],
            },
        )
        self.cache.search(self.cache.generate_embedding("Show all departments"))

        metrics = self.cache.get_metrics()

        self.assertEqual(metrics["cache_hits"], 1)
        self.assertEqual(metrics["cache_misses"], 1)
        self.assertEqual(metrics["cache_entry_count"], 1)
        self.assertEqual(metrics["hit_rate"], 50.0)


if __name__ == "__main__":
    unittest.main()
