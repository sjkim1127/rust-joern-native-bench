#include "tinyxml2.h"

#if defined(_MSC_VER)
#if !defined(_WIN64) || !defined(_M_X64)
#error Expected a Windows x86-64 target
#endif
#else
#if !defined(__linux__) || !defined(__x86_64__)
#error Expected a Linux x86-64 target
#endif
#endif

#if JOERN_STANDARD == 23
constexpr int language_mode() {
    if consteval {
        return 23;
    } else {
        return 0;
    }
}
static_assert(language_mode() == 23, "C++23 immediate branch must be accepted");
#else
static_assert(__cplusplus == 201402L, "expected C++14 mode");
constexpr int language_mode() {
    int mode = 14;
    return mode;
}
static_assert(language_mode() == 14, "C++14 constexpr local must be accepted");
#endif

int main() {
    tinyxml2::XMLDocument doc;
    return doc.Parse("<native/>") == tinyxml2::XML_SUCCESS && doc.RootElement() ? 0 : 1;
}
