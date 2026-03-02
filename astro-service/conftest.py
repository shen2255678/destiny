"""conftest.py — mock swisseph if the C extension is not installed."""
import sys

try:
    import swisseph  # noqa: F401
except ImportError:
    from unittest.mock import MagicMock

    swe_mock = MagicMock()
    swe_mock.SUN = 0
    swe_mock.MOON = 1
    swe_mock.MERCURY = 2
    swe_mock.VENUS = 3
    swe_mock.MARS = 4
    swe_mock.JUPITER = 5
    swe_mock.SATURN = 6
    swe_mock.URANUS = 7
    swe_mock.NEPTUNE = 8
    swe_mock.PLUTO = 9
    swe_mock.CHIRON = 15
    swe_mock.MEAN_APOG = 12
    swe_mock.TRUE_NODE = 11
    swe_mock.AST_OFFSET = 10000
    swe_mock.FLG_SWIEPH = 2
    swe_mock.GREG_CAL = 1
    swe_mock.SE_ECL_NUT = -1
    sys.modules["swisseph"] = swe_mock
