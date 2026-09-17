# Windows Usage

This folder is the Windows package of the converter.

Folder:

- `D:\WHU\26First\data\tools\log2data\win`

Main files:

- `run_me_win.bat`
- `convert_android_logs.py`
- `bundled_android_rinex_src`


## Quick Start

### Method 1: Double-click

Double-click:

- `D:\WHU\26First\data\tools\log2data\win\run_me_win.bat`

Then input the data folder path, for example:

- `D:\WHU\26First\data\0410`
- `D:\WHU\26First\data\0411`

### Method 2: Run with a folder argument

```bat
D:\WHU\26First\data\tools\log2data\win\run_me_win.bat D:\WHU\26First\data\0411
```

### Method 3: Run Python directly

```bat
python D:\WHU\26First\data\tools\log2data\win\convert_android_logs.py --root-dir D:\WHU\26First\data\0411
```


## Input Folder Requirement

The target folder can contain:

### Case 1

Raw logs directly under the folder:

```text
D:\WHU\26First\data\0411\gnss_log_2026_04_11_10_00_00.txt
```

### Case 2

Raw logs already inside the `log` subfolder:

```text
D:\WHU\26First\data\0411\log\gnss_log_2026_04_11_10_00_00.txt
```

The timestamp may be followed by an optional device or experiment label. For example, both of these are accepted:

```text
gnss_log_2026_07_01_15_11_19_google.txt
gnss_log_2026_07_01_15_11_19_redmi.txt
```

This prevents source filename collisions when multiple phones start at the same time. Output device ids come from each log's `Manufacturer` and `Model` metadata; multiple logs from the same device family receive different numeric indexes.


## Output Structure

After running, the target folder will contain:

- `obs`
- `imu`
- `imu_un`
- `mnt`
- `fix`
- `nmea`
- `AGC`
- `log`

The original `gnss_log_*.txt` files are moved into `log`.

Daily output directories and the `DOY` in output filenames are based on each
record's UTC timestamp. A log spanning multiple UTC dates produces one set of
daily files per date. RINEX observation epochs remain on the GPST time scale,
and the RINEX header contains `TIME SYSTEM ID: GPS`.


## Naming Rule

Device id format:

- `3-letter prefix + collection index`

Examples:

- `hua1`
- `xia1`
- `viv1`
- `viv2`

Output filename formats:

- OBS: `<id><DOY>0.<YY>o`
- IMU: `<id><DOY>.<YY>IMU`
- IMU_UN: `<id><DOY>.<YY>IMU`
- DEG: `<id><DOY>Deg.txt`
- FIX: `<id><DOY>fix.txt`
- NMEA: `<id><DOY>.<YY>nmea`
- AGC: `<id><DOY>AGC.txt`

Example:

- `viv11000.26o`
- `viv1100.26IMU`
- `viv1100Deg.txt`
- `viv1100fix.txt`
- `viv1100.26nmea`
- `viv1100AGC.txt`


## Extracted Content

- `obs`: RINEX observation file from `Raw`
- `imu`: `Accel` and `Gyro`
- `imu_un`: `UncalAccel` and `UncalGyro`
- `mnt`: `OrientationDeg`
- `fix`: `Fix`
- `nmea`: parsed position rows from `$GNGGA`, `$GPGGA`, `$GNGNS`, `$GNRMC`, `$GNGLL`, and matching talker variants
- `AGC`: non-empty `AgcDb` values from `Raw`, together with time, satellite, constellation, frequency, code type, `Cn0DbHz`, and `BasebandCn0DbHz`


## Notes

- This Windows package is self-contained in this folder.
- It does not need the old external tool path under `D:\softApp\AndroidLogger2Rinex`.
- Re-running overwrites files generated from the processed logs, while preserving other existing year/DOY output folders.
- The bundled Android RINEX exporter is configured for raw extraction: it does not drop Raw measurements based on code-lock/TOW/CN0/SvTimeUncertainty/multipath quality checks. Do quality control in downstream preprocessing.
