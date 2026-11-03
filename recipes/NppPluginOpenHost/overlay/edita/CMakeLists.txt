# Port de NppPluginOpenHost a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(NppPluginOpenHost C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(NppPluginOpenHost UNICODE
    SOURCES ../src/NppPluginDemo.cpp ../src/PluginDefinition.cpp
    RESOURCES ../src/NppPluginDemo.rc
    INCLUDES ../src)
