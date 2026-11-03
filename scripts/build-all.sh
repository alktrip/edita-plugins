#!/usr/bin/env bash
# Compila y prueba las recetas del catálogo con Edita, sin la interfaz.
#
#   scripts/build-all.sh EDITA SALIDA [receta...]
#
# EDITA es el ejecutable de Edita (con su SDK de plugins al lado o instalado); SALIDA, la
# carpeta donde quedan los paquetes (<plugin>-<versión>.zip y su .sha256) y un registro
# por receta. Sin recetas, todas las de recipes/. Termina con error si alguna receta no
# compila o no pasa su prueba.
set -u

if [ $# -lt 2 ]; then
    echo "Uso: $0 EDITA SALIDA [receta...]" >&2
    exit 2
fi
edita=$1
output=$2
shift 2
root=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$output"
output=$(cd "$output" && pwd)
export QT_QPA_PLATFORM=${QT_QPA_PLATFORM:-offscreen}

recipes=("$@")
if [ ${#recipes[@]} -eq 0 ]; then
    for dir in "$root"/recipes/*/; do
        recipes+=("$(basename "$dir")")
    done
fi

failed=()
for name in "${recipes[@]}"; do
    recipe="$root/recipes/$name/recipe.json"
    log="$output/$name.log"
    echo "=== $name"
    if ! "$edita" --build-recipe "$recipe" --output "$output" >"$log" 2>&1; then
        tail -n 30 "$log"
        failed+=("$name (compilación)")
        continue
    fi
    package=$(sed -n 's/^==> \(.*\.zip\)$/\1/p' "$log" | tail -n 1)
    if ! "$edita" --check-plugin "$package" --recipe "$recipe" 2>&1 | tee -a "$log"; then
        failed+=("$name (prueba)")
    fi
done

if [ ${#failed[@]} -gt 0 ]; then
    echo
    echo "Fallaron ${#failed[@]} de ${#recipes[@]} recetas:"
    printf '  %s\n' "${failed[@]}"
    exit 1
fi
echo
echo "Las ${#recipes[@]} recetas compilan y pasan su prueba"
