FROM nginx:alpine
COPY nginx/nginx.conf /etc/nginx/conf.d/default.conf
COPY Frontend/ /usr/share/nginx/html/
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3     CMD wget -q --spider http://127.0.0.1/healthz || exit 1
