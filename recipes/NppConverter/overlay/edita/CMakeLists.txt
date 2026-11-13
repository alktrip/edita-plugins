# Port de Converter a Edita: el código original con la capa de compatibilidad Win32 del SDK
# (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(NppConverter C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(NppConverter UNICODE
    SOURCES ../source/conversionPanel.cpp ../source/DockingFeature/StaticDialog.cpp
            ../source/NppPluginDemo.cpp ../source/PluginDefinition.cpp
    RESOURCES ../source/conversionPanel.rc
    INCLUDES ../source ../source/DockingFeature)
