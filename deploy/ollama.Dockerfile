FROM ollama/ollama:latest

ENV OLLAMA_HOST=0.0.0.0:11434

COPY deploy/start-ollama.sh /usr/local/bin/start-ollama
RUN chmod +x /usr/local/bin/start-ollama

EXPOSE 11434
CMD ["/usr/local/bin/start-ollama"]
