## Sparts Project: The Software Parts Supply Chain Network

[TOC]

### Overview

The Software Supply Chain Network tracks and stores the compliance artifacts for the open source components used to construct a software solution.   It is very common for software solutions to be comprised of various open source components. In fact, it is not uncommon for the lion share of software developed today to be comprised of open source. We refer to the different open source components as parts. In the more general sense we refer to any software library, application or collection source files as software parts. These parts may themselves may be constructed from a collection of files (atomic parts) or they may be constructed by combining other existing atomic parts  and files which we refer to as composite parts. There are a number of benefits to understanding all the open source parts from which a software solution is comprised. Because software is often the result combining of the sub parts of different suppliers it is often difficult to identify all the open source parts that were used. 

The idea of software parts have become just as important as the more common physical parts. The Software Parts Supply Network is comprised of four core service components: 

1. **Sparts Software Parts Catalog** - A website application that plugs into the supply chain network that provides a catalog of the software parts available within the network. 
2. **Blockchain** Ledger - tracks all the open source parts and the meta data about the compliance artifacts of the open source parts. The Ledge r preserves the integrity and coordinates the of the compliance artifacts incluThe Ledger was built using the Hyperledger Sawtooth Process.
3. **Ledger Dashboard** - an application that enables one to monitor and administer the Ledger blockchain structure. 
4. **Conductor** - system process responsible for the management of the network

In addition to the above four core services two addition important data structures were needed.

- Compliance Envelop - This is an archive of a collection of artifacts prepared to comply with or provide important information about the use of open source in a given software solution. 
- Open Source Software Bill of Materials (OSS BOM).  

### Conductor API

The Conductor serves as  the network coordinator.   

- Ping Service Status(*)

- Get New UUID

- Get Ledger API Address

- Set Ledger API Address

- Register Ledger Node

- Register Application (*)

  vvvvvvvv

#### Ping To See If Active

------

Send request to see if the service is currently available

```
GET /api/sparts/ping
```

Successful response

```
{
   "status": "success"
}
```



#### Reset System Request

------

Reset demo system back to original state. 

```
POST /api/sparts/reset
{
	"passwd":"6172d350-6959-4e3d-7906-6feb99d9030e"
}
```



#### System Reset Status

------

```
GET /api/sparts/reset
```

Successful Response - System (all services) has been successfully reset. 

```
{
   "status": "success"
}
```

Error Response - System has not completed the reset action

```
{
   "status": "failed",
   "error_message": "Not Ready. Waiting on other processes to restart."
}

```



#### Get New UUID 

------

This is a simple service that creates a new universal unique identifier.

**Request**:

```
GET /api/sparts/uuid 
```
**Response**:

```
{ UUID	string	`json:"uuid"`} 
```
**Example**:

```
http://mysite.com/api/uuid
```

```
{"uuid":"fa76476f-dcde-4449-7f50-fed2800ece3d"} 
```
Register Application with Supply Chain

Unregister Application with Supply Chain

Get List of Applications



#### Get Ledger API Address

```
GET /api/sparts/ledger/address
```

**Response**

```
{
	IPAddress	string	`json:"ip_address"`
    Port 		int   	`json:"port"`
	Password	string	`json:"passwd"`
}
```

**Example Response**

```
{
   "ip_address": "147.22.131.45",
   "port": 5000
}
```



#### Set Ledger API Address

```
POST /api/ledger/address
{
	IPAddress	string	`json:"ip_address"`
    Port 		int   	`json:"port"`
	Password	string	`json:"passwd"`
}
```

**Request Example**

```
{	"ip_address": "147.22.131.45", 
	"port": 5000, 
	"passwd": "6172d350-6959-4e3d-7906-6feb99d9030e"
}
```

**Response (Success)**

```
{
   "message": "Request Completed Successfully."
}
```

**Response (Error)**

```
{
   "message": "555: Incorrect Password"
}
```



#### Register Ledger Node

```
POST /api/sparts/ledger/node/register  
{
    Name		string	`json:"name"`  			// Fullname
	ShortId		string	`json:"short_id"`		//	1-5 alphanumeric characters
	IPAddress	string	`json:"ip_address"`		// IP address - e.g., 147.11.153.122
	Port		int 	`json:"port"`			// Port e.g., 5000
	UUID		string	`json:"uuid,omitempty"`	// 	UUID registration, 
	Label		string	`json:"label,omitempty"` // 1-5 words display description
	Description string	 `json:"description,omitempty"` // 2-3 sentence description
} 
```

#### Register Ledger Node

Each Ledger node needs to be registered with the Supply Chain Mgr. If you are registering a Ledger node for the first time the UUID field should be "" and the return value is the assigned UUID. Each successive registration should include the assign UUID and the newly provided info will be used to update the ledger node's information. 

**Request**

```
POST /api/sparts/ledger/register  
{
    Name		string	`json:"name"`  			// Fullname
	ShortId		string	`json:"short_id"`		//	1-5 alphanumeric characters
	IPAddress	string	`json:"ip_address"`		// IP address - e.g., 147.11.153.122
	Port		int 	`json:"port"`			// Port e.g., 5000
	UUID		string	`json:"uuid,omitempty"`	// 	UUID registration, 
	Label		string	`json:"label,omitempty"` // 1-5 words display description
	Description string	 `json:"description,omitempty"` // 2-3 sentence description
} 
```
**Response** - The first time it returns the ledger assigned UUID. This id must be used for future api requests including re-registration. Each additional registration will return this UUID  

```
{ 
	UUID 	string	`json:"uuid"` 
}
```

Response Example:

```
{
	"uuid": "a72dc1b7-1bf6-4fc7-6c06-3a309b99cfcf"
}
```


#### Ledger API Network Address

Obtain Ledger network address information (i.e., ip address and port)

**Request**:

```
GET /api/sparts/ledger/address
```
**Response**:

```
struct {
	IPAddress	string	`json:"ip_address"`
    Port 		int   	`json:"port"`
}
```
**Example Response**:

```
{"ip_address":"147.11.133.45", 
 "port":5050,
}
```
- Get List of Ledger Nodes

- Add Artifact to persistent store (phase II)
