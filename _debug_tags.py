import os
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "clinic_management.settings")
import django
django.setup()
from django.template import engines, Template, TemplateSyntaxError
from pathlib import Path

FP = r"E:\Test_git\appointment\templates\appointment\schedules\list.html"

print("=== 1. 磁盘文件前2行 repr（检查隐藏字符）===")
with open(FP, "r", encoding="utf-8") as f:
    lines = f.readlines()
for i, l in enumerate(lines[:2], 1):
    print(f"  L{i}: {repr(l)}")

print()
print("=== 2. 单独测试 clinic_tags 能否加载/get_item 能否工作 ===")
try:
    t = Template("{% load clinic_tags %}{% with d=\"a\" %}{{ {'a':1,'b':2}|get_item:d }}{% endwith %}")
    out = t.render()
    print(f"  OK, result: {out!r}")
except Exception as e:
    print(f"  FAIL {type(e).__name__}: {e}")

print()
print("=== 3. Django loader 读取 schedules/list.html 的前200字符 ===")
engine = engines["django"].engine
# 先用 app_directories loader 找到源文件路径直接读
import django.template.loaders.app_directories as ad
loader = ad.Loader(engine)
sources = list(loader.get_template_sources("appointment/schedules/list.html"))
print(f"  找到了 {len(sources)} 个候选源")
for idx, origin in enumerate(sources):
    print(f"  [{idx}] Origin: {origin.name}")
    try:
        with open(origin.name, "r", encoding="utf-8") as f:
            head = f.read(250)
        print(f"       内容前250字符 repr: {repr(head)}")
    except Exception as e:
        print(f"       读失败: {e}")

print()
print("=== 4. 让 Django 真正编译 schedules/list.html ===")
try:
    tmpl = engine.get_template("appointment/schedules/list.html")
    print("  编译成功！没有语法错误")
except TemplateSyntaxError as e:
    print(f"  TemplateSyntaxError: {e}")
except Exception as e:
    print(f"  其他错误 {type(e).__name__}: {e}")
