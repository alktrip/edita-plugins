#!/usr/bin/env python3
# This file is part of Edita.
# SPDX-License-Identifier: GPL-3.0-or-later
"""Pruebas de catalog.py: python3 -m unittest discover -s scripts"""

import base64
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import catalog  # noqa: E402


def write(path, text):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path


class Signatures(unittest.TestCase):
    def test_rfc8032_vector(self):
        # RFC 8032, 7.1, TEST 1: la clave sale de la semilla como en libsodium (minisign)
        ed25519, _ = catalog._ed25519()
        seed = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
        key = ed25519.Ed25519PrivateKey.from_private_bytes(seed)
        self.assertEqual(catalog._public_bytes(key).hex(),
                         "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a")
        self.assertEqual(key.sign(b"").hex(),
                         "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555"
                         "fb8821590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b")

    def test_sign_and_verify(self):
        secret, public = catalog.generate_key()
        key_id, private_key = catalog.load_secret(secret)
        public_id, public_key = catalog.load_public(public)
        self.assertEqual(key_id, public_id)
        self.assertEqual(public.splitlines()[0], "untrusted comment: minisign public key " + catalog.key_id_text(key_id))

        data = b'{"npp-plugins": []}\n'
        minisig = catalog.sign(data, key_id, private_key, "timestamp:1\tfile:plugins.json")
        lines = minisig.splitlines()
        self.assertEqual(len(lines), 4)
        raw = base64.b64decode(lines[1])
        self.assertEqual(raw[:2], b"ED")          # prehasheada, como minisign por defecto
        self.assertEqual(raw[2:10], key_id)
        self.assertEqual(catalog.verify(data, minisig, public_id, public_key), "timestamp:1\tfile:plugins.json")
        # La firma es del BLAKE2b-512 del archivo
        ed25519, _ = catalog._ed25519()
        ed25519.Ed25519PublicKey.from_public_bytes(public_key).verify(raw[10:], hashlib.blake2b(data, digest_size=64).digest())

        # Otro contenido, otro comentario de confianza, otra clave: no
        with self.assertRaisesRegex(catalog.CatalogError, "no corresponde"):
            catalog.verify(data + b" ", minisig, public_id, public_key)
        forged = minisig.replace("file:plugins.json", "file:otro.json")
        with self.assertRaisesRegex(catalog.CatalogError, "comentario de confianza"):
            catalog.verify(data, forged, public_id, public_key)
        _, other_public = catalog.generate_key()
        other_id, other_key = catalog.load_public(other_public)
        with self.assertRaisesRegex(catalog.CatalogError, "otra clave"):
            catalog.verify(data, minisig, other_id, other_key)
        with self.assertRaises(catalog.CatalogError):
            catalog.verify(data, minisig, public_id, other_key)
        with self.assertRaises(catalog.CatalogError):
            catalog.sign(data, key_id, private_key, "dos\nlíneas")

    def test_key_id_like_minisign(self):
        self.assertEqual(catalog.key_id_text(bytes([1, 2, 3, 4, 5, 6, 7, 8])), "0807060504030201")

    def test_command_line(self):
        with tempfile.TemporaryDirectory() as tmp:
            secret, public, data = Path(tmp, "clave"), Path(tmp, "catalog.pub"), write(Path(tmp, "plugins.json"), "{}\n")
            self.assertEqual(catalog.main(["keygen", "--secret-out", str(secret), "--public-out", str(public)]), 0)
            self.assertEqual(secret.stat().st_mode & 0o777, 0o600)
            # No se sobrescribe una clave
            self.assertEqual(catalog.main(["keygen", "--secret-out", str(secret), "--public-out", str(public)]), 2)
            self.assertEqual(catalog.main(["sign", "--secret", str(secret), str(data)]), 0)
            self.assertEqual(catalog.main(["verify", "--public", str(public), str(data)]), 0)
            data.write_text("{} \n")
            self.assertEqual(catalog.main(["verify", "--public", str(public), str(data)]), 2)


class Lists(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.recipes = root / "recipes"
        self.packages = root / "paquetes"
        self.sdk = root / "sdk"
        for folder, license_ in (("Libre", "MIT"), ("SoloDos", "GPL-2.0-only"), ("SinPaquete", "GPL-3.0-or-later")):
            write(self.recipes / folder / "recipe.json", json.dumps({
                "folder-name": folder, "display-name": folder + " plugin", "version": "1.2",
                "npp-compatible-versions": "[0.0.1,]", "description": "…", "author": "Autor",
                "homepage": "https://example.org/" + folder, "license": license_}))
            write(self.recipes / folder / "overlay/edita/CMakeLists.txt", "project(%s)\n" % folder)
        for folder in ("Libre", "SoloDos"):
            zip_path = self.packages / ("%s-1.2.zip" % folder)
            zip_path.parent.mkdir(parents=True, exist_ok=True)
            zip_path.write_bytes(b"zip de " + folder.encode())
            write(str(zip_path) + ".sha256", "%s  %s\n" % (catalog.sha256_file(zip_path), zip_path.name))
        write(self.sdk / "edita_plugin.h", "#define EDITA_PLUGIN_API_VERSION 1\n")
        write(self.sdk / "qt/include/QtCore/qconfig.h", '#define QT_VERSION_STR "6.8.3"\n')
        self.recipes_zip = root / "recipes.zip"
        catalog.pack_recipes(self.recipes, self.recipes_zip)

    def tearDown(self):
        self.tmp.cleanup()

    def build(self, version="2026.11.03.1"):
        return catalog.build_list(self.recipes, self.packages, self.sdk, "https://example.org/releases/download/c1",
                                  version, self.recipes_zip, None)

    def test_list(self):
        result = self.build()
        self.assertEqual(result["arch"], "linux-x86_64")
        self.assertEqual(result["edita-plugin-api"], 1)
        self.assertEqual(result["edita-qt"], "6.8.3")
        self.assertEqual(result["edita-recipes"], "https://example.org/releases/download/c1/recipes.zip")
        self.assertEqual(result["edita-recipes-sha256"], catalog.sha256_file(self.recipes_zip))
        plugins = {p["folder-name"]: p for p in result["npp-plugins"]}
        self.assertEqual(list(plugins), ["Libre", "SinPaquete", "SoloDos"])
        # Con licencia compatible y paquete: binario
        libre = plugins["Libre"]
        self.assertEqual(libre["edita-build"], "binary")
        self.assertEqual(libre["repository"], "https://example.org/releases/download/c1/Libre-1.2.zip")
        self.assertEqual(libre["id"], catalog.sha256_file(self.packages / "Libre-1.2.zip"))
        self.assertEqual(libre["edita-recipe"], "recipes/Libre/recipe.json")
        # GPL-2.0-only (incompatible con la capa) o sin paquete: se compila en local
        for folder in ("SoloDos", "SinPaquete"):
            self.assertEqual(plugins[folder]["edita-build"], "recipe")
            self.assertEqual(plugins[folder]["id"], "")
            self.assertEqual(plugins[folder]["repository"], "")
        # Los campos que Edita (y N++) exigen son cadenas
        for p in result["npp-plugins"]:
            for key in ("folder-name", "display-name", "author", "description", "id", "version", "repository", "homepage"):
                self.assertIsInstance(p[key], str)

    def test_package_must_match_its_sha256(self):
        (self.packages / "Libre-1.2.zip").write_bytes(b"otro contenido")
        with self.assertRaisesRegex(catalog.CatalogError, "no coincide"):
            self.build()

    def test_recipes_zip_is_reproducible(self):
        again = Path(self.tmp.name, "otra.zip")
        catalog.pack_recipes(self.recipes, again)
        self.assertEqual(again.read_bytes(), self.recipes_zip.read_bytes())

    def test_changed(self):
        old = self.build("1")
        self.assertEqual(catalog.signature_of_plugins(old), catalog.signature_of_plugins(self.build("2")))
        zip_path = self.packages / "Libre-1.2.zip"
        zip_path.write_bytes(b"paquete nuevo")
        write(str(zip_path) + ".sha256", "%s  %s\n" % (catalog.sha256_file(zip_path), zip_path.name))
        self.assertNotEqual(catalog.signature_of_plugins(old), catalog.signature_of_plugins(self.build("2")))
        self.assertNotEqual(catalog.signature_of_plugins({}), catalog.signature_of_plugins(old))


if __name__ == "__main__":
    unittest.main()
