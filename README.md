# 日志工具

实时捕获 Android / iOS / HarmonyOS 设备日志，支持过滤、追加写入、按天归档。

## 项目结构

```
iOSLog/
├── Android_log.py      # Android logcat 日志工具
├── ios_log.py          # iOS 系统日志工具
├── harmony_log.py      # HarmonyOS hilog 日志工具
└── README.md
```

## 环境依赖

| 平台 | 依赖 | 安装方式 |
|---|---|---|
| Android | Android SDK (adb) | [Android Studio](https://developer.android.com/studio) 或 [SDK Platform Tools](https://developer.android.com/tools/releases/platform-tools) |
| iOS | pymobiledevice3 | `pip install pymobiledevice3` |
| HarmonyOS | HarmonyOS SDK (hdc) | [DevEco Studio](https://developer.huawei.com/consumer/cn/deveco-studio/) 或 [Command Line Tools](https://developer.huawei.com/consumer/cn/download/) |

> Python 版本要求：3.8+

## 快速开始

### Android

```bash
# 自动生成文件名，按天归档到 Android_20260515/ 目录
python Android_log.py

# 文本过滤
python Android_log.py --filter "MyActivity"

# 指定输出文件
python Android_log.py -o my_android.log --filter "Error"
```

### iOS

```bash
# 自动生成文件名，按天归档到 iOS_20260515/ 目录
python ios_log.py

# 文本过滤
python ios_log.py --filter "MyApp"

# 指定设备和输出文件
python ios_log.py --udid 00008020-0015503826D2002E -o my_ios.log --filter "调用"
```

### HarmonyOS

```bash
# 自动生成文件名，按天归档到 HarmonyOS_20260515/ 目录
python harmony_log.py

# 文本过滤
python harmony_log.py --filter "MyAbility"

# 按 domain / tag / 级别过滤
python harmony_log.py --domain 0x0001 --tag MyTag --level W

# 组合使用
python harmony_log.py --filter "调用" --domain 0x0001 --level I
```

## 参数说明

### 通用参数（三个工具均支持）

| 参数 | 说明 |
|---|---|
| `-o, --output-file` | 输出日志文件路径。可选，默认自动生成 `{平台}_{年月日}/{平台}_{年月日时分秒}.log` |
| `--filter` | 文本过滤，只保留包含该字符串的行（不区分大小写） |

### iOS 专属参数

| 参数 | 说明 |
|---|---|
| `--udid` | 指定设备 UDID，多设备时必须指定 |

### HarmonyOS 专属参数

| 参数 | 说明 |
|---|---|
| `--domain` | 按 domain 过滤，如 `0x0001` |
| `--tag` | 按 tag 过滤 |
| `--level` | 最低日志级别，可选 `D` / `I` / `W` / `E` / `F` |

## 日志文件组织

不指定 `-o` 时，日志自动按天归档：

```
iOSLog/
├── Android_20260515/
│   ├── Android_20260515102030.log
│   └── Android_20260515143015.log
├── iOS_20260515/
│   └── iOS_20260515151713.log
└── HarmonyOS_20260515/
    └── HarmonyOS_20260515152245.log
```

每次启动会在文件末尾追加，不会覆盖已有内容。每次会话以分隔线和时间戳标记起止。

## 退出

按 `Ctrl + C` 优雅退出，会自动写入结束标记并关闭文件。

## 常见问题

### Android

- **找不到 adb**：确保 Android SDK 已安装且 `adb` 在 PATH 中，运行 `adb devices` 验证
- **设备未检测到**：检查 USB 连接，确保设备已开启 USB 调试模式

### iOS

- **找不到 pymobiledevice3**：运行 `pip install pymobiledevice3`
- **设备未检测到**：确保设备已通过 USB 连接、解锁并信任此电脑
- **没有日志输出**：iOS 13+ 使用 OsTrace 服务，工具已自动适配

### HarmonyOS

- **找不到 hdc**：确保 HarmonyOS SDK 已安装且 `hdc` 在 PATH 中，运行 `hdc list targets` 验证
- **设备未检测到**：检查 USB 连接，确保设备已开启 USB 调试模式