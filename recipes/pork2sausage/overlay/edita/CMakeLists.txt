# Port de Pork to Sausage a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(pork2sausage C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(pork2sausage UNICODE
    SOURCES ../src/Pork2Sausage.cpp ../src/Process.cpp
    RESOURCES ../src/Pork2Sausage.rc
    INCLUDES . ../src)
