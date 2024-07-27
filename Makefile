####################################################################################################################
# Setup containers to run Airflow

docker-spin-up:
	docker-compose build --no-cache && docker-compose up airflow-init && docker-compose up --build -d 

# perms:
# 	sudo mkdir -p logs plugins temp dags tests data visualization && sudo chmod -R u=rwx,g=rwx,o=rwx logs plugins temp dags tests data visualization

do-sleep:
	sleep 30

# up: perms docker-spin-up 
up: docker-spin-up 

down:
	docker-compose down

restart: down up

sh:
	docker exec -it airflow-airflow-webserver-1 bash