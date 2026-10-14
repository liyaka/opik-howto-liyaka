FROM n8nio/n8n:2.41.7

USER root
# n8n-observability hooks into n8n's lifecycle: one OTel span per workflow run and per node, exported over OTLP to Opik
RUN npm install -g n8n-observability@1.0.3
ENV EXTERNAL_HOOK_FILES=/usr/local/lib/node_modules/n8n-observability/dist/hooks.cjs

USER node
