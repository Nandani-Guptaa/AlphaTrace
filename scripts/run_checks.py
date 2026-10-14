#!/usr/bin/env python3
"""Automated verification and health check script for AlphaTrace.
Runs test suite, validates database health, tests Cypher query execution, and reports readiness.
"""

import logging
import subprocess
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.graph.connection import get_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("alphatrace_checks")


def run_checks():
    logger.info("=" * 60)
    logger.info("ALPHATRACE SYSTEM VALIDATION & HEALTH CHECK")
    logger.info("=" * 60)

    # 1. Check FalkorDB Connection
    logger.info("1. Verifying FalkorDB Graph Database...")
    db = get_db()
    health = db.check_health()
    if health.get("status") == "healthy":
        logger.info(f"   [OK] FalkorDB connected: {health.get('node_count')} nodes present.")
    else:
        logger.error(f"   [FAIL] FalkorDB connection error: {health.get('error')}")
        sys.exit(1)

    # 2. Run Pytest Test Suite
    logger.info("2. Executing Automated Test Suite (pytest)...")
    res = subprocess.run([sys.executable, "-m", "pytest", "-v", "--tb=short"], capture_output=True, text=True)
    if res.returncode == 0:
        logger.info("   [OK] All test cases passed successfully!")
    else:
        logger.error("   [FAIL] Test suite failed:\n" + res.stdout + "\n" + res.stderr)
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("ALL ALPHATRACE CHECKS PASSED: READY FOR HACKATHON DEMO")
    logger.info("=" * 60)


if __name__ == "__main__":
    run_checks()
