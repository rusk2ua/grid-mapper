# Maidenhead Grid Square Contest Map Generator

A Python tool that creates color-coded maps of Maidenhead grid squares from amateur radio contest logs, showing geographic coverage and contact density by frequency band.

## Features

- **Multi-format Support**: Supports both Cabrillo (.cbr/.log) and CSV (.csv) file formats
- **Multi-band Analysis**: Creates separate maps for each frequency band found in the log
- **Automatic Continent Detection**: Auto-selects continents based on grid squares in the log
- **Manual Continent Selection**: Choose specific continents to display
- **Accurate Grid Visualization**: Renders actual grid square boundaries (2° × 1° for 4-character, 5' × 2.5' for 6-character grids)
- **Field Labels**: Displays 2-letter grid field designators (EM, EN, EL, etc.) on the map
- **Contact Density**: Color-coded intensity showing number of contacts per grid square
- **Global Coverage**: Supports all continents with optimized map bounds
- **Local Path Maps**: `--paths` draws a small-area map connecting your home grid to every worked station with a line, labeled with callsign and distance in kilometers (matching ARRL 10 GHz and Up Contest scoring) — great for showing local operators and newcomers what's achievable on VHF/UHF/microwave
- **Multi-Location Detection**: Rover and multi-op logs that report a different home grid on different QSOs (e.g. a rover moving between stops) are automatically split into a separate graphic per band *and* per operating location, instead of mixing locations together on one map
- **Whole-Number Contact Scale**: The contact-density color scale only ever shows whole numbers, since there's no such thing as a fractional contact
- **OpenStreetMap Basemap**: `--osm-basemap` adds a faint (default 30% opacity, adjustable with `--osm-opacity`) OpenStreetMap street-level tile layer underneath every map generated for 902 MHz and higher bands (33cm and up), on top of which all the usual layers still draw normally
- **Interactive HTML Maps**: `--html` generates a website-ready interactive version of every map produced in the same run — hover (or tap, on mobile) a grid square or worked-station point to see a popup with that contact's callsign, date, six-character grid, and other QSO details

## Sample Output

The tool generates high-resolution PNG maps showing:
- Grid squares as colored rectangles with actual geographic boundaries
- Color intensity indicating contact density (light red = few contacts, dark red = many contacts)
- Grid field labels for easy reference
- Callsign and band information in the title
- Geographic features (coastlines, borders, land/ocean)
- Automatic map bounds based on selected continents

## Installation

1. Clone this repository:
```bash
git clone https://github.com/rusk2ua/grid-mapper.git
cd grid-mapper
```

2. Create a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python maidenhead_map.py your_contest_log.cbr
python maidenhead_map.py your_contest_log.csv
```

### Specify Continents
```bash
python maidenhead_map.py your_log.csv --continents north_america europe
python maidenhead_map.py your_log.cbr --continents asia oceania
```

### Local Path Maps (`--paths`)

For small-geographic-area contests like the ARRL 10 GHz and Up Contest, `--paths`
generates an additional map per band showing a line from your home grid square to
each worked station, labeled with callsign and distance in kilometers (the unit
this contest — and most VHF/UHF/microwave distance-based scoring — uses):

```bash
python maidenhead_map.py your_10g_log.cbr --paths
```

Your home grid is auto-detected from the log when possible:
- **Cabrillo**: read from the exchange field on each `QSO:` line (works automatically
  for logs that report your own grid, which is typical for the 10 GHz and Up Contest).
- **CSV**: read from a "my grid" style column (`my_grid`, `mygrid`, `home_grid`,
  `station_grid`, or `source_grid`), if present.

If your log doesn't include your own grid, or you want to override what was
detected, pass it explicitly:

```bash
python maidenhead_map.py your_log.csv --paths --home-grid EM00uf
```

Path maps are saved alongside the regular contact-density maps, named
`{callsign}_{band}_{home_grid}_{region}_grid_paths_map.png`.

### Multi-Location (Rover) Logs

If a log reports a different home grid on different QSOs — typical for a rover
working the same contest from several stops — the tool detects this automatically
and generates a **separate graphic per band and per location**, rather than mixing
several physically distant operating points into one confusing map. This applies
both to the regular contact-density map and, when `--paths` is used, to the path
map (each location gets its own home-grid star and its own set of lines).

```bash
python maidenhead_map.py your_rover_log.cbr --paths
# 10G: 15 operating locations detected (EN91KT, EN91OV, ...); generating a separate map per location
```

Location-specific filenames and titles include the home grid for that stop, e.g.
`K2UA_10G_EN91KT_northeastern_north_america_maidenhead_map.png`. A log with only
one operating location (the common case) is unaffected — filenames stay exactly
as they were before.

To force everything onto a single map regardless of how many locations the log
actually reports, pass `--home-grid` explicitly; this overrides auto-detection
and disables the per-location split.

### OpenStreetMap Basemap (`--osm-basemap`)

For bands at 902 MHz and up (33cm and shorter wavelengths), where contest
activity tends to be very local, `--osm-basemap` adds a faint OpenStreetMap
street-level tile layer underneath the map — useful for orienting a path or
density map against actual roads, towns, and terrain rather than just
coastlines and borders:

```bash
python maidenhead_map.py your_10g_log.cbr --paths --osm-basemap
```

The overlay defaults to 30% opacity so it stays out of the way of the grid
squares, contact paths, and labels drawn on top of it. Adjust it with
`--osm-opacity`:

```bash
python maidenhead_map.py your_10g_log.cbr --paths --osm-basemap --osm-opacity 0.5
```

A few things worth knowing:
- **Band gating is automatic.** `--osm-basemap` only affects maps for bands
  902 MHz and up. Passing it alongside a log that also has, say, 6m or 2m
  contacts doesn't add anything to those bands' maps — only 33cm and up.
- **Requires internet access at run time** to fetch map tiles from
  OpenStreetMap's tile servers. If tiles can't be fetched (no connection,
  tile server unreachable, etc.), the map still generates normally — you
  just get the map without the basemap layer, plus a warning on the
  console.
- **Attribution is automatic.** Any map that includes the OSM layer gets a
  small "© OpenStreetMap contributors" credit in the bottom-right corner,
  as required by OpenStreetMap's tile usage policy.
- Works together with `--paths` and with multi-location/rover logs — every
  graphic generated for an eligible band gets the same underlay.

### Interactive HTML Maps (`--html`)

For putting your maps on a website, `--html` generates an interactive HTML
version of every map produced in the same run — density maps, and path maps
when `--paths` is used — alongside the existing PNGs:

```bash
python maidenhead_map.py your_10g_log.cbr --paths --html
```

The HTML output looks the same as the PNG (same coastlines/borders/land/ocean,
same colors, same `--osm-basemap`/`--osm-opacity` underlay if requested), but
each grid square (on the density map) or worked-station point (on the path
map) is interactive: hovering over it with a mouse, or tapping it on a phone
or tablet, pops up a small card with:
- the callsign, in larger type
- the date (and time, if available) of the contact
- the six-character grid square
- whatever other QSO details are available — mode, frequency, and (for
  Cabrillo logs) any leftover exchange fields the tool couldn't otherwise
  place, such as a serial number

If a grid square or point represents more than one contact, every distinct
callsign worked there is listed. A repeat contact with the *same* station is
collapsed to just the most recent one, with a `(×N)` count next to the
callsign — so, e.g., a station worked 3 times from the same grid shows as
one entry: `W1ABC (×3)`.

Each `.html` file is fully self-contained aside from two small library files
it loads from a public CDN ([Leaflet](https://leafletjs.com/), for the
interactive map) — no server or build step needed, just open the file in a
browser or upload it to your website alongside (or instead of) the PNG. When
`--osm-basemap` is also used, the visitor's own browser fetches the OpenStreetMap
tiles directly, so — like the PNG version — this needs internet access, but
now at *viewing* time rather than at generation time.

Output filenames match the PNG naming exactly, just with a `.html` extension:
`K2UA_10G_EN91KT_northeastern_north_america_grid_paths_map.html`.

CSV-format logs get best-effort popups using whatever columns are present
(callsign, grid, and date if available) — Cabrillo logs carry more detail
(mode, frequency, exchange fields) so their popups are more complete.

### Available Continents
- `north_america` - North America
- `south_america` - South America  
- `europe` - Europe
- `africa` - Africa
- `asia` - Asia
- `oceania` - Australia and Pacific Islands

### File Format Support

#### Cabrillo Format (.cbr, .log)
Standard Cabrillo contest logs with QSO lines:
```
QSO:      50 DG 2025-09-13 1801 K1TO              EL87   WA4GPM            EM90
```

#### CSV Format (.csv)
CSV files with columns for callsign, frequency/band, and grid squares:
```csv
callsign,freq,grid,date,time
K1TO,50,EL87,2025-09-13,1801
WA4GPM,50,EM90,2025-09-13,1801
```

The script automatically detects common CSV column names:
- **Frequency**: freq, frequency, band, freq_mhz
- **Grid**: grid, gridsquare, grid_square, their_grid, dx_grid
- **Callsign**: call, callsign, station_callsign, my_call
- **Home grid** (used by `--paths`): my_grid, mygrid, my_gridsquare, home_grid, station_grid, source_grid

## Command-Line Options

| Option | Description |
| --- | --- |
| `filename` | Contest log file to parse (`.cbr`/`.log` for Cabrillo, `.csv` for CSV) |
| `--continents` | One or more continents to include (auto-detected if omitted) |
| `--paths` | Also generate a local-area path map per band/location (see [Local Path Maps](#local-path-maps---paths)) |
| `--home-grid GRID` | Your 4- or 6-character home grid square; overrides auto-detection and forces a single location (disables the per-location split described in [Multi-Location (Rover) Logs](#multi-location-rover-logs)) |
| `--osm-basemap` | Add a faint OpenStreetMap tile layer underneath every map generated for 902 MHz and higher bands (see [OpenStreetMap Basemap](#openstreetmap-basemap---osm-basemap)) |
| `--osm-opacity 0.0-1.0` | Opacity of the `--osm-basemap` underlay (default `0.3`, i.e. 30%); has no effect without `--osm-basemap` |
| `--html` | Also generate an interactive HTML version of every map produced in this run (see [Interactive HTML Maps](#interactive-html-maps---html)) |

## Output Files

The script creates separate maps for each band (and, for multi-location logs, each
operating location) with descriptive filenames:
- `K1TO_6m_north_america_maidenhead_map.png` - 6m band, North America, single location
- `K1TO_2m_europe_asia_maidenhead_map.png` - 2m band, Europe and Asia, single location
- `K1TO_70cm_world_maidenhead_map.png` - 70cm band, worldwide, single location
- `K5TR_10G_EM00UF_central_north_america_grid_paths_map.png` - 10G band path map (with `--paths`)
- `K2UA_10G_EN91KT_northeastern_north_america_maidenhead_map.png` - 10G band, one of several rover locations
- `K5TR_10G_EM00UF_central_north_america_grid_paths_map.html` - the same 10G path map, interactive (with `--html`)

## Supported Bands

### HF Bands
- **630m** (472-479 kHz)
- **160m** (1.8-2.0 MHz)
- **80m** (3.5-4.0 MHz)
- **60m** (5.3-5.4 MHz)
- **40m** (7.0-7.3 MHz)
- **30m** (10.1-10.15 MHz)
- **20m** (14.0-14.35 MHz)
- **17m** (18.068-18.168 MHz)
- **15m** (21.0-21.45 MHz)
- **12m** (24.89-24.99 MHz)
- **10m** (28.0-29.7 MHz)

### VHF Bands
- **6m** (50-54 MHz)
- **2m** (144-148 MHz)
- **1.25m** (222-225 MHz)

### UHF Bands
- **70cm** (420-450 MHz)
- **33cm** (902-928 MHz)
- **23cm** (1240-1300 MHz)

### Microwave Bands
- **13cm** (2.3-2.45 GHz)
- **9cm** (3.3-3.5 GHz)
- **6cm** (5.65-5.925 GHz)
- **3cm** (10.0-10.5 GHz)
- **1.25cm** (24.0-24.25 GHz)
- **6mm** (47.0-47.2 GHz)
- **4mm** (75.5-81.0 GHz)
- **2.5mm** (119.98-120.02 GHz)
- **2mm** (142-149 GHz)
- **1mm** (241-250 GHz)

> **Note:** Some contest logging software (notably for the ARRL 10 GHz and Up
> Contest) writes the QSO frequency as a bare whole-GHz number instead of a kHz
> frequency — e.g. `10` instead of `10368000`. These are recognized directly and
> mapped to the `10G`, `24G`, `47G`, `75G`, and `123G` band labels used elsewhere
> in this project (see `samples/`).

## Requirements

- Python 3.7+
- matplotlib
- cartopy
- Pillow (used by cartopy for the `--osm-basemap` tile layer)
- scipy (used by cartopy to reproject the `--osm-basemap` tile layer)
- shapely (used to embed background geography in `--html` output)
- numpy (installed with matplotlib)
- Internet access at run time if using `--osm-basemap` (to fetch OpenStreetMap tiles)
- Internet access when *viewing* `--html` output (to load Leaflet from its CDN, and OpenStreetMap tiles if `--osm-basemap` was also used)

## Examples

### Example 1: Auto-detect continents from Cabrillo log
```bash
python maidenhead_map.py contest_log.cbr
```

### Example 2: CSV file with specific continents
```bash
python maidenhead_map.py my_log.csv --continents north_america south_america
```

### Example 3: European contest
```bash
python maidenhead_map.py eu_contest.csv --continents europe
```

### Example 4: Local path map for a 10 GHz and Up contest log
```bash
python maidenhead_map.py 10ghz_contest.cbr --paths
```
Generates the usual contact-density map plus a `..._grid_paths_map.png` for
the 10G band, showing a line from your home grid to each station you worked,
labeled with callsign and distance in km — a quick way to show local operators
and newcomers what's achievable on 10 GHz.

### Example 5: Rover log with multiple locations and bands
```bash
python maidenhead_map.py rover_10ghz_and_up.log --paths --continents north_america
```
Automatically detects every distinct home grid used across the log and every
band worked, then generates one contact-density map and one path map for each
band/location combination — e.g. a rover that operated 5 bands from 15 stops
gets up to 150 graphics, each focused on just that stop's local contacts.

### Example 6: Path map with an OpenStreetMap basemap
```bash
python maidenhead_map.py your_10g_log.cbr --paths --osm-basemap --osm-opacity 0.5
```
Generates the same 10G path map as Example 4, but with a 50%-opacity
OpenStreetMap street-level layer underneath it — useful for showing local
operators exactly which roads and towns their contacts correspond to. The
overlay only applies to bands at 902 MHz and up, so a log with lower-band
contacts would generate those maps without it, unaffected by the flag.

### Example 7: Interactive HTML for a website
```bash
python maidenhead_map.py your_10g_log.cbr --paths --html --osm-basemap
```
Generates the usual PNGs plus a matching `.html` file for each one. Drop the
`.html` files into your website and visitors can hover (or tap, on mobile)
any grid square or worked-station point to see who was worked, when, and
from which six-character grid — a more engaging way to show off local
VHF/UHF/microwave activity than a static image.

## Revision History

| Version | Date | Summary |
| --- | --- | --- |
| 1.5.1 | 2026-10-31 | Fixed `--osm-basemap` and grid-square outlines being skipped for many GHz band labels (`1.2G`, `2.3G`, `3.4G`, `5.7G`, `134G`, `241G`, `300G`, ...). Band labels are now parsed generically, so the street underlay applies to every band at 902 MHz and up. The 2 mm band now starts at 134 GHz; added 134G/241G/300G band codes. |
| 1.5.0 | 2026-08-23 | Added `--html` to generate an interactive, website-ready HTML version of every map produced in a run (density maps and, with `--paths`, path maps). Grid squares / worked-station points become hoverable (desktop) or tappable (mobile) with a popup showing callsign, date, six-character grid, and other QSO details; repeat contacts with the same station collapse to a `(×N)` count. Visually matches the PNG output, including the `--osm-basemap` underlay at the same opacity. Built on Leaflet (loaded from a CDN); background coastlines/borders/land/ocean are embedded per-file from the same Natural Earth data cartopy already uses. Added `shapely` to requirements. |
| 1.4.1 | 2026-08-20 | Fixed `--osm-basemap` crashing with `ImportError: ... requires either pykdtree or scipy` on installs without one of those already present; added `scipy` to requirements. |
| 1.4.0 | 2026-08-20 | Added `--osm-basemap` (with `--osm-opacity`, default 30%) to overlay a faint OpenStreetMap tile layer underneath every map generated for 902 MHz and higher bands, with automatic attribution; added `Pillow` to requirements; fixed a matplotlib figure-leak in contact-density map generation that showed up on large multi-location/multi-band runs. |
| 1.3.0 | 2026-08-20 | Added `--paths` local-area path maps (home grid → each worked station, labeled with callsign + distance in km) for small-area contests like ARRL 10 GHz and Up; added `--home-grid` override; automatic per-band-and-per-location splitting for rover/multi-op logs that report more than one home grid; contact-density color scale now shows whole numbers only; fixed Cabrillo parsing double-counting the operator's own grid as a worked-station contact; fixed bare-GHz frequency values (e.g. `10` for 10 GHz) being mislabeled instead of recognized as `10G`/`24G`/`47G`/`75G`/`123G`. |
| 1.2.0 | 2025-09-17 | Added full HF/VHF/UHF/microwave band support (630m–1mm), Cabrillo standard nomenclature compliance, direct band-name string parsing. |
| 1.1.0 | 2025-09-17 | Added CSV format support with automatic column detection, automatic file-format detection, `--continents` selection, automatic continent detection, dynamic map bounds. |
| 1.0.0 | 2025-09-17 | Initial release: Cabrillo log parsing, multi-band analysis, accurate grid square boundary rendering, contact density visualization. |

See [CHANGELOG.md](CHANGELOG.md) for full change details.

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Designed for Amateur Radio contest analysis and fixed-station grids-worked mapping by band
- Supports worldwide amateur radio activity mapping
- Uses Natural Earth data for geographic features
- Built with matplotlib and cartopy for mapping
- Thanks to George, K5TR, for the distance and direction vector and Open Street Map background suggestion for 10 GHz and up logs.
