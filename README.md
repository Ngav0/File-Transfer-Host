# File Transfer Host

An easy way to wirelessly transfer files without the need of cloud storage.
The Client sends files, and the server recieves them


There is added security so you won't recieve random connections from other people.
The secret key, and you can manually configure the only IP you'll allow to make connection.
I can't guarantee it's foolproof tho. Because there is also no encryption what so ever, so anyone on the same network can just sniff and read your files and the secret key.
Also, there is a possibility RCE could be exploited and executed on the server if you have a malicious client, so be ware!
This isn't meant to be a really secure program, just a little side project.


You'll need the following python library:
tkinterdnd2

You can install it using the following command: pip install tkinterdnd2
