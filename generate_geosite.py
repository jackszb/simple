#!/usr/bin/env python3
import re
import requests
import json
import os
import subprocess
import sys

output_dir = "./rule-set"
url = "https://raw.githubusercontent.com/felixonmars/dnsmasq-china-list/master/accelerated-domains.china.conf"

json_path = os.path.join(output_dir, "geosite-direct.json")
srs_path = os.path.join(output_dir, "geosite-direct.srs")

# geosite-private（内置）
geosite_private = [
    "localhost",
    "local",
    "localdomain",
    "lan",
    "home.arpa",
    "in-addr.arpa",
    "ip6.arpa",
    "test",
    "example",
    "invalid",
]

os.makedirs(output_dir, exist_ok=True)

# 1. 下载数据（失败直接退出）
resp = requests.get(url, timeout=60)
resp.raise_for_status()

domain_suffix_list = []

for line in resp.text.splitlines():
    if not line or line.startswith("#"):
        continue

    # 精确匹配 dnsmasq 规则
    m = re.match(r"server=/([^/]+)/", line)
    if not m:
        continue

    domain = m.group(1)

    if domain.startswith("www."):
        domain = domain[4:]

    domain_suffix_list.append(domain)

# 合并内置域名
domain_suffix_list.extend(geosite_private)

# 去重 + 排序
domain_suffix_list = sorted(set(domain_suffix_list))

if not domain_suffix_list:
    print("ERROR: domain list is empty")
    sys.exit(1)

print(f"Number of domains processed: {len(domain_suffix_list)}")

# 2. 构建 JSON（保持你现有结构）
result = {
    "version": 3,
    "rules": [
        {
            "domain_suffix": domain_suffix_list
        }
    ]
}

new_json = json.dumps(result, indent=4, ensure_ascii=False) + "\n"

# 3. 写入 JSON（无论是否变化，都覆盖）
with open(json_path, "w", encoding="utf-8") as f:
    f.write(new_json)

json_size = os.path.getsize(json_path)
print(f"JSON size: {json_size} bytes")

if json_size < 1000:
    print("ERROR: JSON size too small, abort")
    sys.exit(1)

# 4. 【关键修复】始终重新编译 srs（不再依赖 diff）
print("Compiling srs...")
subprocess.run(
    ["sing-box", "rule-set", "compile", "--output", srs_path, json_path],
    check=True
)

# 5. 强校验 srs 大小
if not os.path.exists(srs_path):
    print("ERROR: srs not generated")
    sys.exit(1)

srs_size = os.path.getsize(srs_path)
print(f"SRS size: {srs_size} bytes")

if srs_size < 100:
    print("ERROR: srs file too small (likely empty)")
    sys.exit(1)

print("geosite-direct updated successfully.")
