#!/usr/bin/env bash
set -o errexit

# Update hệ thống
apt-get update
apt-get install -y curl gnupg apt-transport-https software-properties-common

# Thêm repo Microsoft
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/ubuntu/22.04/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update

# Cài MS ODBC Driver 18 + unixODBC
ACCEPT_EULA=Y apt-get install -y msodbcsql18 mssql-tools18 unixodbc-dev

# Cài Python libs
pip install -r requirements.txt