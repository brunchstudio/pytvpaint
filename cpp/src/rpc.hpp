#pragma once

#include <string>

#include <nlohmann/json.hpp>

// A String specifying the version of the JSON-RPC protocol. MUST be exactly
// "2.0".
#define JSON_RPC_VERSION "2.0"

/**
 * Invalid JSON was received by the server.
 * An error occurred on the server while parsing the JSON text.
 */
#define JSON_RPC_PARSE_ERROR -32700

// The JSON sent is not a valid Request object.
#define JSON_RPC_INVALID_REQUEST -32600

// The method does not exist / is not available.
#define JSON_RPC_METHOD_NOT_FOUND -32601

// Invalid method parameter(s).
#define JSON_RPC_INVALID_PARAMS -32602

// Internal JSON-RPC error.
#define JSON_RPC_SERVER_ERROR -32000

std::string json_rpc_result(int id, std::string result);
std::string json_rpc_error(int id, int code, std::string message);