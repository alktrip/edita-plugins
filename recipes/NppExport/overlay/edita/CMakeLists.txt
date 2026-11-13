# Port de NppExport a Edita: el código original con la capa de compatibilidad Win32 del SDK
# (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(NppExport C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(NppExport UNICODE
    SOURCES ../src/NppExport.cpp ../src/Exporter.cpp ../src/HTMLExporter.cpp ../src/RTFExporter.cpp
            ../src/TXTExporter.cpp ../src/stdafx.cpp
    RESOURCES ../src/resource.rc
    INCLUDES ../src ../src/Notepad_specific)
