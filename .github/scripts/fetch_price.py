#!/usr/bin/env python3
# fetch_price.py - 终极 SSL 修复版

import requests
import json
import os
import re
import ssl
import urllib3
from datetime import datetime
from bs4 import BeautifulSoup
from urllib3.poolmanager import PoolManager
from requests.adapters import HTTPAdapter

# 完全禁用警告
urllib3.disable_warnings()

class SSLAdapter(HTTPAdapter):
    """自定义适配器，允许旧版 SSL 重协商"""
    def init_poolmanager(self, *args, **kwargs):
        # 创建不安全的 SSL 上下文
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        # 关键：允许旧版不安全的重协商
        context.options |= ssl.OP_LEGACY_SERVER_CONNECT
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)

def fetch_icbc_gold():
    url = "https://icbcphp.icbc.com.cn/icbc/newperbank/perbank3/gold/goldaccrual_query_out.jsp"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
    }
    
    try:
        # 使用自定义 SSL 适配器
        session = requests.Session()
        session.mount('https://', SSLAdapter())
        
        print(f"正在请求: {url}")
        response = session.get(
            url, 
            headers=headers, 
            timeout=15,
            verify=False
        )
        
        print(f"状态码: {response.status_code}")
        print(f"返回长度: {len(response.text)}")
        
        response.encoding = 'utf-8'
        
        # 检查是否被拦截
        if 'login' in response.text.lower() or '登录' in response.text:
            raise Exception("页面需要登录")
        
        # 解析价格
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text()
        
        # 保存原始内容用于调试
        os.makedirs('docs/data', exist_ok=True)
        with open('docs/data/debug.html', 'w', encoding='utf-8') as f:
            f.write(response.text[:2000])
        
        price_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'ICBC',
            'status': 'success',
            'prices': {}
        }
        
        # 提取价格
        prices = re.findall(r'(1\d{3}\.\d{2})', text)
        print(f"找到价格: {prices}")
        
        if prices:
            price_data['prices']['积存金'] = float(prices[0])
            if len(prices) > 1:
                price_data['prices']['如意金积存'] = float(prices[1])
            if len(prices) > 2:
                price_data['prices']['主动积存'] = float(prices[2])
        else:
            price_data['status'] = 'error'
            price_data['error'] = '未找到价格数据'
            price_data['debug_snippet'] = text[:500]
            
        return price_data
        
    except Exception as e:
        import traceback
        print(f"错误: {e}")
        print(traceback.format_exc())
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
    
    print(f"数据已保存: {data.get('status')}")

if __name__ == '__main__':
    data = fetch_icbc_gold()
    save_data(data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
