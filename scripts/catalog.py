#!/usr/bin/env python3
# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
"""La lista de plugins del catálogo de Edita y su firma.

  catalog.py pack-recipes --recipes recipes --out recipes.zip
      las recetas en un .zip reproducible (para compilar en local lo que no tiene binario)
  catalog.py list --recipes recipes --packages paquetes --sdk SDK --base-url URL \\
                  --catalog-version V --recipes-zip recipes.zip --out plugins.json
      la lista, con el formato de nppPluginList.json de Notepad++ y los campos de Edita
  catalog.py changed VIEJA NUEVA
      termina con 0 si los plugins cambiaron (versión, paquete, receta o API) y con 1 si no
  catalog.py keygen --secret-out clave --public-out catalog.pub
  catalog.py sign --secret clave ARCHIVO [--trusted-comment TEXTO]   (o la clave en EDITA_CATALOG_KEY)
  catalog.py verify --public catalog.pub ARCHIVO

La firma es Ed25519 con el formato de minisign (https://jedisct1.github.io/minisign/): el
.minisig se puede comprobar con `minisign -Vm plugins.json -p catalog.pub`. Se firma el
BLAKE2b-512 del archivo (el algoritmo «ED», el de minisign por defecto). La clave secreta
es propia: base64 del identificador (8 bytes) y la semilla Ed25519 (32 bytes).

Solo se publican binarios de plugins con una licencia compatible con la GPL-3 (la capa de
compatibilidad del SDK va dentro de cada .so y es GPL-3.0-or-later): los demás se listan
para compilarse en el equipo del usuario a partir de su receta.
"""

import argparse
import base64
import hashlib
import json
import os
import re
import secrets
import sys
import time
import zipfile
from pathlib import Path

# Licencias (SPDX) con las que se puede publicar un binario que lleva la capa del SDK
BINARY_LICENSES = {
    "GPL-2.0-or-later", "GPL-3.0-only", "GPL-3.0-or-later",
    "LGPL-2.0-only", "LGPL-2.0-or-later", "LGPL-2.1-only", "LGPL-2.1-or-later",
    "LGPL-3.0-only", "LGPL-3.0-or-later", "AGPL-3.0-only", "AGPL-3.0-or-later",
    "Apache-2.0", "MIT", "BSD-2-Clause", "BSD-3-Clause", "ISC", "Zlib", "MPL-2.0",
    "BSL-1.0", "0BSD", "Unlicense", "CC0-1.0",
}

ARCH = "linux-x86_64"
LIST_NAME = "Edita plugin catalog"
SIG_ALG_PREHASHED = b"ED"
SIG_ALG_LEGACY = b"Ed"
ZIP_DATE = (1980, 1, 1, 0, 0, 0)


class CatalogError(Exception):
    pass


# --- Ed25519 (con la biblioteca cryptography) ----------------------------------------------

def _ed25519():
    try:
        from cryptography.hazmat.primitives.asymmetric import ed25519
        from cryptography.hazmat.primitives import serialization
    except ImportError as e:
        raise CatalogError("hace falta el módulo cryptography de Python (pip install cryptography)") from e
    return ed25519, serialization


def _public_bytes(private_key):
    _, serialization = _ed25519()
    return private_key.public_key().public_bytes(serialization.Encoding.Raw, serialization.PublicFormat.Raw)


def key_id_text(key_id):
    """El identificador como lo muestra minisign: el entero de 64 bits (little endian) en hexadecimal"""
    return "%016X" % int.from_bytes(key_id, "little")


def generate_key():
    ed25519, _ = _ed25519()
    key_id = secrets.token_bytes(8)
    seed = secrets.token_bytes(32)
    private_key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
    secret = base64.b64encode(key_id + seed).decode() + "\n"
    public = ("untrusted comment: minisign public key %s\n" % key_id_text(key_id)
              + base64.b64encode(b"Ed" + key_id + _public_bytes(private_key)).decode() + "\n")
    return secret, public


def load_secret(text):
    ed25519, _ = _ed25519()
    try:
        raw = base64.b64decode(text.strip(), validate=True)
    except ValueError as e:
        raise CatalogError("la clave secreta no es base64") from e
    if len(raw) != 40:
        raise CatalogError("la clave secreta no tiene 40 bytes (identificador y semilla)")
    return raw[:8], ed25519.Ed25519PrivateKey.from_private_bytes(raw[8:])


def load_public(text):
    """Una clave pública de minisign: el archivo .pub o solo su línea en base64"""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    lines = [line for line in lines if not line.startswith("untrusted comment:")]
    if len(lines) != 1:
        raise CatalogError("la clave pública no tiene el formato de minisign")
    raw = base64.b64decode(lines[0], validate=True)
    if len(raw) != 42 or raw[:2] != b"Ed":
        raise CatalogError("la clave pública no es una clave Ed25519 de minisign")
    return raw[2:10], raw[10:]


def sign(data, key_id, private_key, trusted_comment, untrusted_comment=None):
    """El .minisig de `data`, prehasheado (ED) como minisign 0.10 y posteriores"""
    if "\n" in trusted_comment or "\r" in trusted_comment:
        raise CatalogError("el comentario de confianza debe ser de una línea")
    signature = private_key.sign(hashlib.blake2b(data, digest_size=64).digest())
    global_signature = private_key.sign(signature + trusted_comment.encode())
    untrusted = untrusted_comment or "signature from Edita plugin catalog key %s" % key_id_text(key_id)
    return ("untrusted comment: %s\n" % untrusted
            + base64.b64encode(SIG_ALG_PREHASHED + key_id + signature).decode() + "\n"
            + "trusted comment: %s\n" % trusted_comment
            + base64.b64encode(global_signature).decode() + "\n")


def verify(data, minisig, public_key_id, public_key):
    """Comprueba el .minisig como minisign -V; devuelve el comentario de confianza"""
    ed25519, _ = _ed25519()
    from cryptography.exceptions import InvalidSignature
    lines = minisig.splitlines()
    if len(lines) < 4 or not lines[0].startswith("untrusted comment:") or not lines[2].startswith("trusted comment: "):
        raise CatalogError("la firma no tiene el formato de minisign")
    try:
        raw = base64.b64decode(lines[1].strip(), validate=True)
        global_signature = base64.b64decode(lines[3].strip(), validate=True)
    except ValueError as e:
        raise CatalogError("la firma no es base64") from e
    if len(raw) != 74 or len(global_signature) != 64:
        raise CatalogError("la firma no tiene el tamaño de una firma de minisign")
    algorithm, key_id, signature = raw[:2], raw[2:10], raw[10:]
    if key_id != public_key_id:
        raise CatalogError("la firma es de otra clave (%s, no %s)" % (key_id_text(key_id), key_id_text(public_key_id)))
    if algorithm == SIG_ALG_PREHASHED:
        message = hashlib.blake2b(data, digest_size=64).digest()
    elif algorithm == SIG_ALG_LEGACY:
        message = data
    else:
        raise CatalogError("algoritmo de firma desconocido")
    trusted_comment = lines[2][len("trusted comment: "):]
    key = ed25519.Ed25519PublicKey.from_public_bytes(public_key)
    try:
        key.verify(signature, message)
    except InvalidSignature as e:
        raise CatalogError("la firma no corresponde al archivo") from e
    try:
        key.verify(global_signature, signature + trusted_comment.encode())
    except InvalidSignature as e:
        raise CatalogError("la firma del comentario de confianza no es válida") from e
    return trusted_comment


# --- Recetas y lista ------------------------------------------------------------------------

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def load_recipes(recipes_dir):
    recipes = []
    for path in sorted(Path(recipes_dir).glob("*/recipe.json"), key=lambda p: p.parent.name.lower()):
        with open(path, encoding="utf-8") as f:
            recipe = json.load(f)
        if recipe.get("folder-name") != path.parent.name:
            raise CatalogError("%s: folder-name no es el nombre de su carpeta" % path)
        recipes.append(recipe)
    return recipes


def publishable(recipe):
    return recipe.get("license") in BINARY_LICENSES


def pack_recipes(recipes_dir, out):
    """Las recetas en un .zip que no depende de fechas ni del orden del disco"""
    root = Path(recipes_dir)
    files = sorted(p for p in root.rglob("*") if p.is_file())
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for path in files:
            info = zipfile.ZipInfo("recipes/" + path.relative_to(root).as_posix(), ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            z.writestr(info, path.read_bytes())


def sdk_versions(sdk_dir):
    sdk = Path(sdk_dir)
    api = re.search(r"#define\s+EDITA_PLUGIN_API_VERSION\s+(\d+)", (sdk / "edita_plugin.h").read_text(encoding="utf-8"))
    if not api:
        raise CatalogError("%s no define EDITA_PLUGIN_API_VERSION" % (sdk / "edita_plugin.h"))
    qt = None
    qconfig = sdk / "qt/include/QtCore/qconfig.h"
    if qconfig.is_file():
        m = re.search(r'#define\s+QT_VERSION_STR\s+"([^"]+)"', qconfig.read_text(encoding="utf-8"))
        qt = m.group(1) if m else None
    return int(api.group(1)), qt


def package_of(packages_dir, folder):
    """El paquete <carpeta>-<versión>.zip y su SHA-256 (del .sha256 que deja --build-recipe)"""
    found = sorted(Path(packages_dir).glob(folder + "-*.zip.sha256"))
    found = [p for p in found if re.fullmatch(re.escape(folder) + r"-[^-]+\.zip\.sha256", p.name)]
    if len(found) != 1:
        return None, None
    sha, name = found[0].read_text().split()
    zip_path = found[0].with_name(name)
    if not zip_path.is_file() or sha256_file(zip_path) != sha:
        raise CatalogError("%s no coincide con su .sha256" % zip_path)
    return zip_path, sha


def build_list(recipes_dir, packages_dir, sdk_dir, base_url, catalog_version, recipes_zip, recipes_url):
    api, qt = sdk_versions(sdk_dir)
    base_url = base_url.rstrip("/") + "/"
    entries = []
    for recipe in load_recipes(recipes_dir):
        folder = recipe["folder-name"]
        entry = {key: recipe.get(key, "") for key in
                 ("folder-name", "display-name", "version", "npp-compatible-versions")}
        entry["id"] = ""
        entry["repository"] = ""
        for key in ("description", "author", "homepage", "license"):
            entry[key] = recipe.get(key, "")
        entry["edita-recipe"] = "recipes/%s/recipe.json" % folder
        zip_path, sha = package_of(packages_dir, folder) if packages_dir else (None, None)
        if publishable(recipe) and zip_path:
            entry["id"] = sha
            entry["repository"] = base_url + zip_path.name
            entry["edita-build"] = "binary"
        else:
            entry["edita-build"] = "recipe"
        entries.append(entry)
    result = {
        "name": LIST_NAME,
        "version": catalog_version,
        "arch": ARCH,
        "edita-plugin-api": api,
        "edita-recipes": recipes_url or (base_url + Path(recipes_zip).name),
        "edita-recipes-sha256": sha256_file(recipes_zip),
        "npp-plugins": entries,
    }
    if qt:
        result["edita-qt"] = qt
    return result


def signature_of_plugins(catalog):
    """Lo que importa para saber si hay que publicar: los plugins, sus paquetes y la API"""
    plugins = sorted((p["folder-name"], p["version"], p["id"], p["edita-build"], p.get("license", ""),
                      p.get("description", ""), p.get("display-name", ""))
                     for p in catalog.get("npp-plugins", []))
    return (catalog.get("edita-plugin-api"), catalog.get("edita-recipes-sha256"), plugins)


def dump_json(data):
    return json.dumps(data, ensure_ascii=False, indent="\t") + "\n"


# --- Órdenes --------------------------------------------------------------------------------

def main(argv=None):
    parser = argparse.ArgumentParser(description="Lista y firma del catálogo de plugins de Edita")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("pack-recipes")
    p.add_argument("--recipes", required=True)
    p.add_argument("--out", required=True)

    p = sub.add_parser("list")
    p.add_argument("--recipes", required=True)
    p.add_argument("--packages")
    p.add_argument("--sdk", required=True, help="el plugin-sdk de Edita (en el AppImage: usr/share/edita/plugin-sdk)")
    p.add_argument("--base-url", required=True, help="dónde se publican los paquetes")
    p.add_argument("--catalog-version", required=True)
    p.add_argument("--recipes-zip", required=True)
    p.add_argument("--recipes-url", help="por defecto, junto a los paquetes")
    p.add_argument("--out", required=True)

    p = sub.add_parser("changed")
    p.add_argument("old")
    p.add_argument("new")

    p = sub.add_parser("keygen")
    p.add_argument("--secret-out", required=True)
    p.add_argument("--public-out", required=True)

    p = sub.add_parser("sign")
    p.add_argument("--secret", help="archivo con la clave (si no, la variable EDITA_CATALOG_KEY)")
    p.add_argument("--trusted-comment")
    p.add_argument("file")

    p = sub.add_parser("verify")
    p.add_argument("--public", required=True)
    p.add_argument("--sig")
    p.add_argument("file")

    args = parser.parse_args(argv)
    try:
        if args.command == "pack-recipes":
            pack_recipes(args.recipes, args.out)
        elif args.command == "list":
            catalog = build_list(args.recipes, args.packages, args.sdk, args.base_url, args.catalog_version,
                                 args.recipes_zip, args.recipes_url)
            Path(args.out).write_text(dump_json(catalog), encoding="utf-8")
            for p in catalog["npp-plugins"]:
                print("%-24s %-10s %s" % (p["folder-name"], p["edita-build"], p["license"]))
        elif args.command == "changed":
            old = json.loads(Path(args.old).read_text(encoding="utf-8")) if Path(args.old).is_file() else {}
            new = json.loads(Path(args.new).read_text(encoding="utf-8"))
            changed = signature_of_plugins(old) != signature_of_plugins(new)
            print("hay cambios" if changed else "sin cambios")
            return 0 if changed else 1
        elif args.command == "keygen":
            for path in (args.secret_out, args.public_out):
                if Path(path).exists():
                    raise CatalogError("%s ya existe: no se sobrescribe una clave" % path)
            secret, public = generate_key()
            fd = os.open(args.secret_out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            with os.fdopen(fd, "w") as f:
                f.write(secret)
            Path(args.public_out).write_text(public)
            print(public, end="")
        elif args.command == "sign":
            text = Path(args.secret).read_text() if args.secret else os.environ.get("EDITA_CATALOG_KEY", "")
            if not text.strip():
                raise CatalogError("falta la clave secreta (--secret o EDITA_CATALOG_KEY)")
            key_id, private_key = load_secret(text)
            data = Path(args.file).read_bytes()
            comment = args.trusted_comment or "timestamp:%d\tfile:%s" % (int(time.time()), Path(args.file).name)
            Path(args.file + ".minisig").write_text(sign(data, key_id, private_key, comment))
        elif args.command == "verify":
            key_id, public_key = load_public(Path(args.public).read_text())
            minisig = Path(args.sig or args.file + ".minisig").read_text()
            comment = verify(Path(args.file).read_bytes(), minisig, key_id, public_key)
            print("Firma válida: %s" % comment)
    except (CatalogError, OSError, ValueError, KeyError, json.JSONDecodeError) as e:
        print("Error: %s" % e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
