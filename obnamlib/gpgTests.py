# Copyright (C) 2006  Lars Wirzenius <liw@iki.fi>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.


"""Unit tests for obnamlib.gpg."""


import os
import shutil
import tempfile
import unittest


import obnamlib


class GpgEncryptionFailureTests(unittest.TestCase):

    def testIncludesExitCodeInMessage(self):
        e = obnamlib.gpg.GpgEncryptionFailure(42, "")
        self.failUnless("42" in str(e))

    def testIncludesStderrInMessage(self):
        e = obnamlib.gpg.GpgEncryptionFailure(42, "pink")
        self.failUnless("pink" in str(e))


class GpgDecryptionFailureTests(unittest.TestCase):

    def testIncludesExitCodeInMessage(self):
        e = obnamlib.gpg.GpgDecryptionFailure(42, "")
        self.failUnless("42" in str(e))

    def testIncludesStderrInMessage(self):
        e = obnamlib.gpg.GpgDecryptionFailure(42, "pink")
        self.failUnless("pink" in str(e))


class GpgTests(unittest.TestCase):

    def setUp(self):
        self.block = "pink"
        self.config = obnamlib.config.default_config()
        self.config.set("backup", "gpg-home", "sample-gpg-home")
        self.config.set("backup", "gpg-encrypt-to", "490C9ED1")
        self.config.set("backup", "gpg-sign-with", "490C9ED1")

    def testRoundTrip(self):
        encrypted = obnamlib.gpg.encrypt(self.config, self.block)
        self.failIf(self.block in encrypted)
        decrypted = obnamlib.gpg.decrypt(self.config, encrypted)
        self.failUnlessEqual(self.block, decrypted)

    def testEncryptionWithInvalidKey(self):
        self.config.set("backup", "gpg-encrypt-to", "pretty")
        self.failUnlessRaises(obnamlib.gpg.GpgEncryptionFailure,
                              obnamlib.gpg.encrypt, self.config, "")

    def testDecryptionWithInvalidData(self):
        self.failUnlessRaises(obnamlib.gpg.GpgDecryptionFailure,
                              obnamlib.gpg.decrypt, self.config, "pink")