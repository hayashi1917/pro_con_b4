from libs.azure_client import AzureDocumentIntelligenceClient, AzureOpenAIClient
from langchain_core.prompts import ChatPromptTemplate
from app.schemas.schemas import KnowledgeFromLatexList, KnowledgeFromLatex
import typing
from typing import List, Dict, Any
import json

SYSTEM_PROMPT = """
あなたは学術ドキュメント解析の専門家です。
入力された LaTeX テキストから、有用な知見を「ナレッジ単位」に分割し、
以下フォーマットで JSON 配列として出力してください。
ナレッジは体言止めで出力してください。

# 出力仕様
各要素は必ず次を含む
- "knowledge"       : ナレッジテキスト
- "issue_category"  : ["段落構成" | "文法" | "単語" | "形式"] 

# 制約
* 英文校正に役立つものだけを抽出する
* JSON 以外を返さない
* LaTeX コマンドや数式は日本語へ意訳するか除去
* 同一内容は重複させない
"""

USER_PROMPT = """
# 入力資料（LaTeX）
{content}

# 出力条件
- 文書全体からナレッジを抽出
- 出力は UTF-8 / JSON 配列のみ
"""


def structure_tex_to_knowledge(chunks: List[Dict[str, Any]]) -> KnowledgeFromLatexList:
    aggregated: list[KnowledgeFromLatex] = []
    azure_openai_client = AzureOpenAIClient()
    for document in chunks:
        document_name = document["name"]
        knowledge_type = document["knowledge_type"]
        
        for chunk in document["chunks"]:
            per_chunk: list[KnowledgeFromLatex] = []
            prompt = ChatPromptTemplate.from_messages([
                ("system", SYSTEM_PROMPT),
                ("user", USER_PROMPT),
            ])
            chain = prompt | azure_openai_client.get_openai_client().with_structured_output(KnowledgeFromLatexList)
            chunk_text = chunk["chunk_text"]
            print("--------------------------------")
            print("chunk_text:")
            print(chunk_text)
            print("--------------------------------")
            results = chain.invoke({"content": chunk_text})
            per_chunk: list[KnowledgeFromLatex] = []
            
            for result in results.knowledge_list:   
                result.knowledge_type = knowledge_type
                result.reference_url = document_name
                print("--------------------------------")
                print("result:")
                print(result)
                print("--------------------------------")
                per_chunk.append(result)

            aggregated.extend(per_chunk)

    
    return aggregated






