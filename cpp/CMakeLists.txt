cmake_minimum_required(VERSION 3.25)
project(tvpaint-ws-server C CXX)

# Set C++ standard version requirement
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Output build/compile_commands.json for clangd support
option(CMAKE_EXPORT_COMPILE_COMMANDS ON)

# Microsoft Visual C++
if(MSVC)
    # Export symbols from a .dll that are not in any of its object files but are added by the linker from dependencies
    # See: https://cmake.org/cmake/help/latest/prop_tgt/WINDOWS_EXPORT_ALL_SYMBOLS.html
    set(CMAKE_WINDOWS_EXPORT_ALL_SYMBOLS ON)
    add_definitions(-D_CRT_SECURE_NO_WARNINGS)
    
    # Define WIN64 or WIN32 for TVPaint SDK
    if(CMAKE_SIZEOF_VOID_P EQUAL 8)
        message("64bit")
        add_definitions(-DWIN64)
    elseif(CMAKE_SIZEOF_VOID_P EQUAL 4)
        message("32bit")
        add_definitions(-DWIN32)
    endif()
endif()

# Use static boost libraries
set(Boost_USE_STATIC_LIBS ON)

# Check TVPaint C++ SDK folder
set(TVPAINT_SDK_FOLDER "" CACHE INTERNAL "TVPaint C++ SDK folder location")
if (TVPAINT_SDK_FOLDER STREQUAL "")
  message(FATAL_ERROR "Please provide the TVPaint C++ SDK folder.")
endif()

# Find dependencies
find_package(nlohmann_json REQUIRED)
find_package(websocketpp REQUIRED)
find_package(spdlog REQUIRED)

# Include TVPaint SDK
include_directories("${TVPAINT_SDK_FOLDER}/include")

# Search for source files and configure library
file(GLOB SOURCES "src/*.cpp" "src/*.hpp")
add_library(${PROJECT_NAME} SHARED ${SOURCES} library.def "${TVPAINT_SDK_FOLDER}/lib/dllx.c")

# Link libraries
target_link_libraries(${PROJECT_NAME} PRIVATE nlohmann_json::nlohmann_json)
target_link_libraries(${PROJECT_NAME} PRIVATE websocketpp::websocketpp)
target_link_libraries(${PROJECT_NAME} PRIVATE spdlog::spdlog)