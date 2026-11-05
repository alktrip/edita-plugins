# Port de HLASM Lexer a Edita: el código original con la capa de compatibilidad Win32 del
# SDK. Es un plugin de lexer: exporta las funciones de Lexilla de su exports.def
cmake_minimum_required(VERSION 3.20)
project(HLASMLexer CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
# Lo que hace su build.sh: el XML de estilos, incrustado (el plugin lo escribe en
# plugins/config si no está)
file(READ ../src/config_xml_head.inc head)
file(READ ../config/HLASMLexer.xml xml)
file(READ ../src/config_xml_tail.inc tail)
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/generated/hlasm_config_xml.h "${head}${xml}${tail}")
edita_npp_plugin(HLASMLexer UNICODE
    SOURCES ../src/hlasm_ilexer.cpp
    INCLUDES ../src ${CMAKE_CURRENT_BINARY_DIR}/generated
    EXPORTS ../exports.def)
