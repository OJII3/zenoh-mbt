import json
import os
import platform
import re
import subprocess
import sys
import tarfile
import urllib.error
import urllib.request
from pathlib import Path


def module_name(module_root: Path) -> str:
  manifest = (module_root / "moon.mod").read_text()
  match = re.search(r'^name\s*=\s*"([^"]+)"', manifest, re.MULTILINE)
  if match is None:
    raise RuntimeError("moon.mod does not define a module name")
  return match.group(1)


def target_name() -> str:
  systems = {
    "Darwin": "macos",
    "Linux": "linux",
    "Windows": "windows",
  }
  architectures = {
    "aarch64": "aarch64",
    "arm64": "aarch64",
    "amd64": "x86_64",
    "x86_64": "x86_64",
  }
  system = systems.get(platform.system())
  architecture = architectures.get(platform.machine().lower())
  if system is None or architecture is None:
    raise RuntimeError(
        f"unsupported native target: {platform.system()} {platform.machine()}"
    )
  return f"{system}-{architecture}"


def has_bundle(bundle_root: Path) -> bool:
  include = bundle_root / "include" / "zenoh.h"
  library = bundle_root / "lib"
  libraries = [
    library / "libzenohc.a",
    library / "libzenohc.dylib",
    library / "libzenohc.so",
    library / "zenohc.lib",
    library / "libzenohc.lib",
  ]
  return include.is_file() and any(path.is_file() for path in libraries)


def pkg_config() -> tuple[str, str] | None:
  try:
    cflags = subprocess.run(
        ["pkg-config", "--cflags", "zenohc"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    link_flags = subprocess.run(
        ["pkg-config", "--libs", "zenohc"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
  except (FileNotFoundError, subprocess.CalledProcessError):
    return None
  return cflags, link_flags


def static_link_config(target: str, library_dir: Path) -> dict[str, object]:
  config: dict[str, object] = {
      "package": "",
      "link_search_paths": [str(library_dir)],
      "link_libs": ["zenohc"],
  }
  if target == "linux-x86_64":
    config["link_libs"] = ["zenohc", "rt", "pthread", "m", "dl"]
  elif target.startswith("macos-"):
    config["link_flags"] = "-framework Foundation -framework Security"
  elif target == "windows-x86_64":
    config["link_libs"] = [
        "zenohc",
        "ws2_32",
        "crypt32",
        "secur32",
        "bcrypt",
        "ncrypt",
        "userenv",
        "ntdll",
        "iphlpapi",
        "runtimeobject",
    ]
  return config


def read_version(module_root: Path) -> str:
  manifest = (module_root / "moon.mod").read_text()
  match = re.search(r'^version\s*=\s*"([^"]+)"', manifest, re.MULTILINE)
  if match is None:
    raise RuntimeError("moon.mod does not define a version")
  return match.group(1)


def download_bundle(module_root: Path, output_root: Path, target: str) -> Path:
  version = read_version(module_root)
  url = os.environ.get(
      "ZENOHC_BUNDLE_URL",
      f"https://github.com/OJII3/zenoh-mbt/releases/download/"
      f"v{version}/zenoh-mbt-native-{target}.tar.gz",
  )
  archive = output_root / f"zenoh-mbt-native-{target}.tar.gz"
  bundle = output_root / "bundle"
  output_root.mkdir(parents=True, exist_ok=True)
  try:
    urllib.request.urlretrieve(url, archive)
    with tarfile.open(archive, "r:gz") as source:
      source.extractall(bundle)
  except (OSError, urllib.error.URLError, tarfile.TarError) as error:
    raise RuntimeError(
        f"failed to download the bundled zenoh-c artifact from {url}; "
        "install zenoh-c or set ZENOHC_BUNDLE_URL"
    ) from error
  return bundle


def main() -> None:
  environment = json.load(sys.stdin)
  module_root = Path(environment["paths"]["module_root"])
  output_root = Path(environment["paths"]["out_dir"])
  target = target_name()
  bundle = module_root / "native" / target

  if not has_bundle(bundle):
    configured = pkg_config()
    if configured is not None:
      cflags, link_flags = configured
      print(
          json.dumps(
              {
                  "vars": {"ZENOHC_CFLAGS": cflags},
                  "link_configs": [
                      {
                          "package": module_name(module_root),
                          "link_flags": link_flags,
                      }
                  ],
              }
          )
      )
      return
    bundle = download_bundle(module_root, output_root, target)

  if not has_bundle(bundle):
    raise RuntimeError(f"zenoh-c artifact is incomplete for target {target}")

  include_dir = bundle / "include"
  library_dir = bundle / "lib"
  link_config = static_link_config(target, library_dir)
  link_config["package"] = module_name(module_root)
  print(
      json.dumps(
          {
              "vars": {"ZENOHC_CFLAGS": f"-I{include_dir}"},
              "link_configs": [link_config],
          }
      )
  )


if __name__ == "__main__":
  try:
    main()
  except RuntimeError as error:
    print(f"zenoh-mbt prebuild: {error}", file=sys.stderr)
    sys.exit(1)
