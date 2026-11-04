# Port de MZC8051 a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(MZC8051 C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(MZC8051 UNICODE
    SOURCES ../src/DockingFeature/GoToLineDlg.cpp ../src/DockingFeature/StaticDialog.cpp ../src/NppPluginDemo.cpp ../src/PluginDefinition.cpp ../src/dir_file.cpp ../src/myexecute.cpp ../src/osdialog.c ../src/osdialog_win.c ../src/replace.cpp ../src/text_encode.cpp
    RESOURCES ../src/DockingFeature/goLine.rc ../src/NppPluginDemo.rc
    DEFINITIONS INCLUDE_DEPRECATED_FEATURES
    INCLUDES . ../src ../src/DockingFeature)
