import gzip
import time

from benchmark.connection import CognoDBConnection


DATA_FILE = "data/cit-HepTh.txt.gz"
BATCH_SIZE = 100


def get_current_count(db):
    result = db.run_query(
        "MATCH ()-[r:CITES]->() RETURN count(r) AS count"
    )
    return result[0]["count"]


def load_data():
    db = CognoDBConnection()

    start_time = time.perf_counter()

    try:
        current_count = get_current_count(db)

        print(f"📊 Current relationships in database: {current_count}")

        if current_count >= 352807:
            print("✅ Dataset is already fully loaded!")
            return

        skip = current_count
        processed = 0
        batch = []

        print(f"🚀 Resuming from relationship #{skip + 1}")

        with gzip.open(DATA_FILE, "rt", encoding="utf-8") as file:

            for line in file:
                line = line.strip()

                if not line or line.startswith("#"):
                    continue

                source, target = line.split()

                # Skip relationships already loaded
                if skip > 0:
                    skip -= 1
                    continue

                batch.append({
                    "source": source,
                    "target": target
                })

                if len(batch) >= BATCH_SIZE:

                    db.run_query(
                        """
                        UNWIND $rows AS row
                        MERGE (a:Paper {id: row.source})
                        MERGE (b:Paper {id: row.target})
                        MERGE (a)-[:CITES]->(b)
                        """,
                        {"rows": batch}
                    )

                    processed += len(batch)
                    batch.clear()

                    if processed % 1000 == 0:
                        print(
                            f"✅ Added {processed} new relationships "
                            f"(total ≈ {current_count + processed})"
                        )

        if batch:
            db.run_query(
                """
                UNWIND $rows AS row
                MERGE (a:Paper {id: row.source})
                MERGE (b:Paper {id: row.target})
                MERGE (a)-[:CITES]->(b)
                """,
                {"rows": batch}
            )

            processed += len(batch)

        elapsed = time.perf_counter() - start_time

        print("\n🎉 Loading finished!")
        print(f"Added: {processed}")
        print(f"Time: {elapsed:.2f} seconds")

    finally:
        db.close()


if __name__ == "__main__":
    load_data()