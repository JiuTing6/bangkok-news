import os
import json
import urllib.request
import sys

# 配置
API_KEY = os.getenv("OPENROUTER_API_KEY")
THRESHOLD = 5.0

def check():
    if not API_KEY:
        print("Error: OPENROUTER_API_KEY not found in env.")
        return

    url = "https://openrouter.ai/api/v1/credits"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            
            # OpenRouter logic: remaining = total_credits - total_usage
            total = data.get("data", {}).get("total_credits", 0)
            usage = data.get("data", {}).get("total_usage", 0)
            remaining = total - usage
            
            # 如果低于阈值，输出告警格式
            if remaining < THRESHOLD:
                print(f"⚠️ OpenRouter当前余额/Credits ${remaining:.2f}，请及时充值。")
            else:
                # 否则只输出 debug 信息（cron 脚本会自动吞掉，不吵你）
                print(f"Remaining: ${remaining:.2f}")
    except Exception as e:
        print(f"Error checking balance: {e}")

if __name__ == "__main__":
    check()
