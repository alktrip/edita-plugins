# Port de Select N' Launch a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(selectNLaunch C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(selectNLaunch UNICODE
    SOURCES ../src/SelectNLaunch.cpp ../src/b64.cpp
    RESOURCES ../src/SelectNLaunch.rc
    INCLUDES ../src)
