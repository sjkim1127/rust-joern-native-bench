# Rust-Joern native benchmark pilot

Run Rust-Joern and a compiler-built TinyXML2 smoke program on native Linux x86-64 and Windows x86-64. The two GitHub Actions jobs each exercise C++14 and C++23. Windows uses MSVC and the runner's Windows SDK. Linux uses the runner's GCC.

The [corpus repository](https://github.com/sjkim1127/joern-c-cpp-corpus) maintains input selection and evaluation methods. This repository pins the TinyXML2 source revision already selected in that corpus and the Rust-Joern baseline used for the pilot. Upstream project files are fetched at run time under their original licenses.

The workflow builds and runs the TinyXML2-linked executable in both language modes. The smoke source checks the C++14 language flag and exercises C++23's `if consteval`. Per cell, it preprocesses `tinyxml2.cpp` and the smoke source, then runs the native Rust-Joern CLI on both.

Each Actions artifact contains compiler logs, source and prepared input hashes, exact revisions, native execution status and diagnostics. The runner records strict acceptance separately from permissive graph counts. These counts measure records returned by the parser. CFG correctness, original Joern parity, and timing benchmarks are outside the pilot.

Start the **Native C++ smoke** workflow from the Actions tab for a repeat run. The two runner labels can change image contents over time. The report records their image versions and the native toolchain evidence.
