# City Dataset 2024

> release_version

城市车辆场景下的多手机 GNSS 数据集。数据按采集日期组织，每个日期下的 `phone` 保存手机观测与处理文件。当前发布版本不包含真值数据。

```text
YYYYMMDD/
  phone/<device>/
```

手机数据包含原始 Android GNSS 日志、RINEX 观测、基准站观测、基准站选择辅助记录和部分 RTK 解算结果。

## English Version

# City Dataset 2024

> release_version

A multi-phone GNSS dataset collected in urban vehicle scenarios. Data are organized by collection date, and `phone` under each date contains phone observations and processing files. Truth data are not included in the current public release.

```text
YYYYMMDD/
  phone/<device>/
```

Phone data include raw Android GNSS logs, RINEX observations, base-station observations, auxiliary base-station selection records, and RTK solutions for some phones.
