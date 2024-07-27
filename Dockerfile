FROM apache/airflow:2.9.2
COPY poetry.lock pyproject.toml /opt/airflow/

USER airflow
RUN pip install --no-cache-dir poetry


COPY quarto.sh /
RUN cd / && bash /quarto.sh

ENV AIRFLOW_HOME=/opt/airflow

USER root

# APT 
RUN apt-get update -qq && apt-get install -qq vim wget && chmod -R 755 /var/lib/apt/lists/

# Spark
RUN curl https://dlcdn.apache.org/spark/spark-3.5.1/spark-3.5.1-bin-hadoop3.tgz -o spark-3.5.1-bin-hadoop3.tgz && chmod 755 spark-3.5.1-bin-hadoop3.tgz


USER airflow

RUN poetry install --only=main --no-root

SHELL ["/bin/bash", "-o", "pipefail", "-e", "-u", "-x", "-c"]

USER 0

ARG CLOUD_SDK_VERSION=322.0.0
ENV GCLOUD_HOME=/opt/google-cloud-sdk

ENV PATH="${GCLOUD_HOME}/bin/:${PATH}"


WORKDIR $AIRFLOW_HOME

ENV JAVA_HOME='/usr/lib/jvm/java-17-openjdk-amd64'
ENV PATH=$PATH:$JAVA_HOME/bin
ENV SPARK_HOME='/opt/spark'
ENV PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
