
#!/usr/bin/env python3
"""单独测试008272的API"""

import requests
import time

fund_code = "008272"
report_period = "2025Q4"

print(f"测试基金: {fund_code}")

url = f"http://localhost:8000/api/funds/{fund_code}/report/{report_period}"
print(f"请求API: {url}")

start_time = time.time()
try:
    response = requests.get(url, timeout=150)
    elapsed = time.time() - start_time
    
    print(f"状态码: {response.status_code}, 耗时: {elapsed:.1f}s")
    
    if response.status_code == 200:
        data = response.json()
        viewpoint = data["data"]["viewpoint"]
        fund_info = data["data"]["fund_info"]
        print(f"✓ 成功! 基金: {fund_info['name']}({fund_info['code']}) 经理: {fund_info['manager']}")
        print(f"  观点长度: {len(viewpoint)} 字符")
        if viewpoint:
            print(f"  完整观点: '{viewpoint}'")
        else:
            print(f"  ⚠️ 观点为空")
    else:
        print(f"✗ 失败: {response.text}")
except Exception as e:
    print(f"✗ 异常: {e}")
    import traceback
    traceback.print_exc()

