# CognoDB Benchmark

A Neo4j-based benchmark project for evaluating graph database performance using the **CiteSeer / HepTh citation dataset** and a set of graph query workloads.

## Project Overview

This project benchmarks graph database operations using the Neo4j Python driver. It includes:

* Database connectivity testing
* Dataset loading
* Benchmark query execution
* Query performance metrics
* Mixed workload benchmarking
* JSON-based result generation

## Project Structure

```text
wexa-cognodb-benchmark/
│
├── benchmark/
│   ├── __init__.py
│   ├── config.py
│   ├── connection.py
│   ├── metrics.py
│   ├── queries.py
│   └── runner.py
│
├── data/
│   └── cit-HepTh.txt.gz
│
├── results/
│   ├── cognodb_results.json
│   └── mixed_workload.json
│
├── scripts/
│   ├── load_data.py
│   └── mixed_workload.py
│
├── test_connection.py
├── requirements.txt
└── .gitignore
```

## Requirements

* Python 3.x
* Neo4j database
* pip
* Git

## Installation

Clone the repository:

```bash
git clone https://github.com/RakshithaKarnam24/wexa-cognodb-benchmark.git
cd wexa-cognodb-benchmark
```

Create and activate a virtual environment:

### Windows

```cmd
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```cmd
pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root.

Example:

```env
NEO4J_URI=neo4j://localhost:7687
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your_password
```

**Do not commit `.env` to GitHub.** It is excluded through `.gitignore`.

## Test Database Connection

Run:

```bash
python test_connection.py
```

This verifies that the application can connect to the configured Neo4j database.

## Load Dataset

The project includes the compressed citation dataset:

```text
data/cit-HepTh.txt.gz
```

To load the dataset into Neo4j:

```bash
python scripts/load_data.py
```

## Run the Benchmark

The benchmark runner can be executed using:

```bash
python -m benchmark.runner
```

The benchmark executes the configured graph queries and records performance metrics.

## Mixed Workload

To execute the mixed workload benchmark:

```bash
python scripts/mixed_workload.py
```

## Results

Benchmark results are stored in the `results/` directory.

Current result files include:

```text
results/cognodb_results.json
results/mixed_workload.json
```

These files contain the recorded benchmark measurements and workload results.

## Dependencies

The main Python dependencies are:

```text
neo4j==6.2.0
python-dotenv==1.2.2
pytz==2026.3.post1
```

See `requirements.txt` for the complete dependency specification.

## Notes

* Make sure the Neo4j database is running before executing the benchmark.
* Configure database credentials through environment variables.
* Do not commit passwords, API keys, or other credentials.
* Benchmark results may vary depending on hardware, database configuration, dataset state, and system load.

## Author

**Rakshitha Karnam**

GitHub:
https://github.com/RakshithaKarnam24
