# Port de Indent By Fold a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(IndentByFold C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(IndentByFold UNICODE
    SOURCES ../IBFMenu.cpp ../IBFPlugin.cpp ../IndentByFold.cpp ../NppMessager.cpp ../NppPlugin.cpp ../NppPluginMenu.cpp ../SciMessager.cpp ../WaitCursor.cpp
    RESOURCES ../IndentByFold_res.rc
    INCLUDES . .. ../NPP)
