import argparse
import shutil
import subprocess
import tarfile
from pathlib import Path


def run(*command: str) -> None:
  subprocess.run(command, check=True)


def main() -> None:
  parser = argparse.ArgumentParser()
  parser.add_argument("target")
  args = parser.parse_args()

  root = Path(__file__).resolve().parents[1]
  source = root / "zenoh-c"
  build = root / "build" / "zenoh-c" / args.target
  install = build / "install"
  bundle = root / "native" / args.target
  archive = root / "build" / f"zenoh-mbt-native-{args.target}.tar.gz"

  if not (source / "CMakeLists.txt").is_file():
    raise SystemExit("zenoh-c submodule is not initialized")

  if build.exists():
    shutil.rmtree(build)
  if bundle.exists():
    shutil.rmtree(bundle)
  build.mkdir(parents=True)
  bundle.mkdir(parents=True)

  run(
      "cmake",
      "-S",
      str(source),
      "-B",
      str(build),
      "-DCMAKE_BUILD_TYPE=Release",
      "-DBUILD_SHARED_LIBS=OFF",
      f"-DCMAKE_INSTALL_PREFIX={install}",
  )
  run("cmake", "--build", str(build), "--target", "install", "--config", "Release")

  shutil.copytree(install / "include", bundle / "include")
  library_destination = bundle / "lib"
  library_destination.mkdir()
  install_library_directory = install / "lib"
  if not install_library_directory.is_dir():
    install_library_directory = install / "lib64"
  if not install_library_directory.is_dir():
    raise SystemExit("zenoh-c install did not produce a library directory")
  libraries = [
      path
      for path in install_library_directory.iterdir()
      if path.name in {"libzenohc.a", "zenohc.lib", "libzenohc.lib"}
  ]
  if len(libraries) != 1:
    raise SystemExit(f"expected one static zenoh-c library, found {libraries}")
  shutil.copy2(libraries[0], library_destination / libraries[0].name)

  archive.parent.mkdir(parents=True, exist_ok=True)
  with tarfile.open(archive, "w:gz") as output:
    output.add(bundle / "include", arcname="include")
    output.add(bundle / "lib", arcname="lib")


if __name__ == "__main__":
  main()
