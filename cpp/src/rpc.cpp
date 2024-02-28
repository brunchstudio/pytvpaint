#include "./rpc.hpp"
#include "./utils.hpp"

using json = nlohmann::json;

/**
 * Constructs a JSON RPC result object
 * See: https://www.jsonrpc.org/specification#response_object
 */
std::string json_rpc_result(int id, std::string result) {
  json j;
  j["jsonrpc"] = JSON_RPC_VERSION;
  j["result"] = to_utf8(result);
  j["id"] = id;
  return j.dump();
}

/**
 * Constructs a JSON RPC error object
 * See: https://www.jsonrpc.org/specification#error_object
 */
std::string json_rpc_error(int id, int code, std::string message) {
  json j;
  j["jsonrpc"] = JSON_RPC_VERSION;
  j["error"]["code"] = code;
  j["error"]["message"] = message;

  if (id >= 0) {
    j["id"] = id;
  } else {
    j["id"] = nullptr; // Parse error
  }

  return j.dump();
}