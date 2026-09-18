# 数据说明

## 手机目录 `phone/<device>`

- `rtklogs.txt`：Android 原始 GNSS 测量日志。
- `rtklogs.obs`：手机 RINEX 观测文件。
- `bdrtk_*_station_all.obs`：对应处理会话的基准站 RINEX 观测文件。
- `bdrtk_*.output`：生成对应基准站观测文件时产生的辅助记录，包含导航/基准站索引、逐历元基准站选择和 ECEF 坐标；不是 RTK 位置解。
- `rtklog.pos`：部分手机提供的 GNSS RTK 解算结果。

## 真值

当前发布版本不包含真值数据。

## English Version

# Data Notes

## Phone Directory `phone/<device>`

- `rtklogs.txt`: Raw Android GNSS measurement log.
- `rtklogs.obs`: Phone RINEX observation file.
- `bdrtk_*_station_all.obs`: Base-station RINEX observation file for the corresponding processing session.
- `bdrtk_*.output`: Auxiliary records produced while generating the corresponding base-station observation file. They contain navigation/base-station indices, per-epoch station selections, and ECEF coordinates; they are not RTK position solutions.
- `rtklog.pos`: GNSS RTK solution provided by some phones.

## Truth Data

Truth data are not included in the current public release.
