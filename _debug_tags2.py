# -*- coding: utf-8 -*-
import ast

FP = r"E:\Test_git\appointment\templates\appointment\schedules\list.html"

# === 1. 读字节 + 读文本，检查 BOM 和前两行 ===
with open(FP, "rb") as f:
    raw = f.read(600)
with open(FP, "r", encoding="utf-8") as f:
    text_lines = f.readlines()

print("=== 1. 文件头部字节（60字节）===")
print(" ", raw[:60].hex(" "))
print(f"   BOM check: 前3字节是 EF BB BF? {raw[:3] == b'\\xef\\xbb\\xbf'}")

print()
print("=== 2. 文本前3行 repr（逐字符看）===")
for i, l in enumerate(text_lines[:3], 1):
    print(f"  L{i} len={len(l)}: {repr(l)}")

# === 3. 把第1行按字符展开，查全角空格（\u3000）或奇怪字符 ===
print()
print("=== 3. 第1行逐字符编码排查 === ")
ln1 = text_lines[0].rstrip("\r\n")
bad = []
for pos, ch in enumerate(ln1):
    code = ord(ch)
    # 正常半角 ASCII 打印字符范围 32-126；另外允许 { } % 等都是ASCII；中文允许但这里第一行不该有中文
    if not (32 <= code <= 126):
        bad.append((pos, ch, code, repr(ch)))
if bad:
    for b in bad:
        print(f"  ❌ pos{b[0]}: char={b[1]!r}  U+{b[2]:04X}")
else:
    print("  ✅ 全是正常 ASCII，没有全角空格等异常字符")

# === 4. 检查第1行是否包含 load clinic_tags 的完整字面 ===
target = "{% load clinic_tags %}"
print()
print(f"=== 4. 第1行是否包含 '{target}' ===")
print(f"  包含? {target in ln1}")
if target not in ln1:
    print(f"  可能字符对不上。逐段比较：")
    # 在 ln1 里找相似度最高的一段
    for i in range(len(ln1) - len(target) + 1):
        seg = ln1[i:i+len(target)]
        diffs = [(j, seg[j], target[j]) for j in range(len(target)) if seg[j] != target[j]]
        if len(diffs) <= 5:
            print(f"  位置 {i} 疑似片段 {seg!r}  差异点: {diffs}")

# === 5. 检查 clinic_tags.py 能否被正常 import（纯语法检查）===
print()
print("=== 5. clinic_tags.py 语法检查 & 过滤器存在性 ===")
TAG_FILE = r"E:\Test_git\appointment\templatetags\clinic_tags.py"
with open(TAG_FILE, "r", encoding="utf-8") as f:
    src = f.read()
try:
    tree = ast.parse(src)
    print("  ✅ 语法解析成功")
except SyntaxError as e:
    print(f"  ❌ 语法错误: {e}")

# 在 AST 里找名字是 get_item 的函数/装饰器
found_get_item = False
for node in ast.walk(tree):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "get_item":
        found_get_item = True
        deco_names = []
        for d in node.decorator_list:
            if isinstance(d, ast.Attribute):
                deco_names.append(d.attr)
            elif isinstance(d, ast.Name):
                deco_names.append(d.id)
            elif isinstance(d, ast.Call):
                fn = d.func
                if isinstance(fn, ast.Attribute):
                    deco_names.append(fn.attr)
                elif isinstance(fn, ast.Name):
                    deco_names.append(fn.id)
        print(f"  ✅ 找到 get_item 函数，装饰器: {deco_names}")
if not found_get_item:
    print("  ❌ 没找到 get_item 函数")

# === 6. 检查 templatetags/__init__.py 是否存在且可解析 ===
print()
print("=== 6. templatetags/__init__.py ===")
INIT_FILE = r"E:\Test_git\appointment\templatetags\__init__.py"
import os
print(f"  存在? {os.path.exists(INIT_FILE)}  大小? {os.path.getsize(INIT_FILE) if os.path.exists(INIT_FILE) else 'N/A'} bytes")
