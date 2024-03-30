import requests
import os
from aiohttp import ClientSession
import asyncio
import aiofiles
import aiofiles.os

import typing

class AsyncFile(typing.TypedDict):
    url:str
    path:str

def get_file_contents(url:str, headers:dict={})->str:
    
    res = requests.get(url, headers=headers)
    
    if not res.content:
        print(f"Couldn't access {url}")
    
    return res.content.decode()

async def get_file_contents_async(url:str, headers:dict={})->str:
    res = None
    async with ClientSession() as session:
        async with session.get(url) as response:
            res = await response.read()
    
    if not res:
        print(f"Couldn't access {url}")
    
    return res.decode()

def download_file(url:str, path:str, headers:dict={}, overwrite:bool=False):
    if not overwrite and os.path.exists(path):
        return
    
    os.makedirs(os.path.dirname(path), exist_ok=True)
    data = get_file_contents(url, headers)

    with open(path, "wb") as file:
        file.write(data.encode())

async def download_file_async(url:str, path:str, headers:dict={}, overwrite:bool=False):
    if not overwrite and os.path.exists(path):
        return
    
    await aiofiles.os.makedirs(os.path.dirname(path), exist_ok=True)

    data = await get_file_contents_async(url, headers)
    
    async with aiofiles.open(path, "wb") as out_file:
        await out_file.write(data.encode())

async def download_files_async(files:list[AsyncFile], headers:dict={}, overwrite:bool=False):
    tasks = []
    for file in files:
        t = asyncio.create_task(download_file_async(file["url"], file["path"], headers, overwrite))
        tasks.append(t)
    
    await asyncio.gather(*tasks)