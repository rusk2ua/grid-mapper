"""--animate: the contest-movie timeline and page."""
import json
import os
import re
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import maidenhead_map as mm  # noqa: E402


def rec(band, date, time, call, grid, home):
    return band, {'call': call, 'grid': grid, 'home_grid': home, 'date': date, 'time': time,
                  'freq': band, 'mode': 'CW', 'extra': []}


def records(*rows):
    out = {}
    for band, r in rows:
        out.setdefault(band, []).append(r)
    return out


# Two weekends, five stops (one grid visited twice), a same-minute burst on
# three bands, an evening session that runs past 0000Z, and a long break.
LOG = records(
    rec('10G', '2026-08-15', '1100', 'W1AAA', 'FN31', 'FN32kp'),
    rec('24G', '2026-08-15', '1100', 'W1AAA', 'FN31', 'FN32kp'),
    rec('47G', '2026-08-15', '1100', 'W1AAA', 'FN31', 'FN32kp'),
    rec('10G', '2026-08-15', '1120', 'K2BBB', 'FN22', 'FN32kp'),
    rec('10G', '2026-08-15', '1400', 'K2BBB', 'FN22', 'FN33aa'),   # moved
    rec('10G', '2026-08-15', '2350', 'VE3CCC', 'FN03', 'FN33aa'),  # long break, then evening
    rec('10G', '2026-08-16', '0030', 'W1AAA', 'FN31', 'FN33aa'),   # 0030Z: still Saturday locally
    rec('10G', '2026-08-16', '1300', 'K2BBB', 'FN22', 'FN32kp'),   # back to the first grid
    rec('24G', '2026-09-19', '1200', 'W1AAA', 'FN31', 'FN23bf'),   # weekend 2
    rec('75G', '2026-09-20', '1500', 'K2BBB', 'FN22', 'FN23bf'),
)


def test_parse_qso_datetime():
    assert mm._parse_qso_datetime('2026-08-15', '0937').hour == 9
    assert mm._parse_qso_datetime('2026-08-15', '937').minute == 37
    assert mm._parse_qso_datetime('2026-08-15', '09:37').minute == 37
    assert mm._parse_qso_datetime('2026-08-15', 937.0).minute == 37
    assert mm._parse_qso_datetime('2026-08-15', '1005.0').hour == 10
    assert mm._parse_qso_datetime('2026-08-15', '09:37:00').minute == 37
    for bad in (('2026-08-15', ''), ('2026-08-15', '2575'), ('bogus', '0900'), (None, '0900')):
        assert mm._parse_qso_datetime(*bad) is None


def test_timeline_order_stops_days_and_weekends():
    d = mm.build_animation_data(LOG)
    ev = d['events']
    assert len(ev) == 10 and d['totals']['skipped'] == 0
    assert all(a['t'] < b['t'] for a, b in zip(ev, ev[1:])), "events must play strictly in order"
    assert [s['grid'] for s in d['stops']] == ['FN32KP', 'FN33AA', 'FN32KP', 'FN23BF']
    # 0030Z on the 16th is Saturday evening at FN33 (local solar time), so 4 days, not 5.
    assert [x['label'] for x in d['days']] == ['Sat Aug 15', 'Sun Aug 16', 'Sat Sep 19', 'Sun Sep 20']
    assert [x['weekend'] for x in d['days']] == [1, 1, 2, 2]
    assert ev[6]['day'] == 0
    kinds = [g['kind'] for g in d['segments']]
    assert kinds.count('weekend') == 1 and 'idle' in kinds and kinds.count('move') == 2


def test_duration_hits_the_target_and_bursts_stay_apart():
    d = mm.build_animation_data(LOG, target_seconds=60)
    assert d['duration'] == pytest.approx(60, abs=0.05)
    burst = [e['t'] for e in d['events'][:3]]
    assert burst[1] - burst[0] >= mm._ANIM_MIN_SPACING - 1e-9
    assert burst[2] - burst[1] >= mm._ANIM_MIN_SPACING - 1e-9
    assert d['clock'][0][1] == d['events'][0]['utc']


def test_default_length_scales_with_the_log():
    assert mm.default_animation_seconds(10, 0) == 40
    assert mm.default_animation_seconds(249, 10) == pytest.approx(129.7)
    assert mm.default_animation_seconds(5000, 50) == 150


def test_band_colors_are_fixed_per_band():
    only_24 = mm._animation_band_styles(['24G'])
    full = {b['band']: b for b in mm._animation_band_styles(['10G', '24G', '47G'])}
    assert only_24[0]['color'] == full['24G']['color'] == '#d95926'
    # Non-contest bands take unused contest styles, in frequency order.
    mixed = mm._animation_band_styles(['5.7G', '10G', '2m'])
    assert [b['band'] for b in mixed] == ['2m', '5.7G', '10G']
    assert mixed[2]['color'] == '#3987e5'
    assert len({(b['color'], b['marker']) for b in mixed}) == 3


def test_contacts_without_time_or_grids_are_skipped():
    log = records(rec('10G', '2026-08-15', '1100', 'W1AAA', 'FN31', 'FN32'),
                  rec('10G', '2026-08-15', '', 'W1BBB', 'FN31', 'FN32'),
                  rec('10G', '2026-08-15', '1105', 'W1CCC', 'FN31', None))
    d = mm.build_animation_data(log)
    assert d['totals']['qsos'] == 1 and d['totals']['skipped'] == 2
    # ...unless a fallback operating grid fills the gap.
    assert mm.build_animation_data(log, fallback_home_grid='FN32')['totals']['qsos'] == 2
    assert mm.build_animation_data(records(rec('10G', '', '', 'W1AAA', 'FN31', 'FN32'))) is None


def test_zoom_levels_are_three_consecutive_steps():
    z = mm.build_animation_data(LOG)['zooms']
    assert z['region'] + 1 == z['area'] == z['local'] - 1


def test_page_escapes_log_text(tmp_path, monkeypatch):
    monkeypatch.setattr(mm, '_animation_background', lambda *a, **k: {})
    log = records(rec('10G', '2026-08-15', '1100', '</script><b>X', 'FN31', 'FN32'),
                  rec('10G', '2026-08-15', '1105', 'W1AAA', 'FN31', 'FN32'))
    out = tmp_path / 'movie.html'
    assert mm.create_animation_html(log, 'K2UA', output_file=str(out), contest='ARRL-10-GHZ') == str(out)
    page = out.read_text(encoding='utf-8')
    assert page.count('</script>') == 2           # Leaflet's and ours, nothing from the log
    data = json.loads(re.search(r'const DATA = (.*?);\n', page).group(1))
    assert data['title'] == 'K2UA · ARRL 10 GHz and Up 2026'
    assert data['events'][0]['call'] == '</script><b>X'


def test_cli_animate_only(tmp_path, monkeypatch):
    monkeypatch.setattr(mm, '_animation_background', lambda *a, **k: {})
    log = tmp_path / 'k1abc.log'
    log.write_text('START-OF-LOG: 3.0\nCONTEST: ARRL-10-GHZ\nCALLSIGN: K1ABC\n'
                   'QSO: 10G CW 2026-08-15 1100 K1ABC FN32kp W1AAA FN31pr\n'
                   'QSO: 24G CW 2026-08-15 1103 K1ABC FN32kp W1AAA FN31pr\n'
                   'QSO: 10G CW 2026-08-15 1500 K1ABC FN33aa K2BBB FN22\n'
                   'END-OF-LOG:\n')
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(sys, 'argv', ['maidenhead_map.py', str(log), '--animate-only', '--animate-seconds', '30'])
    mm.main()
    assert sorted(p.name for p in tmp_path.iterdir()) == ['K1ABC_contest_animation.html', 'k1abc.log']
    data = json.loads(re.search(r'const DATA = (.*?);\n',
                                (tmp_path / 'K1ABC_contest_animation.html').read_text(encoding='utf-8')).group(1))
    assert data['duration'] == pytest.approx(30, abs=0.05)
    assert [s['grid'] for s in data['stops']] == ['FN32KP', 'FN33AA']


def test_movie_bundles_leaflet(tmp_path, monkeypatch):
    """A saved movie must play without reaching a CDN."""
    for name in ('leaflet.js', 'leaflet.css'):
        assert os.path.isfile(os.path.join(mm._LEAFLET_DIR, name)), \
            f"vendor/leaflet/{name} is missing: the movie would fall back to the CDN"
    monkeypatch.setattr(mm, '_animation_background', lambda *a, **k: {})
    out = tmp_path / 'movie.html'
    mm.create_animation_html(LOG, 'K2UA', output_file=str(out))
    page = out.read_text(encoding='utf-8')
    assert 'unpkg.com' not in page
    assert 'Leaflet 1.9.4' in page and '.leaflet-container' in page
    assert page.count('</script>') == 2           # the bundled library's and ours


def test_movie_falls_back_to_the_cdn_without_the_bundle(tmp_path, monkeypatch):
    monkeypatch.setattr(mm, '_animation_background', lambda *a, **k: {})
    monkeypatch.setattr(mm, '_LEAFLET_DIR', str(tmp_path / 'missing'))
    out = tmp_path / 'movie.html'
    mm.create_animation_html(LOG, 'K2UA', output_file=str(out))
    page = out.read_text(encoding='utf-8')
    assert 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js' in page
    assert 'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css' in page


def test_street_tiles_are_skipped_for_saved_files():
    # OpenStreetMap answers tile requests without a Referer (a page opened from
    # a file) with "Access blocked" images, so both pages skip them there.
    for template in (mm._ANIMATION_PAGE_TEMPLATE, mm._LEAFLET_PAGE_TEMPLATE):
        assert "location.protocol" in template and "'file:'" in template


# ------------------------------------------------------------------ running score

@pytest.mark.parametrize("home, grid, points", [
    # Reference values from 10ghz-log-analyzer's calculate_distance, rounded up.
    ('FN32KP', 'FN31PR', 108), ('FN32KP', 'FN31', 194), ('EN81UK', 'EN82OA', 77), ('FN23BF', 'FN12EU', 149),
])
def test_points_match_the_analyzer(home, grid, points):
    assert mm._arrl10_points(home, grid, '10G') == points


@pytest.mark.parametrize("band, multiplier", [
    ('10G', 1), ('24G', 2), ('47G', 3), ('75G', 4), ('123G', 5), ('134G', 5), ('241G', 5), ('300G', 5),
    ('5.7G', 1),
])
def test_band_multipliers_follow_the_rules(band, multiplier):
    assert mm._arrl10_multiplier(band) == multiplier


def test_running_score_counts_each_call_once_per_band():
    log = records(rec('10G', '2026-08-15', '1100', 'W1AAA', 'FN31PR', 'FN32KP'),
                  rec('10G', '2026-08-15', '1130', 'W1AAA', 'FN31PR', 'FN32KP'),    # same call, same band
                  rec('24G', '2026-08-15', '1135', 'W1AAA', 'FN31PR', 'FN32KP'))    # new band: bonus again
    d = mm.build_animation_data(log, contest='ARRL-10-GHZ')
    assert [e['sc'] for e in d['events']] == [108 + 100, 108 + 100 + 108, 108 + 100 + 108 + 216 + 100]
    assert d['scoring'] == {'rules': 'ARRL 10 GHz and Up', 'total': 632}


def test_no_score_for_contests_without_known_rules():
    for contest in (None, 'CQ-WW-VHF'):
        d = mm.build_animation_data(LOG, contest=contest)
        assert d['scoring'] is None and 'sc' not in d['events'][0]


def test_score_line_is_on_the_page(tmp_path, monkeypatch):
    monkeypatch.setattr(mm, '_animation_background', lambda *a, **k: {})
    out = tmp_path / 'movie.html'
    mm.create_animation_html(LOG, 'K2UA', output_file=str(out), contest='ARRL-10-GHZ')
    page = out.read_text(encoding='utf-8')
    assert 'Cumulative Score: <b id="score">0</b>' in page
    data = json.loads(re.search(r'const DATA = (.*?);\n', page).group(1))
    assert data['scoring']['total'] == data['events'][-1]['sc'] > 0


# The analyzer's reference rover log (10ghz-log-analyzer tests/test_vhf.py
# JUNE_ROVER): 14 QSO points x (7 band-grids + 2 grids activated) = 126.
JUNE_ROVER = records(
    rec('50',  '2026-06-13', '1800', 'W2FU', 'FN13', 'FN12'),
    rec('144', '2026-06-13', '1801', 'W2FU', 'FN13', 'FN12'),
    rec('902', '2026-06-13', '1802', 'W2FU', 'FN13', 'FN12'),
    rec('10G', '2026-06-13', '1803', 'W2FU', 'FN13', 'FN12'),
    rec('144', '2026-06-13', '1804', 'W2FU', 'FN13', 'FN12'),       # duplicate
    rec('144', '2026-06-13', '1805', 'KF2MR/R', 'FN22', 'FN12'),
    rec('144', '2026-06-13', '1900', 'KF2MR/R', 'FN02', 'FN12'),    # the other rover moved
    rec('144', '2026-06-14', '0100', 'W2FU', 'FN13', 'FN13'),       # this rover moved
    rec('222', '2026-06-14', '0101', 'N2ZN', 'FN13', 'FN13'),
    rec('144', '2026-06-16', '1200', 'K2TER', 'FN13', 'FN13'),      # after the contest
)


def test_vhf_rover_score_matches_the_analyzer():
    d = mm.build_animation_data(JUNE_ROVER, contest='ARRL-VHF-JUN', category='R')
    assert d['scoring'] == {'rules': 'ARRL June VHF', 'total': 126}
    assert d['events'][-1]['sc'] == 126
    fixed = mm.build_animation_data(JUNE_ROVER, contest='ARRL-VHF-JUN', category='SO')
    assert fixed['scoring']['total'] == 14 * 7


def test_january_points_and_category_band_limits():
    jan = records(rec('144', '2025-01-18', '1900', 'W2FU', 'FN13', 'FN12'),
                  rec('10G', '2025-01-18', '1901', 'W2FU', 'FN13', 'FN12'),
                  rec('1.2G', '2025-01-18', '1902', 'W2FU', 'FN13', 'FN12'))
    d = mm.build_animation_data(jan, contest='ARRL-VHF-JAN')
    assert d['scoring']['total'] == (1 + 8 + 4) * 3
    so3b = mm.build_animation_data(jan, contest='ARRL-VHF-JAN', category='SO3B')
    assert so3b['scoring']['total'] == 1 * 1


def test_analog_only_drops_digital_modes():
    log = records(rec('144', '2026-06-13', '1800', 'W2FU', 'FN13', 'FN12'),
                  rec('432', '2026-06-13', '1801', 'N2ZN', 'FN13', 'FN12'))
    log['432'][0]['mode'] = 'DG'
    assert mm.build_animation_data(log, contest='ARRL-VHF-JUN')['scoring']['total'] == 3 * 2
    assert mm.build_animation_data(log, contest='ARRL-VHF-JUN',
                                   analog_only=True)['scoring']['total'] == 1


def test_grids_activated():
    d = mm.build_animation_data(JUNE_ROVER, contest='ARRL-VHF-JUN', category='R')
    assert [a['grid'] for a in d['activated']] == ['FN12', 'FN13']
    assert d['activated'][0]['bounds'] == [[42, -78], [43, -76]]
    assert d['activated'][0]['t'] == d['events'][0]['t']
    one_grid = records(rec('144', '2026-06-13', '1800', 'W2FU', 'FN13', 'FN12'))
    assert mm.build_animation_data(one_grid)['activated'] == []


def test_vhf_category_from_header():
    assert mm.vhf_category({'HQ-CATEGORY': 'Classic Rover'}) == 'R'
    assert mm.vhf_category({'CATEGORY-STATION': 'ROVER-LIMITED'}) == 'RL'
    assert mm.vhf_category({'CATEGORY-BAND': '3-BAND'}) == 'SO3B'
    assert mm.vhf_category({}, 'K2UA/R') == 'R'
    assert mm.vhf_category({}, 'K2UA') == 'SO'
    assert mm.vhf_analog_only({'X-ANALOG-ONLY': 'YES'})


def test_band_labels():
    assert [mm.band_label(b) for b in ('6m', '50', '2m', '144', '70cm', '1.2G', '23cm', '3cm',
                                       '10G', '75G', '4mm', '123G', '142G', '40m')] == \
        ['50 MHz', '50 MHz', '144 MHz', '144 MHz', '432 MHz', '1.2 GHz', '1.2 GHz', '10 GHz',
         '10 GHz', '78 GHz', '78 GHz', '122 GHz', '134 GHz', '40m']


def test_every_band_style_is_unique():
    styles = mm._ANIMATION_BAND_STYLES
    for i, (_, color, dash, marker) in enumerate(styles):
        for _, other_color, other_dash, other_marker in styles[i + 1:]:
            if color == other_color:
                assert dash != other_dash and marker != other_marker


def test_rover_call_is_file_safe(tmp_path, monkeypatch):
    monkeypatch.setattr(mm, '_animation_background', lambda *a, **k: {})
    monkeypatch.chdir(tmp_path)
    assert mm.create_animation_html(JUNE_ROVER, 'K2UA/R', contest='ARRL-VHF-JUN') == \
        'K2UA-R_contest_animation.html'
    page = (tmp_path / 'K2UA-R_contest_animation.html').read_text(encoding='utf-8')
    assert 'id="act-line"' in page and 'ARRL June VHF 2026' in page


def test_interactive_map_data_cannot_end_its_script_block(tmp_path):
    out = tmp_path / 'map.html'
    data = {'title': 'x', 'note': '</script><img src=x onerror=alert(1)> & more'}
    mm._write_leaflet_html(data, str(out), 'K2UA')
    page = out.read_text(encoding='utf-8')
    assert '</script><img' not in page
    blob = re.search(r"const DATA = (.*?);\n", page).group(1)
    assert json.loads(blob)['note'] == data['note']
