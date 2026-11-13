# -*- coding: utf-8 -*-
"""
从《四柱命卦（倪海厦解读）》文档提取六十四卦命卦数据
生成 mingua_data.py 文件
"""

from docx import Document
import re
import os


# 六十四卦名称列表（标准名，用于匹配）
HEXAGRAM_NAMES = [
    "乾为天", "坤为地", "水雷屯", "山水蒙", "水天需", "天水讼",
    "地水师", "水地比", "风天小畜", "天泽履", "地天泰", "天地否",
    "天火同人", "火天大有", "地山谦", "雷地豫", "泽雷随", "山风蛊",
    "地泽临", "风地观", "火雷噬嗑", "山火贲", "山地剥", "地雷复",
    "天雷无妄", "山天大畜", "山雷颐", "泽风大过", "坎为水", "离为火",
    "泽山咸", "雷风恒", "天山遁", "雷天大壮", "火地晋", "地火明夷",
    "风火家人", "火泽睽", "水山蹇", "雷水解", "山泽损", "风雷益",
    "泽天夬", "天风姤", "泽地萃", "地风升", "泽水困", "水风井",
    "泽火革", "火风鼎", "震为雷", "艮为山", "风山渐", "雷泽归妹",
    "雷火丰", "火山旅", "巽为风", "兑为泽", "风水涣", "水泽节",
    "风泽中孚", "雷山小过", "水火既济", "火水未济"
]


def extract_minggua_data(docx_path):
    """从 docx 文件提取命卦数据"""
    doc = Document(docx_path)
    
    # 读取所有非空段落
    paragraphs = []
    for p in doc.paragraphs:
        text = p.text.strip()
        if text:
            paragraphs.append(text)
    
    # 构建卦名到段落索引的映射
    # 匹配格式: "1.卦名" 或 "1.卦名。" 或 "1.卦名：" 等
    name_to_start = {}
    for idx, para in enumerate(paragraphs):
        for seq, name in enumerate(HEXAGRAM_NAMES):
            # 直接匹配（无后缀）
            if para.startswith(f'{seq+1}.{name}'):
                name_to_start[name] = idx
                break
            # 带句号匹配
            if para.startswith(f'{seq+1}.{name}。'):
                name_to_start[name] = idx
                break
            # 带冒号匹配
            if para.startswith(f'{seq+1}.{name}：'):
                name_to_start[name] = idx
                break
    
    print(f"匹配到 {len(name_to_start)}/{len(HEXAGRAM_NAMES)} 个卦名")
    
    # 解析每个卦的三个部分
    results = {}
    
    for i, name in enumerate(HEXAGRAM_NAMES):
        start_idx = name_to_start.get(name)
        if start_idx is None:
            print(f"  ⚠️ 未找到卦名: {name}")
            results[name] = {"xiantian": "", "houtian": "", "liunian": ""}
            continue
        
        # 找到下一个卦的起始位置
        if i + 1 < len(HEXAGRAM_NAMES):
            next_name = HEXAGRAM_NAMES[i + 1]
            end_idx = name_to_start.get(next_name, len(paragraphs))
        else:
            end_idx = len(paragraphs)
        
        # 提取该卦的段落（跳过标题行）
        section = paragraphs[start_idx + 1:end_idx]
        
        # 解析三部分
        xiantian_parts = []
        houtian_parts = []
        liunian_parts = []
        
        current_section = None
        for line in section:
            # 检测段落标题
            if '先天卦' in line:
                current_section = 'xiantian'
                content = re.sub(r'先天卦[：:]', '', line).strip()
                if content:
                    xiantian_parts.append(content)
            elif '后天卦' in line:
                current_section = 'houtian'
                content = re.sub(r'后天卦[：:]', '', line).strip()
                if content:
                    houtian_parts.append(content)
            elif '流年卦' in line or '值年卦' in line:
                current_section = 'liunian'
                content = re.sub(r'(流年卦|值年卦)[：:]', '', line).strip()
                if content:
                    liunian_parts.append(content)
            else:
                # 续行内容
                if current_section == 'xiantian':
                    xiantian_parts.append(line)
                elif current_section == 'houtian':
                    houtian_parts.append(line)
                elif current_section == 'liunian':
                    liunian_parts.append(line)
        
        results[name] = {
            "xiantian": ''.join(xiantian_parts),
            "houtian": ''.join(houtian_parts),
            "liunian": ''.join(liunian_parts),
        }
    
    return results


def generate_python_file(results):
    """生成 mingua_data.py 文件"""
    
    lines = []
    lines.append('# -*- coding: utf-8 -*-')
    lines.append('"""')
    lines.append('minggua_data.py')
    lines.append('=================')
    lines.append('六十四卦命卦数据（倪海厦解读）')
    lines.append('')
    lines.append('数据来源: 《四柱命卦（倪海厦解读，易友编）》')
    lines.append('')
    lines.append('每个卦包含:')
    lines.append('  - xiantian: 先天卦（出生命理、性格特征、六亲缘分）')
    lines.append('  - houtian:  后天卦（事业财运、婚姻、人生轨迹）')
    lines.append('  - liunian:  流年卦（年度运势、吉凶提示、天机）')
    lines.append('')
    lines.append('# 注意: 数据来源于倪海厦易学体系，属于命理预测参考，')
    lines.append('# 非《周易》六十四卦本义。使用时应与卦辞、爻辞等分开看待。')
    lines.append('"""')
    lines.append('')
    lines.append('# ============================================================')
    lines.append('# 六十四卦命卦数据（倪海厦解读）')
    lines.append('# ============================================================')
    lines.append('')
    lines.append('MINGUA_DATA = {')
    
    for i, name in enumerate(HEXAGRAM_NAMES):
        data = results.get(name, {})
        xiantian = data.get('xiantian', '')
        houtian = data.get('houtian', '')
        liunian = data.get('liunian', '')
        
        lines.append(f'    # 第{i+1:02d}卦 {name}')
        lines.append(f'    "{name}": {{')
        lines.append(f'        "xiantian": """{xiantian}""",')
        lines.append(f'        "houtian": """{houtian}""",')
        lines.append(f'        "liunian": """{liunian}""",')
        lines.append(f'    }},')
        lines.append('')
    
    lines.append('}')
    lines.append('')
    
    return '\n'.join(lines)


def main():
    # 查找文档
    possible_paths = [
        r'C:\Users\bj_zz\Desktop\四柱命卦 (倪海厦解读，易友编)  conv.docx',
        r'D:\AI_Projects\yijing-web\四柱命卦 (倪海厦解读，易友编) conv.docx',
    ]
    
    docx_path = None
    for p in possible_paths:
        if os.path.exists(p):
            docx_path = p
            break
    
    if not docx_path:
        print(f'未找到文档，尝试路径:')
        for p in possible_paths:
            print(f'  {p}')
        return
    
    print(f'使用文档: {docx_path}')
    
    # 提取数据
    print('正在提取命卦数据...')
    results = extract_minggua_data(docx_path)
    
    # 生成 Python 文件
    py_content = generate_python_file(results)
    
    # 输出路径：与 hexagram_data.py 同级
    output_path = r'D:\AI_Projects\yijing-web\minggua_data.py'
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(py_content)
    
    print(f'\n已生成: {output_path}')
    
    # 统计
    total_xt = total_ht = total_ln = 0
    for name in HEXAGRAM_NAMES:
        data = results.get(name, {})
        xt = len(data.get('xiantian', ''))
        ht = len(data.get('houtian', ''))
        ln = len(data.get('liunian', ''))
        total_xt += xt
        total_ht += ht
        total_ln += ln
        status = '✓' if (xt + ht + ln) > 0 else '✗'
        print(f'  {status} {name}: 先天={xt} 后天={ht} 流年={ln}')
    
    print(f'\n总计: 先天={total_xt} 后天={total_ht} 流年={total_ln}')


if __name__ == '__main__':
    main()
