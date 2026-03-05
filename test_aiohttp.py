#!/usr/bin/env python3
import asyncio
import aiohttp

async def test():
    async with aiohttp.ClientSession() as session:
        # Получаем токен
        async with session.post('http://localhost:8000/token', data={'username': 'admin', 'password': 'admin123'}) as resp:
            data = await resp.json()
            token = data.get('access_token')
            print(f'Token: {token[:30]}...')
        
        # Отправляем запрос на загрузку
        headers = {'Authorization': f'Bearer {token}'}
        print('Sending POST to process-uploads...')
        
        try:
            async with session.post('http://localhost:8000/admin/global-index/process-uploads', headers=headers, timeout=300) as resp:
                print(f'Status: {resp.status}')
                result = await resp.json()
                print(f'Response: {result}')
        except asyncio.TimeoutError:
            print('Timeout!')
        except Exception as e:
            print(f'Error: {e}')

asyncio.run(test())
