package main

// Licensing: (Apache-2.0 AND BSD-3-Clause AND BSD-2-Clause)

/*
 * NOTICE:
 * =======
 *  Copyright (c) 2017 Wind River Systems, Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at:
 *       http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software  distributed
 * under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES
 * OR CONDITIONS OF ANY KIND, either express or implied.
 */

/*****   github.com/gorilla/mux   *****************

 NOTICE:
 =======
Copyright (c) 2012 Rodrigo Moraes. All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions are
met:
	 * Redistributions of source code must retain the above copyright
notice, this list of conditions and the following disclaimer.
	 * Redistributions in binary form must reproduce the above
copyright notice, this list of conditions and the following disclaimer
in the documentation and/or other materials provided with the
distribution.
	 * Neither the name of Google Inc. nor the names of its
contributors may be used to endorse or promote products derived from
this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
"AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
(INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
******/

/****** "github.com/russross/blackfriday"
NOTICE
=======
Blackfriday is distributed under the Simplified BSD License:

> Copyright © 2011 Russ Ross. All rights reserved.
>
> Redistribution and use in source and binary forms, with or without
> modification, are permitted provided that the following conditions
> are met:
> 1.  Redistributions of source code must retain the above copyright
>     notice, this list of conditions and the following disclaimer.
>
> 2.  Redistributions in binary form must reproduce the above
>     copyright notice, this list of conditions and the following
>     disclaimer in the documentation and/or other materials provided with
>     the distribution.
> THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
> "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
> LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
> FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
> COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
> INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
> BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
> LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
> CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
> LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
> ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
> POSSIBILITY OF SUCH DAMAGE.
********/

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	//"net"
	"net/http"
	//"net/http/httputil"
	"github.com/gorilla/mux"          // BSD-3-Clause
	"github.com/russross/blackfriday" // BSD-2-Clause
	"strconv"
)

// File global state variables
var theLedgerAddress string
var theLedgerPort int
var __systemReset bool

type Envelope struct {
	UUID         string `json:"uuid,omitempty"`
	SupplierUUID string `json:"supplier_uuid,omitempty"`
}

// Standardize method for sending http error status
func httpReportError(error_message string, http_reply http.ResponseWriter) {
	type replyMessage struct {
		Status  string `json:"status"`
		Message string `json:"error_message"`
	}
	var replyData replyMessage
	replyData.Status = "failed"
	replyData.Message = error_message
	httpSendReply(http_reply, replyData)
}

// Standardize method for sending success status for http requests
func httpSuccessReply(http_reply http.ResponseWriter) {
	type messageReply struct {
		Status string `json:"status"`
	}
	httpSuccessReply := messageReply{Status: "success"}
	httpSendReply(http_reply, httpSuccessReply)
}

// Print useful info
func displayURLRequest(request *http.Request) {
	fmt.Println()
	fmt.Println("-----------------------------------------------")
	fmt.Println("URL Request: ", request.URL.Path)
	//fmt.Println ("------------------------------------:")
	log.Println()

	fmt.Println("query params were:", request.URL.Query())
	fmt.Println("Client IP:", GetHostIPAddress())

	/*******
		// Display a copy of this request for debugging.
		requestDump, err := httputil.DumpRequest(request, true)
		if err != nil {
	  	fmt.Println(err)
		}
		fmt.Println(string(requestDump))
		*********/
}

// Display debug info about a url request
func displayURLReply(url_reply string) {
	// Display http reply content for monitoring and testing purposes
	fmt.Println("-----------------------------------------------")
	fmt.Println("URL Reply:")
	fmt.Println("---------------:")
	fmt.Println(url_reply)
}

// Pretty print (format) the json reply.
func httpSendReply(http_reply http.ResponseWriter, data interface{}) {

	// We want to pretty print the json reply. We need to wrap:
	//    json.NewEncoder(http_reply).Encode(reply)
	// with the following code:

	buffer := new(bytes.Buffer)
	encoder := json.NewEncoder(buffer)
	encoder.SetIndent("", "   ") // tells how much to indent "  " spaces.
	err := encoder.Encode(data)

	if MAIN_config.Debug_On {
		displayURLReply(buffer.String())
	}

	if err != nil {
		io.WriteString(http_reply, "error - could not encode reply")
	} else {
		io.WriteString(http_reply, buffer.String())
	}
}

// We provide a response when an api call is made but not found
func notFound(http_reply http.ResponseWriter, request *http.Request) {
	if MAIN_config.Debug_On {
		displayURLRequest(request)
	} // display url data

	type notFoundReply struct {
		Status           string `json:"status"`
		Message          string `json:"error_message"`
		DocumentationUrl string `json:"documentation_url"`
	}

	replyData := notFoundReply{Status: "failed",
		Message:          "Not Found",
		DocumentationUrl: "https://github.com/Wind-river/sparts"}
	httpSendReply(http_reply, replyData)
}


// ==============================================
// ====   API Handler END POINTS routines	=====
// ==============================================

var envelope_list []Envelope

// Handle: GET /api/sparts/help
func GetHelpEndPoint(http_reply http.ResponseWriter, request *http.Request) {

	if MAIN_config.Verbose_On {
		displayURLRequest(request)
	}
	// reply success to indicate running.

	b, err := ioutil.ReadFile("./data/SpartsConductorAPI.md") // just pass the file name
	if err != nil {
		fmt.Print(err)
	}
	// Convert markdown to html and send as html content
	output := blackfriday.MarkdownCommon(b)
	http_reply.Header().Set("Content-Type", "text/html")
	io.WriteString(http_reply, string(output))
}

// Handle:  GET /api/sparts/uuid
func GET_UUID_EndPoint(http_reply http.ResponseWriter, request *http.Request) {

	// Create and return an UUID
	type UUIDReply struct {
		UUID string `json:"uuid"`
	}
	var reply UUIDReply

	if MAIN_config.Verbose_On {
		displayURLRequest(request)
	} // display url data

	// Get the uuid
	reply.UUID = GetUUID()
	httpSendReply(http_reply, reply)
}

// Handle:  GET /api/sparts/ping
func GET_Ping_EndPoint(http_reply http.ResponseWriter, request *http.Request) {

	if MAIN_config.Verbose_On {
		displayURLRequest(request)
	}
	// reply success to indicate running.
	httpSuccessReply(http_reply)
}

// Handle:  GET /api/sparts/reset
func GET_Restore_EndPoint(http_reply http.ResponseWriter, request *http.Request) {

	if MAIN_config.Verbose_On {
		displayURLRequest(request)
	}
	if __systemReset == true {
		// reply success to indicate running.
		httpSuccessReply(http_reply)
	} else {
		httpReportError("Not Ready. Waiting on other processes to restart.", http_reply)
	}
}

// Handle:  POST /api/sparts/reset
func POST_Restore_EndPoint(http_reply http.ResponseWriter, request *http.Request) {

	type ResetRequest struct {
		Password string `json:"passwd"`
	}
	var theRequest ResetRequest
	if MAIN_config.Verbose_On {
		displayURLRequest(request)
	}

	err := json.NewDecoder(request.Body).Decode(&theRequest)
	if err != nil {
		http.Error(http_reply, err.Error(), 400)
		return
	}

	if theRequest.Password != MAIN_config.Ledger_API_Password {
		httpReportError("Incorrect Password", http_reply)
		return

	}

	// This is a hack - DOES NOT work. Done for testing purposes only.
	if __systemReset == true {
		__systemReset = false
	} else {
		__systemReset = true
	}
	httpSuccessReply(http_reply)
	// ToDo ask and wait for other processes
	// Loop for 10 secs checking others
}

// Handle:  GET /api/sparts/ledger/address
func GET_LedgerAPIAddress_EndPoint(http_reply http.ResponseWriter, request *http.Request) {

	type LedgerAddressReply struct {
		IPAddress string `json:"ip_address"`
		Port      int    `json:"port"`
	}

	if MAIN_config.Verbose_On {
		displayURLRequest(request)
	}

	var ledger_address LedgerAddressReply
	ledger_address.IPAddress = theLedgerAddress
	ledger_address.Port = theLedgerPort
	httpSendReply(http_reply, ledger_address)
}

// Handle: POST /api/sparts/ledger/address
func POST_LedgerAPIAddress_EndPoint(http_reply http.ResponseWriter, http_request *http.Request) {
	// This is where the the Ledger address is set.

	// ToDo - need to add requester authentication. Currently any app could call
	//		this routine

	type LedgerAddressRequest struct {
		IPAddress string `json:"ip_address"`
		Port      int    `json:"port"`
		Password  string `json:"passwd"`
	}
	var theRequest LedgerAddressRequest

	if MAIN_config.Verbose_On {
		displayURLRequest(http_request)
	} // display url data

	if http_request.Body == nil {
		http.Error(http_reply, "Please send a request body", 400)
		return
	}
	err := json.NewDecoder(http_request.Body).Decode(&theRequest)
	if err != nil {
		http.Error(http_reply, err.Error(), 400)
		return
	}

	if theRequest.Password == MAIN_config.Ledger_API_Password {
		theLedgerAddress = theRequest.IPAddress
		theLedgerPort = theRequest.Port
		UpdateLedgerAPIAddress(theLedgerAddress, theLedgerPort)

		// Send back standard message stating POST requested completed successfully
		httpSuccessReply(http_reply)

	} else {
		httpReportError("Incorrect Password", http_reply)
	}
}

// Ledger Node record
type LedgerNode struct {
	Name        string `json:"name"`                  // Fullname
	ShortId     string `json:"short_id"`              //	1-5 alphanumeric characters (unique)
	API_URL     string `json:"api_url"`               // e.g., http://147.52.17.33:5000
	UUID        string `json:"uuid,omitempty"`        // 	UUID provide w/previous registration
	Label       string `json:"label,omitempty"`       // 1-5 words display description
	Status      string `json:"status,omitempty"`      // RUNNING,
	Description string `json:"description,omitempty"` // 2-3 sentence description
}

// Handle: GET /api/sparts/ledger_nodes
func GET_LedgerNodes_EndPoint(http_reply http.ResponseWriter, http_request *http.Request) {

	if MAIN_config.Verbose_On {
		displayURLRequest(http_request)
	} // display url data

	list := GetLedgerNodesFromDB()
	httpSendReply(http_reply, list)
}

// Handle POST /api/sparts/ledger/register
func POST_Register_Ledger_EndPoint(http_reply http.ResponseWriter, request *http.Request) {
	type LedgerRegisterRequest struct {
		Name        string `json:"name"`                  // Fullname
		ShortId     string `json:"short_id"`              //	1-5 alphanumeric characters (unique)
		API_URL     string `json:"api_url"`               // e.g., http://147.52.17.33:5000
		UUID        string `json:"uuid,omitempty"`        // 	UUID provide w/previous registration
		Label       string `json:"label,omitempty"`       // 1-5 words display description
		Status      string `json:"status,omitempty"`      // RUNNING,
		Description string `json:"description,omitempty"` // 2-3 sentence description
	}

	type LedgerRegisterReply struct {
		UUID string `json:"uuid"`
	}

	var ledger_register LedgerRegisterRequest
	var reply LedgerRegisterReply

	if MAIN_config.Verbose_On {
		displayURLRequest(request)
	} // display url data

	if request.Body == nil {
		http.Error(http_reply, "Please send a request body", 400)
		return
	}
	err := json.NewDecoder(request.Body).Decode(&ledger_register)
	if err != nil {
		http.Error(http_reply, err.Error(), 400)
		return
	}

	if LedgerNodeExists(ledger_register.UUID) {
		// Return already existing UUID
		reply.UUID = ledger_register.UUID
	} else {
		// Return new UUID
		fmt.Println("its new!!")
		reply.UUID = GetUUID()
	}

	// TODO - ping to see if up.
	status := "RUNNING"

	AddLedgerNodeToDB(reply.UUID,
		ledger_register.Name,
		ledger_register.ShortId,
		ledger_register.API_URL,
		ledger_register.Label,
		ledger_register.Description,
		status) //

	httpSendReply(http_reply, reply)
}

// Handle: POST /api/sparts/app/register
func POST_RegisterApplication_EndPoint(http_reply http.ResponseWriter, request *http.Request) {

	type AppRegisterRequest struct {
		UUID        string `json:"uuid"`                  // 	UUID provide w/previous registration
		Name        string `json:"name"`                  // Fullname
		ShortId     string `json:"short_id"`              //	1-5 alphanumeric characters (unique)
		API_URL     string `json:"api_url"`               // http://host_address:port
		App_Type    string `json:"api_type,omitempty"`    // website, monitor
		Status      string `json:"status,omitempty"`      // RUNNING, DOWN,
		Label       string `json:"label,omitempty"`       // 1-5 words display description
		Description string `json:"description,omitempty"` // 2-3 sentence description
	}

	type AppRegisterReply struct {
		UUID string `json:"uuid"`
	}

	var app_register AppRegisterRequest
	var reply AppRegisterReply

	if MAIN_config.Verbose_On {
		displayURLRequest(request)
	} // display url data

	if request.Body == nil {
		http.Error(http_reply, "Please send a request body", 400)
		return
	}
	err := json.NewDecoder(request.Body).Decode(&app_register)
	if err != nil {
		http.Error(http_reply, err.Error(), 400)
		return
	}

	if ApplicationExists(app_register.UUID) {
		// Return already existing UUID
		reply.UUID = app_register.UUID
	} else {
		// Return new UUID
		fmt.Println("its new!!")
		reply.UUID = GetUUID()
	}
	// TODO ping to see if up.
	status := "RUNNING"

	AddApplicationToDB(reply.UUID,
		app_register.Name,
		app_register.ShortId,
		app_register.API_URL,
		app_register.App_Type,
		app_register.Label,
		app_register.Description,
		status)

	httpSendReply(http_reply, reply)
}

//  Handle: GET /api/sparts/ledger/node/{uuid}
func GET_LedgerNode_EndPoint(http_reply http.ResponseWriter, request *http.Request) {

	vars := mux.Vars(request)
	nodeUUID := vars["uuid"]
	/////fmt.Fprintln(http_reply, "Todo show:", nodeUUID)

	if LedgerNodeExists(nodeUUID) {
		fmt.Println("TRUE")
	} else {
		fmt.Println("FALSE")
	}

	///GetLedgerNodeInfo ("a72dc1b7-1bf6-4fc7-6c06-3a309b99cfce", &ledger)

}

// Handle: GET /api/sparts/db/reset
// Delete data in DB for a clean restart
func GET_DB_Reset_EndPoint(http_reply http.ResponseWriter, request *http.Request) {

	if MAIN_config.Debug_DB_On != true {
		return
	}
	fmt.Println("DB debug on")
}

// Handle: GET /api/sparts/config/reload
// Reloads server config file to allow config updates to used
func GET_Config_Reload_EndPoint(http_reply http.ResponseWriter, request *http.Request) {
	if MAIN_config.ConfigReloadAllowed {
		GetConfigurationInfo(&MAIN_config, false)
		log.Println("Config file reloaded.")
	}
}

// Handle: GET /favicon.ico
func GET_favicon_ico_EndPoint(writer http.ResponseWriter, request *http.Request) {
	// I get the following  additional url request browser icon) on some servers after each
	// normal url request:
	// 	/favicon.ico
	//So we will ignore it by doing nothing.
}

// ==============================================
// ====    Set up API routering calls		=====
// ==============================================

var router = mux.NewRouter()

// Initialie the RESTful API calls
func InitializeRestAPI() {
    fmt.Println("Initializing REST API ...")

	// Initialize Ledger API address based on values from last run
	GetLedgerAPIAddress(&theLedgerAddress, &theLedgerPort)
	// ToDo - ping to see if the Ledger API is still up.

	__systemReset = true

	router.HandleFunc("/api/sparts/uuid", GET_UUID_EndPoint).Methods("GET")
	router.HandleFunc("/api/sparts/ledger/address", GET_LedgerAPIAddress_EndPoint).Methods("GET")
	router.HandleFunc("/api/sparts/ledger/address", POST_LedgerAPIAddress_EndPoint).Methods("POST")
	router.HandleFunc("/api/sparts/ledger_nodes", GET_LedgerNodes_EndPoint).Methods("GET")
	router.HandleFunc("/api/sparts/ledger/register", POST_Register_Ledger_EndPoint).Methods("POST")
	router.HandleFunc("/api/sparts/ledger/node/{uuid}", GET_LedgerNode_EndPoint).Methods("GET")
	router.HandleFunc("/api/sparts/app/register", POST_RegisterApplication_EndPoint).Methods("POST")
	// General requests
	router.HandleFunc("/api/sparts/ping", GET_Ping_EndPoint).Methods("GET")
	router.HandleFunc("/api/sparts/reset", GET_Restore_EndPoint).Methods("GET")
	router.HandleFunc("/api/sparts/reset", POST_Restore_EndPoint).Methods("POST")
	router.HandleFunc("/api/sparts/db/reset", GET_DB_Reset_EndPoint).Methods("GET")
	router.HandleFunc("/api/sparts/config/reload", GET_Config_Reload_EndPoint).Methods("GET")
	router.HandleFunc("/favicon.ico", GET_favicon_ico_EndPoint).Methods("GET")

	// Get help
	router.HandleFunc("/api/sparts/help", GetHelpEndPoint).Methods("GET")

	router.NotFoundHandler = http.HandlerFunc(notFound)
}

// Main wait, listen and response to API requests.
func RunWaitAndRespond(http_port int) {

	// Create port string, e.g., for port 8080 we create ":8080" needed for ListenAndServe ()
	port_str := ":" + strconv.Itoa(http_port)

	fmt.Println("Listening on port", port_str, "...")
	log.Fatal(http.ListenAndServe(port_str, router))
}
