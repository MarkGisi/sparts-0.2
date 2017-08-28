package main

// Licensing: Apache-2.0
/*
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

import (
	"database/sql"
	"fmt"
	_ "github.com/mattn/go-sqlite3"
)

// File state globals
var theDB *sql.DB

const CONFIG_RECORD = "Config_Info"

type Supplier_struct struct {
	Id         string `json:"id",omitempty`
	UUID       string `json:"uuid"`
	Name       string `json:"name"`
	SKU_Symbol string `json:"sku_symbol"` // WR, INTEL, SAMSG
	Short_Id   string `json:"short_id"`   // WR-2e72b7
	Passwd     string `json:"passwd"`
	Type       string `json:"type"` // commercial, non-profit, individual
	Url        string `json:"url"`
}

type ledgerNode struct {
	Id          string `json:"id"`          // Primary key Id
	Name        string `json:"name"`        // Fullname
	ShortId     string `json:"short_id"`    //	1-5 alphanumeric characters (unique)
	IPAddress   string `json:"ip_address"`  // IP address - e.g., 147.11.153.122
	Port        int    `json:"port"`        // Port e.g., 5000
	UUID        string `json:"uuid"`        // 	UUID provide w/previous registration
	Label       string `json:"label"`       // 1-5 words display description
	Description string `json:"description"` // 2-3 sentence description
	Available   int    `json:"available"`   // 0 or 1 int (boolean)
}

func checkErr(err error) {
	if err != nil {
		panic(err)
	}
}

// Open the database.
func openDB() {

	var err error
	// Using SQLite
	theDB, err = sql.Open("sqlite3", MAIN_config.DatabaseFile)
	if err != nil {
		panic(err)
	}
	if theDB == nil {
		panic("DB nil")
	}
}

// Initialize the database
func InitializeDB() {

	fmt.Println("Initializing DB ...")
	createDBTables()
}

// Create database tables
func createDBTables() {

	openDB()
	defer theDB.Close()

	// Create the Ledger Node Table - a list of Ledger node records
	sql_cmd := `
	CREATE TABLE IF NOT EXISTS LedgerNodes (
		Id INTEGER PRIMARY KEY AUTOINCREMENT,
		UUID TEXT,
		Name TEXT,
		Short_Id TEXT,
		API_URL TEXT,
		Label TEXT,
		Description TEXT,
		Status TEXT,
		InsertedDatetime DATETIME
	);
	`
	_, err := theDB.Exec(sql_cmd)
	if err != nil {
		panic(err)
	}

	// Set UUID field to be unique in the Ledger Node table. If Insert detects conflict
	// on UUID it will replace existing with new record.
	sql_cmd = `CREATE UNIQUE INDEX idx_Ledgers_UUID 
				ON LedgerNodes (UUID);`

	firstTime := true // first time we are creating the database
	_, err = theDB.Exec(sql_cmd)
	if err != nil {
		// We expect the following error on the second and succeeding runs
		// after creating the tables. We can use this to determine the db is
		// being created for the first time which is useful later in the function.
		if err.Error() == "index idx_Ledgers_UUID already exists" {
			firstTime = false
		} else {
			fmt.Println(err)
		}
	}

	// Create table to hold a number of system variables.
	// That is make them presisent spanning executions of this program.
	// 		Config_Set_Name - Name give to row for easy query selection
	// 		Ledger_API_IP_Addr - IP address of ledger restful API
	// 		Ledger_API_Port - http Port number of ledger restful API
	sql_cmd = `
	CREATE TABLE IF NOT EXISTS SystemConfig (
		Id INTEGER PRIMARY KEY AUTOINCREMENT,
		Config_Name TEXT, 
		Ledger_IP_Addr TEXT,
		Ledger_Port INTEGER,
		InsertedDatetime DATETIME
	);`

	_, err = theDB.Exec(sql_cmd)
	if err != nil {
		fmt.Println(err)
	}

	if firstTime {
		// Let's create a one time record with default info into just created table.
		// CONFIG_RECORD is a tag name given to this record to make it easier to
		// retreive/update this record in later transactions.
		stmt, err := theDB.Prepare("INSERT INTO SystemConfig (Config_Name, Ledger_IP_Addr, Ledger_Port) values(?,?,?)")
		checkErr(err)
		res, err := stmt.Exec(CONFIG_RECORD, "0.0.0.0", 0)
		checkErr(err)
		id, err := res.LastInsertId()
		checkErr(err)
		fmt.Println("System Configuration Record Created: id =", id)
	}

	// Create the Application Table - a list of network applications
	sql_cmd = `
	CREATE TABLE IF NOT EXISTS Applications (
		Id INTEGER PRIMARY KEY AUTOINCREMENT,
		UUID TEXT,
		Name TEXT,
		Short_Id TEXT,
		API_URL TEXT,
		App_Type TEXT, 
		Label TEXT,
		Description TEXT,
		Status TEXT,
		InsertedDatetime DATETIME
	);
	`
	_, err = theDB.Exec(sql_cmd)
	if err != nil {
		panic(err)
	}

	// Set UUID field to be unique in the Application table. If Insert detects conflict
	// on UUID it will replace existing with new record.
	sql_cmd = `CREATE UNIQUE INDEX idx_Apps_UUID 
				ON Applications (UUID);`

	_, err = theDB.Exec(sql_cmd)
}

// A boolean function that determines if a record with uuid exits in the db/
func ApplicationExists(uuid string) bool {

	openDB()
	defer theDB.Close()
	rows, err := theDB.Query("SELECT UUID FROM Applications WHERE UUID=?", uuid)

	checkErr(err)

	// rows.Next () is a boolean that says whether a next record exists
	// If there is a next record (i.e., at least one) then true else false
	if rows.Next() {
		rows.Close()
		return true
	} else {
		rows.Close()
		return false
	}
}

// A boolean function that determines if a ledger node record with uuid exits in the db
func LedgerNodeExists(uuid string) bool {

	openDB()
	defer theDB.Close()
	rows, err := theDB.Query("SELECT UUID FROM LedgerNodes WHERE UUID=?", uuid)

	checkErr(err)

	// rows.Next () is a boolean that says whether a next record exists
	// If there is a next record (i.e., at least one) then true else false
	if rows.Next() {
		rows.Close()
		return true
	} else {
		rows.Close()
		return false
	}
}

// Get the Ledger node info
func GetLedgerNodeInfo(uuid string, lnode *ledgerNode) {

	openDB()
	defer theDB.Close()
	rows, err := theDB.Query("SELECT UUID, Name, Short_Id, IP_Address, Port, Label, Description FROM LedgerNodes WHERE UUID=?", uuid)
	checkErr(err)

	for rows.Next() {
		err = rows.Scan(&lnode.UUID, &lnode.Name, &lnode.ShortId, &lnode.IPAddress, &lnode.Port,
			&lnode.Label, &lnode.Description)
		checkErr(err)
	}

	rows.Close()
}

// Insert Supply Chain network Application record into the DB
func AddApplicationToDB(uuid string,
	name string,
	short_id string,
	api_url string,
	app_type string,
	label string,
	description string,
	status string) {
	openDB()
	defer theDB.Close()

	sql_additem := `
	INSERT OR REPLACE INTO Applications (
		UUID,
		Name,
		Short_Id,
		API_URL,
		App_Type, 
		Label,
		Description,
		Status, 
		InsertedDatetime
		) values(?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`

	stmt, err := theDB.Prepare(sql_additem)
	defer stmt.Close()
	if err != nil {
		panic(err)
	}

	_, err2 := stmt.Exec(uuid, name, short_id, api_url,
		app_type, label, description, status)
	if err2 != nil {
		panic(err2)
	}

	//_, err = res.LastInsertId()
}

// Insert Ledger node record into the DB
func AddLedgerNodeToDB(uuid string,
	name string,
	short_id string,
	api_url string,
	label string,
	description string,
	status string) {
	openDB()
	defer theDB.Close()

	sql_additem := `
	INSERT OR REPLACE INTO LedgerNodes (
		UUID, 
		Name, 
		Short_Id,
		API_URL,
		Label, 
		Description,
		Status, 
		InsertedDatetime
		) values(?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`

	stmt, err := theDB.Prepare(sql_additem)
	defer stmt.Close()
	if err != nil {
		panic(err)
	}

	_, err2 := stmt.Exec(uuid, name, short_id, api_url,
		label, description, status)
	if err2 != nil {
		panic(err2)
	}
}

// Get ledger node record
func GetLedgerNodesFromDB() []LedgerNode {

	var list []LedgerNode
	var node LedgerNode

	openDB()
	defer theDB.Close()
	rows, err := theDB.Query("SELECT UUID, Name, Short_Id, API_URL, Label, Description FROM LedgerNodes")
	checkErr(err)

	for rows.Next() {
		err = rows.Scan(&node.UUID, &node.Name, &node.ShortId, &node.API_URL,
			&node.Label, &node.Description)
		checkErr(err)
		list = append(list, node)
	}
	rows.Close() //good habit to close
	return list
}

// Get most recently reported Ledger API network address
func GetLedgerAPIAddress(ip_address *string, port *int) {

	openDB()
	defer theDB.Close()
	rows, err := theDB.Query("SELECT Ledger_IP_Addr, Ledger_Port FROM SystemConfig WHERE Config_Name=?", CONFIG_RECORD)
	checkErr(err)
	rows.Next()

	err = rows.Scan(ip_address, port)
	checkErr(err)
	fmt.Println("Ledger IP       = ", *ip_address)
	fmt.Println("Ledger Port     =", *port)
	rows.Close()
}

// Update the Ledger API address
func UpdateLedgerAPIAddress(ip_address string, port int) {
	openDB()
	defer theDB.Close()

	stmt, err := theDB.Prepare("UPDATE SystemConfig SET  Ledger_IP_Addr=?, Ledger_Port=?  WHERE Config_Name=?")
	checkErr(err)
	_, err = stmt.Exec(ip_address, port, CONFIG_RECORD)
}

// Add supplier record to the database
func AddSupplierToDB(s Supplier_struct) {

	openDB()
	defer theDB.Close()

	/****
	      fmt.Println ("UUID__ = ", s.UUID)
	  	fmt.Println ("Name = ", s.Name)
	  	fmt.Println ("SKU_Symbol = ", s.SKU_Symbol)
	  	fmt.Println ("Short_Id = ", s.Short_Id)
	  	fmt.Println ("Passwd = ", s.Passwd)
	  	fmt.Println ("Passwd = ", s.Type)
	  	fmt.Println ("Url = ", s.Url)
	  ****/

	//s.Id = ""
	sql_additem := `
	INSERT OR REPLACE INTO Suppliers (
		UUID, 
		Name, 
		SKU_Symbol, 
		Short_Id, 
		Passwd, 
		Type, 
		Url, 
		InsertedDatetime
		) values(?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)`

	stmt, err := theDB.Prepare(sql_additem)
	defer stmt.Close()
	if err != nil {
		panic(err)
	}

	res, err2 := stmt.Exec(s.UUID, s.Name, s.SKU_Symbol, s.Short_Id, s.Passwd, s.Type, s.Url)
	if err2 != nil {
		panic(err2)
	}

	// for debugging - could probably be removed.
	id, err := res.LastInsertId()
	if err != nil {
		fmt.Println("Error:")
		fmt.Println("last Id inserted", id)
		fmt.Println("Inserted")
		fmt.Println(s)
	}
}

// Get Supplier record from database.
func GetSupplier(db *sql.DB) []Supplier_struct {
	sql_readall := `
	SELECT Id, UUID, Name, SKU_Symbol, Short_Id, Passwd, Type, Url FROM Suppliers
	ORDER BY datetime(InsertedDatetime) DESC
	`

	rows, err := db.Query(sql_readall)
	if err != nil {
		panic(err)
	}
	defer rows.Close()

	var result []Supplier_struct
	for rows.Next() {
		item := Supplier_struct{}
		err2 := rows.Scan(&item.Id, &item.UUID, &item.Name, &item.SKU_Symbol, &item.Short_Id, &item.Passwd, &item.Type, &item.Url)
		if err2 != nil {
			panic(err2)
		}
		result = append(result, item)
	}
	return result
}
