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

## Output Files

The script creates separate maps for each band with descriptive filenames:
- `K1TO_6m_north_america_maidenhead_map.png` - 6m band, North America
- `K1TO_2m_europe_asia_maidenhead_map.png` - 2m band, Europe and Asia
- `K1TO_70cm_world_maidenhead_map.png` - 70cm band, worldwide

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

## Requirements

- Python 3.7+
- matplotlib
- cartopy
- numpy (installed with matplotlib)

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

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Uses Natural Earth data for geographic features
- Built with matplotlib and cartopy for mapping
- Designed for amateur radio VHF/UHF contest analysis
- Supports worldwide amateur radio activity mapping
