# -*- Mode:Python; indent-tabs-mode:nil; tab-width:4 -*-
#
# Copyright (C) 2015-2019 Canonical Ltd
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License version 3 as
# published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import os
import jsonschema
from textwrap import dedent
from unittest import mock

import fixtures
from testtools.matchers import Contains, DirExists, Equals, HasLength, Not

from snapcraft.internal import errors
from snapcraft.project import Project
from snapcraft.plugins import go
from tests import fixture_setup, unit


class GoPluginBaseTest(unit.TestCase):

    deb_arch = None

    def setUp(self):
        super().setUp()

        snapcraft_yaml_path = self.make_snapcraft_yaml(
            dedent(
                """\
            name: go-snap
            base: core18
        """
            )
        )

        self.project = Project(
            target_deb_arch=self.deb_arch, snapcraft_yaml_file_path=snapcraft_yaml_path
        )

        def fake_go_build(command, cwd, *args, **kwargs):
            if command[0] == "go" and command[1] == "build" and "-o" in command:
                open(
                    os.path.join(command[command.index("-o") + 1], "binary"), "w"
                ).close()
            elif command[0] == "go" and command[1] == "build" and "-o" not in command:
                # the package is -1
                open(os.path.join(cwd, os.path.basename(command[-1])), "w").close()

        fake_run = self.useFixture(
            fixtures.MockPatch(
                "snapcraft.internal.common.run", side_effect=fake_go_build
            )
        )
        self.run_mock = fake_run.mock

        fake_run_output = self.useFixture(
            fixtures.MockPatch("snapcraft.internal.common.run_output")
        )
        self.run_output_mock = fake_run_output.mock


class GoPluginPropertiesTest(unit.TestCase):
    def test_schema(self):
        schema = go.GoPlugin.schema()

        properties = schema["properties"]
        for expected in ["go-packages", "go-importpath", "go-buildtags"]:
            self.assertTrue(
                expected in properties,
                "Expected {!r} to be included in properties".format(expected),
            )

        # Check go-channel
        go_channel = properties["go-channel"]
        for expected in ["type", "default"]:
            self.assertTrue(
                expected in go_channel,
                "Expected {!r} to be included in 'go-channel'".format(expected),
            )

        go_channel_type = go_channel["type"]
        self.assertThat(
            go_channel_type,
            Equals("string"),
            'Expected "go-channel" "type" to be "string", but '
            'it was "{}"'.format(go_channel_type),
        )

        go_channel_default = go_channel["default"]
        self.assertThat(
            go_channel_default,
            Equals("latest/stable"),
            'Expected "go-channel" "default" to be '
            '"latest/stable", but it was "{}"'.format(go_channel_default),
        )

        # Check go-packages
        go_packages = properties["go-packages"]
        for expected in ["type", "default", "minitems", "uniqueItems", "items"]:
            self.assertTrue(
                expected in go_packages,
                "Expected {!r} to be included in 'go-packages'".format(expected),
            )

        go_packages_type = go_packages["type"]
        self.assertThat(
            go_packages_type,
            Equals("array"),
            'Expected "go-packages" "type" to be "array", but '
            'it was "{}"'.format(go_packages_type),
        )

        go_packages_default = go_packages["default"]
        self.assertThat(
            go_packages_default,
            Equals([]),
            'Expected "go-packages" "default" to be '
            '"d[]", but it was "{}"'.format(go_packages_default),
        )

        go_packages_minitems = go_packages["minitems"]
        self.assertThat(
            go_packages_minitems,
            Equals(1),
            'Expected "go-packages" "minitems" to be 1, but '
            "it was {}".format(go_packages_minitems),
        )

        self.assertTrue(go_packages["uniqueItems"])

        go_packages_items = go_packages["items"]
        self.assertTrue(
            "type" in go_packages_items,
            'Expected "type" to be included in "go-packages" ' '"items"',
        )

        go_packages_items_type = go_packages_items["type"]
        self.assertThat(
            go_packages_items_type,
            Equals("string"),
            'Expected "go-packages" "item" "type" to be '
            '"string", but it was "{}"'.format(go_packages_items_type),
        )

        # Check go-importpath
        go_importpath = properties["go-importpath"]
        for expected in ["type"]:
            self.assertTrue(
                expected in go_importpath,
                "Expected {!r} to be included in 'go-importpath'".format(expected),
            )

        go_importpath_type = go_importpath["type"]
        self.assertThat(
            go_importpath_type,
            Equals("string"),
            'Expected "go-importpath" "type" to be "string", but '
            'it was "{}"'.format(go_importpath_type),
        )

        go_importpath_default = go_importpath["default"]
        self.assertThat(
            go_importpath_default,
            Equals(""),
            'Expected "go-default" "default" to be "'
            '", but '
            'it was "{}"'.format(go_importpath_default),
        )

        # Check go-buildtags
        go_buildtags = properties["go-buildtags"]
        for expected in ["type", "default", "minitems", "uniqueItems", "items"]:
            self.assertTrue(
                expected in go_buildtags,
                "Expected {!r} to be included in 'go-buildtags'".format(expected),
            )

        go_buildtags_type = go_buildtags["type"]
        self.assertThat(
            go_buildtags_type,
            Equals("array"),
            'Expected "go-buildtags" "type" to be "array", but '
            'it was "{}"'.format(go_buildtags_type),
        )

        go_buildtags_default = go_buildtags["default"]
        self.assertThat(
            go_buildtags_default,
            Equals([]),
            'Expected "go-buildtags" "default" to be "[]", but '
            'it was "{}"'.format(go_buildtags_type),
        )

        go_buildtags_minitems = go_buildtags["minitems"]
        self.assertThat(
            go_buildtags_minitems,
            Equals(1),
            'Expected "go-buildtags" "minitems" to be 1, but '
            "it was {}".format(go_buildtags_minitems),
        )

        self.assertTrue(go_buildtags["uniqueItems"])

        go_buildtags_items = go_buildtags["items"]
        self.assertTrue(
            "type" in go_buildtags_items,
            'Expected "type" to be included in "go-buildtags" ' '"items"',
        )

        go_buildtags_items_type = go_buildtags_items["type"]
        self.assertThat(
            go_buildtags_items_type,
            Equals("string"),
            'Expected "go-buildtags" "item" "type" to be '
            '"string", but it was "{}"'.format(go_packages_items_type),
        )

        # Check required properties
        self.assertNotIn("required", schema)

    def test_get_pull_properties(self):
        expected_pull_properties = ["go-packages", "go-channel"]
        resulting_pull_properties = go.GoPlugin.get_pull_properties()

        self.assertThat(
            resulting_pull_properties, HasLength(len(expected_pull_properties))
        )

        for property in expected_pull_properties:
            self.assertIn(property, resulting_pull_properties)

    def test_get_build_properties(self):
        expected_build_properties = ["go-packages", "go-buildtags", "go-channel"]
        resulting_build_properties = go.GoPlugin.get_build_properties()

        self.assertThat(
            resulting_build_properties, HasLength(len(expected_build_properties))
        )

        for property in expected_build_properties:
            self.assertIn(property, resulting_build_properties)


class MockElfFile:
    def __init__(self, *, path: str) -> None:
        self.path = path
        self.is_dynamic = True


class GoPluginTest(GoPluginBaseTest):
    def setUp(self):

        super().setUp()

        self.useFixture(fixture_setup.CleanEnvironment())

        patcher = mock.patch("sys.stdout")
        patcher.start()
        self.addCleanup(patcher.stop)

    def assert_go_paths(self, plugin: go.GoPlugin) -> None:
        self.assertThat(plugin._gopath, DirExists())
        self.assertThat(plugin._gopath_src, DirExists())

    def test_pull_local_sources(self):
        class Options:
            source = "dir"
            go_channel = "latest/stable"
            go_packages = []
            go_importpath = ""

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)
        open(os.path.join(plugin.sourcedir, "main.go"), "w").close()

        plugin.pull()

        self.run_mock.assert_has_calls(
            [
                mock.call(
                    ["go", "get", "-t", "-d", "./dir/..."],
                    cwd=plugin._gopath_src,
                    env=mock.ANY,
                )
            ]
        )

        self.assert_go_paths(plugin)

    def test_pull_go_mod(self):
        class Options:
            source = "dir"
            go_channel = "latest/stable"
            go_packages = []
            go_importpath = ""

        self.run_output_mock.return_value = "go version go13 linux/amd64"

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)
        open(os.path.join(plugin.sourcedir, "go.mod"), "w").close()

        plugin.pull()

        self.run_output_mock.assert_called_once_with(
            ["go", "version"], cwd=mock.ANY, env=mock.ANY
        )
        self.run_mock.assert_called_once_with(
            ["go", "mod", "download"], cwd=plugin.sourcedir, env=mock.ANY
        )

    def test_go_mod_requires_newer_go_version(self):
        class Options:
            source = "dir"
            go_channel = "latest/stable"
            go_packages = []
            go_importpath = ""
            go_buildtags = ""

        self.run_output_mock.return_value = "go version go1.6.4 linux/amd64"

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)
        open(os.path.join(plugin.sourcedir, "go.mod"), "w").close()

        self.assertRaises(go.GoModRequiredVersionError, plugin.pull)

        self.run_output_mock.assert_called_once_with(
            ["go", "version"], cwd=mock.ANY, env=mock.ANY
        )
        self.run_mock.assert_not_called()

    def test_no_local_source_with_go_packages(self):
        class Options:
            source = None
            go_channel = "latest/stable"
            go_packages = ["github.com/gotools/vet"]
            go_importpath = ""

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)

        plugin.pull()

        self.run_mock.assert_has_calls(
            [
                mock.call(
                    ["go", "get", "-t", "-d", plugin.options.go_packages[0]],
                    env=mock.ANY,
                    cwd=plugin._gopath_src,
                )
            ]
        )

        self.assert_go_paths(plugin)

    def test_pull_with_local_sources_or_go_packages(self):
        class Options:
            source = None
            go_channel = "latest/stable"
            go_packages = []
            go_importpath = ""

        plugin = go.GoPlugin("test-part", Options(), self.project)
        plugin.pull()

        self.run_mock.assert_has_calls([])

        self.assert_go_paths(plugin)

    def test_build_with_local_sources(self):
        class Options:
            source = "dir"
            go_channel = "latest/stable"
            go_packages = []
            go_importpath = ""
            go_buildtags = ""

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)
        open(os.path.join(plugin.sourcedir, "main.go"), "w").close()

        plugin.pull()

        os.makedirs(plugin.builddir)

        self.run_mock.reset_mock()
        self.run_output_mock.reset_mock()
        self.run_output_mock.return_value = "dir/pkg/main main"

        plugin.build()

        self.run_output_mock.assert_called_once_with(
            ["go", "list", "-f", "{{.ImportPath}} {{.Name}}", "./dir/..."],
            cwd=plugin._gopath_src,
            env=mock.ANY,
        )

        self.run_mock.assert_called_once_with(
            ["go", "build", "dir/pkg/main"],
            cwd=os.path.join(plugin.installdir, "bin"),
            env=mock.ANY,
        )

        self.assert_go_paths(plugin)

    def test_build_go_packages(self):
        class Options:
            source = ""
            go_channel = "latest/stable"
            go_packages = ["github.com/gotools/vet"]
            go_importpath = ""
            go_buildtags = ""

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)

        plugin.pull()

        os.makedirs(plugin.builddir)

        self.run_mock.reset_mock()
        plugin.build()

        self.run_mock.assert_called_once_with(
            ["go", "build", plugin.options.go_packages[0]],
            cwd=os.path.join(plugin.installdir, "bin"),
            env=mock.ANY,
        )

        self.assert_go_paths(plugin)

    def test_clean_build(self):
        class Options:
            source = "dir"
            go_channel = "latest/stable"
            go_packages = []
            go_importpath = ""
            go_buildtags = ""

        plugin = go.GoPlugin("test-part", Options(), self.project)

        plugin.pull()

        os.makedirs(plugin._gopath_pkg)
        os.makedirs(plugin.builddir)

        plugin.build()

        self.assert_go_paths(plugin)

        plugin.clean_build()

        self.assertTrue(os.path.exists(plugin._gopath))
        self.assertTrue(os.path.exists(plugin._gopath_src))
        self.assertFalse(os.path.exists(plugin._gopath_bin))
        self.assertFalse(os.path.exists(plugin._gopath_pkg))

    def test_clean_pull(self):
        class Options:
            source = "dir"
            go_channel = "latest/stable"
            go_packages = []
            go_importpath = ""
            go_buildtags = ""

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)
        open(os.path.join(plugin.sourcedir, "main.go"), "w").close()

        plugin.pull()

        self.assertTrue(os.path.exists(plugin._gopath))

        plugin.clean_pull()

        self.assertFalse(os.path.exists(plugin._gopath))

    def test_build_with_local_sources_and_go_importpath(self):
        class Options:
            source = "dir"
            go_channel = "latest/stable"
            go_packages = []
            go_importpath = "github.com/snapcore/launcher"
            go_buildtags = ""

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)
        open(os.path.join(plugin.sourcedir, "main.go"), "w").close()

        plugin.pull()

        os.makedirs(plugin.builddir)
        self.run_output_mock.return_value = "github.com/snapcore/launcher main"

        plugin.build()

        self.run_output_mock.assert_called_once_with(
            [
                "go",
                "list",
                "-f",
                "{{.ImportPath}} {{.Name}}",
                "./github.com/snapcore/launcher/...",
            ],
            cwd=plugin._gopath_src,
            env=mock.ANY,
        )

        self.run_mock.assert_has_calls(
            [
                mock.call(
                    ["go", "get", "-t", "-d", "./github.com/snapcore/launcher/..."],
                    cwd=plugin._gopath_src,
                    env=mock.ANY,
                ),
                mock.call(
                    ["go", "build", "github.com/snapcore/launcher"],
                    cwd=os.path.join(plugin.installdir, "bin"),
                    env=mock.ANY,
                ),
            ]
        )

        self.assertTrue(
            os.path.exists(
                os.path.join(plugin._gopath_src, plugin.options.go_importpath)
            )
        )

        self.assert_go_paths(plugin)

    def test_build_environment(self):
        class Options:
            source = "dir"
            go_channel = "latest/stable"
            go_packages = []
            go_importpath = ""
            go_buildtags = ""

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)
        open(os.path.join(plugin.sourcedir, "main.go"), "w").close()
        os.makedirs(os.path.join(plugin.installdir, "lib"))
        os.makedirs(os.path.join(plugin.installdir, "usr", "lib"))
        os.makedirs(os.path.join(plugin.project.stage_dir, "lib"))
        os.makedirs(os.path.join(plugin.project.stage_dir, "usr", "lib"))
        plugin.pull()

        self.assertThat(self.run_mock.call_count, Equals(1))
        for call_args in self.run_mock.call_args_list:
            env = call_args[1]["env"]
            self.assertTrue("GOPATH" in env, "Expected environment to include GOPATH")
            self.assertThat(env["GOPATH"], Equals(plugin._gopath))

            self.assertTrue(
                "CGO_LDFLAGS" in env, "Expected environment to include CGO_LDFLAGS"
            )
            expected_flags = [
                "-L{}/lib".format(plugin.installdir),
                "-L{}/usr/lib".format(plugin.installdir),
                "-L{}/lib".format(plugin.project.stage_dir),
                "-L{}/usr/lib".format(plugin.project.stage_dir),
            ]
            for flag in expected_flags:
                self.assertTrue(
                    flag in env["CGO_LDFLAGS"],
                    "Expected $CGO_LDFLAGS to include {!r}, but it was "
                    '"{}"'.format(flag, env["CGO_LDFLAGS"]),
                )

    def test_build_with_buildtag(self):
        class Options:
            source = "dir"
            go_channel = "latest/stable"
            go_importpath = ""
            go_packages = []
            go_buildtags = ["testbuildtag1", "testbuildtag2"]

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.options.source)
        os.makedirs(plugin.sourcedir)

        plugin.pull()

        os.makedirs(plugin._gopath_bin)
        os.makedirs(plugin.builddir)

        self.run_mock.reset_mock()
        self.run_output_mock.return_value = "dir/pkg/main main"

        plugin.build()

        self.run_output_mock.assert_called_once_with(
            ["go", "list", "-f", "{{.ImportPath}} {{.Name}}", "./dir/..."],
            cwd=plugin._gopath_src,
            env=mock.ANY,
        )

        self.run_mock.assert_called_once_with(
            ["go", "build", "-tags=testbuildtag1,testbuildtag2", "dir/pkg/main"],
            cwd=os.path.join(plugin.installdir, "bin"),
            env=mock.ANY,
        )

    def test_build_go_mod(self):
        class Options:
            source = "dir"
            go_channel = "latest/stable"
            go_packages = []
            go_importpath = ""
            go_buildtags = ""

        self.run_output_mock.return_value = "go version go13 linux/amd64"

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.builddir)
        open(os.path.join(plugin.builddir, "go.mod"), "w").close()

        plugin.build()

        self.run_output_mock.assert_called_once_with(
            ["go", "version"], cwd=mock.ANY, env=mock.ANY
        )
        self.run_mock.assert_called_once_with(
            ["go", "build", "-o", plugin._install_bin_dir],
            cwd=plugin.builddir,
            env=mock.ANY,
        )

    @mock.patch("snapcraft.internal.elf.ElfFile")
    def test_build_classic_dynamic_relink(self, mock_elffile):
        class Options:
            source = ""
            go_channel = "latest/stable"
            go_packages = ["github.com/gotools/vet"]
            go_importpath = ""
            go_buildtags = ""

        mock_elffile.return_value = MockElfFile(path="foo")
        self.project.info.confinement = "classic"
        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)

        plugin.pull()

        os.makedirs(plugin.builddir)

        self.run_mock.reset_mock()
        plugin.build()

        self.assertThat(self.run_mock.call_count, Equals(2))
        self.run_mock.assert_has_calls(
            [
                mock.call(
                    ["go", "build", plugin.options.go_packages[0]],
                    cwd=os.path.join(plugin.installdir, "bin"),
                    env=mock.ANY,
                ),
                mock.call(
                    [
                        "go",
                        "build",
                        "-ldflags",
                        "-linkmode=external",
                        plugin.options.go_packages[0],
                    ],
                    cwd=os.path.join(plugin.installdir, "bin"),
                    env=mock.ANY,
                ),
            ]
        )

        self.assert_go_paths(plugin)

    @mock.patch("snapcraft.internal.elf.ElfFile")
    def test_build_go_mod_classic_dynamic_relink(self, mock_elffile):
        class Options:
            source = ""
            go_channel = "latest/stable"
            go_packages = ["github.com/gotools/vet"]
            go_importpath = ""
            go_buildtags = ""

        self.run_output_mock.return_value = "go version go13 linux/amd64"

        mock_elffile.return_value = MockElfFile(path="foo")
        self.project.info.confinement = "classic"
        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.builddir)
        open(os.path.join(plugin.builddir, "go.mod"), "w").close()

        plugin.build()

        self.run_output_mock.assert_called_once_with(
            ["go", "version"], cwd=mock.ANY, env=mock.ANY
        )
        self.assertThat(self.run_mock.call_count, Equals(2))
        self.run_mock.assert_has_calls(
            [
                mock.call(
                    ["go", "build", "-o", plugin._install_bin_dir],
                    cwd=plugin.builddir,
                    env=mock.ANY,
                ),
                mock.call(
                    [
                        "go",
                        "build",
                        "-ldflags",
                        "-linkmode=external",
                        "-o",
                        plugin._install_bin_dir,
                    ],
                    cwd=plugin.builddir,
                    env=mock.ANY,
                ),
            ]
        )


class GoPluginSchemaValidationTest(unit.TestCase):
    def test_sources_validation_neither(self):
        schema = self._get_schema()
        properties = {}
        self.assertRaises(
            jsonschema.ValidationError, jsonschema.validate, properties, schema
        )

    def test_sources_validation_source(self):
        schema = self._get_schema()
        properties = {"source": ""}
        jsonschema.validate(properties, schema)

    def test_sources_validation_packages(self):
        schema = self._get_schema()
        properties = {"go-packages": []}
        jsonschema.validate(properties, schema)

    def test_sources_validation_both(self):
        schema = self._get_schema()
        properties = {"source": "foo", "go-packages": []}
        jsonschema.validate(properties, schema)

    def _get_schema(self):
        schema = go.GoPlugin.schema()
        # source definition comes from the main schema
        schema["properties"]["source"] = {"type": "string"}
        return schema


class GoPluginToolSetupTest(GoPluginBaseTest):
    def setUp(self):
        super().setUp()

        class Options:
            source = "dir"
            go_channel = "latest/stable"

        self.options = Options()

    def test_snap(self):
        plugin = go.GoPlugin("test-part", self.options, self.project)

        self.assertThat(plugin.build_packages, Not(Contains("golang-go")))
        self.assertThat(plugin.build_snaps, Contains("go/latest/stable"))

    def test_build_packages(self):
        self.options.go_channel = ""

        plugin = go.GoPlugin("test-part", self.options, self.project)

        self.assertThat(plugin.build_packages, Contains("golang-go"))
        self.assertThat(plugin.build_snaps, Not(Contains("go/latest/stable")))


class GoPluginUnsupportedBase(unit.TestCase):
    def setUp(self):
        super().setUp()

        snapcraft_yaml_path = self.make_snapcraft_yaml(
            dedent(
                """\
            name: go-snap
            base: unsupported-base
        """
            )
        )

        self.project = Project(snapcraft_yaml_file_path=snapcraft_yaml_path)

        class Options:
            source = "dir"
            go_channel = "latest/stable"

        self.options = Options()

    def test_unsupported_base_using_snap(self):
        plugin = go.GoPlugin("test-part", self.options, self.project)

        self.assertThat(plugin.build_packages, Not(Contains("golang-go")))
        self.assertThat(plugin.build_snaps, Contains("go/latest/stable"))

    def test_unsupported_base_using_without_snap_raises(self):
        self.options.go_channel = ""

        self.assertRaises(
            errors.PluginBaseError, go.GoPlugin, "test-part", self.options, self.project
        )


class GoPluginCrossCompileTest(GoPluginBaseTest):

    scenarios = [
        ("armv7l", dict(deb_arch="armhf", go_arch="arm")),
        ("aarch64", dict(deb_arch="arm64", go_arch="arm64")),
        ("i386", dict(deb_arch="i386", go_arch="386")),
        ("x86_64", dict(deb_arch="amd64", go_arch="amd64")),
        ("ppc64le", dict(deb_arch="ppc64el", go_arch="ppc64le")),
    ]

    def setUp(self):
        super().setUp()

        patcher = mock.patch("snapcraft.ProjectOptions.is_cross_compiling")
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_cross_compile(self):
        class Options:
            source = ""
            go_packages = ["github.com/gotools/vet"]
            go_importpath = ""
            go_buildtags = ""
            go_channel = ""

        plugin = go.GoPlugin("test-part", Options(), self.project)

        os.makedirs(plugin.sourcedir)

        plugin.pull()

        self.assertThat(self.run_mock.call_count, Equals(1))
        for call_args in self.run_mock.call_args_list:
            env = call_args[1]["env"]
            self.assertIn("CC", env)
            self.assertThat(
                env["CC"], Equals("{}-gcc".format(self.project.arch_triplet))
            )
            self.assertIn("CXX", env)
            self.assertThat(
                env["CXX"], Equals("{}-g++".format(self.project.arch_triplet))
            )
            self.assertIn("CGO_ENABLED", env)
            self.assertThat(env["CGO_ENABLED"], Equals("1"))
            self.assertIn("GOARCH", env)
            self.assertThat(env["GOARCH"], Equals(self.go_arch))
            if self.deb_arch == "armhf":
                self.assertIn("GOARM", env)
                self.assertThat(env["GOARM"], Equals("7"))


class CGoLdFlagsTest(unit.TestCase):
    scenarios = (
        (
            "none",
            dict(cgo_ldflags_env="", library_paths=[], ldflags_env="", expected=""),
        ),
        (
            "CGO_LDFLAGS",
            dict(
                cgo_ldflags_env="-lbar",
                library_paths=[],
                ldflags_env="",
                expected="-lbar",
            ),
        ),
        (
            "Library Paths",
            dict(
                cgo_ldflags_env="",
                library_paths=["part/part1/usr/lib", "stage/lib"],
                ldflags_env="",
                expected="-Lpart/part1/usr/lib -Lstage/lib",
            ),
        ),
        (
            "LDFLAGS",
            dict(
                cgo_ldflags_env="",
                library_paths=[],
                ldflags_env="-lfoo",
                expected="-lfoo",
            ),
        ),
        (
            "all",
            dict(
                cgo_ldflags_env="-lbar",
                library_paths=["part/part1/usr/lib", "stage/lib"],
                ldflags_env="-lfoo",
                expected="-lbar -Lpart/part1/usr/lib -Lstage/lib -lfoo",
            ),
        ),
    )

    def setUp(self):
        super().setUp()

        self.useFixture(
            fixtures.EnvironmentVariable("CGO_LDFLAGS", self.cgo_ldflags_env)
        )
        self.useFixture(fixtures.EnvironmentVariable("LDFLAGS", self.ldflags_env))

    def test_generated_cgo_ldflags(self):
        self.assertThat(go._get_cgo_ldflags(self.library_paths), Equals(self.expected))
