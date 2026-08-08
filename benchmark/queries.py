# Benchmark query definitions for CognoDB

ONE_HOP = """
MATCH (start:Paper {id: $start_id})-[:CITES]->(neighbor)
RETURN neighbor.id AS id
"""

TWO_HOP = """
MATCH (start:Paper {id: $start_id})
      -[:CITES]->()
      -[:CITES]->(neighbor)
RETURN DISTINCT neighbor.id AS id
"""

THREE_HOP = """
MATCH (start:Paper {id: $start_id})
      -[:CITES]->()
      -[:CITES]->()
      -[:CITES]->(neighbor)
RETURN DISTINCT neighbor.id AS id
"""

POINT_LOOKUP = """
MATCH (p:Paper {id: $paper_id})
RETURN p.id AS id
"""

INDEXED_LOOKUP = """
MATCH (p:Paper {id: $paper_id})
RETURN p.id AS id
"""

AGGREGATION = """
MATCH (p:Paper)
RETURN count(p) AS paper_count
"""