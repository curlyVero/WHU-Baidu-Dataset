# Linux Usage

This folder is the Linux package of the converter.

Folder:

- `D:\WHU\26First\data\tools\log2data\linux`

If you copy this package to Linux, keep the whole folder together.

Main files:

- `run_me_linux.sh`
- `convert_android_logs.py`
- `bundled_android_rinex_src`


## Quick Start

### Step 1: Make the shell script executable

```bash
chmod +x /path/to/tools/log2data/linux/run_me_linux.sh
```

### Step 2: Run the script

```bash
/path/to/tools/log2data/linux/run_me_linux.sh /path/to/data/0411
```

If you run it without arguments:

```bash
/path/to/tools/log2data/linux/run_me_linux.sh
```

it will ask you for the data folder path.

### Alternative: Run Python directly

```bash
python3 /path/to/tools/log2data/linux/convert_android_logs.py --root-dir /path/to/data/0411
```


## Input Folder Requirement

The target folder can contain:

### Case 1

Raw logs directly under the folder:

```text
/path/to/data/0411/gnss_log_2026_04_11_10_00_00.txt
```

### Case 2

Raw logs already inside the `log` subfolder:

```text
/path/to/data/0411/log/gnss_log_2026_04_11_10_00_00.txt
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


## Python Requirement

The Linux launcher tries:

1. `python3`
2. `python`

At least one of them must exist in `PATH`.


## Notes

- This Linux package is self-contained in this folder.
- The bundled dependency folder is local, so it does not depend on the old Windows external path.
- If you move this package to another machine, keep `convert_android_logs.py` and `bundled_android_rinex_src` together.
- The bundled Android RINEX exporter is configured for raw extraction: it does not drop Raw measurements based on code-lock/TOW/CN0/SvTimeUncertainty/multipath quality checks. Do quality control in downstream preprocessing.
