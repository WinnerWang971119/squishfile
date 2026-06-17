"""SquishFile - Local file compressor with smart ML-predicted compression."""
from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("squishfile")
except PackageNotFoundError:  # not installed (e.g. frozen build without metadata)
    __version__ = "0.0.0"
