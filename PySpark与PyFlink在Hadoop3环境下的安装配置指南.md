# PySpark与PyFlink在Hadoop3环境下的安装配置指南

### 核心结论先给你

不用换成纯 Python 框架。**Spark 和 Flink 都原生提供官方 Python API（PySpark / PyFlink）**，你完全可以用 Python 作为主力开发语言，同时完美兼容你已经搭好的 Hadoop \+ HBase 大数据栈。

补充说明：

- 两个引擎底层运行在 JVM 上，但 Python API 做了完整封装，你只需要写 Python 代码，底层自动完成交互；

- 相比纯 Python 计算框架（如 Dask），Spark/Flink 和 HDFS、HBase、YARN 的原生兼容性更好，完全适配你当前的技术栈；

- 下面给你适配 **Hadoop 3\.3\.6 \+ JDK 8** 的版本选型和完整安装步骤，和之前的部署风格完全统一。

---

## 版本匹配说明（和现有环境 100% 兼容）

|引擎|推荐版本|安装包|兼容说明|
|---|---|---|---|
|Spark|3\.5\.3|`spark-3.5.3-bin-hadoop3.tgz`|预编译适配 Hadoop 3\.x，自带 PySpark，JDK 8 完美运行|
|Flink|1\.18\.1|`flink-1.18.1-bin-scala_2.12.tgz`|稳定 LTS 分支，PyFlink 功能完整，可对接 Hadoop 3\.3\.6|

> 前置提示：Ubuntu 18\.04 默认 Python 3\.6 低于 PySpark/PyFlink 最低要求，文末附 Python 3\.8 升级方案。
> 
> 

---

## 一、Spark（PySpark）安装配置

### 1\. 下载安装包（清华镜像，走你的 socks5 代理）

```bash
curl --socks5-hostname 10.10.78.20:1080 -O https://mirrors.tuna.tsinghua.edu.cn/apache/spark/spark-3.5.3/spark-3.5.3-bin-hadoop3.tgz
```

### 2\. 解压并重命名

```bash
tar -zxvf spark-3.5.3-bin-hadoop3.tgz
mv spark-3.5.3-bin-hadoop3 spark
```

### 3\. 配置环境变量

编辑 `~/.bashrc`，在末尾追加：

```bash
# Spark Environment
export SPARK_HOME=$HOME/spark
export PATH=$PATH:$SPARK_HOME/bin:$SPARK_HOME/sbin
# PySpark 指定 Python 解释器
export PYSPARK_PYTHON=python3
export PYSPARK_DRIVER_PYTHON=python3
# 共享 Hadoop 配置，直接读写 HDFS
export HADOOP_CONF_DIR=$HADOOP_HOME/etc/hadoop
export HADOOP_CLASSPATH=$(hadoop classpath)
```

生效配置：

```bash
source ~/.bashrc
```

### 4\. 验证 PySpark

Spark 安装包**自带 PySpark**，无需额外 pip 安装，版本天然一致：

```bash
# 进入 Python 交互式 Spark 环境
pyspark
```

在交互式终端执行测试：

```python
# 测试本地计算
sc.parallelize([1,2,3,4,5]).sum()

# 测试读取 HDFS（需提前在 HDFS 放好测试文件）
spark.read.text("hdfs://localhost:9000/test/test.txt").show()
```

正常输出即配置完成。

---

## 二、Flink（PyFlink）安装配置

### 1\. 下载安装包（清华镜像）

```bash
curl --socks5-hostname 10.10.78.20:1080 -O https://mirrors.tuna.tsinghua.edu.cn/apache/flink/flink-1.18.1/flink-1.18.1-bin-scala_2.12.tgz
```

### 2\. 解压并重命名

```bash
tar -zxvf flink-1.18.1-bin-scala_2.12.tgz
mv flink-1.18.1 flink
```

### 3\. 配置环境变量

编辑 `~/.bashrc`，在末尾追加：

```bash
# Flink Environment
export FLINK_HOME=$HOME/flink
export PATH=$PATH:$FLINK_HOME/bin
```

生效配置：

```bash
source ~/.bashrc
```

### 4\. 配置 Hadoop 集成

让 Flink 直接复用本地 Hadoop 依赖，读写 HDFS：

```bash
echo "env.hadoop.conf.dir: $HADOOP_HOME/etc/hadoop" >> $FLINK_HOME/conf/flink-conf.yaml
```

### 5\. 安装 PyFlink Python SDK

PyFlink 需要单独安装 Python 端包，版本和引擎保持一致：

```bash
# 升级 pip
python3 -m pip install --upgrade pip
# 安装对应版本 PyFlink
python3 -m pip install apache-flink==1.18.1
```

### 6\. 验证运行

1. 启动 Flink 本地集群

```bash
start-cluster.sh
```

执行 `jps` 会新增 `StandaloneSessionClusterEntrypoint`、`TaskManagerRunner` 两个进程，Web UI 地址：`http://localhost:8081`

2. Python 代码测试
新建 `test_flink.py`：

```python
from pyflink.datastream import StreamExecutionEnvironment

env = StreamExecutionEnvironment.get_execution_environment()
data = env.from_collection([1, 2, 3, 4, 5])
data.print()
env.execute()
```

运行测试：

```bash
python3 test_flink.py
```

控制台正常输出数字即配置成功。

---

## 三、Ubuntu 18\.04 升级 Python 3\.8（必备）

Ubuntu 18\.04 默认 Python 3\.6 不满足 PySpark/PyFlink 最低要求，通过官方源升级：

```bash
sudo apt update
sudo apt install -y software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install -y python3.8 python3.8-distutils python3.8-dev

# 设置 python3 默认指向 3.8
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.8 1
```

验证：

```bash
python3 --version
```

输出 `Python 3.8.x` 即为成功。

---

## 四、对接现有 HBase 的说明

### PySpark 读写 HBase

提交任务时引入官方 HBase\-Spark 连接器即可：

```bash
pyspark --packages org.apache.hbase.connectors.spark:hbase-spark:1.0.0
```

支持通过 DataFrame 批量读写 HBase 表。

### PyFlink 读写 HBase

Flink SQL 原生支持 HBase 连接器，在 DDL 中直接定义 HBase 表即可，无需额外 Jar 包，Python 端可直接调用 Flink SQL API。

---

## 补充说明

1. **启停顺序**：先启动 Hadoop → 再启动 Spark/Flink → 最后启动 HBase；停止顺序相反。

2. **资源占用**：单机伪分布式下，Spark/Flink 默认各占 1G 内存，你的 3\.5G 内存完全够用。

3. **开发方式**：全程用 Python 写业务代码即可，不需要写 Java/Scala，两个引擎的 Python API 覆盖了绝大多数批处理、流处理、SQL 场景。

需要我把 Spark \+ Flink 的内容也整合进之前的部署文档，或者给你写一份 Python 读写 HBase 的示例代码吗？

> （注：部分内容可能由 AI 生成）
