#!/usr/bin/env python3
"""Stage the libsyncthing fork plus XunCloud client support, without editing submodules.

python3 scripts/prepare-xuncloud-core.py --cloud-source ../xun-cloud --output build/xuncloud-core
Then configure CMake with -DSYNCTHING_PATH=<absolute output path>.
Fails on unknown integration anchors instead of producing a partial/unsafe merge.
"""
import argparse
from pathlib import Path
import shutil
import subprocess


def once(text, old, new, name):
    if text.count(old) != 1:
        raise ValueError("Unsupported source layout: " + name)
    return text.replace(old, new, 1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cloud-source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    cloud = args.cloud_source.resolve()
    fork = Path(__file__).resolve().parents[1] / "syncthing/go/src/github.com/syncthing/syncthing"
    out = args.output.resolve()
    if out.exists():
        parser.error("Output must not exist; use a new staging directory")
    if not (cloud / "lib/cloudsync/client.go").is_file() or not (fork / "c-bindings/c_bindings.go").is_file():
        parser.error("Account-aware xun-cloud source and populated libsyncthing submodule required")
    for source in (cloud, fork):
        if out == source or source in out.parents:
            parser.error("Output must be outside both source trees")
    patches = {}
    api = "lib/api/api.go"
    anchor = '\t// The POST handlers\n'
    patches[api] = once((fork / api).read_text(encoding="utf-8"), anchor,
                        anchor + '\trestMux.HandlerFunc(http.MethodPost, "/rest/cloud/join", s.postCloudJoin)\n', api)
    index = "gui/default/index.html"
    text = (fork / index).read_text(encoding="utf-8")
    anchor = '              <li><a href="" ng-click="showSettings()">'
    addition = '              <li ng-if="cloud.local"><a href="" ng-click="cloud.open = true"><span class="fa fa-fw fa-cloud"></span>&nbsp;<span translate>Connect cloud account</span></a></li>\n'
    text = once(text, anchor, addition + anchor, index + " menu")
    anchor = '    <div class="container content">\n\n      <!-- Panel: Open, no auth -->'
    replacement = '    <div class="container content">\n      <ng-include src="\'syncthing/core/cloudJoin.html\'"></ng-include>\n\n      <!-- Panel: Open, no auth -->'
    patches[index] = once(text, anchor, replacement, index + " panel")
    controller = "gui/default/syncthing/core/syncthingController.js"
    text = (cloud / controller).read_text(encoding="utf-8")
    start = text.index('        var cloudHost = ')
    end = text.index('        $scope.login = {', start)
    block = text[start:end]
    patches[controller] = once((fork / controller).read_text(encoding="utf-8"), '        $scope.login = {', block + '        $scope.login = {', controller)
    # These are new files or the localized strings for the new panel only.
    import json
    for lang in ("en", "zh-CN"):
        name = "gui/default/assets/lang/lang-" + lang + ".json"
        source = json.loads((cloud / name).read_text(encoding="utf-8"))
        target = json.loads((fork / name).read_text(encoding="utf-8"))
        for key in ("Connect cloud account", "Enrollment server (IP or HTTPS host:port)",
                    "Use the sync account issued by your server administrator, not the Web GUI password.",
                    "Account connected. Local folder:"):
            target[key] = source[key]
        patches[name] = json.dumps(target, ensure_ascii=False, indent=4) + "\n"
    for name in ("lib/cloudsync", "lib/api/cloud.go", "lib/api/cloud_test.go", "gui/default/syncthing/core/cloudJoin.html"):
        if (fork / name).exists():
            parser.error("Already integrated: " + name)
    # Copy only tracked source files. This includes the public update signing
    # key and committed test certificates, but excludes local runtime secrets.
    tracked = subprocess.check_output(["git", "-C", str(fork), "ls-files", "-z"]).decode().split("\0")
    sources = []
    for name in filter(None, tracked):
        source = fork / name
        if source.is_symlink():
            raise ValueError("Refusing source symlink: " + name)
        if source.is_file():
            sources.append((name, source))
    out.mkdir(parents=True)
    for name, source in sources:
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    shutil.copytree(cloud / "lib/cloudsync", out / "lib/cloudsync")
    for name in ("lib/api/cloud.go", "lib/api/cloud_test.go", "gui/default/syncthing/core/cloudJoin.html"):
        shutil.copy2(cloud / name, out / name)
    for name, text in patches.items():
        (out / name).write_text(text, encoding="utf-8")
    # Account joining is client-side; retain all fork-specific C bindings and
    # CLI/log callbacks. The server is built from xun-cloud itself.
    print("Prepared account-aware libsyncthing source:", out)
    print("Configure with -DSYNCTHING_PATH=" + str(out))


if __name__ == "__main__":
    main()
