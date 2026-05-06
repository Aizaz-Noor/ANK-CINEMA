"""
ANK-Cinema test suite.

Tests cover all pure/deterministic functions in ank_cinema_core.
Run with:  pytest tests/ -v
"""

import sys
import os
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# ── Add project root to import path ───────────────────────────────────────────
sys.path.insert(0, str(Path(__file__).parent.parent))

import ank_cinema_core as core


# ─────────────────────────────────────────────────────────────────────────────
# _size_to_bytes
# ─────────────────────────────────────────────────────────────────────────────
class TestSizeToBytes:
    def test_gigabytes(self):
        assert core._size_to_bytes("1.5 GiB") == int(1.5 * 1024**3)

    def test_megabytes(self):
        assert core._size_to_bytes("700 MiB") == 700 * 1024**2

    def test_kilobytes(self):
        assert core._size_to_bytes("512 KiB") == 512 * 1024

    def test_terabytes(self):
        assert core._size_to_bytes("2 TiB") == 2 * 1024**4

    def test_plain_bytes(self):
        assert core._size_to_bytes("1024") == 1024

    def test_empty_string(self):
        assert core._size_to_bytes("") == 0

    def test_unknown_unit(self):
        assert core._size_to_bytes("5 ZB") == 0

    def test_uppercase_unit(self):
        # Units are lowercased internally so GIB should work too
        result = core._size_to_bytes("1.0 GiB")
        assert result == 1024**3


# ─────────────────────────────────────────────────────────────────────────────
# health
# ─────────────────────────────────────────────────────────────────────────────
class TestHealth:
    def test_excellent_above_50(self):
        style, label = core.health(100)
        assert style == "h.hi"
        assert "Excellent" in label

    def test_good_between_10_and_50(self):
        style, label = core.health(25)
        assert style == "h.mid"
        assert "Good" in label

    def test_low_zero(self):
        style, label = core.health(0)
        assert style == "h.lo"
        assert "Low" in label

    def test_boundary_51_is_excellent(self):
        style, _ = core.health(51)
        assert style == "h.hi"

    def test_boundary_10_is_low(self):
        # seeds == 10 → not > 10 → Low
        style, _ = core.health(10)
        assert style == "h.lo"

    def test_boundary_11_is_good(self):
        style, _ = core.health(11)
        assert style == "h.mid"


# ─────────────────────────────────────────────────────────────────────────────
# enrich_magnet
# ─────────────────────────────────────────────────────────────────────────────
class TestEnrichMagnet:
    BASE_MAGNET = "magnet:?xt=urn:btih:AABBCCDDEEFF00112233445566778899AABBCCDD"

    def test_trackers_are_appended(self):
        enriched = core.enrich_magnet(self.BASE_MAGNET)
        assert "&tr=" in enriched

    def test_no_duplicate_trackers(self):
        # Enrich twice — should still have the same count of &tr= occurrences
        once = core.enrich_magnet(self.BASE_MAGNET)
        twice = core.enrich_magnet(once)
        assert once.count("&tr=") == twice.count("&tr=")

    def test_original_hash_preserved(self):
        enriched = core.enrich_magnet(self.BASE_MAGNET)
        assert "AABBCCDDEEFF00112233445566778899AABBCCDD" in enriched

    def test_all_trackers_from_list_included(self):
        enriched = core.enrich_magnet(self.BASE_MAGNET)
        # Every tracker in the constant list should appear (URL-encoded or raw)
        assert enriched.count("&tr=") == len(core.TRACKERS_LIST)


# ─────────────────────────────────────────────────────────────────────────────
# load_config / save_config
# ─────────────────────────────────────────────────────────────────────────────
class TestConfig:
    def test_load_returns_defaults_when_no_file(self, tmp_path):
        """When config file doesn't exist, defaults should be returned."""
        # Temporarily redirect CONFIG_F to a non-existent path
        original_config_d = core.CONFIG_D
        original_config_f = core.CONFIG_F
        try:
            core.CONFIG_D = tmp_path / "config"
            core.CONFIG_F = core.CONFIG_D / "config.json"
            result = core.load_config()
            assert result["max_results"] == core.DEFAULT_CFG["max_results"]
            assert result["splits"] == core.DEFAULT_CFG["splits"]
        finally:
            core.CONFIG_D = original_config_d
            core.CONFIG_F = original_config_f

    def test_save_and_load_roundtrip(self, tmp_path):
        """Saved config should be loadable and equal to what was saved."""
        original_config_d = core.CONFIG_D
        original_config_f = core.CONFIG_F
        try:
            core.CONFIG_D = tmp_path / "config"
            core.CONFIG_F = core.CONFIG_D / "config.json"
            custom = {**core.DEFAULT_CFG, "max_results": 42, "splits": 8}
            core.save_config(custom)
            loaded = core.load_config()
            assert loaded["max_results"] == 42
            assert loaded["splits"] == 8
        finally:
            core.CONFIG_D = original_config_d
            core.CONFIG_F = original_config_f

    def test_load_merges_with_defaults(self, tmp_path):
        """A partial config file should be merged with defaults."""
        original_config_d = core.CONFIG_D
        original_config_f = core.CONFIG_F
        try:
            core.CONFIG_D = tmp_path / "config"
            core.CONFIG_D.mkdir(parents=True, exist_ok=True)
            core.CONFIG_F = core.CONFIG_D / "config.json"
            # Write a config with only one key
            core.CONFIG_F.write_text(json.dumps({"max_results": 5}))
            loaded = core.load_config()
            assert loaded["max_results"] == 5
            # Other keys should come from DEFAULT_CFG
            assert loaded["splits"] == core.DEFAULT_CFG["splits"]
        finally:
            core.CONFIG_D = original_config_d
            core.CONFIG_F = original_config_f

    def test_load_handles_corrupt_json(self, tmp_path):
        """A corrupt config file should silently fall back to defaults."""
        original_config_d = core.CONFIG_D
        original_config_f = core.CONFIG_F
        try:
            core.CONFIG_D = tmp_path / "config"
            core.CONFIG_D.mkdir(parents=True, exist_ok=True)
            core.CONFIG_F = core.CONFIG_D / "config.json"
            core.CONFIG_F.write_text("{{INVALID JSON}}")
            loaded = core.load_config()
            assert loaded == core.DEFAULT_CFG
        finally:
            core.CONFIG_D = original_config_d
            core.CONFIG_F = original_config_f


# ─────────────────────────────────────────────────────────────────────────────
# find_aria2c
# ─────────────────────────────────────────────────────────────────────────────
class TestFindAria2c:
    def test_returns_local_bin_when_exists(self, tmp_path):
        """Should prefer local bin/ over system PATH."""
        fake_bin = tmp_path / "bin"
        fake_bin.mkdir()
        exe = "aria2c.exe" if core.OS == "Windows" else "aria2c"
        (fake_bin / exe).write_text("fake")

        original_script_dir = core._SCRIPT_DIR
        try:
            core._SCRIPT_DIR = tmp_path
            result = core.find_aria2c()
            assert result is not None
            assert "aria2c" in result.lower()
        finally:
            core._SCRIPT_DIR = original_script_dir

    def test_returns_none_when_missing(self, tmp_path):
        """Should return None when no aria2c is found anywhere."""
        original_script_dir = core._SCRIPT_DIR
        with patch("shutil.which", return_value=None):
            try:
                core._SCRIPT_DIR = tmp_path  # empty dir, no bin/aria2c
                result = core.find_aria2c()
                assert result is None
            finally:
                core._SCRIPT_DIR = original_script_dir


# ─────────────────────────────────────────────────────────────────────────────
# search deduplication logic
# ─────────────────────────────────────────────────────────────────────────────
class TestSearchDedup:
    """Test the deduplication and sorting logic inside search()."""

    def _make_result(self, info_hash: str, name: str, seeds: int, source: str) -> dict:
        return {
            "name": name,
            "size": "1.0 GiB",
            "seeders": seeds,
            "leechers": 0,
            "magnet": f"magnet:?xt=urn:btih:{info_hash}&dn={name}",
            "source": source,
        }

    def test_dedup_removes_same_hash(self):
        """Two results with the same info_hash should be deduplicated."""
        r1 = self._make_result("AAAA1111", "Movie 1080p", 100, "TPB")
        r2 = self._make_result("AAAA1111", "Movie 1080p", 80, "TGX")  # same hash

        with patch.object(core, "scrape_apibay", return_value=[r1]):
            with patch.object(core, "scrape_tgx", return_value=[r2]):
                results = core.search("Movie")

        assert len(results) == 1

    def test_results_sorted_by_seeders_descending(self):
        """Results should come back sorted highest seeds first."""
        r1 = self._make_result("AAAA0001", "Low Seeds",  10, "TPB")
        r2 = self._make_result("BBBB0002", "High Seeds", 500, "TGX")
        r3 = self._make_result("CCCC0003", "Mid Seeds",  150, "TPB")

        with patch.object(core, "scrape_apibay", return_value=[r1, r2]):
            with patch.object(core, "scrape_tgx", return_value=[r3]):
                results = core.search("something")

        assert results[0]["seeders"] == 500
        assert results[1]["seeders"] == 150
        assert results[2]["seeders"] == 10
