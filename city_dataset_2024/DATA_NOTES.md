# 数据说明

## 手机目录 `phone/<device>`

- `rtklogs.txt`：Android 原始 GNSS 测量日志。
- `rtklogs.obs`：手机 RINEX 观测文件。
- `bdrtk_*_station_all.obs`：对应处理会话的基准站 RINEX 观测文件。
- `bdrtk_*.output`：每历元的基准站选择与 ECEF 坐标记录。
- `rtklog.pos`：部分手机提供的 GNSS RTK 解算结果。

## 真值目录 `true`

- `*.ieout`：Inertial Explorer 导出的平滑 GNSS/INS 组合结果，包含位置、速度、姿态、质量因子和精度指标。

## English Version

# Data Notes

## Phone Directory `phone/<device>`

- `rtklogs.txt`: Raw Android GNSS measurement log.
- `rtklogs.obs`: Phone RINEX observation file.
- `bdrtk_*_station_all.obs`: Base-station RINEX observation file for the corresponding processing session.
- `bdrtk_*.output`: Per-epoch base-station selection and ECEF coordinate records.
- `rtklog.pos`: GNSS RTK solution provided by some phones.

## Truth Directory `true`

- `*.ieout`: Smoothed GNSS/INS integrated solution exported by Inertial Explorer, including position, velocity, attitude, quality factors, and accuracy indicators.
