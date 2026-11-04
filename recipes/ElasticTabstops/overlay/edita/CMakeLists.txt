# Port de ElasticTabstops a Edita: el código original con la capa de compatibilidad
# Win32 del SDK (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(ElasticTabstops C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(ElasticTabstops UNICODE
    SOURCES ../src/AboutDialog.cpp ../src/ElasticTabstops.cpp ../src/Hyperlinks.cpp
    RESOURCES ../src/resource.rc
    INCLUDES . ../src)
