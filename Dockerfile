FROM python:3.13.7-slim-bookworm@sha256:adafcc17694d715c905b4c7bebd96907a1fd5cf183395f0ebc4d3428bd22d92d
RUN pip install --no-cache-dir numpy==2.3.5
RUN python -c "import urllib.request; urllib.request.urlretrieve('https://github.com/jgm/pandoc/releases/download/3.8.3/pandoc-3.8.3-linux-arm64.tar.gz','/tmp/pandoc.tar.gz')" && tar -xzf /tmp/pandoc.tar.gz -C /tmp && cp /tmp/pandoc-3.8.3/bin/pandoc /usr/local/bin/pandoc && rm -rf /tmp/pandoc*
WORKDIR /artifact
