#ifdef _WIN32
// Include <winsock2.h> before <windows.h> (needed for websocketpp)
#include <winsock2.h>
#endif

#include <chrono>
#include <fstream>
#include <iostream>
#include <memory>
#include <thread>

#include "spdlog/sinks/rotating_file_sink.h"
#include "spdlog/spdlog.h"

#include "plugdllx.h"
#include "plugx.h"

#include "./rpc.hpp"
#include "./server.hpp"
#include "./utils.hpp"

// Global WebSockets server instance
WSServer *wsserver;

/**
 * Replaces the default logger and log to a file
 */
void replace_default_logger() {
  auto log_file = home_dir() + "/" + ".tvpaint-ws-server.log";
  auto max_size = 1048576 * 1; // 1 Mb
  auto max_files = 2;
  auto logger = spdlog::rotating_logger_mt("tvpaint-ws-server", log_file,
                                           max_size, max_files);

  spdlog::flush_on(spdlog::level::info);
  spdlog::set_default_logger(logger);
}

/**
 * Called first during the TVPaint plugin initialization
 */
int FAR PASCAL PI_Open(PIFilter *iFilter) {
  replace_default_logger();

  // Set plugin name
  strcpy(iFilter->PIName, "George WebSocket server");

  // Set plugin version.revision
  iFilter->PIVersion = 1;
  iFilter->PIRevision = 0;

  // Get the listen port
  const char *port_env = std::getenv("TVP_WS_PORT");
  int port = port_env ? atoi(port_env) : 3000;

  // Create a new server instance
  wsserver = new WSServer(iFilter);

  // Start the WebSocket server
  try {
    wsserver->run(port);
  } catch (const std::exception &e) {
    spdlog::error(e.what());
  }

  // Create an empty requester to force enabling ticks
  DWORD req = TVOpenFilterReqEx(iFilter, 80, 80, NULL, NULL,
                                PIRF_STANDARD_REQ | PIRF_COLLAPSABLE_REQ,
                                FILTERREQ_NO_TBAR);
  TVGrabTicks(iFilter, req, PITICKS_FLAG_ON);

  return 1;
}

/**
 * Called on plugin shutdown, do the necessary cleanup here
 */
void FAR PASCAL PI_Close(PIFilter *iFilter) {
  // Shutting down the server
  if (wsserver) {
    wsserver->stop();
    delete wsserver;
  }
}

/**
 * Handle George commands in the main thread
 */
void processGeorgeCommands(PIFilter *iFilter) {
  if (wsserver->george_commands.empty()) {
    return;
  }

  auto payload = wsserver->george_commands.front();

  // Execute the George command and store the result
  char result[2048];
  int executionStatus = TVSendCmd(iFilter, payload.command.c_str(), result);

  if (executionStatus == NULL) { // Handle an error
    auto error = json_rpc_error(payload.id, JSON_RPC_SERVER_ERROR,
                                "Error when executing George command");
    wsserver->wsserver.send(payload.hdl, error, payload.opcode);
  } else { // Send the result
    auto json_response = json_rpc_result(payload.id, result);
    wsserver->wsserver.send(payload.hdl, json_response, payload.opcode);
  }

  wsserver->george_commands.pop();
}

/**
 * We have something to process
 */
int FAR PASCAL PI_Msg(PIFilter *iFilter, INTPTR iEvent, INTPTR iReq,
                      INTPTR *iArgs) {
  switch (iEvent) {
  case PICBREQ_TICKS: // Called every 20 milliseconds at each timer ticks
    processGeorgeCommands(iFilter);
  }

  return 1;
}

// Below this line, not needed for this plugin
// ------------------------------------------------------------------

void FAR PASCAL PI_About(PIFilter *iFilter) {}

int FAR PASCAL PI_Parameters(PIFilter *iFilter, char *iArg) { return 1; }

int FAR PASCAL PI_Start(PIFilter *iFilter, double pos, double size) {
  return 1;
}

int FAR PASCAL PI_Work(PIFilter *iFilter) { return 1; }

void FAR PASCAL PI_Finish(PIFilter *iFilter) {}
