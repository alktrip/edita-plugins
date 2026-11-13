# Port de HEX-Editor a Edita: el código original con la capa de compatibilidad Win32 del SDK
# (UNICODE, como los plugins de N++ desde la 8.0)
cmake_minimum_required(VERSION 3.20)
project(HexEditor C CXX)
include(${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
set(H ../HexEditor/src)
set(C ../Common/Ccpp)
edita_npp_plugin(HexEditor UNICODE
    SOURCES ${C}/Common.cpp ${C}/dpiManagerV2.cpp ${C}/StaticDialog.cpp ${C}/NppDarkModeDummy.cpp
            ${H}/HelpDlg/HelpDialog.cpp ${H}/HelpDlg/URLCtrl.cpp ${H}/Hex.cpp ${H}/HEXDialog.cpp
            ${H}/misc/ColorCombo.cpp ${H}/misc/ColorPopup.cpp ${H}/misc/ModifyMenu.cpp ${H}/misc/MultiTypeCombo.cpp
            ${H}/OptionDlg/ColumnDialog.cpp ${H}/OptionDlg/OptionDialog.cpp
            ${H}/UserDlg/CompareDialog.cpp ${H}/UserDlg/FindReplaceDialog.cpp ${H}/UserDlg/GotoDialog.cpp
            ${H}/UserDlg/PatternDialog.cpp ${H}/Utf8_16.cpp
    RESOURCES ${H}/HEXDialog.rc
    INCLUDES ${H} ${H}/HelpDlg ${H}/misc ${H}/OptionDlg ${H}/UserDlg ${C} ../NativeLang/src)
