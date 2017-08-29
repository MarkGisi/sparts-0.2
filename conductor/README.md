## The Conductor

The conductor is a server side component written in Go that services as a coordinator among all the different running components of a supply chain network. Because it provides services to all the other applications and blockchain  nodes it must be started before the others. Each of the other services and applications must register with the conductor first. Therefore the conductor's IP address and listening port needs to be known by all the participants. 

The conductor provides all services via a RESTful API. You can find the documantation in the /data directory or by making the following  request:

http://<conductor-host-addr>:<port>/api/sparts/help



## Build & Run

The conductor is written in Go and therefore you will need to compile it for your platform. You will need to install the following dependencies:

```
go get github.com/mattn/go-sqlite3
go get github.com/gorilla/mux
go get github.com/russross/blackfriday
go get github.com/nu7hatch/gouuid
```

In the conductor directory execute the following build command

```
go build -o conductor
```

Copy the conductor and directory /data to a directory where you want to run it and execute the conductor:

```
conductor  /data
```

There is a configuration file conductor_config.json in directory /data that you can set certain parameters such as the the ip port to listen on, to turn on or off verbose message mode and  so forth. The first time you run the conductor it will create a database file in /data so make sure the program has read/write permissions. 



