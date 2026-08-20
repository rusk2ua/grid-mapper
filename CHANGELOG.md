# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.4.1] - 2026-08-20

### Fixed
- `--osm-basemap` crashed with `ImportError: Using image transforms requires
  either pykdtree or scipy` on installs that didn't already have `scipy` or
  `pykdtree` present. Cartopy's tile-reprojection code (used to warp OSM
  tiles onto the map's projection) needs one of the two; added `scipy` to
  `requirements.txt` so a fresh `pip install -r requirements.txt` covers it.
  Existing installs: run `pip install scipy` (or `pip install -r
  requirements.txt` again) inside your virtual environment.

## [1.4.0] - 2026-08-20

### Added
- `--osm-basemap` CLI option: adds a faint OpenStreetMap tile layer underneath
  every map generated for bands at 902 MHz and up (33cm and shorter
  wavelengths — the point at which contest activity tends to be extremely
  local and street-level map context becomes genuinely useful for orienting
  a path or density map). Applies to both the contact-density map and, when
  `--paths` is used, the path map. All existing layers (coastline, borders,
  land/ocean, grid squares, contact paths, labels, etc.) are kept exactly as
  before, drawn on top of the OSM layer.
- `--osm-opacity 0.0-1.0` CLI option to control the OSM underlay's
  transparency (default `0.3`, i.e. 30%, per the original request). Only
  takes effect together with `--osm-basemap`.
- `band_is_osm_eligible()` helper: determines whether a band qualifies for
  the OSM underlay, using the same band-name table as the rest of the script
  plus a fallback regex parse for unrecognized frequency-style labels (e.g.
  `"915MHz"`, `"3.4GHz"`).
- `© OpenStreetMap contributors` attribution is automatically added to the
  bottom-right corner of any map that includes the OSM underlay, per
  OpenStreetMap's tile usage policy.
- Required `Pillow` explicitly in `requirements.txt` (previously pulled in
  transitively via cartopy/matplotlib); `cartopy.io.img_tiles`, used for the
  OSM tile layer, depends on it directly.

### Fixed
- Contact-density map generation (`create_grid_map()`) never closed its
  matplotlib figure after saving. This didn't affect single-map runs, but a
  log that generates many maps in one run — e.g. a rover log split across
  several bands and operating locations — would accumulate open figures for
  the whole run, growing memory usage the longer the run went and eventually
  triggering matplotlib's "more than 20 figures" warning. Path map
  generation already closed its figure correctly; both now do.

### Notes
- `--osm-basemap` requires internet access at run time to fetch map tiles
  from OpenStreetMap's tile servers. If a tile can't be fetched (e.g. no
  connection), the map still generates normally, just without the
  underlay, and a warning is printed.

## [1.3.0] - 2026-08-20

### Added
- `--paths` CLI option: generates a local-area "path map" per band showing your
  home grid station connected by a line to each worked station, labeled with
  callsign and distance in kilometers (matching ARRL 10 GHz and Up Contest
  scoring, which is distance-based in km). Aimed at small-geographic-area
  contests, to show local operators and newcomers what's achievable.
- `--home-grid GRID` CLI option to explicitly set or override the home
  station's grid square used as the origin for `--paths` (falls back to
  auto-detection from the log when omitted); also forces single-location
  treatment for logs that would otherwise be split by location (see below).
- Automatic home-grid detection from Cabrillo QSO exchange fields and from CSV
  files that include a "my grid" style column (`my_grid`, `mygrid`,
  `my_gridsquare`, `home_grid`, `station_grid`, `source_grid`).
- Automatic multi-location detection and splitting: a log that reports more
  than one home grid across its QSOs (e.g. a rover working the contest from
  several stops) now gets a separate contact-density map, and — with
  `--paths` — a separate path map, for every band/location combination,
  instead of merging physically distant operating points into one map.
- `grid_center()`, `haversine_distance()`, `grid_distance_km()`, and
  `grid_distance_miles()` helpers for great-circle distance between grid
  square centers.
- Recognition of whole-GHz frequency shorthand ("10", "24", "47", "75", "123")
  used by some contest logging software for the ARRL 10 GHz and Up Contest,
  mapped to the existing "10G"/"24G"/"47G"/"75G"/"123G" band labels.
- `logs/` added to `.gitignore` so personal contest logs aren't tracked by git.

### Fixed
- Cabrillo parsing no longer counts the logging station's own grid square as a
  worked-station contact. Previously, when a QSO's exchange included the
  operator's own grid (common for 6-character microwave-contest exchanges),
  it was appended to that band's contact list on every QSO line, inflating
  that grid square's contact-density count and coloring.
- Frequency values reported as a bare GHz number (e.g. `10` for 10 GHz) were
  previously mislabeled as, e.g., `10MHz`; they're now correctly recognized as
  the corresponding microwave contest band.

### Changed
- Path map distances are now labeled in kilometers instead of statute miles.
- The contact-density map's colorbar now shows whole-number ticks only, since
  fractional contact counts aren't meaningful.
- `parse_cabrillo_grids()` and `parse_csv_grids()` now return two additional
  values: the detected (overall most common) `home_grid` and a
  `contacts_by_band` dict of `(callsign, grid, qso_home_grid)` tuples per
  band, used to build path maps and to detect/split multi-location logs.
- Path map filenames now always include the home grid
  (`{callsign}_{band}_{home_grid}_{region}_grid_paths_map.png`), and
  contact-density map filenames include the home grid too when a log has
  multiple operating locations, so per-location graphics never collide.
- `setup.py` version synced to match this release (was previously stuck at
  1.0.0 while `CHANGELOG.md` had already moved past it).

## [1.2.0] - 2025-09-17

### Added
- Comprehensive amateur radio band support from 630m to 1mm (241 GHz)
- Full HF band support: 630m, 160m, 80m, 60m, 40m, 30m, 20m, 17m, 15m, 12m, 10m
- Extended VHF/UHF support: 6m, 2m, 1.25m, 70cm, 33cm, 23cm
- Microwave band support: 13cm, 9cm, 6cm, 3cm, 1.25cm, 6mm, 4mm, 2.5mm, 2mm, 1mm
- Cabrillo standard nomenclature compliance
- Support for both frequency ranges and common discrete frequencies
- Direct band name string parsing (e.g., "6M", "70CM", "23CM")

### Enhanced
- Improved frequency parsing with multiple format support
- Better handling of contest log frequency formats
- More accurate band identification for all amateur radio allocations

## [1.1.0] - 2025-09-17

### Added
- CSV file format support with automatic column detection
- Automatic file format detection based on file extension (.csv, .cbr, .log)
- Continent selection functionality with --continents argument
- Automatic continent detection based on grid squares in log
- Support for 6 continents: north_america, south_america, europe, africa, asia, oceania
- Dynamic map bounds based on selected continents
- Grid square filtering by continent
- Example CSV file for testing
- Command-line argument parsing with argparse

### Changed
- Map bounds now automatically adjust to selected continents instead of fixed Americas view
- Output filenames now include continent information
- Grid field labels only show for visible map areas
- Improved error handling and user feedback

### Enhanced
- Better CSV parsing with flexible column name detection
- More accurate continent boundary definitions
- Optimized map rendering for different geographic regions

## [1.0.0] - 2025-09-17

### Added
- Initial release of Maidenhead Contest Map Generator
- Support for Cabrillo format contest log parsing
- Multi-band analysis with separate maps per frequency band
- Accurate grid square boundary rendering (2° × 1° and 5' × 2.5')
- Grid field labels (EM, EN, EL, etc.) displayed on maps
- Color-coded contact density visualization
- Support for 6m, 2m, 1.25m, 70cm, 33cm, and 23cm bands
- Americas region coverage optimization
- High-resolution PNG output with callsign and band in filename
- MIT License
- Comprehensive documentation and examples

### Features
- Parses standard Cabrillo contest logs
- Creates separate maps for each frequency band found
- Shows actual geographic grid square boundaries
- Color intensity indicates contact density per grid
- Includes coastlines, borders, and geographic features
- Automatic callsign extraction from log headers
