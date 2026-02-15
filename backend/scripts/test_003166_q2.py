import requests
import time

fund_code = "003166"
report_periods = ["2025Q4", "2025Q3", "2025Q2"]

for report_period in report_periods:
    print(f"\n{'='*60}")
    print(f"测试基金: {fund_code} {report_period}")
    print(f"{'='*60}")
    
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
                print(f"  观点预览: {viewpoint[:150]}...")
        else:
            print(f"✗ 失败: {response.text}")
    except Exception as e:
        print(f"✗ 异常: {e}")
