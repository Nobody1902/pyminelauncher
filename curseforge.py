import urllib.request
import urllib
import os
import shutil
import hashlib
import zipfile
import tempfile
import json
import minecraft_launcher_lib
import requests
import asyncio

CURSEFORGE_HEADERS={
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/json,text/html,application/xhtml+xml,application/xml",
}
LAUNCHER_NAME = "PyLauncher"

def update_status(callback:minecraft_launcher_lib.types.CallbackDict|None, status:str):
    if not callback:
        return

    callback["setStatus"](status)

def update_progress(callback:minecraft_launcher_lib.types.CallbackDict|None, progress:int):
    if not callback:
        return

    callback["setProgress"](progress)

def update_max(callback:minecraft_launcher_lib.types.CallbackDict|None, max:int):
    if not callback:
        return

    callback["setMax"](max)

async def download_curseforge_file(project_id:str, file_id:str, download_path:str, overwrite:bool=False):

    CURSEFORGE_DOWNLOAD = f"https://www.curseforge.com/api/v1/mods/{project_id}/files/{file_id}/download"

    os.makedirs(os.path.dirname(download_path), exist_ok=True)
    if not overwrite and os.path.exists(download_path):
        return
    
    request = urllib.request.Request(CURSEFORGE_DOWNLOAD, None, CURSEFORGE_HEADERS)

    with urllib.request.urlopen(request) as response, open(download_path, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

def json_read(path:str):
    if not os.path.exists(path):
        print("Couldn't find json file.")
        return
    o = None
    with open(path, "r") as f:
        o = json.loads(f.read())
    
    return o

def unzip(archive:str, output:str):
    if not os.path.exists(archive):
        print("Couldn't find the archive.")
        return
    
    with zipfile.ZipFile(archive, "r") as zip_ref:
        zip_ref.extractall(output)

async def get_filename(project_id:str, file_id:str):
    CURSE_FORGE_FILES_JSON = f"https://www.curseforge.com/api/v1/mods/{project_id}/files/{file_id}/"
    json_data = None
    
    response = await asyncio.gather(asyncio.to_thread(requests.get(CURSE_FORGE_FILES_JSON, headers=CURSEFORGE_HEADERS),))
    json_data = json.loads(response.content)
    
    if json_data == None:
        print("Failed to fetch mod data.")
        return
    
    return json_data["data"]["fileName"]

async def fetch_mod_names(files:list)->dict[str,tuple[str, str]]:
    mod_names = {}
    for file in files:
        if not file["required"]:
            continue
        
        project_id = file["projectID"]
        file_id = file["fileID"]

        filename = await get_filename(project_id, file_id)
        mod_names[filename] = (project_id, file_id)
    
    return mod_names

def install_modpack(modpack_zip:str, install_location:str, callback:minecraft_launcher_lib.types.CallbackDict|None=None)->tuple[str, tuple[str, str]]:
    if not os.path.exists(modpack_zip):
        return
    
    TEMP_PATH = os.path.join(tempfile.gettempdir(), f"{LAUNCHER_NAME}")
    pack_folder = os.path.join(TEMP_PATH, str(int(hashlib.sha1(os.path.basename(modpack_zip).encode("utf-8")).hexdigest(), 16) % (10 ** 8)))

    # unzip modpack
    update_status(callback, "Unzipping modpack")
    unzip(modpack_zip, pack_folder)

    # read the manifest.json
    pack_info = json_read(os.path.join(pack_folder, "manifest.json"))

    # copy the overrides
    update_status(callback, "Copying overrides")
    overrides_path = os.path.join(pack_folder, "overrides")

    overrides = []

    if os.path.exists(overrides_path):
        for root, dirs, files in os.walk(overrides_path):
            for file in files:
                overrides.append(os.path.join(root,file))
    
    update_max(callback, len(overrides))
    update_status(callback, "Copying overrides")
    
    for i, value in enumerate(overrides):
        update_progress(callback, i)
        update_status(callback, f"Copying {os.path.basename(value)}")
        local_path = os.path.relpath(value, overrides_path)

        destination_path = os.path.join(install_location, local_path)
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        shutil.copy(value, destination_path)
    
    # download mods
    mods_folder = os.path.join(install_location, "mods")
    
    file_count = len(pack_info["files"])
    update_status(callback, "Downloading pack dependencies")
    update_max(callback, file_count)

    mods:dict[str,tuple[str,str]] = asyncio.run(fetch_mod_names(pack_info["files"]))

    print(mods)
    return

    for mod in pack_info["files"]:
        if mod["required"]:
            project_id = mod["projectID"]
            file_id = mod["fileID"]

            file_name = get_filename(project_id, file_id)

            mods[file_name] = (project_id, file_id)
    
    
    shutil.rmtree(pack_folder)

    minecraft_version = pack_info["minecraft"]["version"]
    mod_loader:str|None = None
    
    for loader in pack_info["minecraft"]["modLoaders"]:
        if loader["primary"]:
            mod_loader = loader["id"]
            continue
    
    if not mod_loader:
        return (minecraft_version, (None, None))

    loader_name = mod_loader.split("-")[0].replace("-", "")
    loader_version = mod_loader.split("-")[1].replace("-", "")

    return (minecraft_version, (loader_name, loader_version))


