class DistributionNotFound(Exception):
    """Fallback exception used when setuptools isn't available."""


class _Distribution:
    def __init__(self, version: str = "0"):
        self.version = version


def get_distribution(_name: str) -> _Distribution:
    """Return a minimal distribution object with a default version.

    The real ``pkg_resources`` module from ``setuptools`` exposes this helper,
    but our runtime environment may not always provide the package.  The
    simplified implementation keeps dependencies optional while satisfying the
    small subset of functionality that ``fastkml`` requires during imports.
    """

    return _Distribution()
