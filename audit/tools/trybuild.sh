#!/bin/bash
# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
# trybuild.sh <src-dir> <work-root>: copia el código, genera un CMakeLists genérico y compila
set -u
SRC=$(realpath $1); NAME=$(basename $SRC); W=$(realpath $2)/$NAME
ED=${EDITA_SRC:?Falta EDITA_SRC (carpeta del código de Edita)}
rm -rf $W; mkdir -p $W; cp -r $SRC $W/code
find $W/code -iname 'Scintilla.h' -delete -o -iname 'Sci_Position.h' -delete -o -iname 'SciLexer.h' -delete -o -iname 'ILexer.h' -delete
python3 -I "$(dirname "$(realpath "$0")")/normalize.py" $W/code $ED/plugin-sdk/compat $ED/third_party/scintilla/include $ED/third_party/lexilla/include > $W/normalize.log
EXCL='/(scintilla|lexilla|test|tests|unittest|example|examples|docs?|boost)/'
# Fuentes: sin las plantillas de plugins ni el código de N++ que algunos traen como submódulo
SRCEXCL='/(plugintemplate|npp_plugintemplate|notepad-plus-plus|gtest|googletest)/'
SRCS=$(find $W/code \( -name '*.cpp' -o -name '*.c' -o -name '*.cc' -o -name '*.cxx' \) | grep -viE "$EXCL" | grep -viE "$SRCEXCL" | sort)
[ -z "$SRCS" ] && { echo "nosrc" > $W/result; exit; }
INCS=$(find $W/code \( -name '*.h' -o -name '*.hpp' \) -printf '%h\n' | grep -viE "$EXCL" | sort -u)
cat > $W/CMakeLists.txt <<CM
cmake_minimum_required(VERSION 3.20)
project(Try C CXX)
set(EDITA_PLUGIN_SDK $ED/plugin-sdk)
set(EDITA_SCINTILLA_INCLUDE $ED/third_party/scintilla/include)
include(\${EDITA_PLUGIN_SDK}/cmake/EditaNppPlugin.cmake)
edita_npp_plugin(try UNICODE SOURCES $(echo $SRCS) INCLUDES $(echo $INCS) $W/stubs $ED/third_party/lexilla/include)
target_link_options(try PRIVATE -Wl,--no-undefined)
CM
cd $W
export LC_ALL=C
mkdir -p stubs; : > stubs.txt
if ! cmake -S . -B b -G Ninja >cfg.log 2>&1; then echo cfgfail > result; exit; fi
# Hasta 20 vueltas: cada cabecera de Windows que falte se crea vacía (si el plugin
# usa su API, fallará después con «not declared»). Las que tienen ruta (../external/…)
# suelen ser submódulos de git que no vienen en el archivo: esas no se inventan
for i in $(seq 20); do
  timeout 600 cmake --build b -j2 -- -k 0 >build.log 2>&1 && { [ -s stubs.txt ] && echo stubs > result || echo ok > result; break; }
  missing=$(grep -oE "fatal error: [^:]+: No such file" build.log | sed -E 's/fatal error: (.+): No such file/\1/' | sort -u)
  new=0
  for h in $missing; do
    case "$h" in */*|boost*) continue;; esac
    grep -qxF "$h" stubs.txt && continue
    touch "stubs/$h"; echo "$h" >> stubs.txt; new=1
  done
  if [ $new = 0 ]; then
    if grep -q 'undefined reference' build.log; then echo link > result
    elif grep -qE "fatal error: [^:]*/[^:]+: No such file" build.log; then echo deps > result
    else echo compile > result; fi
    break
  fi
done
[ -f result ] || echo compile > result
grep -c 'error:' build.log > nerr 2>/dev/null
