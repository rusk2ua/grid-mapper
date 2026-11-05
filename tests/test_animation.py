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
