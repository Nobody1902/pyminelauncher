from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but they might need fine-tuning.
build_exe_options = {
    "zip_include_packages": ["setuptools"],
}

setup(
    name="PyMineLauncher",
    version="1.0",
    url="https://github.com/Nobody1902/pyminelauncher",
    download_url="https://github.com/Nobody1902/pyminelauncher",
    description="CLI minecraft launcher",
    options={"build_exe": build_exe_options},
    executables=[Executable("pml.py", base="console")],
)