# honeypot-IoT

Creates a honeypot camera by utilizing multiple camera frames.
The purpose is to deceive an attacker using Nmap, because the protocol headers have been modified

The images to be uploaded should be in JPEG format and placed in the `img/` folder

Dependencies:

- Tornado Web 
- Python PIL

Usage:
```
python camera.py
```
For login:
- username: `username`
- password: `password`
