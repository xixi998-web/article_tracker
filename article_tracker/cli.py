from __future__ import annotations

import logging
import sys
from datetime import date, timedelta
from pathlib import Path

import click

from article_tracker.collect.collector import Collector
from article_tracker.config.config import Config
from article_tracker.config.config_schema import UnifiedConfig
from article_tracker.dedup.deduplicator import Deduplicator
from article_tracker.dedup.seen_store import SeenStore
from article_tracker.enrich.abstract_enricher import AbstractEnricher
from article_tracker.enrich.code_link_enricher import CodeLinkEnricher
from article_tracker.enrich.llm_enricher import LLMEnricher
from article_tracker.infra.logging import RunLog
from article_tracker.models.article import Article
from article_tracker.output.output_manager import OutputManager
from article_tracker.screen.tier_classifier import TierClassifier


def _setup_logging(verbose: bool) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def _run_track(config: UnifiedConfig, source: str, since_days: int | None, dry_run: bool) -> RunLog:
    log = RunLog()
    logger = logging.getLogger("article_tracker")

    since = date.today() - timedelta(days=since_days or config.freshness.since_days)

    logger.info(f"=== Paper Tracker Run (sources={source}, since={since}) ===")

    # 1. Collect
    logger.info("Step 1: Collecting papers...")
    collector = Collector(config)
    collected = collector.collect(source=source, since=since)
    all_articles: list[Article] = []
    for src_name, arts in collected.items():
        log.sources[src_name] = len(arts)
        all_articles.extend(arts)
        logger.info(f"  {src_name}: {len(arts)} papers")
    logger.info(f"Total collected: {len(all_articles)}")

    if not all_articles:
        logger.info("No papers found. Exiting.")
        log.finish()
        return log

    # 2. Deduplicate
    logger.info("Step 2: Deduplicating...")
    seen_store = SeenStore(config.dedup.seen_path)
    dedup = Deduplicator(seen_store, config.dedup.title_threshold, config.dedup.prefer_source)
    unique_articles, dedup_stats = dedup.deduplicate(all_articles)
    log.dedup = dedup_stats
    logger.info(f"  After dedup: {len(unique_articles)} new papers (removed {dedup_stats['dedup_doi'] + dedup_stats['dedup_arxiv_id'] + dedup_stats['dedup_title']})")

    # 3. Enrich: abstract fallback
    logger.info("Step 3: Enriching abstracts (S2 → OpenAlex → Crossref)...")
    abstract_enricher = AbstractEnricher(config.s2, config.openalex)
    enrich_stats = abstract_enricher.enrich(unique_articles)
    log.enrichment.update(enrich_stats)

    # 4. Enrich: code links
    logger.info("Step 4: Enriching code links...")
    code_enricher = CodeLinkEnricher(config.s2)
    code_stats = code_enricher.enrich(unique_articles)
    log.enrichment["code_structured"] = code_stats.get("structured", 0)
    log.enrichment["code_scraped"] = code_stats.get("scraped", 0)

    # 5. Screen
    logger.info("Step 5: Screening by profile...")
    classifier = TierClassifier.from_config(config.screening)
    screen_stats = classifier.classify(unique_articles)
    log.screening = screen_stats
    logger.info(f"  Core: {screen_stats['core']}, Proxy: {screen_stats['proxy']}, Eco: {screen_stats['eco']}, Noise: {screen_stats['noise']}")

    # Filter by tiers
    filtered = classifier.filter_by_tiers(unique_articles)
    logger.info(f"  After tier filter: {len(filtered)} papers")

    # 5b. Fallback when insufficient
    min_papers = config.freshness.fallback_top_n if config.freshness.fallback_when_empty else 0
    if len(filtered) < min_papers:
        logger.info(f"Step 5b: Only {len(filtered)} papers (min {min_papers}), filling from recent papers...")
        seen_ids = {a.doi or a.arxiv_id or a.title for a in filtered}
        pool = unique_articles if unique_articles else all_articles
        if pool:
            classifier.classify(pool)
            pool_filtered = classifier.filter_by_tiers(pool)
            for a in pool_filtered:
                aid = a.doi or a.arxiv_id or a.title
                if aid not in seen_ids and len(filtered) < min_papers:
                    seen_ids.add(aid)
                    a.is_fallback = True
                    filtered.append(a)
        logger.info(f"  After fallback: {len(filtered)} papers (minimum {min_papers})")

    # 6. Enrich: LLM bilingual summary (after screening, only for filtered papers)
    if config.llm.enabled:
        llm_limit = min(max(config.llm.max_papers, config.output.max_papers), len(filtered))
        llm_articles = filtered[:llm_limit]
        logger.info(f"Step 6: Generating LLM bilingual summaries for up to {llm_limit} papers...")
        llm_enricher = LLMEnricher(config.llm)
        llm_stats = llm_enricher.enrich(llm_articles)
        log.enrichment["llm_success"] = llm_stats.get("success", 0)
        log.enrichment["llm_failed"] = llm_stats.get("failed", 0)

        logger.info("Step 6b: Translating titles/abstracts...")
        for a in llm_articles:
            llm_enricher.translate(a)
    else:
        logger.info("Step 6: LLM disabled, skipping.")

    # 7. Output
    if not dry_run:
        max_out = config.output.max_papers
        if len(filtered) > max_out:
            logger.info(f"  Capping output to {max_out} papers (from {len(filtered)})")
            filtered = filtered[:max_out]
        logger.info("Step 7: Generating outputs...")
        output_mgr = OutputManager(config)
        output_results = output_mgr.output(filtered)
        log.output = output_results
        for ch, result in output_results.items():
            logger.info(f"  {ch}: {result}")

        # Persist seen store
        seen_store.persist()
        logger.info(f"  Seen store persisted ({seen_store.count} records)")
    else:
        logger.info("Step 7: Dry run, skipping output.")

    # 8. Print summary
    logger.info(f"=== Run complete: {len(filtered)} papers output, {log.duration_s:.1f}s ===")
    log.finish()
    return log


@click.group()
@click.version_option(package_name="article_tracker")
def cli():
    pass


@cli.command()
@click.option("--config", "config_path", default="config.yaml", help="Config YAML path")
@click.option("--source", default="all", type=click.Choice(["all", "arxiv", "top_journal"]), help="Source filter")
@click.option("--since-days", default=None, type=int, help="Days to look back")
@click.option("--dry-run", is_flag=True, help="Skip output/push")
@click.option("--verbose", is_flag=True, help="Debug logging")
@click.option("--out-dir", default=None, help="Override output directory")
@click.option("--profile", "profile_path", default=None, help="Override research profile path")
def track(config_path, source, since_days, dry_run, verbose, out_dir, profile_path):
    _setup_logging(verbose)
    try:
        cfg = Config.load(config_path)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)

    if out_dir:
        cfg.output.dir = out_dir
    if profile_path:
        cfg.profile_path = profile_path
    if dry_run:
        cfg.dry_run = True

    run_log = _run_track(cfg, source, since_days, dry_run)

    if not dry_run:
        log_path = Path(cfg.output.dir) / "run_log.json"
        run_log.save(log_path)


@cli.command("weekly-report")
@click.option("--config", "config_path", default="config.yaml", help="Config YAML path")
@click.option("--days", default=7, type=int, help="Days to summarize")
@click.option("--verbose", is_flag=True)
def weekly_report(config_path, days, verbose):
    _setup_logging(verbose)
    try:
        cfg = Config.load(config_path)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    run_log = _run_track(cfg, "all", days, cfg.dry_run)
    click.echo(f"Weekly report: {run_log.screening}")


@cli.group()
def watchlist():
    pass


@watchlist.command("build")
@click.option("--path", default="references/top-journal-families.md", help="Watchlist MD path")
@click.option("--pool", default="all", help="Journal family pool filter")
def watchlist_build(path, pool):
    from article_tracker.source.top_journal_source import build_watchlist as _build
    entries = _build(path, pool)
    click.echo(f"Watchlist: {len(entries)} journals")
    for e in entries[:20]:
        click.echo(f"  {e['family']}: {e['name']}")


@watchlist.command("show")
@click.option("--path", default="references/top-journal-families.md", help="Watchlist MD path")
def watchlist_show(path):
    from article_tracker.source.top_journal_source import build_watchlist as _build
    entries = _build(path)
    click.echo(f"Watchlist: {len(entries)} journals")
    for e in entries:
        click.echo(f"  {e['family']}: {e['name']} (ISSN: {e.get('issn', 'N/A')})")


@cli.command()
@click.option("--config", "config_path", default="config.yaml", help="Config YAML path")
@click.option("--from-arxiv", default=None, help="Old Arxiv-tracker config.yaml path")
@click.option("--from-frontier", default=None, help="Old frontier-tracker reading_state.json path")
def migrate(config_path, from_arxiv, from_frontier):
    from article_tracker.config.migrate import migrate_arxiv_config, migrate_frontier_state
    if from_arxiv:
        result = migrate_arxiv_config(from_arxiv, config_path)
        click.echo(f"Migrated Arxiv config to {config_path}")
    if from_frontier:
        count = migrate_frontier_state(from_frontier, ".state/seen.json")
        click.echo(f"Merged {count} frontier state records into .state/seen.json")


@cli.command()
@click.option("--config", "config_path", default="config.yaml", help="Config YAML path")
def validate(config_path):
    errors = Config.validate(config_path)
    if errors:
        click.echo("Validation errors:\n" + "\n".join(f"  - {e}" for e in errors), err=True)
        sys.exit(1)
    else:
        click.echo("Configuration is valid.")
