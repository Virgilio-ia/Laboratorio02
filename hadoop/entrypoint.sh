#!/bin/bash
set -euo pipefail

HADOOP_HOME="${HADOOP_HOME:-/opt/hadoop}"
export PATH="${JAVA_HOME:-/usr}/bin:$HADOOP_HOME/bin:$HADOOP_HOME/sbin:$PATH"

# Formatear el NameNode solo la primera vez
if [ ! -d /hadoop/dfs/name/current ]; then
  echo ">>> Formateando NameNode (primer arranque)..."
  hdfs namenode -format -force -nonInteractive
fi

stop_all() {
  echo ">>> Deteniendo demonios..."
  yarn --daemon stop nodemanager      || true
  yarn --daemon stop resourcemanager  || true
  hdfs --daemon stop datanode         || true
  hdfs --daemon stop namenode         || true
  exit 0
}
trap stop_all SIGTERM SIGINT

echo ">>> Arrancando HDFS..."
hdfs --daemon start namenode
hdfs --daemon start datanode

echo ">>> Arrancando YARN..."
yarn --daemon start resourcemanager
yarn --daemon start nodemanager

echo ">>> Esperando a que HDFS salga del modo seguro..."
hdfs dfsadmin -safemode wait || true

echo ">>> Demonios activos (jps):"
${JAVA_HOME:-/usr}/bin/jps 2>/dev/null || jps || true

echo ">>> Listo. NameNode UI: http://localhost:9870 | YARN UI: http://localhost:8088"

tail -F -n 0 "$HADOOP_HOME"/logs/*.log &
wait $!