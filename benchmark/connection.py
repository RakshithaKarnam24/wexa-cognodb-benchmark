from neo4j import GraphDatabase
from benchmark.config import (
    COGNODB_URI,
    COGNODB_USERNAME,
    COGNODB_PASSWORD,
)

class CognoDBConnection:
    def __init__(self):
        self.driver = GraphDatabase.driver(
            COGNODB_URI,
            auth=(COGNODB_USERNAME, COGNODB_PASSWORD)
        )

    def close(self):
        self.driver.close()

    def run_query(self, query, parameters=None):
        with self.driver.session() as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]