# Port de Auto Detect Indention a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(nppAutoDetectIndent C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(nppAutoDetectIndent UNICODE
    SOURCES ../src/dllmain.cpp ../src/nppAutoDetectIndent.cpp ../src/settings.cpp ../src/stdafx.cpp
    RESOURCES ../src/nppAutoDetectIndent.rc
    INCLUDES ../src)
