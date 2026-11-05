# Port de OCaml Lexer a Edita: el código original con la capa de compatibilidad Win32 del
# SDK. Es un plugin de lexer: exporta las funciones de Lexilla de su exports.def
cmake_minimum_required(VERSION 3.20)
project(OCamlLexer CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
# Lo que hace su build.sh: el XML de estilos, incrustado (el plugin lo escribe en
# plugins/config si no está)
file(READ ../src/config_xml_head.inc head)
file(READ ../config/OCamlLexer.xml xml)
file(READ ../src/config_xml_tail.inc tail)
file(WRITE ${CMAKE_CURRENT_BINARY_DIR}/generated/ocaml_config_xml.h "${head}${xml}${tail}")
edita_npp_plugin(OCamlLexer UNICODE
    SOURCES ../src/ocaml_ilexer.cpp
    INCLUDES ../src ${CMAKE_CURRENT_BINARY_DIR}/generated
    EXPORTS ../exports.def)
