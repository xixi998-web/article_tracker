import pytest
from article_tracker.models.article import Article, SourceType, ScreeningTier, AbstractSource
from article_tracker.models.profile import ResearchProfile
from article_tracker.utils.text import similarity, is_similar, normalize_title
from article_tracker.dedup.seen_store import SeenStore
from article_tracker.dedup.deduplicator import Deduplicator
from article_tracker.screen.tier_classifier import TierClassifier
from article_tracker.screen.profile_loader import ProfileLoader
from article_tracker.config.config import Config
from article_tracker.config.config_schema import UnifiedConfig


class TestArticle:
    def test_create_arxiv(self):
        a = Article(title="Test Paper", source_type=SourceType.arxiv, arxiv_id="2301.00001")
        assert a.title == "Test Paper"
        assert a.source_type == SourceType.arxiv
        assert a.arxiv_id == "2301.00001"

    def test_create_top_journal(self):
        a = Article(title="Nature Paper", source_type=SourceType.top_journal, doi="10.1234/test")
        assert a.doi == "10.1234/test"
        assert a.dedup_key_doi == "10.1234/test"

    def test_title_not_empty(self):
        with pytest.raises(ValueError):
            Article(title="", source_type=SourceType.arxiv)

    def test_dedup_keys(self):
        a = Article(title="Test", source_type=SourceType.arxiv, doi="10.1234/test", arxiv_id="2301.00001")
        assert a.dedup_key_doi == "10.1234/test"
        assert a.dedup_key_arxiv == "2301.00001"


class TestTextUtils:
    def test_similarity_identical(self):
        assert similarity("hello world", "hello world") == 1.0

    def test_similarity_case_insensitive(self):
        assert is_similar("A Deep Learning Approach", "a deep learning approach", 0.99)

    def test_similarity_different(self):
        assert similarity("hello", "world") < 0.5

    def test_normalize_title(self):
        assert normalize_title("  A   Deep   Learning  Paper  ") == "a deep learning paper"


class TestDeduplicator:
    def test_dedup_by_doi(self, tmp_path):
        store = SeenStore(str(tmp_path / "seen.json"))
        dedup = Deduplicator(store, prefer_source="top_journal")
        a1 = Article(title="Paper A", source_type=SourceType.top_journal, doi="10.1234/test")
        a2 = Article(title="Paper A", source_type=SourceType.arxiv, doi="10.1234/test")
        unique, stats = dedup.deduplicate([a1, a2])
        assert len(unique) == 1
        assert stats["dedup_doi"] == 1

    def test_dedup_by_arxiv_id(self, tmp_path):
        store = SeenStore(str(tmp_path / "seen.json"))
        dedup = Deduplicator(store)
        a1 = Article(title="Paper B", source_type=SourceType.arxiv, arxiv_id="2301.00001")
        a2 = Article(title="Paper B", source_type=SourceType.top_journal, arxiv_id="2301.00001")
        unique, stats = dedup.deduplicate([a1, a2])
        assert len(unique) == 1

    def test_dedup_by_title(self, tmp_path):
        store = SeenStore(str(tmp_path / "seen.json"))
        dedup = Deduplicator(store, title_threshold=0.85)
        a1 = Article(title="A Deep Learning Approach to Image Segmentation", source_type=SourceType.arxiv)
        a2 = Article(title="A deep learning approach to image segmentation", source_type=SourceType.top_journal)
        unique, stats = dedup.deduplicate([a1, a2])
        assert len(unique) == 1

    def test_no_dedup_different(self, tmp_path):
        store = SeenStore(str(tmp_path / "seen.json"))
        dedup = Deduplicator(store)
        a1 = Article(title="Paper About Cats", source_type=SourceType.arxiv)
        a2 = Article(title="Paper About Dogs", source_type=SourceType.top_journal)
        unique, stats = dedup.deduplicate([a1, a2])
        assert len(unique) == 2


class TestTierClassifier:
    def test_classify_core(self):
        profile = ResearchProfile(
            core_keywords=["deep learning"], proxy_keywords=["optimization"],
            eco_keywords=["statistics"], exclusion_keywords=[],
        )
        classifier = TierClassifier(profile)
        a = Article(title="Deep Learning for Vision", abstract="A deep learning method", source_type=SourceType.arxiv)
        stats = classifier.classify([a])
        assert a.screening_tier == ScreeningTier.core
        assert stats["core"] == 1

    def test_classify_noise(self):
        profile = ResearchProfile(
            core_keywords=["deep learning"], proxy_keywords=["optimization"],
            eco_keywords=["statistics"], exclusion_keywords=[],
        )
        classifier = TierClassifier(profile)
        a = Article(title="Cooking Recipes", abstract="How to bake bread", source_type=SourceType.arxiv)
        stats = classifier.classify([a])
        assert a.screening_tier == ScreeningTier.noise

    def test_filter_by_tiers(self):
        profile = ResearchProfile(
            core_keywords=["deep learning"], proxy_keywords=["optimization"],
            eco_keywords=["statistics"], exclusion_keywords=[],
        )
        classifier = TierClassifier(profile, output_tiers=["core", "proxy"])
        a1 = Article(title="Deep Learning Paper", abstract="deep learning", source_type=SourceType.arxiv)
        a2 = Article(title="Optimization Paper", abstract="optimization method", source_type=SourceType.arxiv)
        a3 = Article(title="Cooking Paper", abstract="cooking", source_type=SourceType.arxiv)
        classifier.classify([a1, a2, a3])
        filtered = classifier.filter_by_tiers([a1, a2, a3])
        assert len(filtered) == 2

    def test_must_track_journals_empty_no_privilege(self):
        profile = ResearchProfile(
            core_keywords=["deep learning"], proxy_keywords=["optimization"], eco_keywords=["statistics"],
            exclusion_keywords=[], must_track_journals=[],
        )
        classifier = TierClassifier(profile)
        a = Article(title="RNA Sequencing Analysis", abstract="A study of gene expression", venue="Nature", source_type=SourceType.top_journal, doi="10.1038/test")
        stats = classifier.classify([a])
        assert a.screening_tier == ScreeningTier.noise

    def test_must_track_journals_nonempty_privilege(self):
        profile = ResearchProfile(
            core_keywords=["deep learning"], proxy_keywords=["optimization"], eco_keywords=["statistics"],
            exclusion_keywords=[], must_track_journals=["Nature"],
        )
        classifier = TierClassifier(profile)
        a = Article(title="RNA Sequencing Analysis", abstract="A study of gene expression", venue="Nature", source_type=SourceType.top_journal, doi="10.1038/test")
        stats = classifier.classify([a])
        assert a.screening_tier == ScreeningTier.core


class TestSeenStore:
    def test_mark_and_check(self, tmp_path):
        store = SeenStore(str(tmp_path / "seen.json"))
        assert not store.has("doi:10.1234/test")
        store.mark("doi:10.1234/test")
        assert store.has("doi:10.1234/test")

    def test_persist_and_reload(self, tmp_path):
        path = str(tmp_path / "seen.json")
        store = SeenStore(path)
        store.mark("doi:10.1234/test", {"source": "arxiv"})
        store.persist()
        store2 = SeenStore(path)
        assert store2.has("doi:10.1234/test")

    def test_corrupt_file_backup(self, tmp_path):
        path = tmp_path / "seen.json"
        path.write_text("NOT JSON!!!", encoding="utf-8")
        store = SeenStore(str(path))
        assert store.count == 0
        assert (tmp_path / "seen.json.bak").exists()


class TestConfig:
    def test_load_example(self):
        cfg = Config.load("config.yaml")
        assert isinstance(cfg, UnifiedConfig)
        assert cfg.arxiv.enabled is True
        assert cfg.top_journal.enabled is True

    def test_file_not_found(self):
        with pytest.raises(FileNotFoundError):
            Config.load("nonexistent.yaml")
