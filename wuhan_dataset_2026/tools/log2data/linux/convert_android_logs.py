#!/usr/bin/env python
from __future__ import annotations

import argparse
import contextlib
import csv
import datetime as dt
import io
import math
import re
import shutil
import sys
from pathlib import Path
from typing import Dict, List, Sequence


DEFAULT_CONVERTER_SRC = Path(__file__).resolve().parent / "bundled_android_rinex_src"
UTC = dt.timezone.utc
OBSERVABLE_ORDER = ("C", "L", "S", "D")
SYSTEM_ORDER = ("C", "G", "R", "E", "J")
SUPPORTED_CONSTELLATIONS = {1, 3, 4, 5, 6}
RAW_CLOCK_FIELDS = ("utcTimeMillis", "TimeNanos", "FullBiasNanos", "BiasNanos")
SUPPORTED_BANDS_BY_SYSTEM = {
    "G": {1, 5},
    "R": {1, 2},
    "E": {1, 5},
    "C": {1, 2, 5},
    "J": {1, 5},
}
OBS_CODE_ATTR = {
    "G": {1: "C", 5: "X"},
    "R": {1: "C", 2: "C"},
    "E": {1: "X", 5: "X"},
    "C": {1: "P", 2: "I", 5: "P"},
    "J": {1: "C", 5: "X"},
}
BAND_SORT_ORDER = {
    "G": [1, 5],
    "R": [1, 2],
    "E": [1, 5],
    "C": [2, 1, 5],
    "J": [1, 5],
}
STATION_CODE_MAP = {
    "huawei": "hua",
    "vivo": "viv",
    "xiaomi": "xia",
    "chinatelecom": "chi",
}
SUBDIRS = {
    "obs": "obs",
    "imu": "imu",
    "imu_un": "imu_un",
    "deg": "mnt",
    "fix": "fix",
    "nmea": "nmea",
    "agc": "AGC",
    "log": "log",
}
DEFAULT_EXTRACT_HEADERS = {
    "OrientationDeg": "MessageType,utcTimeMillis,elapsedRealtimeNanos,yawDeg,rollDeg,pitchDeg,CalibrationAccuracy",
    "Fix": (
        "MessageType,Provider,LatitudeDegrees,LongitudeDegrees,AltitudeMeters,SpeedMps,"
        "AccuracyMeters,BearingDegrees,UnixTimeMillis,SpeedAccuracyMps,BearingAccuracyDegrees,"
        "elapsedRealtimeNanos,VerticalAccuracyMeters,MockLocation,NumberOfUsedSignals,"
        "VerticalSpeedAccuracyMps,SolutionType"
    ),
}
NMEA_POSITION_HEADER = [
    "MessageType",
    "utcTimeMillis",
    "Talker",
    "SentenceType",
    "NmeaUtcTime",
    "LatitudeDegrees",
    "LongitudeDegrees",
    "FixQualityOrMode",
    "Status",
    "SatelliteCount",
    "Hdop",
    "AltitudeMeters",
    "GeoidSeparationMeters",
    "SpeedKnots",
    "CourseDegrees",
    "NmeaDate",
    "Checksum",
    "RawSentence",
]
AGC_OUTPUT_FIELDS = [
    "utcTimeMillis",
    "Svid",
    "ConstellationType",
    "CarrierFrequencyHz",
    "CodeType",
    "Cn0DbHz",
    "BasebandCn0DbHz",
    "AgcDb",
]
DATED_RECORD_TYPES = {
    "Raw",
    "Accel",
    "Gyro",
    "UncalAccel",
    "UncalGyro",
    "OrientationDeg",
    "Fix",
    "NMEA",
}
TIMESTAMP_FIELDS = ("utcTimeMillis", "UnixTimeMillis")
VERSION_LINE = "     3.04           OBSERVATION DATA    M (MIXED)           RINEX VERSION / TYPE"
POS_LINE = "        0.0000        0.0000        0.0000                  APPROX POSITION XYZ"
HEN_LINE = "        0.0000        0.0000        0.0000                  ANTENNA: DELTA H/E/N"


def import_converter_modules(converter_src: Path):
    converter_src = converter_src.resolve()
    if not converter_src.exists():
        raise FileNotFoundError(f"Converter source directory not found: {converter_src}")

    converter_path = str(converter_src)
    if converter_path not in sys.path:
        sys.path.insert(0, converter_path)

    import gnsslogger as alogger  # type: ignore
    import rinex3 as arinex  # type: ignore

    return alogger, arinex


def parse_metadata(log_path: Path) -> Dict[str, str]:
    version_line = None
    with log_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if line.startswith("# Version:"):
                version_line = line.strip()
                break

    if version_line is None:
        raise ValueError(f"Cannot find metadata header in {log_path}")

    manufacturer_match = re.search(r"Manufacturer:\s*(.*?)\s+Model:", version_line)
    model_match = re.search(r"Model:\s*(.*?)\s+GNSS Hardware Model Name:", version_line)

    if not manufacturer_match or not model_match:
        raise ValueError(f"Cannot parse Manufacturer/Model from {log_path}")

    return {
        "manufacturer": manufacturer_match.group(1).strip(),
        "model": model_match.group(1).strip(),
    }


def normalize_key(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def station_prefix(manufacturer: str, model: str) -> str:
    normalized = normalize_key(manufacturer)
    if normalized in STATION_CODE_MAP:
        return STATION_CODE_MAP[normalized]

    model_key = normalize_key(model)
    if model_key in STATION_CODE_MAP:
        return STATION_CODE_MAP[model_key]

    letters = "".join(ch for ch in normalized if ch.isalpha())
    if len(letters) >= 3:
        return letters[:3]

    model_letters = "".join(ch for ch in model_key if ch.isalpha())
    if len(model_letters) >= 3:
        return model_letters[:3]

    seed = (letters + model_letters + "xxx")[:3]
    return seed


def acquisition_date(log_path: Path) -> dt.date:
    match = re.match(r"gnss_log_(\d{4})_(\d{2})_(\d{2})_", log_path.name)
    if not match:
        raise ValueError(f"Cannot parse acquisition date from {log_path.name}")
    year, month, day = map(int, match.groups())
    return dt.date(year, month, day)


def utc_date_from_millis(value: object) -> dt.date | None:
    timestamp = numeric_value(value)
    if timestamp is None:
        return None

    try:
        return dt.datetime.fromtimestamp(timestamp / 1000.0, tz=UTC).date()
    except (OverflowError, OSError, ValueError):
        return None


def record_timestamp_indices(log_path: Path) -> Dict[str, int]:
    indices: Dict[str, int] = {}
    with log_path.open("r", encoding="utf-8", errors="ignore") as source:
        for line in source:
            if not line.startswith("# ") or "," not in line:
                continue
            fields = next(csv.reader([line[2:].rstrip("\n")]))
            if not fields or fields[0] not in DATED_RECORD_TYPES:
                continue
            for field_name in TIMESTAMP_FIELDS:
                if field_name in fields:
                    indices[fields[0]] = fields.index(field_name)
                    break
    return indices


def log_utc_dates(log_path: Path) -> List[dt.date]:
    timestamp_indices = record_timestamp_indices(log_path)
    dates: set[dt.date] = set()
    with log_path.open("r", encoding="utf-8", errors="ignore") as source:
        for line in source:
            if line.startswith("#"):
                continue
            fields = next(csv.reader([line.rstrip("\n")]))
            if not fields:
                continue
            timestamp_index = timestamp_indices.get(fields[0])
            if timestamp_index is None or timestamp_index >= len(fields):
                continue
            date_value = utc_date_from_millis(fields[timestamp_index])
            if date_value is not None:
                dates.add(date_value)

    if not dates:
        raise ValueError(f"No valid UTC timestamps found in {log_path.name}")
    return sorted(dates)


def year_suffix(date_value: dt.date) -> str:
    return f"{date_value.year % 100:02d}"


def doy_code(date_value: dt.date) -> str:
    return f"{date_value.timetuple().tm_yday:03d}"


def system_letter(constellation_type: int) -> str | None:
    return {
        1: "G",
        3: "R",
        4: "J",
        5: "C",
        6: "E",
    }.get(constellation_type)


def band_for_measurement(alogger, measurement: Dict[str, object]) -> int | None:
    try:
        return alogger.get_rnx_band_from_freq(alogger.get_frequency(measurement))
    except Exception:
        return None


def numeric_value(value: object) -> float | None:
    if value in ("", None):
        return None

    try:
        number = float(value)
    except (TypeError, ValueError):
        return None

    if not math.isfinite(number):
        return None

    return number


def has_valid_raw_clock(measurement: Dict[str, object]) -> bool:
    return all(numeric_value(measurement.get(field)) is not None for field in RAW_CLOCK_FIELDS)


def measurement_supported(alogger, measurement: Dict[str, object]) -> bool:
    if not has_valid_raw_clock(measurement):
        return False

    try:
        constellation_type = int(measurement["ConstellationType"])
    except (KeyError, TypeError, ValueError):
        return False

    if constellation_type not in SUPPORTED_CONSTELLATIONS:
        return False

    system = system_letter(constellation_type)
    band = band_for_measurement(alogger, measurement)
    if system is None or band is None:
        return False

    return band in SUPPORTED_BANDS_BY_SYSTEM[system]


def sample_lookup_frequency(alogger, measurement: Dict[str, object], glo_freq_chns: Dict[str, int]):
    measured_frequency = alogger.get_frequency(measurement)
    constellation_type = int(measurement["ConstellationType"])
    band = band_for_measurement(alogger, measurement)

    if constellation_type == alogger.CONSTELLATION_GLONASS and band == 1:
        actual_frequency = alogger.FREQ1_GLO
        satname = alogger.get_satname(measurement)
        slot = glo_freq_chns.get(satname)
        if slot is not None:
            actual_frequency += slot * alogger.DFREQ1_GLO
        return actual_frequency

    return measured_frequency


def sample_obscode(alogger, measurement: Dict[str, object]) -> str:
    constellation_type = int(measurement["ConstellationType"])
    system = system_letter(constellation_type)
    band = band_for_measurement(alogger, measurement)

    if system is None or band is None:
        raise ValueError(f"Unsupported constellation/frequency in measurement: {measurement}")

    attr = OBS_CODE_ATTR[system].get(band)
    if attr is None:
        raise ValueError(f"Unsupported system/band combination: {system}{band}")

    return f"{band}{attr}"


def collect_filtered_batches(alogger, gnsslog) -> List[List[Dict[str, object]]]:
    filtered_batches: List[List[Dict[str, object]]] = []
    for batch in gnsslog.raw_batches():
        filtered = [measurement for measurement in batch if measurement_supported(alogger, measurement)]
        if filtered:
            filtered_batches.append(filtered)
    return filtered_batches


def collect_filtered_batches_by_utc_date(alogger, gnsslog) -> List[tuple[dt.date, List[Dict[str, object]]]]:
    dated_batches: List[tuple[dt.date, List[Dict[str, object]]]] = []
    for batch in gnsslog.raw_batches():
        batches_by_date: Dict[dt.date, List[Dict[str, object]]] = {}
        for measurement in batch:
            if not measurement_supported(alogger, measurement):
                continue
            date_value = utc_date_from_millis(measurement.get("utcTimeMillis"))
            if date_value is not None:
                batches_by_date.setdefault(date_value, []).append(measurement)
        dated_batches.extend(sorted(batches_by_date.items()))
    return dated_batches


def build_obslist(alogger, raw_batches: Sequence[Sequence[Dict[str, object]]]) -> Dict[str, List[str]]:
    raw_codes: Dict[str, set[str]] = {}

    for batch in raw_batches:
        for measurement in batch:
            system = system_letter(int(measurement["ConstellationType"]))
            if system is None:
                continue
            raw_codes.setdefault(system, set()).add(sample_obscode(alogger, measurement))

    obslist: Dict[str, List[str]] = {}
    for system in SYSTEM_ORDER:
        if system not in raw_codes:
            continue

        sort_order = BAND_SORT_ORDER[system]
        ordered_codes = sorted(
            raw_codes[system],
            key=lambda code: (sort_order.index(int(code[0])), code),
        )
        obslist[system] = [prefix + code for code in ordered_codes for prefix in OBSERVABLE_ORDER]

    return obslist


def first_valid_epoch(batches: Sequence[dict]):
    valid_epochs = [batch["epoch"] for batch in batches if batch and "epoch" in batch]
    if not valid_epochs:
        raise ValueError("No valid GNSS epochs remained after filtering")
    return valid_epochs[0]


def format_obs_types_line(system: str, observables: Sequence[str]) -> str:
    content = f"{system}  {len(observables):3d}"
    for observable in observables:
        content += f" {observable:3s}"
    return f"{content:60s}SYS / # / OBS TYPES"


def format_time_of_first_obs(epoch_info) -> str:
    epoch, epoch_seconds = epoch_info
    whole_seconds = math.floor(epoch_seconds)
    fractional_digits = int(round((epoch_seconds - whole_seconds) * 1e7))
    rounded_to_next_second = False
    if fractional_digits >= 10000000:
        whole_seconds += 1
        fractional_digits -= 10000000
        rounded_to_next_second = True
    epoch_for_format = epoch
    if not rounded_to_next_second and fractional_digits > 5000000 and epoch.microsecond < 500000:
        epoch_for_format -= dt.timedelta(seconds=1)
    seconds = epoch_for_format.second + fractional_digits / 1e7
    content = (
        f"  {epoch_for_format.year:4d}"
        f"{epoch_for_format.month:6d}"
        f"{epoch_for_format.day:6d}"
        f"{epoch_for_format.hour:6d}"
        f"{epoch_for_format.minute:6d}"
        f"{seconds:13.7f}"
    )
    return f"{content:60s}TIME OF FIRST OBS"


def build_header(obslist: Dict[str, List[str]], first_epoch, manufacturer: str, model: str) -> str:
    header_lines = [
        VERSION_LINE,
        f"{'':20s}{manufacturer:20s}{'':20s}REC # / TYPE / VERS",
        f"{model:20s}{'':40s}ANT # / TYPE",
        POS_LINE,
        HEN_LINE,
    ]

    for system in SYSTEM_ORDER:
        observables = obslist.get(system)
        if observables:
            header_lines.append(format_obs_types_line(system, observables))

    header_lines.append(f"{'GPS':60s}TIME SYSTEM ID")
    header_lines.append(format_time_of_first_obs(first_epoch))
    header_lines.append(f"{'':60s}END OF HEADER")
    return "\n".join(header_lines) + "\n"


def write_observation_batch(batch: dict, obslist: Dict[str, List[str]]) -> str:
    if not batch or "epoch" not in batch:
        return ""

    epoch, epoch_seconds = batch["epoch"]
    whole_seconds = math.floor(epoch_seconds)
    fractional_digits = int(round((epoch_seconds - whole_seconds) * 1e7))
    rounded_to_next_second = False
    if fractional_digits >= 10000000:
        whole_seconds += 1
        fractional_digits -= 10000000
        rounded_to_next_second = True
    epoch_for_format = epoch
    if not rounded_to_next_second and fractional_digits > 5000000 and epoch.microsecond < 500000:
        epoch_for_format -= dt.timedelta(seconds=1)
    epoch_line = epoch_for_format.strftime("> %Y %m %d %H %M %S.") + f"{fractional_digits:07d}"
    epoch_line += f"  0 {len(batch) - 1:2d}\n"

    body_lines = [epoch_line]
    for sat in batch:
        if sat == "epoch":
            continue

        line = sat
        for observable in obslist[sat[0]]:
            value = batch[sat].get(observable, 0.0)
            if value > 1e8:
                value = 0.0
            line += f"{value:14.3f}  "
        body_lines.append(line + "\n")

    return "".join(body_lines)


def convert_log_to_rinex(
    alogger,
    _arinex,
    log_path: Path,
    output_paths: Dict[dt.date, Path],
    manufacturer: str,
    model: str,
) -> Dict[dt.date, int]:
    old_obs_order = list(alogger.OBS_LIST)
    old_get_obscode = alogger.get_obscode
    old_lookup_frequency = alogger.lookup_frequency

    try:
        alogger.OBS_LIST = list(OBSERVABLE_ORDER)
        alogger.get_obscode = lambda measurement: sample_obscode(alogger, measurement)
        alogger.lookup_frequency = lambda measurement, glo_freq_chns: sample_lookup_frequency(
            alogger,
            measurement,
            glo_freq_chns,
        )

        gnsslog = alogger.GnssLog(str(log_path))
        dated_raw_batches = collect_filtered_batches_by_utc_date(alogger, gnsslog)
        if not dated_raw_batches:
            raise ValueError(f"No usable GNSS Raw measurements found in {log_path.name}")

        raw_batches = [batch for _date_value, batch in dated_raw_batches]
        glo_freq_chns = alogger.get_glo_freq_chn_list(raw_batches)
        alogger.reset_clock()

        process_one = lambda measurement: alogger.process(
            measurement,
            model=model,
            fix_bias=False,
            timeadj=float(1e-7),
            pseudorange_bias=0,
            filter_mode="sync",
            glo_freq_chns=glo_freq_chns,
            slip_mask=3,
        )

        with contextlib.redirect_stderr(io.StringIO()):
            dated_batches = [
                (date_value, alogger.merge([process_one(measurement) for measurement in raw_batch]))
                for date_value, raw_batch in dated_raw_batches
            ]

        row_counts: Dict[dt.date, int] = {}
        for date_value, output_path in sorted(output_paths.items()):
            selected_raw_batches = [raw_batch for batch_date, raw_batch in dated_raw_batches if batch_date == date_value]
            selected_batches = [batch for batch_date, batch in dated_batches if batch_date == date_value and batch]
            if not selected_batches:
                continue

            obslist = build_obslist(alogger, selected_raw_batches)
            header = build_header(obslist, first_valid_epoch(selected_batches), manufacturer, model)
            body = "".join(write_observation_batch(batch, obslist) for batch in selected_batches)

            output_path.parent.mkdir(parents=True, exist_ok=True)
            with output_path.open("w", encoding="utf-8", newline="\n") as handle:
                handle.write(header + body)
            row_counts[date_value] = len(selected_batches)
        return row_counts
    finally:
        alogger.OBS_LIST = old_obs_order
        alogger.get_obscode = old_get_obscode
        alogger.lookup_frequency = old_lookup_frequency


def replace_first_header_field(header_line: str, replacement: str) -> str:
    parts = [part.strip() for part in header_line.strip().split(",")]
    if not parts:
        return replacement
    parts[0] = replacement
    return ",".join(parts)


def extract_header_from_log(log_path: Path, prefix: str, replacement: str) -> str:
    marker = f"# {prefix},"
    with log_path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if line.startswith(marker):
                return replace_first_header_field(line[2:], replacement)
    fallback = DEFAULT_EXTRACT_HEADERS.get(prefix)
    if fallback is not None:
        return fallback
    raise ValueError(f"Cannot find header definition for {prefix} in {log_path}")


def record_created(created: Dict[str, List[str]], folder_key: str, path: Path, detail: str = "") -> None:
    suffix = f" ({detail})" if detail else ""
    created.setdefault(folder_key, []).append(f"{path}{suffix}")


@contextlib.contextmanager
def daily_output_handles(output_paths: Dict[dt.date, Path]):
    with contextlib.ExitStack() as stack:
        handles = {}
        for date_value, output_path in sorted(output_paths.items()):
            output_path.parent.mkdir(parents=True, exist_ok=True)
            handles[date_value] = stack.enter_context(
                output_path.open("w", encoding="utf-8", newline="\n")
            )
        yield handles


def write_imu_file(
    log_path: Path,
    output_paths: Dict[dt.date, Path],
    record_prefixes: Sequence[str],
) -> Dict[dt.date, int]:
    row_counts = {date_value: 0 for date_value in output_paths}
    line_prefixes = tuple(prefix + "," for prefix in record_prefixes)
    header = [
        "MessageType",
        "utcTimeMillis",
        "MeasurementX",
        "MeasurementY",
        "MeasurementZ",
        "BiasX",
        "BiasY",
        "BiasZ",
    ]
    with log_path.open("r", encoding="utf-8", errors="ignore") as source, daily_output_handles(output_paths) as handles:
        writers = {date_value: csv.writer(handle, lineterminator="\n") for date_value, handle in handles.items()}
        for writer in writers.values():
            writer.writerow(header)

        for line in source:
            if not line.startswith(line_prefixes):
                continue

            parts = line.strip().split(",")
            if len(parts) < 6:
                continue
            date_value = utc_date_from_millis(parts[1])
            if date_value not in writers:
                continue

            bias_values = parts[6:9] if parts[0].startswith("Uncal") and len(parts) >= 9 else ["0", "0", "0"]
            writers[date_value].writerow([parts[0], parts[1], parts[3], parts[4], parts[5], *bias_values])
            row_counts[date_value] += 1
    return row_counts


def write_agc_file(log_path: Path, output_paths: Dict[dt.date, Path]) -> Dict[dt.date, int]:
    raw_header = None
    with log_path.open("r", encoding="utf-8", errors="ignore") as source:
        for line in source:
            if line.startswith("# Raw,"):
                raw_header = next(csv.reader([line[2:].rstrip("\n")]))
                break

    row_counts = {date_value: 0 for date_value in output_paths}
    if raw_header is None or "AgcDb" not in raw_header:
        with daily_output_handles(output_paths) as handles:
            for handle in handles.values():
                csv.writer(handle, lineterminator="\n").writerow(["MessageType", *AGC_OUTPUT_FIELDS])
        return row_counts

    indices = {field: raw_header.index(field) if field in raw_header else None for field in AGC_OUTPUT_FIELDS}
    agc_index = indices["AgcDb"]
    timestamp_index = indices["utcTimeMillis"]
    with log_path.open("r", encoding="utf-8", errors="ignore") as source, daily_output_handles(output_paths) as handles:
        writers = {date_value: csv.writer(handle, lineterminator="\n") for date_value, handle in handles.items()}
        for writer in writers.values():
            writer.writerow(["MessageType", *AGC_OUTPUT_FIELDS])
        for line in source:
            if not line.startswith("Raw,"):
                continue
            row = next(csv.reader([line.rstrip("\n")]))
            if agc_index is None or agc_index >= len(row) or not row[agc_index].strip():
                continue
            date_value = utc_date_from_millis(row[timestamp_index]) if timestamp_index is not None and timestamp_index < len(row) else None
            if date_value not in writers:
                continue
            values = [row[index] if index is not None and index < len(row) else "" for index in indices.values()]
            writers[date_value].writerow(["Raw", *values])
            row_counts[date_value] += 1
    return row_counts


def nmea_coordinate_to_degrees(value: str, hemisphere: str) -> float | None:
    if not value or hemisphere not in ("N", "S", "E", "W"):
        return None
    degree_digits = 2 if hemisphere in ("N", "S") else 3
    if len(value) <= degree_digits:
        return None
    try:
        degrees = int(value[:degree_digits])
        minutes = float(value[degree_digits:])
    except ValueError:
        return None
    decimal_degrees = degrees + minutes / 60.0
    if hemisphere in ("S", "W"):
        decimal_degrees *= -1.0
    return decimal_degrees


def parse_nmea_position(timestamp: str, message: str) -> List[str] | None:
    raw_sentence = message.strip()
    if not raw_sentence.startswith("$"):
        return None

    payload = raw_sentence[1:]
    checksum = ""
    if "*" in payload:
        payload, checksum = payload.split("*", 1)

    fields = payload.split(",")
    if not fields or len(fields[0]) < 5:
        return None

    sentence_id = fields[0]
    talker = sentence_id[:2]
    sentence_type = sentence_id[2:]
    values = fields[1:]
    nmea_time = ""
    latitude = None
    longitude = None
    fix_quality_or_mode = ""
    status = ""
    satellite_count = ""
    hdop = ""
    altitude = ""
    geoid_separation = ""
    speed_knots = ""
    course_degrees = ""
    nmea_date = ""

    if sentence_type == "GGA" and len(values) >= 11:
        nmea_time = values[0]
        latitude = nmea_coordinate_to_degrees(values[1], values[2])
        longitude = nmea_coordinate_to_degrees(values[3], values[4])
        fix_quality_or_mode = values[5]
        satellite_count = values[6]
        hdop = values[7]
        altitude = values[8]
        geoid_separation = values[10]
    elif sentence_type == "GNS" and len(values) >= 10:
        nmea_time = values[0]
        latitude = nmea_coordinate_to_degrees(values[1], values[2])
        longitude = nmea_coordinate_to_degrees(values[3], values[4])
        fix_quality_or_mode = values[5]
        satellite_count = values[6]
        hdop = values[7]
        altitude = values[8]
        geoid_separation = values[9]
    elif sentence_type == "RMC" and len(values) >= 9:
        nmea_time = values[0]
        status = values[1]
        latitude = nmea_coordinate_to_degrees(values[2], values[3])
        longitude = nmea_coordinate_to_degrees(values[4], values[5])
        speed_knots = values[6]
        course_degrees = values[7]
        nmea_date = values[8]
    elif sentence_type == "GLL" and len(values) >= 6:
        latitude = nmea_coordinate_to_degrees(values[0], values[1])
        longitude = nmea_coordinate_to_degrees(values[2], values[3])
        nmea_time = values[4]
        status = values[5]
    else:
        return None

    if latitude is None or longitude is None:
        return None

    return [
        "NMEA",
        timestamp,
        talker,
        sentence_type,
        nmea_time,
        f"{latitude:.10f}",
        f"{longitude:.10f}",
        fix_quality_or_mode,
        status,
        satellite_count,
        hdop,
        altitude,
        geoid_separation,
        speed_knots,
        course_degrees,
        nmea_date,
        checksum,
        raw_sentence,
    ]


def write_nmea_position_file(log_path: Path, output_paths: Dict[dt.date, Path]) -> Dict[dt.date, int]:
    row_counts = {date_value: 0 for date_value in output_paths}
    with log_path.open("r", encoding="utf-8", errors="ignore") as source, daily_output_handles(output_paths) as handles:
        writers = {date_value: csv.writer(handle, lineterminator="\n") for date_value, handle in handles.items()}
        for writer in writers.values():
            writer.writerow(NMEA_POSITION_HEADER)
        for line in source:
            if not line.startswith("NMEA,"):
                continue
            parts = line.rstrip("\n").split(",", 2)
            if len(parts) < 3:
                continue
            date_value = utc_date_from_millis(parts[1])
            if date_value not in writers:
                continue
            row = parse_nmea_position(parts[1], parts[2])
            if row is None:
                continue
            writers[date_value].writerow(row)
            row_counts[date_value] += 1
    return row_counts


def extract_rows(
    log_path: Path,
    record_prefix: str,
    output_paths: Dict[dt.date, Path],
    header_replacement: str = "MessageType",
) -> Dict[dt.date, int]:
    header = extract_header_from_log(log_path, record_prefix, header_replacement)
    timestamp_index = record_timestamp_indices(log_path).get(record_prefix)
    row_counts = {date_value: 0 for date_value in output_paths}
    with log_path.open("r", encoding="utf-8", errors="ignore") as source, daily_output_handles(output_paths) as handles:
        for handle in handles.values():
            handle.write(header + "\n")
        for line in source:
            if not line.startswith(record_prefix + ","):
                continue
            fields = next(csv.reader([line.rstrip("\n")]))
            if timestamp_index is None or timestamp_index >= len(fields):
                continue
            date_value = utc_date_from_millis(fields[timestamp_index])
            if date_value not in handles:
                continue
            handles[date_value].write(line.rstrip("\n") + "\n")
            row_counts[date_value] += 1
    return row_counts


def find_logs(root_dir: Path) -> List[Path]:
    candidates = list(root_dir.glob("gnss_log_*.txt")) + list((root_dir / SUBDIRS["log"]).glob("gnss_log_*.txt"))
    unique_logs: Dict[str, Path] = {}
    for path in sorted(candidates):
        unique_logs[str(path.resolve())] = path.resolve()
    return list(unique_logs.values())


def assign_station_ids(logs: Sequence[Path]) -> Dict[Path, str]:
    grouped: Dict[str, List[Path]] = {}
    metadata_cache: Dict[Path, Dict[str, str]] = {}

    for log_path in logs:
        metadata = parse_metadata(log_path)
        metadata_cache[log_path] = metadata
        prefix = station_prefix(metadata["manufacturer"], metadata["model"])
        grouped.setdefault(prefix, []).append(log_path)

    station_ids: Dict[Path, str] = {}
    for prefix, paths in grouped.items():
        for index, log_path in enumerate(sorted(paths), start=1):
            station_ids[log_path] = f"{prefix}{index}"

    return station_ids


def ensure_subdirs(root_dir: Path) -> Dict[str, Path]:
    resolved = {}
    for key, name in SUBDIRS.items():
        path = root_dir / name
        path.mkdir(parents=True, exist_ok=True)
        resolved[key] = path
    return resolved


def move_log_to_folder(log_path: Path, log_dir: Path) -> Path:
    destination = log_dir / log_path.name
    if log_path.resolve() == destination.resolve():
        return destination

    if destination.exists():
        destination.unlink()

    shutil.move(str(log_path), str(destination))
    return destination


def convert_directory(root_dir: Path, converter_src: Path) -> Dict[str, List[str]]:
    alogger, arinex = import_converter_modules(converter_src)
    subdirs = ensure_subdirs(root_dir)
    logs = find_logs(root_dir)
    if not logs:
        raise FileNotFoundError(f"No gnss_log_*.txt files found in {root_dir} or {root_dir / SUBDIRS['log']}")

    created: Dict[str, List[str]] = {}
    station_ids = assign_station_ids(logs)
    seen_output_keys: set[str] = set()

    for log_index, log_path in enumerate(logs, start=1):
        print(f"[{log_index}/{len(logs)}] Processing {log_path.name}", flush=True)
        metadata = parse_metadata(log_path)
        utc_dates = log_utc_dates(log_path)
        station = station_ids[log_path]

        daily_paths: Dict[str, Dict[dt.date, Path]] = {
            key: {} for key in ("obs", "imu", "imu_un", "deg", "fix", "nmea", "agc")
        }
        for utc_date_value in utc_dates:
            doy = doy_code(utc_date_value)
            yy = year_suffix(utc_date_value)
            year = str(utc_date_value.year)
            output_key = f"{station}{year}{doy}"
            if output_key in seen_output_keys:
                raise ValueError(
                    f"Duplicate station/day naming collision detected for {log_path.name}: {output_key}"
                )
            seen_output_keys.add(output_key)

            for key in daily_paths:
                (subdirs[key] / year / doy).mkdir(parents=True, exist_ok=True)
            daily_paths["obs"][utc_date_value] = subdirs["obs"] / year / doy / f"{station}{doy}0.{yy}o"
            daily_paths["imu"][utc_date_value] = subdirs["imu"] / year / doy / f"{station}{doy}.{yy}IMU"
            daily_paths["imu_un"][utc_date_value] = subdirs["imu_un"] / year / doy / f"{station}{doy}.{yy}IMU"
            daily_paths["deg"][utc_date_value] = subdirs["deg"] / year / doy / f"{station}{doy}Deg.txt"
            daily_paths["fix"][utc_date_value] = subdirs["fix"] / year / doy / f"{station}{doy}fix.txt"
            daily_paths["nmea"][utc_date_value] = subdirs["nmea"] / year / doy / f"{station}{doy}.{yy}nmea"
            daily_paths["agc"][utc_date_value] = subdirs["agc"] / year / doy / f"{station}{doy}AGC.txt"

        def record_daily_counts(folder_key: str, counts: Dict[dt.date, int]) -> None:
            for date_value, path in sorted(daily_paths[folder_key].items()):
                record_created(created, folder_key, path, f"{counts.get(date_value, 0)} rows")

        imu_rows = write_imu_file(log_path, daily_paths["imu"], ("Accel", "Gyro"))
        print(f"  IMU: {sum(imu_rows.values())} rows", flush=True)
        imu_un_rows = write_imu_file(log_path, daily_paths["imu_un"], ("UncalAccel", "UncalGyro"))
        print(f"  IMU_UN: {sum(imu_un_rows.values())} rows", flush=True)
        deg_rows = extract_rows(log_path, "OrientationDeg", daily_paths["deg"])
        print(f"  MNT: {sum(deg_rows.values())} rows", flush=True)
        fix_rows = extract_rows(log_path, "Fix", daily_paths["fix"])
        print(f"  FIX: {sum(fix_rows.values())} rows", flush=True)
        nmea_rows = write_nmea_position_file(log_path, daily_paths["nmea"])
        print(f"  NMEA: {sum(nmea_rows.values())} rows", flush=True)
        agc_rows = write_agc_file(log_path, daily_paths["agc"])
        print(f"  AGC: {sum(agc_rows.values())} rows", flush=True)
        record_daily_counts("imu", imu_rows)
        record_daily_counts("imu_un", imu_un_rows)
        record_daily_counts("deg", deg_rows)
        record_daily_counts("fix", fix_rows)
        record_daily_counts("nmea", nmea_rows)
        record_daily_counts("agc", agc_rows)

        print("  OBS: converting RINEX...", flush=True)
        try:
            obs_rows = convert_log_to_rinex(
                alogger,
                arinex,
                log_path,
                daily_paths["obs"],
                metadata["manufacturer"],
                metadata["model"],
            )
        except Exception as exc:
            print(f"Warning: skipped OBS for {log_path.name}: {exc}")
        else:
            record_daily_counts("obs", obs_rows)
            print("  OBS: done", flush=True)

        moved_log = move_log_to_folder(log_path, subdirs["log"])
        record_created(created, "log", moved_log)
        print(f"  LOG: moved to {moved_log}", flush=True)

    return created


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Convert Android GnssLogger logs into obs/imu/imu_un/mnt/fix/nmea/AGC/log subfolders."
    )
    parser.add_argument(
        "--root-dir",
        "--input-dir",
        dest="root_dir",
        type=Path,
        default=Path(r"D:\WHU\26First\data\0410"),
        help="Data root directory that contains gnss_log_*.txt files or a log subfolder.",
    )
    parser.add_argument(
        "--converter-src",
        type=Path,
        default=DEFAULT_CONVERTER_SRC,
        help="Path to android_rinex-master/src.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    created = convert_directory(args.root_dir.resolve(), args.converter_src.resolve())
    print("Created or updated files by folder:")
    for folder_key, folder_name in SUBDIRS.items():
        entries = created.get(folder_key, [])
        if not entries:
            continue
        print(f"[{folder_name}]")
        for entry in entries:
            print(f"  {entry}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
