#include <map>
#include <string>
#include <thread>

#include "spdlog/spdlog.h"
#include <nlohmann/json.hpp>
#include <websocketpp/config/asio_no_tls.hpp>
#include <websocketpp/server.hpp>

#include "plugdllx.h"

#include "./rpc.hpp"
#include "./server.hpp"

using json = nlohmann::json;
using namespace std::placeholders;
using websocketpp::connection_hdl;

WSServer::WSServer(PIFilter *iFilter) {
  this->iFilter = iFilter;

  // Disable websocket logging
  wsserver.clear_access_channels(websocketpp::log::alevel::all);
  wsserver.clear_error_channels(websocketpp::log::elevel::all);

  // Initialize the Asio transport policy
  wsserver.init_asio();

  // Set the message handlers
  wsserver.set_message_handler(
      std::bind(&WSServer::on_message, this, &wsserver, _1, _2));
}

void WSServer::on_message(server *s, connection_hdl hdl,
                          server::message_ptr msg) {
  try {
    json payload = json::parse(msg->get_payload());

    // Extract JSON RPC data from the payload
    payload["jsonrpc"].get<std::string>();
    auto id = payload["id"].get<int>();
    auto method = payload["method"].get<std::string>();
    std::vector<std::string> params = payload["params"];

    if (method == "execute_george") {
      if (params.size() != 1) {
        auto error = json_rpc_error(
            id, JSON_RPC_INVALID_PARAMS,
            "Give a single parameter which is the George command");
        s->send(hdl, error, msg->get_opcode());
        return;
      }

      // Add the necessary data for future processing in the main thread
      george_commands.push({id, params[0], hdl, msg->get_opcode()});
    } else if (method == "ping") {
      s->send(hdl, json_rpc_result(id, "pong"), msg->get_opcode());
    } else {
      auto error =
          json_rpc_error(id, JSON_RPC_METHOD_NOT_FOUND, "Method not found");
      s->send(hdl, error, msg->get_opcode());
    }
  } catch (const json::parse_error &e) {
    auto error = json_rpc_error(-1, JSON_RPC_PARSE_ERROR, e.what());
    s->send(hdl, error, msg->get_opcode());
  } catch (const json::exception &e) {
    auto error = json_rpc_error(-1, JSON_RPC_INVALID_REQUEST, e.what());
    s->send(hdl, error, msg->get_opcode());
  } catch (const std::exception &e) {
    auto error = json_rpc_error(-1, JSON_RPC_SERVER_ERROR, e.what());
    s->send(hdl, error, msg->get_opcode());
  }
}

void WSServer::run(uint16_t port) {
  try {
    wsserver.listen(port);
  } catch (websocketpp::exception const &e) {
    spdlog::error(e.what());
  }

  spdlog::info("Server listening...");

  websocketpp::lib::error_code ec;
  wsserver.start_accept(ec);

  if (ec) {
    spdlog::error(ec.message());
  }

  spdlog::info("Start accepting connections...");

  // Run the server in a new thread
  run_thread.reset(new websocketpp::lib::thread(&server::run, &wsserver));
}

void WSServer::stop() {
  spdlog::info("Stopping the server...");
  wsserver.stop();
  run_thread->join();
  spdlog::info("Server thread finished!");
}