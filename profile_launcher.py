from os import path
import os
import sys
import json
import shutil
import asyncio

from wrapper import Wrapper

def delete_last_line():
    # Deletes the last line in the STDOUT
    # cursor up one line
    sys.stdout.write('\x1b[1A')
    # delete last line
    sys.stdout.write('\x1b[2K')

def print_status(wrapper:dict):
    PROGRESS_BAR_LENGHT = 20

    progress = wrapper["progress"]
    max_progress = wrapper["max"]
    status = wrapper["status"]
    if max_progress == 0 or max_progress < progress:
        print(f"{status:<76}")
        return
    print("{:<76}".format(status) + f"| {'#'*int((progress/max_progress)*PROGRESS_BAR_LENGHT)}{"_"*int((max_progress-progress)/max_progress * PROGRESS_BAR_LENGHT)} - {int(progress/max_progress*100)}%\r")
    delete_last_line()

class Launcher:
    LAUNCHER_NAME:str
    LAUNCHER_VERSION:str

    MINECRAFT_DIRECTORY:str
    PROFILES_DIRECTORY:str

    _wrapper: Wrapper

    def __init__(self, minecraft_directory:str=path.join(path.curdir, ".minecraft"), launcher_name:str="PYLauncher", launcher_version:str="1.0") -> None:
        self.LAUNCHER_NAME = launcher_name
        self.LAUNCHER_VERSION = launcher_version
        
        self.MINECRAFT_DIRECTORY = minecraft_directory
    
    async def load(self):
        os.makedirs(self.MINECRAFT_DIRECTORY, exist_ok=True)

        self.PROFILES_DIRECTORY = path.join(self.MINECRAFT_DIRECTORY, "profiles")
        os.makedirs(self.PROFILES_DIRECTORY, exist_ok=True)

        self._wrapper = Wrapper(self.LAUNCHER_NAME, self.LAUNCHER_VERSION, self.MINECRAFT_DIRECTORY)
        await self._wrapper.load()

        self._wrapper.get_status = print_status
    
    # Helper methods
    def get_versions(self)->list[str]:
        return self._wrapper.VERSIONS

    def get_forge_supported_versions(self)->list[str]:
        return self._wrapper.FORGE_VERSIONS.keys()

    def get_forge_version(self, version_id)->str:
        return self._wrapper.FORGE_VERSIONS[version_id]
    
    def get_fabric_supported_versions(self)->list[str]:
        return self._wrapper.FABRIC_VERSIONS

    def get_quilt_supported_versions(self)->list[str]:
        return self._wrapper.FABRIC_VERSIONS
    
    # Main methods
    def download_version(self, version_id:str)->str:
        if "*" in version_id:
            if "fabric" in version_id:
                minecraft_version = version_id.split("*")[-1]
                return self._wrapper.download_fabric_version(minecraft_version)
            elif "forge" in version_id:
                minecraft_version = version_id.split("*")[-1]
                return self._wrapper.download_forge_version(minecraft_version)
            
            elif "quilt" in version_id:
                minecraft_version = version_id.split("*")[-1]
                return self._wrapper.download_quilt_version(minecraft_version)
        elif "forge" in version_id:
            minecraft_version = version_id.split("-")[0]
            forge_version = version_id.split("-")[2]
            return self._wrapper.download_forge_version(minecraft_version, forge_version)
        else:
            return self._wrapper.download_version(version_id)

    def create_profile(self, version_id:str, profile_name:str, install_versions=True, overwrite=False):
        profile_path = path.join(self.PROFILES_DIRECTORY, profile_name)
        if path.exists(profile_path) and not overwrite:
            print("Profile already exists.")
            return
        
        print(f"Installing version {version_id}")

        # download the version if not jet installed
        version_name = self.download_version(version_id)

        if version_name == None:
            print("Couldn't create profile")
            return
        
        os.makedirs(profile_path, exist_ok=overwrite)
        os.makedirs(path.join(profile_path, "game"), exist_ok=True)

        profile_data = {
            "profile_name": profile_name,
            "profile_version": version_name
        }
        with open(path.join(profile_path, "profile.json"), "w") as f:
            f.write(json.dumps(profile_data))
        
        print("Profile created successfully.")

    def launch_profile(self, profile:str, username:str, memory_alloc:str=4096):
        profile_path = path.join(self.PROFILES_DIRECTORY, profile)
        profile_json = path.join(profile_path, "profile.json")

        if not os.path.exists(profile_path) or not os.path.exists(profile_json):
            print("Cannot launch profile as it doesn't exist.")
            print("Check the profiles directory and if the profile has the profile.json file.")
            return

        game_directory = path.join(profile_path, "game")
        os.makedirs(game_directory, exist_ok=True)

        with open(profile_json) as file:
            profile_data = json.load(file)

        profile_name = profile_data["profile_name"]
        profile_version = profile_data["profile_version"]

        if not self._wrapper.is_installed(profile_version):
            print(f"Version {profile_version} isn't installed.")
            return

        print(f"Launching profile '{profile_name} ({profile_version})'")

        self._wrapper.launch_version(profile_version, username, memory_alloc=memory_alloc, gameDir=game_directory)

    def delete_profile(self, profile:str):
        profile_path = path.join(self.PROFILES_DIRECTORY, profile)

        if not os.path.exists(profile_path):
            print("Cannot delete profile as it doesn't exist.")
            print("Check the profiles directory and delete it manually.")
            return
        
        shutil.rmtree(profile_path)

        print(f"Profile '{profile}' deleted successfully.")

    def get_profile(self, profile:str)->dict[str,str]:
        profile_path = path.join(self.PROFILES_DIRECTORY, profile)
        profile_json = path.join(profile_path, "profile.json")

        if not os.path.exists(profile_path) or not os.path.exists(profile_json):
            print("Cannot get profile as it doesn't exist.")
            print("Check the profiles directory and if the profile has the profile.json file.")
            return
        
        with open(profile_json) as file:
            profile_data = json.load(file)

        return profile_data

    def get_profiles(self)->list[str]:
        profiles = []
        for subdir, dirs, files in os.walk(self.PROFILES_DIRECTORY):
            for file in files:
                if file == "profile.json":
                    profiles.append(f"{os.path.basename(subdir)}")
        
        return profiles
    
    def create_mrpack_profile(self, mrpack:str, profile_name:str, overwrite:bool=False):
        profile_path = path.join(self.PROFILES_DIRECTORY, profile_name)
        if path.exists(profile_path) and not overwrite:
            print("Profile already exists.")
            return
    
        print(f"Installing mrpack '{mrpack}'")

        game_directory = path.join(profile_path, "game")
        os.makedirs(profile_path, exist_ok=overwrite)
        os.makedirs(game_directory, exist_ok=True)

        version_name = self._wrapper.download_mrpack(mrpack, game_directory)
        
        profile_data = {
            "profile_name": profile_name,
            "profile_version": version_name
        }
        with open(path.join(profile_path, "profile.json"), "w") as f:
            f.write(json.dumps(profile_data))
        
        print("Profile created successfully.")
        
    def create_curseforge_profile(self, curseforge_zip:str, profile_name:str, overwrite:bool=False):
        profile_path = path.join(self.PROFILES_DIRECTORY, profile_name)
        if path.exists(profile_path) and not overwrite:
            print("Profile already exists.")
            return
    
        print(f"Installing curseforge modpack '{curseforge_zip}'")

        game_directory = path.join(profile_path, "game")
        os.makedirs(profile_path, exist_ok=overwrite)
        os.makedirs(game_directory, exist_ok=True)

        version_name = self._wrapper.download_curseforge_pack(curseforge_zip, game_directory)

        if version_name == None:
            print("Failed to create profile.")
            shutil.rmtree(profile_path)
            return
        
        profile_data = {
            "profile_name": profile_name,
            "profile_version": version_name
        }
        with open(path.join(profile_path, "profile.json"), "w") as f:
            f.write(json.dumps(profile_data))
        
        print("Profile created successfully.")
