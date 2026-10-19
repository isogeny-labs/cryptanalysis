# Build from the workmesh directory:
#   docker build -f platforms/Dockerfile -t workmesh:research .
# For GPU work, replace this base with a matching provider CUDA-devel image.
FROM debian:bookworm-slim
ARG PROFILE=research
RUN apt-get update && apt-get install -y --no-install-recommends sudo ca-certificates curl python3 python3-venv \
    && useradd --create-home --uid 1000 --shell /bin/bash workspace \
    && mkdir -p /opt/workmesh /workspace \
    && chown workspace:workspace /opt/workmesh /workspace \
    && printf 'workspace ALL=(ALL) NOPASSWD:ALL\n' > /etc/sudoers.d/workspace \
    && chmod 440 /etc/sudoers.d/workspace
COPY --chmod=755 bootstrap.sh /usr/local/bin/workmesh
USER workspace
ENV WB_ROOT=/opt/workmesh
RUN PROFILE="${PROFILE}" DOCKER_MODE=client bash /usr/local/bin/workmesh install
WORKDIR /workspace
# Supply a real configuration or environment when launching. For a prepared image,
# mount durable state at /opt/workmesh/state and preserve vendor login directories.
ENTRYPOINT ["/usr/local/bin/workmesh", "run"]
CMD ["--", "sleep", "infinity"]
