# City Dataset 2024

> release_version

城市车辆场景下的多手机 GNSS 数据集。数据按采集日期组织；每个日期下的 `phone` 是手机观测与处理文件，`true` 是该日期可用的 GNSS/INS 真值。

```text
YYYYMMDD/
  phone/<device>/
  true/<date>.ieout
```

手机数据包含原始 Android GNSS 日志、RINEX 观测、基准站观测、基准站切换记录和部分 RTK 解算结果。

## English Version

# City Dataset 2024

> release_version

A multi-phone GNSS dataset collected in urban vehicle scenarios. Data are organized by collection date; under each date, `phone` contains phone observation and processing files, while `true` contains the GNSS/INS truth available for that date.

```text
YYYYMMDD/
  phone/<device>/
  true/<date>.ieout
```

Phone data include raw Android GNSS logs, RINEX observations, base-station observations, base-station switching records, and RTK solutions for some phones.
