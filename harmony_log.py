#!/usr/bin/env python3
"""
HarmonyOS hilog 实时记录器（追加模式）
使用 hdc hilog 捕获原生鸿蒙设备实时日志
控制台和文件都只保存过滤后的行，文件采用追加模式，不覆盖原有内容
"""

import subprocess
import sys
import argparse
import os
import signal
from datetime import datetime


def check_devices():
    result = subprocess.run(['hdc', 'list', 'targets'], capture_output=True, text=True)
    lines = result.stdout.strip().split('\n')
    devices = [line for line in lines if line.strip()]
    if not devices:
        print("[ERROR] 没有检测到已连接的 HarmonyOS 设备，请运行 'hdc list targets' 检查。", file=sys.stderr)
        return False
    print(f"[INFO] 检测到 {len(devices)} 台 HarmonyOS 设备", file=sys.stderr)
    return True


def main():
    parser = argparse.ArgumentParser(description='实时记录 HarmonyOS hilog 日志到文件并显示（追加模式）')
    parser.add_argument('-o', '--output-file', default=None, help='输出日志文件路径（默认自动生成: HarmonyOS_年月日时分秒.log）')
    parser.add_argument('--filter', default=None, help='只显示包含该字符串的行（不区分大小写）')
    parser.add_argument('--domain', default=None, help='按 domain 过滤（如 0x0001）')
    parser.add_argument('--tag', default=None, help='按 tag 过滤')
    parser.add_argument('--level', default=None, choices=['D', 'I', 'W', 'E', 'F'], help='最低日志级别（D/I/W/E/F）')
    args, unknown = parser.parse_known_args()

    if not check_devices():
        sys.exit(1)

    cmd = ['hdc', 'hilog']

    if args.domain:
        cmd += ['-D', args.domain]
    if args.tag:
        cmd += ['-T', args.tag]
    if args.level:
        cmd += ['-L', args.level]

    cmd += unknown

    print(f"[INFO] 执行命令: {' '.join(cmd)}", file=sys.stderr)

    output_file = args.output_file or f"HarmonyOS_{datetime.now().strftime('%Y%m%d')}/HarmonyOS_{datetime.now().strftime('%Y%m%d%H%M%S')}.log"
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

    out_file = None
    process = None
    line_count = 0

    try:
        out_file = open(output_file, 'a', encoding='utf-8')

        separator = f"\n{'=' * 60}\n# HarmonyOS Log session started at {datetime.now()}\n{'=' * 60}\n"
        out_file.write(separator)
        out_file.flush()
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
            end_mark = f"\n# HarmonyOS Log session ended at {datetime.now()}\n{'=' * 60}\n"
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
        print("[ERROR] 找不到 hdc 命令，请确保 HarmonyOS SDK 已安装且 hdc 在 PATH 中。", file=sys.stderr)
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


# # 基本用法
# python harmony_log.py -o harmony.log

# # 文本过滤
# python harmony_log.py -o harmony.log --filter "MyAbility"

# # 按 domain 过滤
# python harmony_log.py -o harmony.log --domain 0x0001

# # 按日志级别过滤（只显示 Warn 及以上）
# python harmony_log.py -o harmony.log --level W

# # 组合使用
# python harmony_log.py -o harmony.log --filter "调用" --domain 0x0001 --level I