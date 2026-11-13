# -*- coding: utf-8 -*-
"""测试 HEXAGRAM_DATA 和 HEXAGRAM_LINES 查找"""
import sys
sys.stdout.reconfigure(encoding='utf-8')

from hexagram_data import HEXAGRAM_DATA
from hexagram_lines import HEXAGRAM_LINES
from core import find_hexagram

# 测试 艮为山
name = '艮为山'
print(f'Testing hexagram: {name}')
print(f'In HEXAGRAM_DATA: {name in HEXAGRAM_DATA}')
if name in HEXAGRAM_DATA:
    d = HEXAGRAM_DATA[name]
    print(f'  Judgment: {d.get("judgment", "")[:30]}')
    print(f'  Xiang: {d.get("xiang_comment", "")}')
    print(f'  Line types: {d.get("line_type", [])}')
print(f'In HEXAGRAM_LINES: {name in HEXAGRAM_LINES}')
if name in HEXAGRAM_LINES:
    lines = HEXAGRAM_LINES[name]
    print(f'  Lines count: {len(lines)}')
    print(f'  Line 3 (index 2): {lines[2] if len(lines) > 2 else "N/A"}')

# 测试 find_hexagram 返回
result = find_hexagram('艮', '艮')
print(f'\nfind_hexagram("艮", "艮"): {result}')
if result:
    print(f'  name: {result.get("name")}')
    print(f'  judgment: {result.get("judgment", "")[:30]}')
    
    # 查找 HEXAGRAM_DATA
    hx_data = HEXAGRAM_DATA.get(result['name'], {})
    print(f'\nHEXAGRAM_DATA.get("{result["name"]}"):')
    print(f'  xiang_comment: {hx_data.get("xiang_comment", "")}')
    print(f'  line_type: {hx_data.get("line_type", [])}')
