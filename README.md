Bruno Server
============

This project is WIP and school project. Just before release on GitHub, I successfully made
transeferred live audio from peer to peer over network (not lan). In lack of
working hardware on another end, we weren't able to make a real call. So feel
free to test this, client can be found [here](https://github.com/vhakulinen/bruno-client).

Running the server
==================

Clone this repo and

```
python brunod.py
```

For all the options use the `--help` switch. Default TCP port is `9090`
and UDP `31500`. Default ip is `localhost`.

Cotributing
===========

Open issue if you come across any bug or if you know python and have free time,
clone the repo, fix the bug and make pull request!

There is stuff to do with SSL connection which is fairly easy on server
side but this work on client side before we can apply it. Protocol
between peers (UDP connections) needs to be designed but server <-> client protocol
is pretty much locked down.

Some todos:
  * SSL
  * Text messaging
  * Groups chats
  * Friends
  * Password hashing
  * Video calls
  * File transfer

If you are really bored, you could write tests :)
