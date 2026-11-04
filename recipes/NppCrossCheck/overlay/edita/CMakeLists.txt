# Port de NppCrossCheck a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(NppCrossCheck C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(NppCrossCheck UNICODE
    SOURCES ../src/DockingFeature/GoToLineDlg.cpp ../src/DockingFeature/StaticDialog.cpp ../src/NppCrossCheck.cpp ../src/PluginDefinition.cpp
    RESOURCES ../src/DockingFeature/goLine.rc ../src/NppCrossCheck.rc
    INCLUDES . ../src ../src/DockingFeature)
