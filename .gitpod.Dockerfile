FROM gitpod/workspace-full:latest

USER gitpod

RUN pip3 install flask flask_cors requests fastapi python-jose[cryptography] passlib[bcrypt] uvicorn python-multipart aiofiles firebase-admin
