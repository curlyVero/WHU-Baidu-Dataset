# Baidu GNSS/IMU Dataset

## 摘要

本数据集面向智能终端 GNSS 定位与多传感器融合研究。数据覆盖城市车载、操场步行、多设备静态以及 Wi-Fi/蓝牙连接状态切换等场景，包含 Android 原始 GNSS 测量、设备传感器记录以及部分系统定位和 RTK 中间数据。多设备同步参与同一批次采集，便于比较不同厂商、不同终端类型和不同运动状态下的观测质量与定位性能。

数据集由 2024 城市车辆数据、2026 城市车辆数据和 2026 武汉多场景数据组成，可用于智能手机 GNSS 质量分析、单点与精密定位、GNSS/INS 融合、可穿戴设备定位以及无线连接状态对 GNSS 观测影响等研究。武汉数据同时提供配套采集 APK 和跨平台日志转换工具，便于复现从 Android 原始日志到 RINEX、IMU 及其他辅助数据的处理流程。

## 数据下载

完整数据按子数据集打包并发布在本仓库的 [Releases](https://github.com/curlyVero/WHU-Baidu-Dataset/releases) 页面。由于单个数据包较大，每个 `tar.zst` 压缩包被拆分为若干个 `.part-*` 文件。下载同一数据包的全部分卷后，可在 Linux 下合并并解压：

```bash
cat WHU-Baidu-Dataset-<subset>.tar.zst.part-* | tar --use-compress-program=unzstd -xf -
```

其中 `<subset>` 为 `city_dataset_2024`、`city_dataset_2026` 或 `wuhan_dataset_2026`。可使用 Release 中提供的 `SHA256SUMS` 检查下载文件的完整性。

## 目录结构

```text
dataset_release/
├── city_dataset_2024/       # 2024 城市车辆手机 GNSS 数据
├── city_dataset_2026/       # 2026 城市车辆手机 GNSS/IMU 数据
└── wuhan_dataset_2026/      # 2026 武汉多场景采集日志
    ├── 0720static/
    ├── 0804walk/
    ├── 0813walk/
    ├── 0827vehicle/
    ├── 0907vehicle/
    └── 0915static/
```

## 武汉数据批次

| 批次 | 采集日期 | 年积日 | 场景 |
| --- | --- | ---: | --- |
| `0720static` | 2026-07-20 | 201/202 | 静态 |
| `0804walk` | 2026-08-04 | 216 | 操场步行 |
| `0813walk` | 2026-08-13 | 225 | 操场步行 |
| `0827vehicle` | 2026-08-27 | 239 | 车载 |
| `0907vehicle` | 2026-09-07 | 250 | 车载 |
| `0915static` | 2026-09-15 | 258 | 静态无线连接实验 |

武汉数据批次下的 `log/` 保存 Android GNSS 原始日志。采集 APK 和日志转换工具位于 `wuhan_dataset_2026/tools/`。文件名前缀通常为 `goo`（Google）、`viv`（vivo）、`xia`（Xiaomi）和 `sam`（Samsung）。

## 日志采集与转换

可以使用 `wuhan_dataset_2026/tools/apk/` 中的手机或手表 APK 采集 Android GNSS 日志，再使用 `wuhan_dataset_2026/tools/log2data/` 中的平台工具处理日志。转换器可生成 RINEX 观测、IMU 以及其他辅助输出；运行方法和输出格式见工具目录中的 README。

采集 APK 和日志格式基于 Google 开源的 [GnssLogger](https://github.com/google/gps-measurement-tools) 项目。本数据集配套的是经过修改和修复的版本。感谢 Google 及 GnssLogger 开源项目的贡献。

## English Version

# Baidu GNSS/IMU Dataset

## Abstract

This dataset is designed for research on GNSS positioning and multi-sensor fusion with consumer smart devices. The scenarios include urban driving, playground walking, multi-device static collection, and controlled Wi-Fi/Bluetooth connectivity transitions. The data include raw Android GNSS measurements, device sensor records, and selected system-location and RTK intermediate data. Multiple devices participated in the same collection sessions, enabling comparisons across manufacturers, device types, and motion conditions.

The dataset consists of urban vehicle data collected in 2024, urban vehicle data collected in 2026, and multi-scenario Wuhan data collected in 2026. It supports studies of smartphone GNSS observation quality, standalone and precise positioning, GNSS/INS integration, wearable positioning, and the effects of wireless connectivity on GNSS measurements. The Wuhan subset also includes collection APKs and cross-platform conversion tools, enabling reproducible processing from raw Android logs to RINEX observations, IMU files, and other auxiliary outputs.

## Data Download

The complete data are packaged by subset and published on this repository's [Releases](https://github.com/curlyVero/WHU-Baidu-Dataset/releases) page. Because the archives are large, each `tar.zst` archive is split into multiple `.part-*` files. After downloading all parts of an archive, concatenate and extract them on Linux with:

```bash
cat WHU-Baidu-Dataset-<subset>.tar.zst.part-* | tar --use-compress-program=unzstd -xf -
```

Replace `<subset>` with `city_dataset_2024`, `city_dataset_2026`, or `wuhan_dataset_2026`. Use the `SHA256SUMS` file included with the Release to verify downloaded files.

## Directory Structure

```text
dataset_release/
├── city_dataset_2024/       # 2024 urban vehicle phone GNSS data
├── city_dataset_2026/       # 2026 urban vehicle phone GNSS/IMU data
└── wuhan_dataset_2026/      # 2026 Wuhan multi-scenario collection logs
    ├── 0720static/
    ├── 0804walk/
    ├── 0813walk/
    ├── 0827vehicle/
    ├── 0907vehicle/
    └── 0915static/
```

## Wuhan Batches

| Batch | Collection date | Day of year | Scenario |
| --- | --- | ---: | --- |
| `0720static` | 2026-07-20 | 201/202 | Static |
| `0804walk` | 2026-08-04 | 216 | Playground walking |
| `0813walk` | 2026-08-13 | 225 | Playground walking |
| `0827vehicle` | 2026-08-27 | 239 | Vehicle-mounted |
| `0907vehicle` | 2026-09-07 | 250 | Vehicle-mounted |
| `0915static` | 2026-09-15 | 258 | Static wireless-connectivity experiment |

For the Wuhan batches, `log/` contains raw Android GNSS logs. Collection APKs and log-conversion tools are provided under `wuhan_dataset_2026/tools/`. File-name prefixes are usually `goo` (Google), `viv` (vivo), `xia` (Xiaomi), and `sam` (Samsung).

## Log Collection and Conversion

Use the phone or watch APKs under `wuhan_dataset_2026/tools/apk/` to collect Android GNSS logs, then use the platform-specific tools under `wuhan_dataset_2026/tools/log2data/` to process them. The converter can generate RINEX observations, IMU files, and other auxiliary outputs; see the tool READMEs for usage and output details.

The collection APKs and log format are based on Google's open-source [GnssLogger](https://github.com/google/gps-measurement-tools) project. The accompanying version has been modified and fixed for this dataset. We acknowledge and thank Google and the GnssLogger open-source project.
