# Port de SQL Column Highlighter a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(SqlColumnHighlighter C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(SqlColumnHighlighter UNICODE
    SOURCES ../src/Highlighter.cpp ../src/PluginMain.cpp
    RESOURCES ../src/version.rc
    INCLUDES ../src)
