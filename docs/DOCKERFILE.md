# Read the Dockerfile from top to bottom

The [production recipe](../reference/worker/Dockerfile) is selected implementation source. The [root recipe](../Dockerfile) keeps that structure but changes the default command and verification script to the fictional public examples.

| Instruction | What it does | Why it matters |
| --- | --- | --- |
| `FROM ...@sha256:... AS runtime` | Starts from a named Playwright browser image at a recorded digest. | The browser and operating-system foundation are explicit. |
| `WORKDIR /app` | Chooses the program's working folder. | Later relative paths have a clear location. |
| `COPY package.json package-lock.json ./` | Copies dependency descriptions before application source. | Source-only changes may reuse an unchanged dependency layer. |
| `RUN npm ci --omit=dev ...` | Installs the versions resolved by the lockfile. | The lockfile and package manifest must agree. |
| `RUN apt-get ...` | Refreshes installed operating-system packages and removes build-time package-manager files. | Security refreshes add time and mean builds can differ as repositories change. |
| `COPY src ./src` | Adds the worker code. | The ignore file helps keep unrelated local files out of the context. |
| `USER pwuser` | Switches to the browser image's lower-permission account. | The program does not need to run as root. |
| `ENTRYPOINT ["node"]` | Selects Node as the executable. | Arguments supplied to `docker run` replace the default command arguments. |
| `CMD [...]` | Selects the default script. | The production recipe uses `worker-cli`, while the public image uses a fictional demo. |
| `FROM runtime AS verify` | Adds a final verification stage based on the runtime. | The default build must complete that stage. |
| `RUN node ...smoke...` | Runs the selected synthetic check during the build. | Building the earlier `runtime` target directly would skip this check. |

## Two important limits

This is a verification-stage design, not an automatic image-size reduction. The final stage inherits the runtime rather than copying a small executable into an empty final image.

A pinned base and lockfile improve control, but the package-upgrade step still reads changing repositories. Retaining and deploying the built image by its registry digest avoids assuming that a later rebuild will produce the same bytes.

The `.dockerignore` permits package files and `src` only. The public subset includes no provider credentials, session state, employee records or production configuration.

References: [Dockerfile instructions](https://docs.docker.com/reference/dockerfile/), [multi-stage builds](https://docs.docker.com/build/building/multi-stage/).
