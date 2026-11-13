# Port de JSON Viewer a Edita (C++20): el código original (con su UtilityLib y rapidjson, que llega
# como fuente extra) con la capa de compatibilidad Win32 del SDK, en UNICODE
cmake_minimum_required(VERSION 3.20)
project(NPPJSONViewer C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
set(V ../src/NppJsonViewer)
edita_npp_plugin(NPPJSONViewer UNICODE CXX_STANDARD 20
    SOURCES ${V}/AboutDlg.cpp ${V}/dllmain.cpp ${V}/JsonHandler.cpp ${V}/JsonViewDlg.cpp
            ${V}/NppJsonPlugin.cpp ${V}/Profile.cpp ${V}/RapidJsonHandler.cpp ${V}/ScintillaEditor.cpp
            ${V}/SettingsDlg.cpp ${V}/ShortcutCommand.cpp ${V}/SliderCtrl.cpp ${V}/TreeViewCtrl.cpp
            ${V}/npp_include/DockingFeature/StaticDialog.cpp
            ../src/UtilityLib/Execute.cpp ../src/UtilityLib/StringHelper.cpp ../src/UtilityLib/Utility.cpp
    RESOURCES ${V}/resource.rc
    INCLUDES ${V} ${V}/npp_include ${V}/npp_include/DockingFeature ../src/UtilityLib
             ../external/rapidjson/include)
