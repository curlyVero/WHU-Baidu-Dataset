# 数据说明

## 手机目录 `phone/<device>`

- `raw.txt`：Android 风格原始 GNSS 测量记录。
- `sensor.txt`：手机 IMU。列顺序为 `timestamp, gyro_x, gyro_y, gyro_z, acc_x, acc_y, acc_z, sys_time, measurement_time, temperature`；角速度单位 rad/s，加速度单位 m/s²。
- `location.txt`：手机系统定位输出，19 列。
- `rtk_location.txt`：RTK/增强定位位置输出，19 列。
- `satellites.txt`：逐历元卫星状态；一行包含多个以 `|` 分隔的卫星记录。
- `rtk.txt`：RTK 引擎的逐历元、逐卫星中间记录，含嵌套分号字段，不是普通二维 CSV。

## 真值目录 `true`

- `*.ieout`：Inertial Explorer 平滑紧组合 GNSS/INS 结果，包含 WGS84 位置、速度、航向/俯仰/横滚、卫星数、PDOP 和精度指标。

`sensor.txt` 的第一列时间基准和 IMU 轴向定义尚需结合采集程序最终确认。真值文件只删除本机绝对路径，不改数值。

## English Version

# Data Notes

## Phone Directory `phone/<device>`

- `raw.txt`: Android-style raw GNSS measurement records.
- `sensor.txt`: Phone IMU. Column order is `timestamp, gyro_x, gyro_y, gyro_z, acc_x, acc_y, acc_z, sys_time, measurement_time, temperature`; angular rates are in rad/s and accelerations are in m/s².
- `location.txt`: Phone system location output with 19 columns.
- `rtk_location.txt`: RTK/assisted location output with 19 columns.
- `satellites.txt`: Per-epoch satellite status; each line contains multiple satellite records separated by `|`.
- `rtk.txt`: Per-epoch, per-satellite intermediate records from the RTK engine. It contains nested semicolon-delimited fields and is not a conventional two-dimensional CSV.

## Truth Directory `true`

- `*.ieout`: Smoothed tightly integrated GNSS/INS results from Inertial Explorer, including WGS84 position, velocity, heading/pitch/roll, satellite count, PDOP, and accuracy indicators.

The time basis of the first column in `sensor.txt` and the IMU axis convention still require final confirmation against the collection program. Truth files only have local absolute paths removed; their numeric values are unchanged.
