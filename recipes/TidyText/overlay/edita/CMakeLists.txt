# Port de TidyText a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(TidyText C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(TidyText UNICODE
    SOURCES ../src/ContextMenu.cpp ../src/NonPrintingChars.cpp ../src/PluginDefinition.cpp ../src/SendToAI.cpp ../src/TidyText.cpp
    RESOURCES ../src/TidyText.rc
    INCLUDES ../src)
