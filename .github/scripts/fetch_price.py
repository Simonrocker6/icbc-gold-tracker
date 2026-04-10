#!/usr/bin/env python3
# fetch_price.py - 爬取工行积存金价格

import requests
import re
import json
import os
from datetime import datetime
from bs4 import BeautifulSoup

def fetch_icbc_gold():
    url = "https://icbcphp.icbc.com.cn/icbc/newperbank/perbank3/gold/goldaccrual_query_out.jsp"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        # 设置超时和重试
        session = requests.Session()
        response = session.get(url, headers=headers, timeout=15)
        response.encoding = 'utf-8'  # 工行页面通常是 UTF-8
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 查找积存金价格（根据实际页面结构调整选择器）
        # 策略1：查找包含"如意金积存"或"积存金"的表格行
        price_data = {
            'timestamp': datetime.now().isoformat(),
            'source': 'ICBC',
            'prices': {}
        }
        
        # 尝试多种解析方式
        # 方式1：查找特定 class 或 id
        tables = soup.find_all('table')
        
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                text = row.get_text()
                
                # 匹配积存金相关行
                if '积存金' in text or '如意金' in text:
                    # 提取价格（假设价格格式为 xxxx.xx）
                    price_match = re.search(r'(\d{3,4}\.\d{2})', text)
                    if price_match:
                        price_type = '积存金'
                        if '如意' in text:
                            price_type = '如意金积存'
                        elif '主动' in text:
                            price_type = '主动积存价'
                        elif '定期' in text:
                            price_type = '定期积存价'
                            
                        price_data['prices'][price_type] = float(price_match.group(1))
        
        # 如果没有找到表格数据，尝试正则全局匹配（备用方案）
        if not price_data['prices']:
            all_text = soup.get_text()
            # 匹配形如 1046.67 的数字（通常价格在 800-2000 之间）
            prices = re.findall(r'(1[0-9]{3}\.[0-9]{2})', all_text)
            if prices:
                price_data['prices']['积存金'] = float(prices[0])
                if len(prices) > 1:
                    price_data['prices']['如意金'] = float(prices[1])
        
        # 添加状态
        price_data['status'] = 'success' if price_data['prices'] else 'error'
        if not price_data['prices']:
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
    # 确保目录存在
    os.makedirs('docs/data', exist_ok=True)
    
    # 保存当前价格
    with open('docs/data/current.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 追加历史记录（保留最近 100 条）
    history_file = 'docs/data/history.json'
    history = []
    if os.path.exists(history_file):
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                history = json.load(f)
        except:
            history = []
    
    # 添加新记录
    history.append({
        'timestamp': data['timestamp'],
        'price': data['prices'].get('积存金') or data['prices'].get('如意金积存') or list(data['prices'].values())[0] if data['prices'] else None
    })
    
    # 只保留最近 100 条
    history = history[-100:]
    
    with open(history_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    data = fetch_icbc_gold()
    save_data(data)
    print(json.dumps(data, ensure_ascii=False, indent=2))
