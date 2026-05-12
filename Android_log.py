# !/usr/bin/env python3
"""
Android Logcat 实时记录器（追加模式）
控制台和文件都只保存过滤后的行，文件采用追加模式，不覆盖原有内容
"""

import subprocess
import sys
import argparse
import signal
from datetime import datetime


def check_devices():
    result = subprocess.run(['adb', 'devices'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')[1:]
    devices = [line for line in lines if line.strip() and 'device' in line]
    if not devices:
        print("[ERROR] 没有检测到已连接的 Android 设备，请运行 'adb devices' 检查。", file=sys.stderr)
        return False
    return True


def main():
    parser = argparse.ArgumentParser(description='实时记录 Android logcat 日志到文件并显示（追加模式）')
    parser.add_argument('-o', '--output-file', required=True, help='输出日志文件路径')
    parser.add_argument('--filter', default=None, help='只显示包含该字符串的行（不区分大小写）')
    args, unknown = parser.parse_known_args()

    if not check_devices():
        sys.exit(1)

    cmd = ['adb', 'logcat'] + unknown
    print(f"[INFO] 执行命令: {' '.join(cmd)}", file=sys.stderr)

    out_file = None
    process = None
    line_count = 0

    try:
        # 修改点：使用 'a' 模式追加，而不是 'w' 覆盖
        out_file = open(args.output_file, 'a', encoding='utf-8')

        # 可选：在文件开头写入一条分隔线和启动时间，便于区分多次运行
        separator = f"\n{'=' * 60}\n# Log session started at {datetime.now()}\n{'=' * 60}\n"
        out_file.write(separator)
        out_file.flush()
        # 同时也在控制台打印这条分隔线（可选，便于观察）
        print(separator, end='', file=sys.stderr)

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding='utf-8',
            errors='replace',
            bufsize=1
        )

        def signal_handler(sig, frame):
            # 可选：在退出时也写入一条结束标记
            end_mark = f"\n# Log session ended at {datetime.now()}\n{'=' * 60}\n"
            if out_file:
                out_file.write(end_mark)
                out_file.flush()
            print(f"\n[INFO] 已捕获 {line_count} 行日志，正在退出...", file=sys.stderr)
            if process:
                process.terminate()
            if out_file:
                out_file.close()
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)

        for line in process.stdout:
            if args.filter and args.filter.lower() not in line.lower():
                continue
            line_count += 1
            sys.stdout.write(line)
            sys.stdout.flush()
            out_file.write(line)
            out_file.flush()

    except FileNotFoundError:
        print("[ERROR] 找不到 adb 命令，请确保 Android SDK 已安装且 adb 在 PATH 中。", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] 发生异常: {e}", file=sys.stderr)
    finally:
        if process:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
        if out_file:
            out_file.close()


if __name__ == '__main__':
    main()
    
# python Android_log.py -o Android_log.log --filter "CommAdSDKOver"

# python Android_log.py -o Android_log.log