#!/usr/bin/env python3
"""跨平台数据源路径解析。

Agent Monitor 需要读取 Hermes / OpenCode 的 SQLite 库和配置文件，
但这些文件在不同操作系统上的位置不同。本模块负责：
  1. 展开路径里的 `~`（家目录）和 `%VAR%` / `$VAR`（环境变量）；
  2. 当配置里写 `auto`（或配置的路径在当前机器不存在）时，
     按当前系统自动探测默认路径。

这样同一份 config.yaml 可以同时在 Windows / macOS / Linux 上使用，
不用每次换机器都改路径。
"""

import os
import sys

# 各系统下 Hermes / OpenCode 的默认路径。
# 结构：数据源名 → 平台名 → {db, config}
PLATFORM_DEFAULTS = {
    'hermes': {
        'win32': {
            'db': '%LOCALAPPDATA%\\hermes\\state.db',
            'config': '%LOCALAPPDATA%\\hermes\\config.yaml',
        },
        'darwin': {
            'db': '~/.hermes/state.db',
            'config': '~/.hermes/config.yaml',
        },
        'linux': {
            'db': '~/.hermes/state.db',
            'config': '~/.hermes/config.yaml',
        },
    },
    'opencode': {
        'win32': {
            'db': '%USERPROFILE%\\.local\\share\\opencode\\opencode.db',
            'config': '%USERPROFILE%\\.config\\opencode\\opencode.jsonc',
        },
        'darwin': {
            'db': '~/.local/share/opencode/opencode.db',
            'config': '~/.config/opencode/opencode.json',
        },
        'linux': {
            'db': '~/.local/share/opencode/opencode.db',
            'config': '~/.config/opencode/opencode.json',
        },
    },
}


def get_platform() -> str:
    """返回当前平台名：win32 / darwin / linux。"""
    if sys.platform.startswith('win'):
        return 'win32'
    if sys.platform == 'darwin':
        return 'darwin'
    return 'linux'


def expand_path(path):
    """展开路径里的 `~` 和环境变量（`%VAR%`、`$VAR`、`${VAR}`）。"""
    if not path:
        return path
    return os.path.expandvars(os.path.expanduser(str(path)))


def resolve_path(kind, configured, key):
    """解析某个数据源的 db/config 实际路径。

    参数：
      kind       'hermes' 或 'opencode'
      configured  config.yaml 里写的那一档值（'auto'、空串、或显式绝对路径）
      key        'db' 或 'config'

    规则（优先级从高到低）：
      1. 配置里写 `auto` 或留空 → 直接用当前平台的默认路径；
      2. 否则展开配置里的 `~` / 环境变量，若该文件存在则用它；
      3. 若配置的路径在当前机器不存在 → 退回当前平台的默认路径
         （典型场景：换了一台机器，旧路径失效）。
    """
    platform = get_platform()
    default = PLATFORM_DEFAULTS.get(kind, {}).get(platform, {}).get(key)

    if configured in (None, '', 'auto'):
        return expand_path(default) if default else ''

    expanded = expand_path(configured)
    if os.path.exists(expanded):
        return expanded

    # 显式路径不存在 → 退回默认；没有默认就保留原值让调用方报「找不到」
    return expand_path(default) if default else expanded
