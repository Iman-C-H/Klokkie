# Generator für die Klokkie-Sprachdateien (Piper TTS, läuft komplett offline)
FROM debian:bookworm-slim
ARG TARGETARCH
ARG PIPER_VERSION=2023.11.14-2
# Andere Stimme: --build-arg VOICE=nl/nl_BE/rdh/medium/nl_BE-rdh-medium
ARG VOICE=nl/nl_NL/mls/medium/nl_NL-mls-medium

RUN apt-get update \
 && apt-get install -y --no-install-recommends ca-certificates wget ffmpeg \
 && rm -rf /var/lib/apt/lists/*

RUN case "$TARGETARCH" in arm64) A=aarch64 ;; *) A=x86_64 ;; esac \
 && wget -qO- "https://github.com/rhasspy/piper/releases/download/${PIPER_VERSION}/piper_linux_${A}.tar.gz" | tar -xz -C /opt
ENV PATH="/opt/piper:${PATH}"

RUN mkdir -p /opt/voices \
 && wget -qO /opt/voices/voice.onnx      "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/${VOICE}.onnx" \
 && wget -qO /opt/voices/voice.onnx.json "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/${VOICE}.onnx.json"

COPY phrases.tsv generate.sh /opt/klokkie/
WORKDIR /work
ENTRYPOINT ["/opt/klokkie/generate.sh"]
