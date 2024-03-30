import json
from os import path
import os
import zipfile
import tempfile
import hashlib
import shutil
import urllib.request
import minecraft_launcher_lib

LAUNCHER_NAME = "PyLauncher"

MODERINTH_REQUEST_HEADER={
    "User-Agent": f"nobody1902/{LAUNCHER_NAME}/1.0",
    "Accept-Encoding": "gzip, deflate",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "application/java-archive,text/html,application/xhtml+xml,application/xml",
}

def json_read(path:str):
    if not os.path.exists(path):
        print("Couldn't find json file.")
        return
    o = None
    with open(path, "r") as f:
        o = json.loads(f.read())
    
    return o

def unzip(archive:str, output:str):
    if not path.exists(archive):
        print("Couldn't find the archive.")
        return
    
    with zipfile.ZipFile(archive, "r") as zip_ref:
        zip_ref.extractall(output)

def download_file(url:str, install_location:str, overwrite=False):
    os.makedirs(path.dirname(install_location), exist_ok=True)
    if not overwrite and path.exists(install_location):
        return
    
    request = urllib.request.Request(url, None, MODERINTH_REQUEST_HEADER)

    with urllib.request.urlopen(request) as response, open(install_location, "wb") as out_file:
        shutil.copyfileobj(response, out_file)

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

def install_mrpack(mrpack:str, install_location:str, callback:minecraft_launcher_lib.types.CallbackDict|None=None)->tuple[str, tuple[str, str]]:
    if not path.exists(mrpack):
        return
    
    TEMP_PATH = path.join(tempfile.gettempdir(), f"{LAUNCHER_NAME}")
    pack_folder = path.join(TEMP_PATH, str(int(hashlib.sha1(path.basename(mrpack).encode("utf-8")).hexdigest(), 16) % (10 ** 8)))

    # unzip mrpack
    update_status(callback, "Unzipping mrpack")
    unzip(mrpack, pack_folder)

    # read the index.json
    pack_info = json_read(path.join(pack_folder, "modrinth.index.json"))

    # copy overrides
    update_status(callback, "Copying overrides")
    overrides_path = path.join(pack_folder, "overrides")

    overrides = []

    if path.exists(overrides_path):
        for root, dirs, files in os.walk(overrides_path):
            for file in files:
                overrides.append(os.path.join(root,file))
    
    update_max(callback, len(overrides))
    update_status(callback, "Copying overrides")

    for i, value in enumerate(overrides):
        update_progress(callback, i)
        update_status(callback, f"Copying {path.basename(value)}")
        local_path = path.relpath(value, overrides_path)

        destination_path = path.join(install_location, local_path)
        os.makedirs(path.dirname(destination_path), exist_ok=True)
        shutil.copy(value, destination_path)
    
    # download pack files
    file_count = len(pack_info["files"])
    update_status(callback, "Downloading pack dependencies")
    update_max(callback, file_count)
    
    for i, file in enumerate(pack_info["files"]):
        file_path = file["path"]
        downloads = file["downloads"]
        filesize = file["fileSize"]

        update_progress(callback, i)
        update_status(callback, f"Downloading {path.basename(file_path)}")
        
        download_file(downloads[0], path.join(install_location, file_path))

    shutil.rmtree(pack_folder)
    
    # download version

    dependencies:dict[str, str] = dict(pack_info["dependencies"])
    minercaft_version = dependencies["minecraft"]
    mod_loader = None
    mod_loader_version = None

    if dependencies.get("forge", None):
        mod_loader = "forge"
        mod_loader_version = dependencies["forge"]
    
    elif dependencies.get("fabric-loader", None):
        mod_loader = "fabric"
        mod_loader_version = dependencies["fabric-loader"]

    elif dependencies.get("quilt-loader", None):
        mod_loader = "quilt"
        mod_loader_version = dependencies["quilt-loader"]
    
    elif dependencies.get("neoforge", None):
        print("Neoforge is not supported.")
        return None

    return (minercaft_version, (mod_loader, mod_loader_version))

