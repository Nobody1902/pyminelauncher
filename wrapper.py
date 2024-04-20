import minecraft_launcher_lib
import subprocess
import os
import json
import requests
import socket
import mrpack
import shutil
import pathlib
import networkutils
import asyncio

def internet_on(host="8.8.8.8", port=53, timeout=2):
    """
    Host: 8.8.8.8 (google-public-dns-a.google.com)
    OpenPort: 53/tcp
    Service: domain (DNS/TCP)
    """
    try:
        socket.setdefaulttimeout(timeout)
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((host, port))
        return True
    except socket.error as ex:
        return False

FORGE_VERSIONS_URL = "https://files.minecraftforge.net/net/minecraftforge/forge/promotions_slim.json"

class Wrapper:
    LAUNCHER_NAME:str
    LAUNCHER_VERSION:str

    MINECRAFT_DIRECTORY:str = ""
    VERSIONS:list[str] = []
    FORGE_VERSIONS:dict[str,str] = {}
    FORGE_LATEST_VERSIONS:dict[str,str] = {}
    FORGE_RECOMMENDED_VERSIONS:dict[str,str] = {}
    FABRIC_VERSIONS:list[str] = []
    FABRIC_LOADER_VERSIONS:list[str] = []
    FABRIC_LATEST_LOADER:str
    QUILT_VERSIONS:list[str] = []
    QUILT_LOADER_VERSIONS:list[str] = []
    QUILT_LATEST_LOADER:str

    LATEST_VERSION:str

    versions_file:str
    forge_versions_file:str
    fabric_versions_file:str
    quilt_versions_file:str

    status:dict = {
        "status": "null",
        "max": 0,
        "progress": 0
    }

    OFFLINE_MODE = False

    def get_status(status:dict):
        # os.system('cls' if os.name == 'nt' else 'clear')
        print(status)
        return status
    
    def _set_status(self, status:str):
        self.status["status"] = status
        self.get_status(self.status)

    def _set_progress(self, progress:int):
        self.status["progress"] = progress
        self.get_status(self.status)

    def _set_max(self, max:int):
        self.status["max"] = max
        self.get_status(self.status)

    def __init__(self, launcher_name:str, launcher_version:str, minecraft_directory=minecraft_launcher_lib.utils.get_minecraft_directory(), silent=False) -> None:
        self.LAUNCHER_NAME = launcher_name
        self.LAUNCHER_VERSION = launcher_version
        
        self.MINECRAFT_DIRECTORY = minecraft_directory

        self.versions_file = os.path.join(self.MINECRAFT_DIRECTORY, "versions.json")
        self.forge_versions_file = os.path.join(self.MINECRAFT_DIRECTORY, "forge_versions.json")
        self.fabric_versions_file = os.path.join(self.MINECRAFT_DIRECTORY, "fabric_versions.json")
        self.quilt_versions_file = os.path.join(self.MINECRAFT_DIRECTORY, "quilt_versions.json")

    async def load(self):
        # if there is internet download version jsons otherwise load in the versions
        if not internet_on():
            print("There is no internet.\nLaunching offline mode...")
            
            with open(self.versions_file, "r") as f:
                versions = json.loads(f.read())
                self.VERSIONS = versions["versions"]
                self.LATEST_VERSION = versions["latest"]
            
            with open(self.forge_versions_file, "r") as f:
                forge_versions = json.loads(f.read())
                self.FORGE_VERSIONS = forge_versions["versions"]
                self.FORGE_LATEST_VERSIONS = forge_versions["latest"]
                self.FORGE_RECOMMENDED_VERSIONS = forge_versions["recommended"]
            
            with open(self.fabric_versions_file, "r") as f:
                fabric_versions = json.loads(f.read())
                self.FABRIC_VERSIONS = fabric_versions["versions"]
                self.FABRIC_LOADER_VERSIONS = fabric_versions["loader_versions"]
                self.FABRIC_LATEST_LOADER = fabric_versions["latest_loader"]

            with open(self.quilt_versions_file, "r") as f:
                quilt_versions = json.loads(f.read())
                self.QUILT_VERSIONS = quilt_versions["versions"]
                self.QUILT_LOADER_VERSIONS = quilt_versions["loader_versions"]
                self.QUILT_LATEST_LOADER = quilt_versions["latest_loader"]

            self.OFFLINE_MODE = True

            return

        # Get versions, forge_versions, fabric_versions and quilt_versions
        versions_task = asyncio.create_task(self.get_versions())
        forge_versions_task = asyncio.create_task(self.get_forge_versions())
        fabric_versions_task = asyncio.create_task(self.get_fabric_versions())
        quilt_versions_task = asyncio.create_task(self.get_quilt_versions())

        results = await asyncio.gather(versions_task, forge_versions_task, fabric_versions_task, quilt_versions_task)

        versions = results[0]
        forge_versions = results[1]
        fabric_versions = results[2]
        quilt_versions = results[3]

        # Write the versions
        self.VERSIONS = versions["versions"]
        self.LATEST_VERSION = versions["latest"]
        with open(self.versions_file, "w") as f:
            f.write(json.dumps(versions, indent=4))
        
        # Write forge versions
        self.FORGE_VERSIONS = forge_versions["versions"]
        self.FORGE_LATEST_VERSIONS = forge_versions["latest"]
        self.FORGE_RECOMMENDED_VERSIONS = forge_versions["recommended"]
        with open(self.forge_versions_file, "w") as f:
            f.write(json.dumps(forge_versions, indent=4))
        
        
        # Write fabric versions
        self.FABRIC_VERSIONS = fabric_versions["versions"]
        self.FABRIC_LOADER_VERSIONS = fabric_versions["loader_versions"]
        self.FABRIC_LATEST_LOADER = fabric_versions["latest_loader"]
        with open(self.fabric_versions_file, "w") as f:
            f.write(json.dumps(fabric_versions, indent=4))
        
        
        # Write quilt versions
        self.QUILT_VERSIONS = quilt_versions["versions"]
        self.QUILT_LOADER_VERSIONS = quilt_versions["loader_versions"]
        self.QUILT_LATEST_LOADER = quilt_versions["latest_loader"]
        with open(self.quilt_versions_file, "w") as f:
            f.write(json.dumps(quilt_versions, indent=4))

    async def get_versions(self)->dict[str, list[str]|str]:
        versions = []

        for version in minecraft_launcher_lib.utils.get_version_list():
            version_id = version["id"]
            versions.append(version_id)

        return {"versions":versions, "latest":minecraft_launcher_lib.utils.get_latest_version()["snapshot"]}

    async def get_forge_versions(self)->dict[str,dict[str, str]]:
        forge_versions_json = json.loads(await networkutils.get_file_contents_async(FORGE_VERSIONS_URL))

        latest = {}
        recommended = {}
        
        for name in forge_versions_json["promos"]:

            if str(name).endswith("-recommended"):
                recommended[str(name).removesuffix("-recommended")] = forge_versions_json["promos"][name]
            elif str(name).endswith("-latest"):
                latest[str(name).removesuffix("-latest")] = forge_versions_json["promos"][name]

        # https://www.geeksforgeeks.org/python-combine-dictionary-with-priority/
        prio_dict = {1 : recommended, 2: latest} 
        
        # Combine dictionary with priority 
        # Using loop + copy() 
        versions = prio_dict[2].copy() 
        for key, val in prio_dict[1].items(): 
            versions[key] = val

        return {"versions":versions, "latest":latest, "recommended":recommended}

    async def get_fabric_versions(self)->dict[str, list[str]|str]:
        stable = minecraft_launcher_lib.fabric.get_stable_minecraft_versions()
        versions = []

        loader_versions = [v["version"] for v in minecraft_launcher_lib.fabric.get_all_loader_versions()]
        latest_loader = minecraft_launcher_lib.fabric.get_latest_loader_version()

        for version in minecraft_launcher_lib.fabric.get_all_minecraft_versions():
            if not version["version"] in stable:
                versions.append(version["version"])
        
        stable.extend(versions)
        return {"versions":stable, "loader_versions":loader_versions, "latest_loader":latest_loader}
    
    async def get_quilt_versions(self)->dict[str, list[str]|str]:
        stable = minecraft_launcher_lib.quilt.get_stable_minecraft_versions()
        versions = []

        loader_versions = [v["version"] for v in minecraft_launcher_lib.quilt.get_all_loader_versions()]
        latest_loader = minecraft_launcher_lib.quilt.get_latest_loader_version()

        for version in minecraft_launcher_lib.quilt.get_all_minecraft_versions():
            if not version["version"] in stable:
                versions.append(version["version"])
        
        stable.extend(versions)
        return {"versions":stable, "loader_versions":loader_versions, "latest_loader":latest_loader}

    def is_installed(self, version_id:str) -> bool:
        for version in minecraft_launcher_lib.utils.get_installed_versions(self.MINECRAFT_DIRECTORY):
            if version["id"] == version_id:
                return True
        
        return False

    def download_version(self, vannila_version:str)->str:
        callback = {
            "setStatus": self._set_status,
            "setProgress": self._set_progress,
            "setMax": self._set_max
        }

        if not vannila_version in self.VERSIONS:
            print(f"Version {vannila_version} doesn't exist.")
            return
        
        if self.is_installed(vannila_version):
            print(f"Version {vannila_version} already installed.")
            return vannila_version
        
        if self.OFFLINE_MODE:
            print("Cannot download version without internet.")
            return

        minecraft_launcher_lib.install.install_minecraft_version(vannila_version, self.MINECRAFT_DIRECTORY, callback=callback)
        return vannila_version

    def download_forge_version(self, vannila_version:str, forge_version:str|None=None)->str:
        callback = {
            "setStatus": self._set_status,
            "setProgress": self._set_progress,
            "setMax": self._set_max
        }
        
        if not vannila_version in self.FORGE_VERSIONS.keys():
            print(f"Minecraft version {vannila_version} is not supported by Forge.")
            return
        
        if not forge_version:
            forge_version = self.FORGE_VERSIONS[vannila_version]

        if self.is_installed(f"{vannila_version}-forge-{forge_version}"):
            print(f"Version {vannila_version}-forge-{forge_version} already installed.")
            return f"{vannila_version}-forge-{forge_version}"


        if self.OFFLINE_MODE:
            print("Cannot download version without internet.")
            return

        minecraft_launcher_lib.forge.install_forge_version(f"{vannila_version}-{forge_version}", self.MINECRAFT_DIRECTORY, callback)
        return f"{vannila_version}-forge-{forge_version}"

    def download_fabric_version(self, vannila_version:str, fabric_loader:str=None)->str:
        if not vannila_version in self.FABRIC_VERSIONS:
            print(f"Minecraft version {vannila_version} is not supported by Fabric.")
            return
        
        if fabric_loader != None and not fabric_loader in self.FABRIC_LOADER_VERSIONS:
            print(f"Fabric loader version {fabric_loader} doesn't exist.")
            return

        callback = {
            "setStatus": self._set_status,
            "setProgress": self._set_progress,
            "setMax": self._set_max
        }

        fabric_installer_version = self.FABRIC_LATEST_LOADER

        if fabric_loader:
            fabric_installer_version = fabric_loader

        if self.is_installed(f"fabric-loader-{fabric_installer_version}-{vannila_version}"):
            print(f"Version fabric-loader-{fabric_installer_version}-{vannila_version} already installed.")
            return f"fabric-loader-{fabric_installer_version}-{vannila_version}"
        
        if self.OFFLINE_MODE:
            print("Cannot download version without internet.")
            return

        minecraft_launcher_lib.fabric.install_fabric(vannila_version, self.MINECRAFT_DIRECTORY, fabric_installer_version, callback=callback)
        return f"fabric-loader-{fabric_installer_version}-{vannila_version}"

    def download_quilt_version(self, vannila_version:str, quilt_loader:str=None)->str:
        if not vannila_version in self.QUILT_VERSIONS:
            print(f"Minecraft version {vannila_version} is not supported by Quilt.")
            return

        if quilt_loader != None and not quilt_loader in self.QUILT_LOADER_VERSIONS:
            print(f"Quilt loader version {quilt_loader} doesn't exist.")
            return
        
        callback = {
            "setStatus": self._set_status,
            "setProgress": self._set_progress,
            "setMax": self._set_max
        }

        quilt_installer_version = self.QUILT_LATEST_LOADER

        if quilt_loader:
            quilt_installer_version = quilt_loader

        if self.is_installed(f"quilt-loader-{quilt_installer_version}-{vannila_version}"):
            print(f"Version quilt-loader-{quilt_installer_version}-{vannila_version} already installed.")
            return f"quilt-loader-{quilt_installer_version}-{vannila_version}"

        if self.OFFLINE_MODE:
            print("Cannot download version without internet.")
            return

        minecraft_launcher_lib.quilt.install_quilt(vannila_version, self.MINECRAFT_DIRECTORY, quilt_installer_version, callback=callback)
        return f"quilt-loader-{quilt_installer_version}-{vannila_version}"

    def download_mrpack(self, file, install_path)->str:
        
        if not os.path.exists(file):
            print(f"Cannot install {file} as the file doesn't exist.")
            return

        callback = {
            "setStatus": self._set_status,
            "setProgress": self._set_progress,
            "setMax": self._set_max
        }
        
        version_info = mrpack.install_mrpack(file, install_path, callback=callback)

        minecraft_version = version_info[0]
        mod_loader = version_info[1][0]
        mod_loader_version = version_info[1][1]

        version = minecraft_version
        
        callback["setStatus"]("Installing mrpack minecraft version")

        # Install mrpack version
        if not mod_loader:
            version = self.download_version(minecraft_version)
        elif mod_loader == "forge":
            version = self.download_forge_version(minecraft_version, mod_loader_version)
        elif mod_loader == "fabric":
            version = self.download_fabric_version(minecraft_version, mod_loader_version)
        elif mod_loader == "quilt":
            version = self.download_quilt_version(minecraft_version, mod_loader_version)
        
        return version

    def download_curseforge_pack(self, file:str, install_path:str)->str:
        if not os.path.exists(file):
            print(f"Cannot install {file} as the file doesn't exist.")
            return

        callback = {
            "setStatus": self._set_status,
            "setProgress": self._set_progress,
            "setMax": self._set_max
        }

        print("Currently not supported.")
        return
        # version_info = curseforge.install_modpack(file, install_path, callback=callback)

        minecraft_version = version_info[0]
        mod_loader = version_info[1][0]
        mod_loader_version = version_info[1][1]

        version = minecraft_version
        
        callback["setStatus"]("Installing modpack minecraft version")

        # Install mrpack version
        if not mod_loader:
            version = self.download_version(minecraft_version)
        elif mod_loader == "forge":
            version = self.download_forge_version(minecraft_version, mod_loader_version)
        elif mod_loader == "fabric":
            version = self.download_fabric_version(minecraft_version, mod_loader_version)
        elif mod_loader == "quilt":
            version = self.download_quilt_version(minecraft_version, mod_loader_version)
        
        return version

    def launch_version(self, version:str, username:str, memory_alloc:int=4096, gameDir:str|None = None):

        options = minecraft_launcher_lib.utils.generate_test_options()
        options["username"] = username
        if gameDir:
            options["gameDirectory"] = gameDir

        options["launcherName"] = self.LAUNCHER_NAME
        options["launcherVersion"] = self.LAUNCHER_VERSION
        options["jvmArguments"] = [f"-Xmx{memory_alloc}m"]
        command = minecraft_launcher_lib.command.get_minecraft_command(version, self.MINECRAFT_DIRECTORY, options)
        
        # translate all paths into absolute paths
        for c in range(len(command)):
            all_paths = command[c].split(os.path.pathsep)
            for i in range(len(all_paths)):
                start_line = ""
                p = all_paths[i].replace(os.path.pathsep, "")
                # in case of -Dj-library=path
                if "=" in all_paths[i]:
                    p = all_paths[i].split("=")[1].replace("=", "")
                    start_line = all_paths[i].split("=")[0] + "="

                # if it is a path turn it into an absolute path
                if pathlib.Path(p).exists():
                    path = os.path.normpath(os.path.abspath(p))
                    all_paths[i] = start_line + path

            # join all paths, if there is more than one
            command[c] = os.path.pathsep.join(all_paths)

        print(command)

        subprocess.run(command, cwd=os.path.abspath(gameDir))