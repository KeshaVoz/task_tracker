FROM nginx:alpine

# Удаляем дефолтный конфиг
RUN rm /etc/nginx/conf.d/default.conf

# Копируем свою конфигурацию nginx
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Копируем статику
COPY . /usr/share/nginx/html

EXPOSE 80