"""Band-label handling: which bands get the OSM street underlay and the
1x2 degree grid-square outlines."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from maidenhead_map import (  # noqa: E402
    band_has_grid_outlines, band_is_osm_eligible, band_min_freq_mhz,
)

UNDERLAY = ["33cm", "23cm", "3cm", "1mm", "902MHz", "915MHz", "3.4GHz", "1.2G", "2.3G",
            "3.4G", "5.7G", "10G", "24G", "47G", "75G", "123G", "134G", "142G", "241G",
            "300G", "2mm", "10 GHz", "78 GHz", "134 GHz", "300 GHz", "1296", "999999G"]
NO_UNDERLAY = ["160m", "80m", "20m", "10m", "6m", "2m", "1.25m", "70cm", "144", "432", "50",
               "28000kHz", "WIDGET", "", "G", "LIGHT"]


@pytest.mark.parametrize("band", UNDERLAY)
def test_underlay_applies_at_902_mhz_and_up(band):
    assert band_is_osm_eligible(band), band


@pytest.mark.parametrize("band", NO_UNDERLAY)
def test_no_underlay_below_902_mhz_or_unknown(band):
    assert not band_is_osm_eligible(band), band


@pytest.mark.parametrize("band, mhz", [
    ("134G", 134000), ("241G", 241000), ("300G", 300000), ("5.7G", 5700),
    ("1.2G", 1200), ("2mm", 134000), ("3.4GHz", 3400), ("144", 144),
])
def test_min_frequency(band, mhz):
    assert band_min_freq_mhz(band) == pytest.approx(mhz)


@pytest.mark.parametrize("band", ["6m", "2m", "70cm", "1.2G", "5.7G", "10G", "134G",
                                  "300G", "10 GHz", "unknown GHz"])
def test_grid_outlines_from_6m_up(band):
    assert band_has_grid_outlines(band), band


@pytest.mark.parametrize("band", ["160m", "20m", "10m", "WIDGET"])
def test_no_grid_outlines_on_hf(band):
    assert not band_has_grid_outlines(band), band


def test_wavelength_labels_not_in_table():
    # 9 mm is ~33 GHz; 5 cm is ~6 GHz; 3 m is ~100 MHz
    assert band_is_osm_eligible("9mm") and band_is_osm_eligible("5cm")
    assert not band_is_osm_eligible("3m")
