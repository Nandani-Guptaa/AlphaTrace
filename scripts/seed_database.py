#!/usr/bin/env python3
"""CLI utility to seed FalkorDB with AlphaTrace synthetic scenario data."""

import logging
import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))

from app.graph.seed import seed_database

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")

if __name__ == "__main__":
    logging.info("Starting AlphaTrace database seeding...")
    result = seed_database()
    logging.info(f"Seeding completed successfully: {result}")
