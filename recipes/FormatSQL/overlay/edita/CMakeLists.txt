# Port de Datamodder SQL Formatter a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(FormatSQL C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(FormatSQL UNICODE
    SOURCES ../src/dialects.cpp ../src/dllmain.cpp ../src/formatter.cpp ../src/settings_dialog.cpp ../src/settings_io.cpp
    RESOURCES ../src/settings.rc
    INCLUDES . ../src)
