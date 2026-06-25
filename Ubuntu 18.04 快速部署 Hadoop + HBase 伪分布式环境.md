# Ubuntu 18\.04 快速部署 Hadoop \+ HBase 伪分布式环境

以下是 **Ubuntu 18\.04 快速部署 Hadoop \+ HBase 伪分布式环境** 的完整步骤，采用官方稳定二进制包安装，全程无需编译，适合快速测试与开发。

### 前置说明

- **部署模式**：伪分布式（单机模拟集群，单节点即可运行）

- **版本选型**：Hadoop 3\.3\.6 \+ HBase 2\.5\.8（官方验证兼容，适配 Ubuntu 18\.04 \+ JDK 8）

- **依赖要求**：OpenJDK 8、SSH 免密登录

---

## 步骤一：系统依赖与 Java 环境安装

### 1\. 更新系统并安装基础工具

```bash
sudo apt update && sudo apt install -y wget ssh openssh-server rsync vim
```

### 2\. 安装 OpenJDK 8

Hadoop 3\.x 与 HBase 2\.x 最稳定的运行环境是 JDK 8：

```bash
sudo apt install -y openjdk-8-jdk
```

验证安装：

```bash
java -version
# 输出 openjdk version "1.8.0_xxx" 即为成功
```

---

## 步骤二：配置 SSH 免密登录

Hadoop 节点间通信依赖 SSH，伪分布式模式需要本机 `localhost` 免密登录：

```bash
# 生成密钥对（一路回车即可）
ssh-keygen -t rsa -P '' -f ~/.ssh/id_rsa

# 配置公钥授权
cat ~/.ssh/id_rsa.pub >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
chmod 700 ~/.ssh
```

验证免密：

```bash
ssh localhost
# 无需输入密码直接登录即为成功，输入 exit 退出
```

---

## 步骤三：安装并配置 Hadoop 3\.3\.6

### 1\. 下载并解压二进制包

```bash
cd ~
wget https://archive.apache.org/dist/hadoop/common/hadoop-3.3.6/hadoop-3.3.6.tar.gz
tar -zxvf hadoop-3.3.6.tar.gz
mv hadoop-3.3.6 hadoop  # 重命名简化路径
```

### 2\. 配置环境变量

编辑 `~/.bashrc` 文件：

```bash
vim ~/.bashrc
```

在文件末尾添加以下内容：

```bash
# Hadoop Environment
export HADOOP_HOME=$HOME/hadoop
export PATH=$PATH:$HADOOP_HOME/bin:$HADOOP_HOME/sbin
export HADOOP_MAPRED_HOME=$HADOOP_HOME
export HADOOP_COMMON_HOME=$HADOOP_HOME
export HADOOP_HDFS_HOME=$HADOOP_HOME
export YARN_HOME=$HADOOP_HOME
```

生效环境变量：

```bash
source ~/.bashrc
```

### 3\. 修改 Hadoop 核心配置文件

配置文件路径：`$HADOOP_HOME/etc/hadoop/`

#### （1）`hadoop-env.sh` —— 指定 JDK 路径

```bash
vim $HADOOP_HOME/etc/hadoop/hadoop-env.sh
```

找到 `# export JAVA_HOME=` 一行，替换为：

```bash
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
```

#### （2）`core-site.xml` —— HDFS 核心配置

```bash
vim $HADOOP_HOME/etc/hadoop/core-site.xml
```

在 `<configuration>` 标签内添加：

```xml
<property>
    <name>fs.defaultFS</name>
    <value>hdfs://localhost:9000</value>
</property>
<property>
    <name>hadoop.tmp.dir</name>
    <value>${user.home}/hadoop/tmp</value>
</property>
```

#### （3）`hdfs-site.xml` —— HDFS 副本配置

```bash
vim $HADOOP_HOME/etc/hadoop/hdfs-site.xml
```

在 `<configuration>` 标签内添加：

```xml
<property>
    <name>dfs.replication</name>
    <value>1</value>
</property>
```

#### （4）`mapred-site.xml` —— MapReduce 配置

先复制模板文件：

```bash
cp $HADOOP_HOME/etc/hadoop/mapred-site.xml.template $HADOOP_HOME/etc/hadoop/mapred-site.xml
```

编辑文件：

```bash
vim $HADOOP_HOME/etc/hadoop/mapred-site.xml
```

在 `<configuration>` 标签内添加：

```xml
<property>
    <name>mapreduce.framework.name</name>
    <value>yarn</value>
</property>
<property>
    <name>mapreduce.application.classpath</name>
    <value>$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/*:$HADOOP_MAPRED_HOME/share/hadoop/mapreduce/lib/*</value>
</property>
```

#### （5）`yarn-site.xml` —— YARN 资源调度配置

```bash
vim $HADOOP_HOME/etc/hadoop/yarn-site.xml
```

在 `<configuration>` 标签内添加：

```xml
<property>
    <name>yarn.nodemanager.aux-services</name>
    <value>mapreduce_shuffle</value>
</property>
<property>
    <name>yarn.nodemanager.env-whitelist</name>
    <value>JAVA_HOME,HADOOP_COMMON_HOME,HADOOP_HDFS_HOME,HADOOP_CONF_DIR,CLASSPATH_PREPEND_DISTCACHE,HADOOP_YARN_HOME,HADOOP_MAPRED_HOME</value>
</property>
```

### 4\. 格式化 HDFS（仅执行一次）

```bash
hdfs namenode -format
```

> 注意：**不要重复格式化**，否则会导致 NameNode 与 DataNode 集群 ID 不一致，启动失败。
> 
> 

### 5\. 启动 Hadoop 并验证

```bash
# 启动 HDFS
start-dfs.sh
# 启动 YARN
start-yarn.sh
```

验证进程：执行 `jps` 命令，出现以下 5 个进程即为成功：

- NameNode

- DataNode

- SecondaryNameNode

- ResourceManager

- NodeManager

Web 控制台访问：

- HDFS：`http://localhost:50070`

- YARN：`http://localhost:8088`

---

## 步骤四：安装并配置 HBase 2\.5\.8

### 1\. 下载并解压二进制包

使用 HBase 内置 ZooKeeper，无需单独部署 ZK，最大化安装速度：

```bash
cd ~
wget https://archive.apache.org/dist/hbase/2.5.8/hbase-2.5.8-bin.tar.gz
tar -zxvf hbase-2.5.8-bin.tar.gz
mv hbase-2.5.8 hbase  # 重命名简化路径
```

### 2\. 配置环境变量

编辑 `~/.bashrc`：

```bash
vim ~/.bashrc
```

末尾添加：

```bash
# HBase Environment
export HBASE_HOME=$HOME/hbase
export PATH=$PATH:$HBASE_HOME/bin
```

生效：

```bash
source ~/.bashrc
```

### 3\. 修改 HBase 核心配置文件

配置文件路径：`$HBASE_HOME/conf/`

#### （1）`hbase-env.sh` —— JDK 与内置 ZK 配置

```bash
vim $HBASE_HOME/conf/hbase-env.sh
```

找到 `# export JAVA_HOME=` 替换为：

```bash
export JAVA_HOME=/usr/lib/jvm/java-8-openjdk-amd64
# 使用 HBase 内置 ZooKeeper，无需单独安装
export HBASE_MANAGES_ZK=true
```

#### （2）`hbase-site.xml` —— 核心配置

```bash
vim $HBASE_HOME/conf/hbase-site.xml
```

在 `<configuration>` 标签内添加：

```xml
<!-- HBase 数据存储到 HDFS 上 -->
<property>
    <name>hbase.rootdir</name>
    <value>hdfs://localhost:9000/hbase</value>
</property>
<!-- 开启分布式模式 -->
<property>
    <name>hbase.cluster.distributed</name>
    <value>true</value>
</property>
<!-- 内置 ZooKeeper 数据目录 -->
<property>
    <name>hbase.zookeeper.property.dataDir</name>
    <value>${user.home}/hbase/zookeeper</value>
</property>
<!-- ZooKeeper 地址 -->
<property>
    <name>hbase.zookeeper.quorum</name>
    <value>localhost</value>
</property>
```

### 4\. 启动 HBase 并验证

确保 Hadoop 已正常启动后，执行：

```bash
start-hbase.sh
```

验证进程：执行 `jps`，新增以下 3 个进程即为成功：

- HMaster

- HRegionServer

- HQuorumPeer（内置 ZooKeeper）

进入 HBase Shell 测试：

```bash
hbase shell
```

在 Shell 中执行测试命令：

```bash
# 查看版本
version

# 创建测试表
create 'test_table', 'info'

# 查看所有表
list
```

能正常输出结果即部署完成。

---

## 服务启停命令汇总

```bash
# 停止 HBase
stop-hbase.sh

# 停止 Hadoop
stop-yarn.sh
stop-dfs.sh

# 启动顺序：先启 Hadoop，再启 HBase
start-dfs.sh && start-yarn.sh && start-hbase.sh
```

---

## 常见问题排查

1. **JAVA\_HOME 找不到**：确认 `hadoop-env.sh` 和 `hbase-env.sh` 中的 JDK 路径与实际一致，可通过 `ls /usr/lib/jvm/` 查看真实路径。

2. **SSH 免密失效**：检查 `~/.ssh` 目录权限为 700，`authorized_keys` 文件权限为 600。

3. **DataNode 启动失败**：多为重复格式化导致，删除 `~/hadoop/tmp` 目录后重新格式化 HDFS 即可。

4. **版本不兼容**：严格遵循 HBase 官方兼容矩阵，2\.5\.x 分支仅适配 Hadoop 3\.3\.x 系列。

需要我补充集群模式的部署步骤，或者提供一键安装的 Shell 脚本吗？

> （注：部分内容可能由 AI 生成）
