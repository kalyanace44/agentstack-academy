.PHONY: up down test discover

up:
	docker-compose up -d
	@echo "Waiting for agents..." && sleep 3
	@./test.sh

down:
	docker-compose down

test:
	@./test.sh

discover:
	@echo "Agent Cards:"
	@curl -s http://localhost:8001/.well-known/agent.json | python3 -m json.tool
	@curl -s http://localhost:8002/.well-known/agent.json | python3 -m json.tool
	@curl -s http://localhost:8003/.well-known/agent.json | python3 -m json.tool

# Run orchestrator (delegates to running agents)
orchestrate:
	python orchestrator.py
