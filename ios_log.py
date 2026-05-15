#!/usr/bin/env python3
"""
iOS 实时日志记录器（追加模式）
基于 pymobiledevice3（纯 Python 实现，无需原生依赖）
控制台和文件都只保存过滤后的行，文件采用追加模式，不覆盖原有内容
"""

import sys
import argparse
import asyncio
import os
import posixpath
from datetime import datetime


def check_pymobiledevice3():
    try:
        import pymobiledevice3
        return True
    except ImportError:
        print("[ERROR] 未安装 pymobiledevice3。", file=sys.stderr)
        print("[INFO] 请运行: pip install pymobiledevice3", file=sys.stderr)
        return False


async def list_devices():
    from pymobiledevice3.usbmux import list_devices as _list_devices

    if asyncio.iscoroutinefunction(_list_devices):
        devices = await _list_devices()
    else:
        devices = _list_devices()

    if not devices:
        print("[ERROR] 没有检测到已连接的 iOS 设备。", file=sys.stderr)
        print("[INFO] 请确保：", file=sys.stderr)
        print("  1. iOS 设备已通过 USB 连接到电脑", file=sys.stderr)
        print("  2. 设备已解锁并信任此电脑", file=sys.stderr)
        return None
    result = []
    for d in devices:
        udid = d.serial
        conn_type = d.connection_type
        result.append(udid)
        print(f"[INFO] 发现设备: {udid} (连接方式: {conn_type})", file=sys.stderr)
    return result


async def create_lockdown(udid=None):
    from pymobiledevice3.lockdown import create_using_usbmux as _create

    if asyncio.iscoroutinefunction(_create):
        return await _create(serial=udid)
    else:
        return _create(serial=udid)


def format_log_line(entry):
    timestamp = entry.timestamp
    pid = entry.pid
    level = entry.level.name
    filename = entry.filename
    image_name = posixpath.basename(entry.image_name) if entry.image_name else ""
    message = entry.message
    process_name = posixpath.basename(filename) if filename else ""

    if image_name:
        return f"{timestamp} {process_name}({image_name})[{pid}] <{level}>: {message}"
    else:
        return f"{timestamp} {process_name}[{pid}] <{level}>: {message}"


async def capture_logs(target_udid, output_file, filter_text):
    from pymobiledevice3.services.os_trace import OsTraceService

    out_file = None
    line_count = 0

    try:
        out_file = open(output_file, 'a', encoding='utf-8')

        separator = f"\n{'=' * 60}\n# iOS Log session started at {datetime.now()}\n# Device: {target_udid}\n{'=' * 60}\n"
        out_file.write(separator)
        out_file.flush()
        print(separator, end='', file=sys.stderr)

        lockdown = await create_lockdown(udid=target_udid)
        os_trace = OsTraceService(lockdown=lockdown)

        async for entry in os_trace.syslog():
            line_str = format_log_line(entry)
            if not line_str.endswith('\n'):
                line_str += '\n'
            if filter_text and filter_text.lower() not in line_str.lower():
                continue
            line_count += 1
            sys.stdout.write(line_str)
            sys.stdout.flush()
            out_file.write(line_str)
            out_file.flush()

    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"[ERROR] 发生异常: {e}", file=sys.stderr)
    finally:
        end_mark = f"\n# iOS Log session ended at {datetime.now()}\n{'=' * 60}\n"
        if out_file:
            out_file.write(end_mark)
            out_file.flush()
        print(f"\n[INFO] 已捕获 {line_count} 行日志，正在退出...", file=sys.stderr)
        if out_file:
            out_file.close()


async def main():
    parser = argparse.ArgumentParser(
        description='实时记录 iOS 设备系统日志到文件并显示（追加模式）',
        epilog='示例: python ios_log.py -o ios.log --filter "MyApp"'
    )
    parser.add_argument('-o', '--output-file', default=None, help='输出日志文件路径（默认自动生成: iOS_年月日时分秒.log）')
    parser.add_argument('--filter', default=None, help='只显示包含该字符串的行（不区分大小写）')
    parser.add_argument('--udid', default=None, help='指定设备的 UDID（多设备时需要）')
    args, unknown = parser.parse_known_args()

    if not check_pymobiledevice3():
        sys.exit(1)

    udids = await list_devices()
    if udids is None:
        sys.exit(1)

    target_udid = args.udid
    if target_udid:
        if target_udid not in udids:
            print(f"[ERROR] 指定的 UDID {target_udid} 不在已连接设备列表中。", file=sys.stderr)
            sys.exit(1)
    else:
        target_udid = udids[0]
        if len(udids) > 1:
            print(f"[INFO] 多设备连接，默认使用第一台: {target_udid}", file=sys.stderr)
            print(f"[INFO] 可使用 --udid 参数指定设备", file=sys.stderr)

    print(f"[INFO] 开始捕获 iOS 设备 {target_udid} 的实时日志...", file=sys.stderr)

    output_file = args.output_file or f"iOS_{datetime.now().strftime('%Y%m%d')}/iOS_{datetime.now().strftime('%Y%m%d%H%M%S')}.log"
    os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)

    task = asyncio.create_task(
        capture_logs(target_udid, output_file, args.filter)
    )

    try:
        await task
    except KeyboardInterrupt:
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass