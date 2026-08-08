import json
import random
import threading
import time
from pathlib import Path

from benchmark.connection import CognoDBConnection


# ============================================================
# MIXED WORKLOAD CONFIGURATION
# ============================================================

CLIENTS = 10
DURATION_SECONDS = 60

READ_PERCENTAGE = 80
WRITE_PERCENTAGE = 20

MAX_RETRIES = 5
RETRY_BASE_DELAY = 0.05


# ============================================================
# GET PAPER IDS
# ============================================================

def get_paper_ids(db, limit=100):
    rows = db.run_query(
        """
        MATCH (p:Paper)
        RETURN p.id AS id
        LIMIT $limit
        """,
        {"limit": limit},
    )

    return [row["id"] for row in rows]


# ============================================================
# READ OPERATION
# ============================================================

def run_read(db, paper_id):
    db.run_query(
        """
        MATCH (p:Paper {id: $paper_id})
        RETURN p.id AS id
        """,
        {"paper_id": paper_id},
    )


# ============================================================
# WRITE OPERATION
# ============================================================

def run_write(db, paper_id):
    db.run_query(
        """
        MATCH (p:Paper {id: $paper_id})
        SET p.benchmark_updated = true
        RETURN p.id AS id
        """,
        {"paper_id": paper_id},
    )


# ============================================================
# RETRY TRANSIENT TRANSACTION ERRORS
# ============================================================

def run_with_retry(operation, db, paper_id):
    for attempt in range(MAX_RETRIES):
        try:
            operation(db, paper_id)
            return True

        except Exception as error:
            error_text = str(error)

            retryable = (
                "TransientError" in error_text
                or "DeadlockDetected" in error_text
                or "transaction conflict" in error_text
            )

            if not retryable:
                print(
                    f"Non-retryable error: "
                    f"{type(error).__name__}: {error}"
                )
                return False

            if attempt == MAX_RETRIES - 1:
                print(
                    f"Operation failed after "
                    f"{MAX_RETRIES} retries: {error}"
                )
                return False

            delay = RETRY_BASE_DELAY * (attempt + 1)
            time.sleep(delay)

    return False


# ============================================================
# WORKER THREAD
# ============================================================

def worker(paper_ids, results, lock, stop_event, worker_id):
    db = None

    local_operations = 0
    local_reads = 0
    local_writes = 0
    local_failures = 0

    try:
        db = CognoDBConnection()

        while not stop_event.is_set():

            paper_id = random.choice(paper_ids)

            # Decide whether this operation is a read or write.
            if random.randint(1, 100) <= READ_PERCENTAGE:

                success = run_with_retry(
                    run_read,
                    db,
                    paper_id,
                )

                if success:
                    local_reads += 1
                    local_operations += 1
                else:
                    local_failures += 1

            else:

                success = run_with_retry(
                    run_write,
                    db,
                    paper_id,
                )

                if success:
                    local_writes += 1
                    local_operations += 1
                else:
                    local_failures += 1

    except Exception as error:

        print(
            f"WORKER {worker_id} CRASHED: "
            f"{type(error).__name__}: {error}"
        )

    finally:

        if db is not None:
            db.close()

        with lock:
            results["operations"] += local_operations
            results["reads"] += local_reads
            results["writes"] += local_writes
            results["failures"] += local_failures


# ============================================================
# RUN MIXED WORKLOAD
# ============================================================

def run_mixed_workload():

    print("========================================")
    print("CognoDB Mixed Read/Write Workload")
    print("========================================")

    print(f"Clients: {CLIENTS}")
    print(
        f"Read/Write mix: "
        f"{READ_PERCENTAGE}% / {WRITE_PERCENTAGE}%"
    )
    print(f"Duration: {DURATION_SECONDS} seconds")
    print()

    # --------------------------------------------------------
    # Get Paper IDs before starting workers
    # --------------------------------------------------------

    db = CognoDBConnection()

    try:
        paper_ids = get_paper_ids(db)

    finally:
        db.close()

    if not paper_ids:
        raise RuntimeError(
            "No Paper nodes found in CognoDB."
        )

    print(
        f"Using {len(paper_ids)} Paper IDs."
    )

    print("Starting workload...")

    # --------------------------------------------------------
    # Shared result counters
    # --------------------------------------------------------

    results = {
        "operations": 0,
        "reads": 0,
        "writes": 0,
        "failures": 0,
    }

    lock = threading.Lock()
    stop_event = threading.Event()

    threads = []

    # --------------------------------------------------------
    # Start timer
    # --------------------------------------------------------

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # Start concurrent clients
    # --------------------------------------------------------

    for worker_id in range(1, CLIENTS + 1):

        thread = threading.Thread(
            target=worker,
            args=(
                paper_ids,
                results,
                lock,
                stop_event,
                worker_id,
            ),
            name=f"CognoDB-Worker-{worker_id}",
        )

        thread.start()
        threads.append(thread)

    # --------------------------------------------------------
    # Keep workload running for configured duration
    # --------------------------------------------------------

    try:

        time.sleep(DURATION_SECONDS)

    except KeyboardInterrupt:

        print()
        print("Interrupted by user.")

    finally:

        # Tell all workers to stop.
        stop_event.set()

    # --------------------------------------------------------
    # Wait for every worker to finish
    # --------------------------------------------------------

    for thread in threads:
        thread.join()

    # --------------------------------------------------------
    # Calculate final timing
    # --------------------------------------------------------

    end_time = time.perf_counter()

    elapsed_seconds = end_time - start_time

    total_operations = results["operations"]
    total_reads = results["reads"]
    total_writes = results["writes"]
    total_failures = results["failures"]

    # --------------------------------------------------------
    # Calculate QPS
    # --------------------------------------------------------

    if elapsed_seconds > 0:
        qps = total_operations / elapsed_seconds
    else:
        qps = 0

    # --------------------------------------------------------
    # Calculate actual read/write percentages
    # --------------------------------------------------------

    if total_operations > 0:

        actual_read_percentage = (
            total_reads
            / total_operations
            * 100
        )

        actual_write_percentage = (
            total_writes
            / total_operations
            * 100
        )

    else:

        actual_read_percentage = 0
        actual_write_percentage = 0

    # --------------------------------------------------------
    # Prepare results
    # --------------------------------------------------------

    benchmark_results = {
        "database": "CognoDB",

        "workload": {
            "clients": CLIENTS,
            "duration_seconds": elapsed_seconds,

            "configured_read_percentage": (
                READ_PERCENTAGE
            ),

            "configured_write_percentage": (
                WRITE_PERCENTAGE
            ),

            "actual_read_percentage": (
                actual_read_percentage
            ),

            "actual_write_percentage": (
                actual_write_percentage
            ),
        },

        "operations": {
            "total": total_operations,
            "reads": total_reads,
            "writes": total_writes,
            "failed": total_failures,
        },

        "performance": {
            "qps": qps,
        },
    }

    # --------------------------------------------------------
    # Save JSON results
    # --------------------------------------------------------

    output_dir = Path("results")

    output_dir.mkdir(
        exist_ok=True
    )

    output_file = (
        output_dir
        / "mixed_workload.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            benchmark_results,
            file,
            indent=2,
        )

    # --------------------------------------------------------
    # Display results
    # --------------------------------------------------------

    print()
    print("========================================")
    print("Mixed workload complete!")
    print("========================================")

    print(
        f"Elapsed time: "
        f"{elapsed_seconds:.2f} seconds"
    )

    print(
        f"Clients: {CLIENTS}"
    )

    print(
        f"Total successful operations: "
        f"{total_operations}"
    )

    print(
        f"Reads: "
        f"{total_reads}"
    )

    print(
        f"Writes: "
        f"{total_writes}"
    )

    print(
        f"Failed operations: "
        f"{total_failures}"
    )

    print(
        f"Actual read percentage: "
        f"{actual_read_percentage:.2f}%"
    )

    print(
        f"Actual write percentage: "
        f"{actual_write_percentage:.2f}%"
    )

    print(
        f"QPS: "
        f"{qps:.2f}"
    )

    print(
        f"Results saved to: "
        f"{output_file}"
    )

    print("========================================")


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    run_mixed_workload()