[![Build Status](https://travis-ci.org/vhakulinen/bruno-server.svg)](https://travis-ci.org/vhakulinen/bruno-server)
Bruno Server
============

This project is WIP and school project. Just before release on GitHub, I successfully made
transeferred live audio from peer to peer over network (not lan). In lack of
working hardware on another end, we weren't able to make a real call. So feel
free to test this, client can be found [here](https://github.com/vhakulinen/bruno-client).

Running the server
==================

Create SSL stuff with the following commands
```
openssl genrsa -des3 -out server.orig.key 2048
openssl rsa -in server.orig.key -out server.key
openssl req -new -key server.key -out server.csr
openssl x509 -req -days 365 -in server.csr -signkey server.key -out server.crt
```
Remember to copy the server.crt file to client's directory.

Create the database in python
```python
from bruno.db import init_db
init_db()
```

Run the server
```
python brunod.py
```

For all the options use the `--help` switch. Default TCP port is `9090`
and UDP `31500`. Default ip is `localhost`.

Contributing
===========

Open issue if you come across any bug or if you know python and have free time,
clone the repo, fix the bug and make pull request!

There is stuff to do with SSL connection which is fairly easy on server
side but this work on client side before we can apply it. Protocol
between peers (UDP connections) needs to be designed but server <-> client protocol
is pretty much locked down.

Some todos:
  * Text messaging
  * Groups chats
  * Friends
  * Video calls
  * File transfer

If you are really bored, you could write tests :)
