import lancedb
# LanceDB：一个向量数据库，用来存储 embedding 向量并进行相似度搜索

from langchain_community.document_loaders import TextLoader
# 文档加载器，用来读取文本文件

from langchain_community.vectorstores import LanceDB
# LangChain 封装的 LanceDB 向量库接口

from langchain_text_splitters import RecursiveCharacterTextSplitter
# 文本切分器，用于把长文本切成小块

from web.documents.utils.custom_embeddings import CustomEmbeddings
# 自定义的 embedding 模型（把文本转成向量）


def insert_documents():

    # 1️⃣ 加载文本文件
    loader = TextLoader("./web/documents/data.txt", encoding="utf-8")
    documents = loader.load()
    # load() 返回 Document 对象列表
    # 每个 Document 结构：
    # Document(
    #   page_content="文本内容",
    #   metadata={}
    # )

    # 2️⃣ 创建文本切分器
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,     # 每个文本块最大 500 字符
        chunk_overlap=200   # 相邻块之间重叠 200 字符
    )

    # 3️⃣ 对文档进行切分
    texts = text_splitter.split_documents(documents)

    print(f'已切分成{len(texts)}个片段')

    # texts 是 Document[]，例如
    # [
    #   Document("xxxxx"),
    #   Document("xxxxx"),
    #   ...
    # ]

    # 4️⃣ 初始化 embedding 模型
    embeddings = CustomEmbeddings()
    # 作用：把文本变成向量
    # "你好世界" → [0.123, -0.233, 0.992 ...]

    # 5️⃣ 连接 LanceDB 向量数据库
    db = lancedb.connect('./web/documents/lancedb_storage')
    # 如果目录不存在会自动创建

    # 6️⃣ 创建向量库并插入数据
    vector_db = LanceDB.from_documents(
        documents=texts,        # 文档块
        embedding=embeddings,   # embedding模型
        connection=db,          # 数据库连接
        table_name='my_knowledge_base',  # 表名
        mode='overwrite',       # 覆盖已有表
    )

    # from_documents 内部会做三件事：
    # 1 计算 embedding
    # 2 建表
    # 3 写入向量数据

    # 7️⃣ 打印插入数量
    print(f'已插入 {vector_db._table.count_rows()} 行数据')