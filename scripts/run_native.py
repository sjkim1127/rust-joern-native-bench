"""Compile and execute one pinned native source build, then exercise Rust-Joern."""

import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess


def execute(argv, cwd):
    print(subprocess.list2cmdline([str(arg) for arg in argv]), flush=True)
    return subprocess.run(argv, cwd=cwd, capture_output=True, timeout=120)


def checked(argv, cwd, log, *, log_stdout=True):
    run = execute(argv, cwd)
    log.write_bytes((run.stdout if log_stdout else b"") + run.stderr)
    if run.returncode:
        raise SystemExit(f"{argv[0]} exited with {run.returncode}. See {log}.")
    return run.stdout


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def revision(repo):
    return subprocess.check_output(["git", "-C", repo, "rev-parse", "HEAD"], text=True).strip()


def inspect_cfg(joern, source, out):
    argv = [joern, "analyze", source, "--language", "cpp", "--preprocessed"]
    regular = checked(argv, out, out / f"{source.stem}-parser.log", log_stdout=False)
    result = json.loads(regular)
    strict = execute([*argv, "--strict"], out)
    (out / f"{source.stem}-strict.log").write_bytes(strict.stderr)
    if strict.returncode not in (0, 1):
        raise SystemExit(f"Unexpected strict exit code {strict.returncode} for {source.name}")
    diagnostics = result["diagnostics"]
    functions = result["functions"]
    return {
        "prepared_sha256": sha256(source),
        "function_records": len(functions),
        "nonempty_cfg_records": sum(bool(row["cfg"]["nodes"]) for row in functions),
        "error_diagnostics": sum(d["severity"] == "error" for d in diagnostics),
        "strict": "accepted" if strict.returncode == 0 else "rejected",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--standard", choices=(14, 23), type=int, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    host = platform.system()
    machine = platform.machine().lower()
    if host not in {"Linux", "Windows"} or machine not in {"amd64", "x86_64"}:
        raise SystemExit(f"Expected a Linux or Windows x86-64 runner, got {host} {machine}")
    windows = host == "Windows"
    source = root / "tinyxml2" / "tinyxml2.cpp"
    probe = root / "fixtures" / "probe.cpp"
    backend = root / "backend"
    suffix = ".exe" if windows else ""
    joern = backend / "target" / "release" / f"rust-joern{suffix}"
    compiler = shutil.which("cl" if windows else "g++")
    if compiler is None:
        raise SystemExit("Native C++ compiler is unavailable")

    out = root / "results" / f"{host.lower()}-x64-cpp{args.standard}"
    out.mkdir(parents=True, exist_ok=True)
    executable = out / f"native-smoke{suffix}"
    if windows:
        standard = "/std:c++23preview" if args.standard == 23 else "/std:c++14"
        flags = ["/nologo", "/EHsc", "/Zc:__cplusplus", "/utf-8", "/Od", "/Z7",
                 standard, f"/DJOERN_STANDARD={args.standard}", f"/I{source.parent}"]
        build = [compiler, *flags, "/Bv", source, probe, f"/Fe{executable}"]
    else:
        standard = f"-std=c++{args.standard}"
        flags = [standard, "-O0", "-g", f"-DJOERN_STANDARD={args.standard}", "-I", source.parent]
        build = [compiler, *flags, source, probe, "-o", executable]
        checked([compiler, "--version"], out, out / "compiler-version.log")
        checked([compiler, "-dumpmachine"], out, out / "compiler-target.log")

    checked(build, out, out / "compile.log")
    checked([executable], out, out / "run.log")

    cases = {}
    for unit in (source, probe):
        output = out / f"{unit.stem}.ii"
        if windows:
            preprocess = [compiler, *flags, "/P", f"/Fi{output}", unit]
            checked(preprocess, out, out / f"{unit.stem}-preprocess.log")
        else:
            preprocess = [compiler, *flags, "-E", unit]
            output.write_bytes(checked(preprocess, out, out / f"{unit.stem}-preprocess.log", log_stdout=False))
        cases[unit.name] = {
            "source_sha256": sha256(unit),
            "preprocess_argv": list(map(str, preprocess)),
            **inspect_cfg(joern, output, out),
        }

    result = {
        "host": host,
        "arch": machine,
        "runner_image": os.getenv("ImageVersion"),
        "standard_flag": standard,
        "compiler": compiler,
        "msvc_version": os.getenv("VCToolsVersion") if windows else None,
        "windows_sdk": os.getenv("WindowsSDKVersion") if windows else None,
        "rust_toolchain": os.getenv("RUSTUP_TOOLCHAIN"),
        "source_commit": revision(source.parent),
        "rust_joern_commit": revision(backend),
        "rust_joern_sha256": sha256(joern),
        "build_argv": list(map(str, build)),
        "native_exit": 0,
        "executable_sha256": sha256(executable),
        "cases": cases,
    }
    report = json.dumps(result, indent=2)
    (out / "report.json").write_text(report + "\n", encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
