.PHONY: up down test logs restart

up:
	docker-compose up -d
	@echo "Waiting for proxy..." && sleep 3
	@./test.sh

down:
	docker-compose down

test:
	@./test.sh

logs:
	docker-compose logs -f litellm

restart:
	docker-compose restart litellm
	@sleep 2 && ./test.sh

# Pull a local model (free, private)
pull-local:
	docker exec -it $$(docker-compose ps -q ollama) ollama pull llama3.1:8b
