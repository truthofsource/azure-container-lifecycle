# Public local adaptation: fictional demo command and browser smoke; production recipe is in reference/worker.
FROM mcr.microsoft.com/playwright:v1.63.0-noble@sha256:eff16c30e6f3f4af0a03fa4b706120d5e9b0891c344a27d64559aff5900a4a27 AS runtime
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci --omit=dev --no-audit --no-fund
# Keep the supported browser version while refreshing its installed OS packages.
# The worker uses Node directly; global package managers are build-time tools.
RUN apt-get update && apt-get upgrade -y && rm -rf /var/lib/apt/lists/* /root/.npm \
    /usr/lib/node_modules/npm /usr/lib/node_modules/corepack \
    /usr/local/lib/node_modules/npm /usr/local/lib/node_modules/corepack \
    && rm -f /usr/bin/npm /usr/bin/npx /usr/bin/corepack /usr/bin/yarn /usr/bin/yarnpkg /usr/bin/pnpm /usr/bin/pnpx \
        /usr/local/bin/npm /usr/local/bin/npx /usr/local/bin/corepack \
        /usr/local/bin/yarn /usr/local/bin/yarnpkg /usr/local/bin/pnpm /usr/local/bin/pnpx
COPY src ./src
USER pwuser
ENTRYPOINT ["node"]
CMD ["src/demo.mjs"]

# Default publication builds must pass the unprivileged synthetic browser/MFA check.
FROM runtime AS verify
RUN node src/browser-smoke.mjs
