import json
import random
import time
from pathlib import Path

from benchmark.connection import CognoDBConnection
from benchmark.metrics import calculate_metrics
from benchmark.queries import (
    ONE_HOP,
    TWO_HOP,
    THREE_HOP,
    POINT_LOOKUP,
    INDEXED_LOOKUP,
    AGGREGATION,
)

WARMUP_RUNS = 10
MEASURED_RUNS = 100


def measure_query(db, query, parameters):
    latencies = []

    print(f"  Warming up ({WARMUP_RUNS} runs)...")

    for _ in range(WARMUP_RUNS):
        db.run_query(query, parameters)

    print(f"  Measuring ({MEASURED_RUNS} runs)...")

    for i in range(MEASURED_RUNS):
        start = time.perf_counter()

        db.run_query(query, parameters)

        end = time.perf_counter()

        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)

        if (i + 1) % 25 == 0:
            print(f"    {i + 1}/{MEASURED_RUNS}")

    return calculate_metrics(latencies)


def get_start_ids(db, limit=100):
    rows = db.run_query(
        """
        MATCH (p:Paper)
        RETURN p.id AS id
        LIMIT $limit
        """,
        {"limit": limit},
    )

    return [row["id"] for row in rows]


def run_benchmark():
    db = CognoDBConnection()

    workloads = {
        "1_hop": ONE_HOP,
        "2_hop": TWO_HOP,
        "3_hop": THREE_HOP,
        "point_lookup": POINT_LOOKUP,
        "indexed_lookup": INDEXED_LOOKUP,
        "aggregation": AGGREGATION,
    }

    results = {}

    try:
        print("Getting start nodes...")
        start_ids = get_start_ids(db)

        if not start_ids:
            raise RuntimeError("No Paper nodes found.")

        print(f"Using {len(start_ids)} start nodes.")
        print()

        for name, query in workloads.items():

            if name == "aggregation":
                parameters = {}
            else:
                paper_id = random.choice(start_ids)

                if name in ("point_lookup", "indexed_lookup"):
                    parameters = {"paper_id": paper_id}
                else:
                    parameters = {"start_id": paper_id}

            print(f"Running {name}...")

            results[name] = measure_query(
                db,
                query,
                parameters,
            )

            print(f"  Result: {results[name]}")
            print()

    finally:
        db.close()

    output_dir = Path("results")
    output_dir.mkdir(exist_ok=True)

    output_file = output_dir / "cognodb_results.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("========================================")
    print("CognoDB benchmark complete!")
    print(f"Results saved to: {output_file}")
    print("========================================")


if __name__ == "__main__":
    run_benchmark()