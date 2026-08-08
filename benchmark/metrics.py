import statistics


def calculate_metrics(latencies):
    if not latencies:
        return {
            "p50_ms": 0,
            "p95_ms": 0,
            "average_ms": 0,
            "min_ms": 0,
            "max_ms": 0,
        }

    sorted_latencies = sorted(latencies)

    def percentile(values, p):
        index = (len(values) - 1) * p
        lower = int(index)
        upper = min(lower + 1, len(values) - 1)

        if lower == upper:
            return values[lower]

        return values[lower] + (
            values[upper] - values[lower]
        ) * (index - lower)

    return {
        "p50_ms": percentile(sorted_latencies, 0.50),
        "p95_ms": percentile(sorted_latencies, 0.95),
        "average_ms": statistics.mean(sorted_latencies),
        "min_ms": min(sorted_latencies),
        "max_ms": max(sorted_latencies),
    }