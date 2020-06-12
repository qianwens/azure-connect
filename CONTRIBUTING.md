# Contributing
## Dev Env Setup
### Clone Required repo in one folder
1. https://github.com/Azure/azure-cli
2. https://github.com/VSChina/azure-connect.git

### Set the Python VEnv
1. Install Python 3.6+ from http://python.org.
2. Init the Python venv in the source folder
    ```BatchFile
    python -m venv env
    ```
    or
    ```Shell
    python3 -m venv env
    ```
    The result folder structure under the source folder is like
    ```
    source-directory/
    |-- azure-cli/
    |-- azure-connect/
    |-- env/
    ```
3. Activate the virtual environment by running
   Windows CMD.exe:
    ```BatchFile
    env\Scripts\activate.bat
    ```

    Windows Powershell:
    ```
    env\Scripts\activate.ps1
    ```

    OSX/Linux (bash):
    ```Shell
    source env/bin/activate
    ```
4. Install `azdev` tool by running: `pip install azdev`
5. Complete setup by running: `azdev setup -c -r azure-connect`
6. Install the extension by running: `azdev extension add azure-connect`

### VSCode
1. Install the python extension
   * ([ms-python.python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) is recommended)
2. Open the `azure-connect` folder in VSCode. The settings should be loaded.
3. Update `args` configuration in `launch.json` to debug different commands.
