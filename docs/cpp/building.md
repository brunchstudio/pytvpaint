# Building the plugin

!!! Note

    The C++ plugin is currently Windows only.

## Setup

To install the build dependencies, we use [Conan](https://conan.io/) which is a C/C++ package manager.

To install it, use [Hatch](https://hatch.pypa.io/). 

If you do not have Hatch, you can install it via Python pip :

```shell
❯ pip install hatch
```

Then configure your Conan compilation profile:

```shell
❯ hatch run conan profile detect
```

### Windows

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
❯ hatch run conan profile show
```

#### Install the C++ dependencies

Install the dependencies specified in [`conanfile.txt`](https://github.com/brunchstudio/tvpaint-rpc/blob/main/conanfile.txt):

```shell
❯ hatch run conan install . --output-folder=build --build=missing
```

The above command generates CMake build files that helps to find those libraries.

#### Build

You first need to download the TVPaint C/C++ SDK in a local folder.

Configure the project with CMake and Conan by going into the `build` folder:

```shell
❯ cd build
❯ cmake .. -G "Visual Studio 17 2022" -DCMAKE_TOOLCHAIN_FILE="conan_toolchain.cmake" -DTVPAINT_SDK_FOLDER="/path/to/TVPaint_SDK"
```

(the above command assumes you are using `Visual Studio 17`, if not match that with your Conan profile)

Build the project in release mode:

```console
❯ cmake --build . --config Release
```
