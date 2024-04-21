from profile_launcher import Launcher
import sys
from setuptools._distutils.util import strtobool
import asyncio

LAUNCHER_NAME = "PyMineLauncher"
LAUNCHER_VERSION = "1.0"
LAUNCHER_LINK = "https://github.com/Nobody1902/pyminelauncher"
LAUNCHER_DESCRIPTION = "A simple minecraft launcher with full mod support and profiles."
LAUNCHER_HELP = f"If you encounter any issues, please report them here: {LAUNCHER_LINK}/issues/new"

def print_help(create=None):
    if create == None:
        print(f"\n{LAUNCHER_NAME} {LAUNCHER_VERSION} - {LAUNCHER_LINK}")
        print("")
        print(f"    {LAUNCHER_DESCRIPTION}")
        print(f"    {LAUNCHER_HELP}")
        print("\nUsage")
        print("")
        print(f"    help - prints this screen")
        print(f"    versions - lists all vannila versions")
        print(f"    forge - lists all vannila versions supported by forge")
        print(f"    forge [version] - prints forge version for the given vannila version")
        print(f"    fabric - lists all vannila versions supported by fabric")
        print(f"    quilt - lists all vannila versions supported by quilt")
        print(f"")
        print(f"    create [version] [name] [overwrite = false] - creates a new profile")
        print(f"    mrpack [mrpack] [name] [overwrite = false] - creates a new mrpack profile")
        print(f"    curseforge [zip] [name] [overwrite = false] - creates a new curseforge profile")
        print(f"    launch [name] [username] - launcher the profile with offline username")
        print(f"")
        print(f"    profiles - lists all profiles")
        print(f"    profile [name] - prints profile info")
        print(f"    delete [name] - deletes the profile")
        print(f"\nType 'help create' for information regarding version names.")
        print(f"The profile names aren't case sensitive!")
    else:
        print(f"\n{LAUNCHER_NAME} {LAUNCHER_VERSION} - {LAUNCHER_LINK}")
        print("")
        print(f"Usage of {create} [version] [name] [overwrite = false]")
        print(f"    Vannila version - e. 1.20.2")
        print(f"    Latest forge version - e. forge*1.20.2")
        print(f"    Forge version - e. 1.12.2-forge-14.23.5.2860")
        print(f"    Fabric version - e. fabric*1.20.2")
        print(f"    Quilt version - e. quilt*1.20.2")

def print_arguments_error(mode, num = False):
    print(f"{'Too many' if num else 'Not enough'} arguments provided for {mode}.")
    print(f"Type 'help' for more information.")

async def main():

    args = sys.argv[1:]
    try:
        mode = args[0]
    except:
        print("No arguments provided.\nType 'help' for more information.")
        sys.exit()

    arg1 = None
    arg2 = None
    arg3 = None

    try:
        arg1 = args[1]
        arg2 = args[2]
        arg3 = args[3]
    except:
        pass

    if mode == "help":
        if arg1 == "create":
            print_help(arg1)
        else:
            print_help()
        sys.exit()

    launcher = Launcher(launcher_name=LAUNCHER_NAME, launcher_version=LAUNCHER_VERSION)
    await launcher.load()

    if mode == "create":
        # check if both version and profile name are set
        if not arg1 or not arg2:
            print_arguments_error(mode)
            exit()
        
        overwrite = False

        # read the overwrite argument
        if arg3:
            try:
                overwrite = strtobool(arg3)
            except ValueError:
                pass
        
        profile_version = arg1
        profile_name = arg2

        launcher.create_profile(profile_version, profile_name, overwrite=overwrite)
    
    elif mode == "mrpack":
        # check if both mrpack and profile name are set
        if not arg1 or not arg2:
            print_arguments_error(mode)
            sys.exit()
        
        overwrite = False

        # read the overwrite argument
        if arg3:
            try:
                overwrite = strtobool(arg3)
            except ValueError:
                pass
        
        mrpack = arg1
        profile_name = arg2

        launcher.create_mrpack_profile(mrpack, profile_name, overwrite=overwrite)

    elif mode == "curseforge":
        # check if both curseforge and profile name are set
        if not arg1 or not arg2:
            print_arguments_error(mode)
            sys.exit()
        
        overwrite = False

        # read the overwrite argument
        if arg3:
            try:
                overwrite = strtobool(arg3)
            except ValueError:
                pass
        
        curseforge = arg1
        profile_name = arg2

        launcher.create_curseforge_profile(curseforge, profile_name, overwrite=overwrite)

    elif mode == "versions":
        versions = launcher.get_versions()
        for version in versions:
            print(version)
    
    elif mode == "forge":
        version = None
        if arg1:
            version = arg1
        
        if version == None:
            versions = launcher.get_forge_supported_versions()
            for v in versions:
                print(v)
        else:
            try:
                v = launcher.get_forge_version(version)
                print(v)
            except:
                print(f"Version '{version}' either doesn't exist or isn't supported by forge.")
                sys.exit()
    elif mode == "fabric":
        versions = launcher.get_fabric_supported_versions()
        for v in versions:
                print(v)
    
    elif mode == "quilt":
        versions = launcher.get_quilt_supported_versions()
        for v in versions:
                print(v)

    elif mode == "profile":
        if not arg1:
            print_arguments_error(mode)
            sys.exit()
        
        profile_name = arg1

        profile_info = launcher.get_profile(profile_name)

        if profile_info:
            print(profile_info)
    
    elif mode == "profiles":
        for profile in launcher.get_profiles():
            print(profile)

    elif mode == "delete":
        if not arg1:
            print_arguments_error(mode)
            sys.exit()
        
        profile_name = arg1

        launcher.delete_profile(profile_name)

    elif mode == "launch":
        # check if both profile name and username are set
        if not arg1 or not arg2:
            print_arguments_error(mode, not arg1)
            sys.exit()
        
        profile_name = arg1
        username = arg2

        launcher.launch_profile(profile_name, username)
    else:
        print("Unknown command.\nType 'help' for more information.")


if __name__ == "__main__":
    asyncio.run(main())