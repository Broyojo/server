# Server Infrastructure

## Description
This is an improved version of my previous Minecraft server management tool, [mc-server-utils](https://github.com/Broyojo/mc-server-utils). This version improves over the last version by giving the user fine-grained control over what actions are applied to servers through command line arguments.

## How To Run It

There are 5 main actions:

1. `start`
2. `backup`
3. `render`
4. `upgrade`
5. `schedule` 

Commands are structured like this:
```
$ python3 server [action] [selector]
```
In the `selector` field above, you can provide nothing, which will just run the action over all servers in all server groups. A server group is a collection of servers, a directory. If you provide a group, it will run the action over all servers in that group. If you provide the server, the program will look through all servers in all groups and apply the action to the specified server once it is found. <br/><br/>Because the program can detect when servers are running, you cannot start a running server and you cannot stop a stopped server. This adds some extra safety.

## Examples
Perform `start` on all servers:
```
$ python3 server start
```
Perform `backup` on the `extra` group:
```
$ python3 server backup extra
```
Perform `render` on the `survival` server:
```
$ python3 server render survival
```