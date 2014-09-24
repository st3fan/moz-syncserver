// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/

package main

import (
	"code.google.com/p/gcfg"
	"flag"
	"fmt"
	"github.com/gorilla/mux"
	"github.com/st3fan/moz-storageserver/storageserver"
	"github.com/st3fan/moz-tokenserver/tokenserver"
	"log"
	"net/http"
)

const (
	DEFAULT_CONFIG_FILE        = "/etc/syncserver.ini"
	DEFAULT_API_LISTEN_ADDRESS = "0.0.0.0"
	DEFAULT_API_LISTEN_PORT    = 5000
)

func VersionHandler(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"version":"0.1"}`))
}

type Config struct {
	SyncServer struct {
		ListenAddress  string
		ListenPort     int
		PublicHostname string
		SharedSecret   string
		DataSource     string
	}
}

func main() {
	configFile := flag.String("config", DEFAULT_CONFIG_FILE, "config file path")
	flag.Parse()

	// Parse and validate the configuration

	var config Config
	if err := gcfg.ReadFileInto(&config, *configFile); err != nil {
		log.Fatal("Could not read config file: ", err)
	}

	if config.SyncServer.SharedSecret == "ThisIsAnImportantSecretThatYouShouldChange" {
		log.Fatal("Cannot run without a proper shared secret set")
	}

	// Setup the http mux and mount the token server and storage server on it

	router := mux.NewRouter()
	router.HandleFunc("/version", VersionHandler)

	tokenServerConfig := tokenserver.Config{
		PersonaVerifier:   "https://verifier.accounts.firefox.com/v2",
		PersonaAudience:   config.SyncServer.PublicHostname,
		AllowNewUsers:     true,
		TokenDuration:     300,
		SharedSecret:      config.SyncServer.SharedSecret,
		StorageServerNode: config.SyncServer.PublicHostname + "/storage",
		DatabaseUrl:       config.SyncServer.DataSource,
	}

	_, err := tokenserver.SetupRouter(router.PathPrefix("/token").Subrouter(), tokenServerConfig)
	if err != nil {
		log.Fatal(err)
	}

	storageServerConfig := storageserver.Config{
		DatabaseUrl:  config.SyncServer.DataSource,
		SharedSecret: config.SyncServer.SharedSecret,
	}

	_, err = storageserver.SetupRouter(router.PathPrefix("/storage").Subrouter(), storageServerConfig)
	if err != nil {
		log.Fatal(err)
	}

	// Start listening to http requests

	addr := fmt.Sprintf("%s:%d", config.SyncServer.ListenAddress, config.SyncServer.ListenPort)
	log.Printf("Starting sync server on http://%s", addr)
	http.Handle("/", router)
	err = http.ListenAndServe(addr, nil)
	if err != nil {
		log.Fatal(err)
	}
}
