// This Source Code Form is subject to the terms of the Mozilla Public
// License, v. 2.0. If a copy of the MPL was not distributed with this
// file, You can obtain one at http://mozilla.org/MPL/2.0/

package main

import (
	"fmt"
	"github.com/gorilla/mux"
	"github.com/st3fan/moz-storageserver/storageserver"
	"github.com/st3fan/moz-tokenserver/tokenserver"
	"log"
	"net/http"
)

const (
	DEFAULT_API_LISTEN_ADDRESS = "0.0.0.0"
	DEFAULT_API_LISTEN_PORT    = 5000
)

func VersionHandler(w http.ResponseWriter, r *http.Request) {
	w.Write([]byte(`{"version":"0.1"}`))
}

func main() {
	router := mux.NewRouter()
	router.HandleFunc("/version", VersionHandler)

	sharedSecret := "vgfvghbnjmnjhbvgfghjuyhgtfrt56yt"

	tokenServerConfig := tokenserver.Config{
		PersonaVerifier:   "https://verifier.accounts.firefox.com/v2",
		PersonaAudience:   "https://sync.sateh.com",
		AllowNewUsers:     true,
		TokenDuration:     300,
		SharedSecret:      sharedSecret,
		StorageServerNode: "https://sync.sateh.com/storage",
		DatabaseUrl:       "postgres://tokenserver:tokenserver@localhost/tokenserver",
	}

	_, err := tokenserver.SetupRouter(router.PathPrefix("/token").Subrouter(), tokenServerConfig)
	if err != nil {
		log.Fatal(err)
	}

	storageServerConfig := storageserver.Config{
		DatabaseUrl:  "postgres://storageserver:storageserver@localhost/storageserver",
		SharedSecret: sharedSecret,
	}

	_, err = storageserver.SetupRouter(router.PathPrefix("/storage").Subrouter(), storageServerConfig)
	if err != nil {
		log.Fatal(err)
	}

	addr := fmt.Sprintf("%s:%d", DEFAULT_API_LISTEN_ADDRESS, DEFAULT_API_LISTEN_PORT)
	log.Printf("Starting sync server on http://%s", addr)
	http.Handle("/", router)
	err = http.ListenAndServe(addr, nil)
	if err != nil {
		log.Fatal(err)
	}
}
