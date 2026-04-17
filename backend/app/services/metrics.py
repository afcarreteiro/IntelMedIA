try:
    from prometheus_client import Counter, Histogram
except ModuleNotFoundError:
    class _NullMetric:
        def labels(self, **_kwargs):
            return self

        def inc(self, _value: float = 1.0):
            return None

        def observe(self, _value: float):
            return None

    def Counter(*_args, **_kwargs):
        return _NullMetric()

    def Histogram(*_args, **_kwargs):
        return _NullMetric()


stream_connections_total = Counter(
    "stream_connections_total",
    "Total real-time streaming websocket connections",
)
stream_messages_total = Counter(
    "stream_messages_total",
    "Total websocket stream messages",
    ["type"],
)
stream_latency_seconds = Histogram(
    "stream_latency_seconds",
    "Latency of streaming pipeline stages",
    ["stage"],
)
