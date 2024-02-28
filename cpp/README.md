# TVPaint George WebSocket server plugin

## Setup

To install the build dependencies, we use [Conan](https://conan.io/) which is a C/C++ package manager.

To install it, use the virtualenv provided by [Poetry](https://python-poetry.org/):

```shell
$ poetry install # Installs Conan
$ poetry shell # Enter a new venv shell
```

Then configure your Conan compilation profile:

```shell
(venv) $ conan profile detect
```

To compile the project with MSVC, an example configuration would be:

```ini
# C:\Users\$USER\.conan2\profiles\default

[settings]
arch=x86_64
build_type=Release
compiler=msvc
compiler.cppstd=17
compiler.runtime=static
compiler.version=193
os=Windows
```

- On MSVC, to check your `compiler.version`, run the command `cl` in a [Developer Command Prompt for VS](https://learn.microsoft.com/en-us/visualstudio/ide/reference/command-prompt-powershell?view=vs-2022) and check the `C/C++ Optimizing Compiler Version` for example `19.35.32215`

To check if your profile is correct, use:

```shell
(venv) $ conan profile show
```

## Install dependencies

Install the dependencies specified in [`conanfile.txt`](./conanfile.txt):

```shell
(venv) $ conan install . --output-folder=build --build=missing
```

The above command generates CMake build files that helps finding those libraries.

## Build

You first need to download the TVPaint C/C++ SDK in a local folder.

Configure the project with CMake and Conan by going into the `build` folder:

```shell
$ cd build
$ cmake .. -G "Visual Studio 17 2022" -DCMAKE_TOOLCHAIN_FILE="conan_toolchain.cmake" -DTVPAINT_SDK_FOLDER="/path/to/TVPaint_SDK"
```

(the above command assumes you are using `Visual Studio 17`, if not match that with your Conan profile)

Build the project in release mode:

```
$ cmake --build . --config Release
```

## Install

You can find the generated `.dll` file under `./build/Release/tvpaint-ws-server.dll` after compilation.

To install it, copy the DLL into your `plugins` folder (depending on your TVPaint version):

- On Windows: `C:/Program Files/TVPaint Developpement/TVPaint Animation 11.5 Pro (64bits)/plugins`

## Usage

The WebSocket server is launched at TVPaint's startup.

By default it listens on the port `3000` but you can set the `TVP_WS_PORT` environment variable to set another port.

The protocol used is [JSON RPC](https://www.jsonrpc.org/specification). It allows us to send a request that contains a method and some params to execute.

For example:

```
--> {"jsonrpc": "2.0", "method": "execute_george", "params": ["tv_version"], "id": 0}
<-- {'id': 0, 'jsonrpc': '2.0', 'result': '"TVP Animation 11 Pro" 11.5.3 fr'}

--> {"jsonrpc": "2.0", "method": "unknown_method", "params": [], "id": 0}
<-- {'error': {'code': -32601, 'message': 'Method not found'}, 'id': 0, 'jsonrpc': '2.0'}
```

The logs are located in `{HOME}/.tvpaint-ws-server.log`

## Limitations

- This plugin is Windows only, the CMake configuration would need to be tested and updated
- Due to UTF-8 handling when receiving results from TVPaint's George commands, some characters outside of UTF-16 range are not recognized (example: emoji characters in a layer name)

## Libraries

- TVPaint SDK (get it from customer support)
- [JSON for Modern C++ (nlohmann/json)](https://json.nlohmann.me/)
- [WebSocket++ (websocketpp)](https://github.com/zaphoyd/websocketpp/)
- [spdlog](https://github.com/gabime/spdlog): Very fast, header-only/compiled, C++ logging library

## Ressources

- [Build a simple CMake project](https://docs.conan.io/2/tutorial/consuming_packages/build_simple_cmake_project.html) with Conan.
- Ynput's [OpenPype TVPaint plugin](https://github.com/ynput/OpenPype/tree/develop/openpype/hosts/tvpaint/tvpaint_plugin/plugin_code) was a great inspiration
