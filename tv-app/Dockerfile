FROM node:22-bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates zip unzip openssl && rm -rf /var/lib/apt/lists/*
COPY sdb /usr/local/bin/sdb
COPY tizen.js /opt/tizen.js
RUN cd /opt/tizen.js && npm install --omit=dev --no-audit --no-fund && ln -s /opt/tizen.js/cli.js /usr/local/bin/tizenjs && chmod +x /opt/tizen.js/cli.js
WORKDIR /work
