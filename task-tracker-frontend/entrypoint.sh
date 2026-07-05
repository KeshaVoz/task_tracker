#!/bin/sh
sed -i "s|http://localhost:8080/api|${API_URL}|g" /usr/share/nginx/html/script.js
nginx -g 'daemon off;'