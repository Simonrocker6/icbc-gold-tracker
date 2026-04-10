#!/usr/bin/env python3
"""
GitHub Actions 版 - 修复 SSL 问题
本地测试 3 通过，此版本应该可用
"""

import requests
import json
import os
import re
import ssl
from datetime import datetime
from requests.adapters import HTTPAdapter

class CustomSSLAdapter(HTTPAdapter):
    """自定义 SSL 适配器 - 允许旧版重协商"""
    def init_poolmanager(self, *args, **kwargs):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # 使用数值 0x4 代替 OP_LEGACY_SERVER_CONNECT（兼容性更好）
        context.options |= 0x4
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def fetch_icbc_gold():
    url = "https://icbcphp.icbc.com.cn/icbc/newperbank/perbank3/gold/goldaccrual_query_out.jsp"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    }
    
    try:
        # 使用自定义适配器
        session = requests.Session()
        session.mount('https://', CustomSSLAdapter())
        
        response = session.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'
        
        # 解析价格
        prices = re.findall(r'(1\d{3}\.\d{2})', response.text)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'source': 'ICBC',
            'status': 'success',
            'prices': {
                '积存金': float(prices[0]),
                '如意金积存': float(prices[1]) if len(prices) > 1 else None
            } if prices else {}
        }
        
    except Exception as e:
        return {
            'timestamp': datetime.now().isoformat(),
            'status': 'error',
            'error': str(e),
            'prices': {}
        }

def save_data(data):
    os.makedirs('docs/data', exist_ok=True)
    
    with open('docs/data/current.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 更新历史
    if data['status'] == 'success' and data.get('prices'):
        history = []
        if os.path.exists('docs/data/history.json'):
            try:
                with open('docs/data/history.json', 'r') as f:
                    history = json.load(f)
            except:
                pass
        
        price = list(data['prices'].values())[0]
        history.append({
            'timestamp': data['timestamp'],
            'price': price
        })
        history = history[-100:]
        
        with open('docs/data/history.json', 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    data = fetch_icbc_gold()
    save_data(data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
    
    # 退出码供 Actions 判断
    exit(0 if data['status'] == 'success' else 1)
