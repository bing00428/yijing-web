#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""模拟浏览器 fetch 请求"""
import sys, json, urllib.request, http.client
sys.stdout.reconfigure(encoding='utf-8')
import subprocess, time

p = subprocess.Popen([sys.executable, 'server.py'], cwd='.', stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(3)

base = 'http://127.0.0.1:5500'
data = json.dumps({'year':1990,'month':5,'day':15,'hour_index':6})

# 用 http.client 模拟 fetch
conn = http.client.HTTPConnection('127.0.0.1', 5500)
headers = {'Content-Type': 'application/json'}
conn.request('POST', '/api/benming/calculate', body=data.encode('utf-8'), headers=headers)
resp = conn.getresponse()
body = resp.read().decode('utf-8')
print('Status:', resp.status)
print('Headers:', dict(resp.getheaders()))
print('Body:', body[:300])
print()

parsed = json.loads(body)
print('Parsed success:', parsed.get('success'))
print('Has data:', 'data' in parsed)
if parsed.get('success'):
    print('OK - benming:', parsed['data']['mingben']['benming_wuxing'])
else:
    print('ERROR:', body)

conn.close()
p.terminate()
p.wait()
