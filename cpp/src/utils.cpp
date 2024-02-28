#pragma once

#include "./utils.hpp"

/**
 * Cross platform way to get the home directory
 */
std::string home_dir() {
#if _WIN32 || _WIN64
  return std::string(std::getenv("HOMEDRIVE")) + "/" +
         std::string(std::getenv("HOMEPATH"));
#elif __linux__ || __APPLE__
  return std::string(std::getenv("HOME"));
#else
  throw "OS not supported"
#endif
}

/**
 * Converts a wide string into utf-8
 * From: https://stackoverflow.com/a/21575607
 * TODO: Windows only and doesn't handle emojis
 */
std::string to_utf8(std::string codepage_str) {
#if _WIN32 || _WIN64
  int size = MultiByteToWideChar(CP_ACP, MB_COMPOSITE, codepage_str.c_str(),
                                 codepage_str.length(), nullptr, 0);
  std::wstring utf16_str(size, '\0');
  MultiByteToWideChar(CP_ACP, MB_COMPOSITE, codepage_str.c_str(),
                      codepage_str.length(), &utf16_str[0], size);

  int utf8_size =
      WideCharToMultiByte(CP_UTF8, 0, utf16_str.c_str(), utf16_str.length(),
                          nullptr, 0, nullptr, nullptr);
  std::string utf8_str(utf8_size, '\0');
  WideCharToMultiByte(CP_UTF8, 0, utf16_str.c_str(), utf16_str.length(),
                      &utf8_str[0], utf8_size, nullptr, nullptr);
  return utf8_str;
#else
  return codepage_str;
#endif
}