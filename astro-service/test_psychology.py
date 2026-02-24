"""Tests for psychology.py — per-user tag extraction."""
import pytest
from psychology import extract_sm_dynamics, extract_critical_degrees, compute_element_profile, extract_retrograde_karma, extract_karmic_axis


def _chart(**kwargs):
    return {k: v for k, v in kwargs.items()}


def test_sm_natural_dom_sun_pluto_conjunction():
    chart = _chart(sun_degree=10.0, pluto_degree=14.0)
    tags = extract_sm_dynamics(chart)
    assert "Natural_Dom" in tags

def test_sm_natural_dom_mars_pluto_trine():
    chart = _chart(mars_degree=10.0, pluto_degree=130.0)
    tags = extract_sm_dynamics(chart)
    assert "Natural_Dom" in tags

def test_sm_sadist_dom_mars_pluto_square():
    chart = _chart(mars_degree=10.0, pluto_degree=100.0)
    tags = extract_sm_dynamics(chart)
    assert "Sadist_Dom" in tags

def test_sm_anxious_sub_moon_pluto_conjunction():
    chart = _chart(moon_degree=200.0, pluto_degree=204.0)
    tags = extract_sm_dynamics(chart)
    assert "Anxious_Sub" in tags

def test_sm_brat_sub_mercury_mars_square():
    chart = _chart(mercury_degree=0.0, mars_degree=90.0)
    tags = extract_sm_dynamics(chart)
    assert "Brat_Sub" in tags

def test_sm_service_sub_venus_in_taurus():
    chart = _chart(venus_sign="taurus")
    tags = extract_sm_dynamics(chart)
    assert "Service_Sub" in tags

def test_sm_masochist_sub_mars_neptune_opposition():
    chart = _chart(mars_degree=0.0, neptune_degree=180.0)
    tags = extract_sm_dynamics(chart)
    assert "Masochist_Sub" in tags

def test_sm_no_tags_empty_chart():
    tags = extract_sm_dynamics({})
    assert tags == []

def test_sm_daddy_dom_saturn_sun_conjunction():
    chart = _chart(saturn_degree=50.0, sun_degree=54.0)
    tags = extract_sm_dynamics(chart)
    assert "Daddy_Dom" in tags

def test_critical_karmic_venus_29_degree():
    # 269.5 % 30 = 29.5 → Karmic_Crisis
    chart = _chart(venus_degree=269.5)
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Karmic_Crisis_VENUS" in tags

def test_critical_blind_sun_0_degree():
    chart = _chart(sun_degree=0.5)
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Blind_Impulse_SUN" in tags

def test_critical_moon_excluded_tier23():
    chart = _chart(moon_degree=269.5)
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Karmic_Crisis_MOON" not in tags

def test_critical_moon_included_tier1():
    chart = _chart(moon_degree=269.5)
    tags = extract_critical_degrees(chart, is_exact_time=True)
    assert "Karmic_Crisis_MOON" in tags

def test_critical_asc_excluded_tier23():
    chart = _chart(asc_degree=0.3)
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Blind_Impulse_ASC" not in tags

def test_critical_asc_included_tier1():
    chart = _chart(asc_degree=0.3)
    tags = extract_critical_degrees(chart, is_exact_time=True)
    assert "Blind_Impulse_ASC" in tags

def test_critical_normal_degree_no_tag():
    chart = _chart(sun_degree=91.0)  # 91 % 30 = 1.0, not < 1.0 and not >= 29.0
    tags = extract_critical_degrees(chart, is_exact_time=False)
    assert "Blind_Impulse_SUN" not in tags
    assert "Karmic_Crisis_SUN" not in tags

def test_critical_no_degrees_no_tags():
    tags = extract_critical_degrees({}, is_exact_time=True)
    assert tags == []

def test_element_profile_all_fire_weighted():
    # Even without Moon (no exact time), all fire signs get fire scores
    chart = {
        "sun_sign": "aries",        # fire, 3.0
        "mercury_sign": "sagittarius",  # fire, 2.0
        "venus_sign": "aries",      # fire, 2.0
        "mars_sign": "leo",         # fire, 2.0
        "jupiter_sign": "sagittarius",  # fire, 1.0
        "saturn_sign": "aries",     # fire, 1.0
    }
    profile = compute_element_profile(chart, is_exact_time=False)
    assert profile["scores"]["Fire"] == 11.0   # 3+2+2+2+1+1 without moon/asc
    assert profile["scores"]["Earth"] == 0.0
    assert "Fire" in profile["dominant"]   # 11 >= 7
    assert "Earth" in profile["deficiency"]  # 0 <= 1

def test_element_profile_mixed():
    # Without exact time: sun(3)+mars(2)=5 fire, jupiter(1)=1 earth, mercury(2)+saturn(1)=3 air, venus(2)=2 water
    chart = {
        "sun_sign": "aries",        # fire, 3.0
        "moon_sign": "taurus",       # earth -- excluded (no exact time)
        "mercury_sign": "gemini",    # air, 2.0
        "venus_sign": "cancer",      # water, 2.0
        "mars_sign": "leo",          # fire, 2.0
        "jupiter_sign": "virgo",     # earth, 1.0
        "saturn_sign": "libra",      # air, 1.0
        "uranus_sign": "scorpio",    # excluded
        "neptune_sign": "sagittarius", # excluded
        "pluto_sign": "capricorn",   # excluded
    }
    profile = compute_element_profile(chart, is_exact_time=False)
    assert profile["scores"]["Fire"] == 5.0   # sun(3)+mars(2)
    assert profile["scores"]["Earth"] == 1.0  # jupiter(1)
    assert profile["scores"]["Air"] == 3.0    # mercury(2)+saturn(1)
    assert profile["scores"]["Water"] == 2.0  # venus(2)
    assert "Earth" in profile["deficiency"]   # 1.0 <= 1.0
    assert profile["dominant"] == []          # nothing >= 7

def test_element_profile_missing_planets_graceful():
    chart = {"sun_sign": "aries"}  # only sun known, weight=3.0
    profile = compute_element_profile(chart, is_exact_time=False)
    assert profile["scores"]["Fire"] == 3.0
    assert "Earth" in profile["deficiency"]
    assert "Air" in profile["deficiency"]
    assert "Water" in profile["deficiency"]

def test_element_profile_unknown_sign_ignored():
    chart = {"sun_sign": "aries", "moon_sign": None}
    profile = compute_element_profile(chart, is_exact_time=False)
    assert profile["scores"]["Fire"] == 3.0  # only sun counted (moon=None)


def test_element_profile_moon_counted_with_exact_time():
    chart = {"sun_sign": "aries", "moon_sign": "leo"}  # both fire
    profile_inexact = compute_element_profile(chart, is_exact_time=False)
    profile_exact   = compute_element_profile(chart, is_exact_time=True)
    assert profile_inexact["scores"]["Fire"] == 3.0   # only sun (moon excluded)
    assert profile_exact["scores"]["Fire"] == 6.0     # sun(3)+moon(3)


def test_element_profile_dominant_requires_score_7():
    # Sun(3) + Moon(3) = 6 -- NOT dominant
    chart = {"sun_sign": "aries", "moon_sign": "leo"}
    profile = compute_element_profile(chart, is_exact_time=True)
    assert profile["dominant"] == []   # 6 < 7

    # Sun(3) + Moon(3) + Mercury(2) = 8 -- dominant
    chart2 = {"sun_sign": "aries", "moon_sign": "leo", "mercury_sign": "sagittarius"}
    profile2 = compute_element_profile(chart2, is_exact_time=True)
    assert "Fire" in profile2["dominant"]


# -- extract_retrograde_karma --------------------------------------------------

def test_retrograde_venus_tag():
    chart = {"venus_rx": True}
    tags = extract_retrograde_karma(chart)
    assert "Karmic_Love_Venus_Rx" in tags


def test_retrograde_mars_tag():
    chart = {"mars_rx": True}
    tags = extract_retrograde_karma(chart)
    assert "Suppressed_Anger_Mars_Rx" in tags


def test_retrograde_mercury_tag():
    chart = {"mercury_rx": True}
    tags = extract_retrograde_karma(chart)
    assert "Internal_Dialogue_Mercury_Rx" in tags


def test_retrograde_no_rx_no_tags():
    chart = {"venus_rx": False, "mars_rx": False, "mercury_rx": False}
    tags = extract_retrograde_karma(chart)
    assert tags == []


def test_retrograde_missing_keys_no_error():
    tags = extract_retrograde_karma({})
    assert tags == []


# -- extract_karmic_axis -------------------------------------------------------

def test_karmic_axis_sign_tag():
    """North Node Gemini → Axis_Sign_Gemini_Sag tag."""
    chart = _chart(north_node_sign="Gemini")
    tags = extract_karmic_axis(chart)
    assert "Axis_Sign_Gemini_Sag" in tags

def test_karmic_axis_north_node_sign_tag():
    """Should produce North_Node_Sign_Gemini."""
    chart = _chart(north_node_sign="Gemini")
    tags = extract_karmic_axis(chart)
    assert "North_Node_Sign_Gemini" in tags

def test_karmic_axis_house_tier1():
    """Tier 1 with ASC Aries + NN Cancer → house = (3-0)%12+1 = 4 → Axis_House_4_10."""
    chart = _chart(north_node_sign="Cancer", ascendant_sign="Aries", data_tier=1)
    tags = extract_karmic_axis(chart)
    assert "Axis_House_4_10" in tags
    assert "North_Node_House_4" in tags

def test_karmic_axis_no_house_tier2():
    """Tier 2 should NOT produce house axis tags even if ascendant_sign is present."""
    chart = _chart(north_node_sign="Leo", ascendant_sign="Aries", data_tier=2)
    tags = extract_karmic_axis(chart)
    house_tags = [t for t in tags if "House" in t]
    assert house_tags == []

def test_karmic_axis_empty_chart():
    """Empty chart returns no tags."""
    tags = extract_karmic_axis({})
    assert tags == []


# ── Essential Dignities ───────────────────────────────────────────────────────

from psychology import ESSENTIAL_DIGNITIES, evaluate_planet_dignity


class TestEssentialDignities:
    def test_all_four_planets_present(self):
        for p in ("Sun", "Moon", "Venus", "Mars"):
            assert p in ESSENTIAL_DIGNITIES

    def test_venus_in_scorpio_is_detriment(self):
        assert evaluate_planet_dignity("Venus", "scorpio") == "Detriment"

    def test_mars_in_capricorn_is_exaltation(self):
        assert evaluate_planet_dignity("Mars", "capricorn") == "Exaltation"

    def test_moon_in_taurus_is_exaltation(self):
        assert evaluate_planet_dignity("Moon", "taurus") == "Exaltation"

    def test_sun_in_aquarius_is_detriment(self):
        assert evaluate_planet_dignity("Sun", "aquarius") == "Detriment"

    def test_venus_in_libra_is_dignity(self):
        assert evaluate_planet_dignity("Venus", "libra") == "Dignity"

    def test_unknown_planet_is_peregrine(self):
        assert evaluate_planet_dignity("Jupiter", "aries") == "Peregrine"

    def test_unknown_sign_is_peregrine(self):
        assert evaluate_planet_dignity("Sun", "unknown") == "Peregrine"

    def test_title_case_sign_accepted(self):
        """Sign can be "Scorpio" or "scorpio" — both should work."""
        assert evaluate_planet_dignity("Venus", "Scorpio") == "Detriment"

    def test_moon_in_cancer_is_dignity(self):
        assert evaluate_planet_dignity("Moon", "cancer") == "Dignity"


from psychology import MODERN_RULERSHIPS, find_dispositor_chain


class TestDispositorChain:
    def _chart(self, **signs):
        """Build a minimal western_chart with {planet}_sign keys."""
        return {f"{k}_sign": v for k, v in signs.items()}

    def test_rulerships_has_all_12_signs(self):
        expected = {
            "aries", "taurus", "gemini", "cancer", "leo", "virgo",
            "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"
        }
        assert set(MODERN_RULERSHIPS.keys()) == expected

    def test_final_dispositor_self_ruling(self):
        """Venus in Taurus → Venus rules Taurus → Final Dispositor = Venus."""
        chart = self._chart(venus="taurus")
        result = find_dispositor_chain(chart, "Venus")
        assert result["status"] == "final_dispositor"
        assert result["final_dispositor"] == "Venus"
        assert "Venus" in result["chain"]

    def test_final_dispositor_moon_in_cancer(self):
        """Moon in Cancer → self-rules → Final Dispositor = Moon."""
        chart = self._chart(moon="cancer")
        result = find_dispositor_chain(chart, "Moon")
        assert result["status"] == "final_dispositor"
        assert result["final_dispositor"] == "Moon"

    def test_mutual_reception_venus_mars(self):
        """Venus in Aries (ruled by Mars) + Mars in Taurus (ruled by Venus) → MR."""
        chart = self._chart(venus="aries", mars="taurus")
        result = find_dispositor_chain(chart, "Venus")
        assert result["status"] == "mutual_reception"
        assert set(result["mutual_reception"]) == {"Venus", "Mars"}

    def test_mutual_reception_bidirectional(self):
        """Same chart — starting from Mars should also detect the MR."""
        chart = self._chart(venus="aries", mars="taurus")
        result = find_dispositor_chain(chart, "Mars")
        assert result["status"] == "mutual_reception"
        assert set(result["mutual_reception"]) == {"Venus", "Mars"}

    def test_mixed_loop_terminates(self):
        """3+ planets with no resolution → mixed_loop, no infinite loop."""
        # Sun in Capricorn → Saturn; Saturn in Aries → Mars; Mars in Libra → Venus...
        chart = self._chart(sun="capricorn", saturn="aries", mars="libra", venus="gemini")
        result = find_dispositor_chain(chart, "Sun")
        assert result["status"] == "mixed_loop"

    def test_incomplete_when_sign_missing(self):
        """Moon sign is None (Tier 3) → incomplete immediately."""
        chart = {}  # no moon_sign key
        result = find_dispositor_chain(chart, "Moon")
        assert result["status"] == "incomplete"

    def test_chain_records_path(self):
        """Chain list should record all visited planets in order."""
        # Sun in Leo → Sun rules Leo → Final Dispositor immediately
        chart = self._chart(sun="leo")
        result = find_dispositor_chain(chart, "Sun")
        assert result["chain"][0] == "Sun"
        assert result["status"] == "final_dispositor"
