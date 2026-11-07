# Port de XML Tools a Edita: XMLToolsEdita.cpp (las órdenes del menú del original
# sobre la API de Edita) con la biblioteca QuickXml del original, sin cambios.
# libxml2 sustituye a MSXML para la sintaxis, la validación y XPath, y libxslt, para
# la transformación XSL.
#
# libxml2 y libxslt van dentro del plugin (estáticas, de extra-sources): la de cada
# distribución cambia de versión de ABI (libxml2.so.2 hasta la 2.13, libxml2.so.16 desde
# la 2.14) y un plugin compilado en una no carga en la otra. Sin ICU, zlib, lzma ni red:
# no hacen falta y serían más bibliotecas del sistema. Sus símbolos no salen del .so
# (--exclude-libs), para no chocar con otra libxml2 cargada en el proceso.
cmake_minimum_required(VERSION 3.20)
project(XMLTools C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)

set(BUILD_SHARED_LIBS OFF CACHE BOOL "" FORCE)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)
foreach(option ICU LZMA ZLIB HTTP FTP PYTHON PROGRAMS TESTS MODULES DEBUG LEGACY)
    set(LIBXML2_WITH_${option} OFF CACHE BOOL "" FORCE)
endforeach()
foreach(option PYTHON PROGRAMS TESTS MODULES PROFILER CRYPTO DEBUGGER)
    set(LIBXSLT_WITH_${option} OFF CACHE BOOL "" FORCE)
endforeach()
# Su código no es el del plugin: sin los avisos del SDK
set(CMAKE_C_FLAGS "${CMAKE_C_FLAGS} -w")
add_subdirectory(../libxml2 libxml2 EXCLUDE_FROM_ALL)
add_subdirectory(../libxslt libxslt EXCLUDE_FROM_ALL)

edita_native_plugin(XMLTools
    SOURCES XMLToolsEdita.cpp ../QuickXmlLib/QuickXml/src/XmlParser.cpp ../QuickXmlLib/QuickXml/src/XmlFormater.cpp
    INCLUDES ../QuickXmlLib/QuickXml/src
    LIBRARIES LibXslt LibXml2
    DEFINITIONS XMLTOOLS_HAVE_XSLT)
target_link_options(XMLTools PRIVATE -Wl,--exclude-libs,ALL)
# QuickXml se escribió para MSVC, que incluye <cstring> de forma indirecta
set_source_files_properties(../QuickXmlLib/QuickXml/src/XmlParser.cpp ../QuickXmlLib/QuickXml/src/XmlFormater.cpp
    PROPERTIES COMPILE_OPTIONS "-include;cstring;-w")
