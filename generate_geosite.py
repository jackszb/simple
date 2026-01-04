#!/usr/bin/env python3
import re
import requests
import json
import os
import subprocess

output_dir = "./rule-set"
url = "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf"

json_path = os.path.join(output_dir, "geosite-direct.json")
srs_path = os.path.join(output_dir, "geosite-direct.srs")

# geosite-private（内置，规范 & 稳定）
geosite_private = [
    # RFC / IANA 保留
    "localhost",
    "local",
    "localdomain",
    "lan",

    # ARPA / DNS 基础设施
    "home.arpa",
    "in-addr.arpa",
    "ip6.arpa",

    # RFC 2606 / 6761
    "test",
    "example",
    "invalid",
]

# 创建输出目录
os.makedirs(output_dir, exist_ok=True)

# 下载并解析
r = requests.get(url, timeout=60)
r.raise_for_status()

domain_suffix_list = []

for line in r.text.splitlines():
    if line.startswith("#"):
        continue

    m = re.match(r"server=\/(.*)\/.*", line)
    if not m:
        continue

    domain = m.group(1)

    # 去掉开头的 www.
    if domain.startswith("www."):
        domain = domain[4:]

    domain_suffix_list.append(domain)

# 合并 geosite-private
domain_suffix_list.extend(geosite_private)

# 去重（保持稳定顺序）
domain_suffix_list = list(dict.fromkeys(domain_suffix_list))

# 排序（保证输出稳定）
domain_suffix_list.sort()

# 构建规则
result = {
    "version": 3,
    "rules": [
        {
            "domain_suffix": domain_suffix_list
        }
    ]
}

print(f"Number of domains processed: {len(domain_suffix_list)}")

# 格式化 JSON
new_json = json.dumps(result, indent=4, ensure_ascii=False) + "\n"

# 判断是否变化
if os.path.exists(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        old_json = f.read()
else:
    old_json = ""

if new_json != old_json:
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(new_json)

    subprocess.run(
        ["sing-box", "rule-set", "compile", "--output", srs_path, json_path],
        check=True
    )
    print("Updated files.")
else:
    print("No changes detected, skip update.")
