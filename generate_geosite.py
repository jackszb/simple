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

os.makedirs(output_dir, exist_ok=True)

# 下载并解析
r = requests.get(url)
domain_suffix_list = []
for line in r.text.splitlines():
    if not line.startswith("#"):
        m = re.match(r"server=\/(.*)\/.*", line)
        if m:
            domain = m.group(1)
            # 去掉开头的 www.
            if domain.startswith("www."):
                domain = domain[4:]
            domain_suffix_list.append(domain)

result = {
    "version": 3,
    "rules": [{"domain_suffix": domain_suffix_list}]
}

# 输出域名数量
print(f"Number of domains processed: {len(domain_suffix_list)}")

# 判断 JSON 是否变化
new_json = json.dumps(result, indent=4)
if os.path.exists(json_path):
    with open(json_path, "r") as f:
        old_json = f.read()
else:
    old_json = ""

if new_json != old_json:
    with open(json_path, "w") as f:
        f.write(new_json)
    # 生成 SRS
    subprocess.run(["sing-box", "rule-set", "compile", "--output", srs_path, json_path], check=True)
    print("Updated files.")
else:
    print("No changes detected, skip update.")
