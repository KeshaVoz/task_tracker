#!/bin/sh
sed -i "s|http://localhost:8080/api|${API_URL}|g" /usr/share/nginx/html/script.js
cp /usr/share/nginx/html/nginx.conf /etc/nginx/conf.d/default.conf
nginx -g 'daemon off;'