FROM debian:bookworm-slim@sha256:c67e92c8099ba22853ab4cfda7cfb494d253d6012ca82dee98ba8976772af018

# Packaging only. The three tools were source-compiled in the separately pinned
# CI archive. This file neither repeats that compilation nor runs a science tool.
RUN apt-get update \
 && apt-get install --no-install-recommends -y bash ca-certificates coreutils git jq \
      tar xz-utils unzip time python3 python3-venv libgcc-s1 \
 && python3 -m venv /opt/lp-awscli \
 && /opt/lp-awscli/bin/python -m pip install --disable-pip-version-check awscli==1.46.2 \
 && mkdir -p /opt/lp/runtime-package-metadata \
 && dpkg-query --show > /opt/lp/runtime-package-metadata/entire-dpkg-query.txt \
 && /opt/lp-awscli/bin/python -m pip freeze --all > /opt/lp/runtime-package-metadata/entire-pip-freeze.txt

ARG RECIPE_REVISION
LABEL org.opencontainers.image.source="https://github.com/isogeny-labs/cryptanalysis" \
      org.opencontainers.image.revision="${RECIPE_REVISION}" \
      org.isolab.lp.pure-source="2c44ee2ebb0be9b5fc0375818cc18924cef82c41" \
      org.isolab.lp.original-baseline-source="b7b91903888ffa9dea85e643e5a86e828767e7c8"

COPY --chown=1000:1000 recipe/ /opt/lp/recipe/
COPY --chown=1000:1000 build-info.json /opt/lp/build-info.json
RUN test ! -s /opt/lp/recipe/entire-actual-recipe-checkout-status.txt \
 && printf '%s' "$RECIPE_REVISION" | grep -Eq '^[a-f0-9]{40}$' \
 && jq --exit-status --arg revision "$RECIPE_REVISION" \
      '.actual_recipe_checkout_head==$revision' /opt/lp/build-info.json
COPY --chown=1000:1000 entire-guarded-file-snapshot.tar /opt/lp/entire-guarded-file-snapshot.tar
COPY --chown=1000:1000 entire-pure-CI-artifact.zip /opt/lp/entire-pure-CI-artifact.zip
COPY --chown=1000:1000 baseline/ /opt/lp/baseline/
COPY --chown=1000:1000 pure-build/ /opt/lp/pure-build/
COPY --chown=1000:1000 fixture-source/ /opt/lp/fixture-source/
COPY --chown=1000:1000 --chmod=0555 pure-build/extract_public /opt/lp/pure-build/extract_public
COPY --chown=1000:1000 --chmod=0555 pure-build/historical_certificates /opt/lp/pure-build/historical_certificates
COPY --chown=1000:1000 --chmod=0555 pure-build/lp-post-character /opt/lp/pure-build/lp-post-character
COPY --chown=1000:1000 --chmod=0555 baseline/native/original-rank-replayer /opt/lp/baseline/native/original-rank-replayer
COPY --chown=1000:1000 --chmod=0555 baseline/native/original-character-auditor /opt/lp/baseline/native/original-character-auditor

ENV PATH="/opt/lp-awscli/bin:${PATH}"
WORKDIR /work
USER 1000:1000
ENTRYPOINT []
