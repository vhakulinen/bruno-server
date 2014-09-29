Bruno Server
============

This project is WIP. Just before release on GitHub, I successfully made
transeferred live audio from peer to peer over network (not lan). In lack of
working hardware on another end, we weren't able to make a real call. So feel
free to test this, client can be found here(TODO: add link).

Running the server
==================

Clone this repo and

```
python brunod.py
```

For all the options use the `--help` switch. Default port TCP port is `9090`
and UDP `31500`. Default ip is `localhost`.

Cotributing
===========

Open issue if you come across any bug or if you know python and have free time,
clone the repo, fix the bug and make pull request!

There is stuff to do with SSL connection which is fairly easy to do on server
side but this needs work on client side before we can apply it. Protocol
between peers (UDP connections) needs to be designed but server client protocl
is pretty much locked down.

If you are really bored, you could write tests :)
