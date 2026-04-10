#!/usr/bin/env python3
# fetch_price.py - 修复 SSL 问题

import requests
import urllib3
import json
import os
import re
from datetime import datetime
from bs4 import BeautifulSoup

# 禁用 SSL 警告（可选）
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def fetch_icbc_gold():
    url = "https://icbcphp.icbc.com.cn/icbc/newperbank/perbank3/gold/goldaccrual_query_out.jsp"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
    }
    
    try:
        # 关键：禁用 SSL 验证
        response = requests.get(
            url, 
            headers=headers, 
            timeout=15,
            verify=False  # <-- 禁用 SSL 验证
        )
        
        response.encoding = 'utf-8'
        
        # 解析 HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        price_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'ICBC',
            'status': 'success',
            'prices': {}
        }
        
        # 查找价格（简化版）
        text = soup.get_text()
        prices = re.findall(r'(1\d{3}\.\d{2})', text)
        
        if prices:
            price_data['prices']['积存金'] = float(prices[0])
            if len(prices) > 1:
                price_data['prices']['如意金积存'] = float(prices[1])
        else:
            price_data['status'] = 'error'
            price_data['error'] = '未找到价格数据'
            
        return price_data
        
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
    
    # 保存历史
    if data['status'] == 'success' and data.get('prices'):
        history_file = 'docs/data/history.json'
        history = []
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except:
                history = []
        
        main_price = list(data['prices'].values())[0]
        history.append({
            'timestamp': data['timestamp'],
            'price': main_price
        })
        history = history[-100:]  # 保留最近100条
        
        with open(history_file, 'w', encoding='utf-8') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    print("开始爬取...")
    data = fetch_icbc_gold()
    print(f"结果: {json.dumps(data, ensure_ascii=False, indent=2)}")
    save_data(data)
