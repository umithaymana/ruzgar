from bench_pkg.service import handler


def endpoint() -> str:
    return f"{handler()}-ok"
