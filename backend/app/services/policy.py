"""
政策文件管理服务
支持上传、解析、检索政策文件
"""
import os
import re
from typing import List, Optional, Dict
from pathlib import Path
from datetime import datetime

import yaml

from app.core.config import settings
from app.services.vector_search import vector_search


class PolicyService:
    """政策文件服务"""
    
    def __init__(self):
        self.base_path = Path(settings.KNOWLEDGE_BASE_PATH) / "policies"
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def _get_year_dir(self, year: int) -> Path:
        """获取年份目录"""
        year_dir = self.base_path / str(year)
        year_dir.mkdir(exist_ok=True)
        return year_dir
    
    def _extract_metadata(self, content: str) -> Dict:
        """
        从政策文件内容中提取元数据
        
        支持的格式：
        - 文号：国发〔2026〕1号
        - 发文机关：国务院
        - 标题：通常在第一行
        """
        metadata = {
            "title": "",
            "document_number": "",
            "issuer": "",
            "date": "",
            "key_points": []
        }
        
        lines = content.split("\n")
        
        # 提取标题（第一行非空）
        for line in lines[:5]:
            line = line.strip()
            if line and not metadata["title"]:
                metadata["title"] = line
                break
        
        # 提取文号
        doc_num_pattern = r'([\u4e00-\u9fa5]+发?〔\d{4}〕\d+号)'
        match = re.search(doc_num_pattern, content)
        if match:
            metadata["document_number"] = match.group(1)
        
        # 提取发文机关
        issuer_patterns = [
            r'(中共中央|国务院|全国人大常委会|[^，。\n]{2,20})(?:关于|印发|发布)',
            r'^(.*?)(?:办公厅|办公室|委员会|部|局|厅)'
        ]
        for pattern in issuer_patterns:
            match = re.search(pattern, content[:500])
            if match:
                metadata["issuer"] = match.group(1)
                break
        
        # 提取日期
        date_pattern = r'(\d{4})年(\d{1,2})月(\d{1,2})日'
        match = re.search(date_pattern, content)
        if match:
            metadata["date"] = f"{match.group(1)}-{match.group(2).zfill(2)}-{match.group(3).zfill(2)}"
        
        # 提取要点（简单实现：找包含"一、"、"二、"等的段落）
        key_points = []
        point_pattern = r'[一二三四五六七八九十]+[、\.．]([^\n]+)'
        matches = re.findall(point_pattern, content[:2000])
        for m in matches[:5]:  # 最多取5个要点
            key_points.append(m.strip())
        metadata["key_points"] = key_points
        
        return metadata
    
    async def add_policy(
        self,
        filename: str,
        content: str,
        year: int = None,
        custom_metadata: Dict = None
    ) -> Dict:
        """
        添加政策文件
        
        Args:
            filename: 文件名
            content: 文件内容
            year: 年份（可选，自动提取）
            custom_metadata: 自定义元数据
            
        Returns:
            文件信息
        """
        # 提取元数据
        metadata = self._extract_metadata(content)
        if custom_metadata:
            metadata.update(custom_metadata)
        
        # 确定年份
        if not year and metadata.get("date"):
            try:
                year = int(metadata["date"][:4])
            except:
                year = datetime.now().year
        elif not year:
            year = datetime.now().year
        
        # 生成文件ID
        doc_id = f"policy_{year}_{filename.replace(' ', '_').replace('.', '_')}"
        
        # 保存文件
        year_dir = self._get_year_dir(year)
        file_path = year_dir / f"{doc_id}.md"
        
        # 构建 Markdown 内容
        md_content = f"""---
title: {metadata.get('title', filename)}
document_number: {metadata.get('document_number', '')}
issuer: {metadata.get('issuer', '')}
date: {metadata.get('date', '')}
year: {year}
id: {doc_id}
---

# {metadata.get('title', filename)}

## 基本信息
- **文号**: {metadata.get('document_number', '待补充')}
- **发文机关**: {metadata.get('issuer', '待补充')}
- **发布日期**: {metadata.get('date', '待补充')}

## 内容要点
"""
        for i, point in enumerate(metadata.get('key_points', []), 1):
            md_content += f"{i}. {point}\n"
        
        md_content += f"\n## 原文\n\n{content}\n"
        
        file_path.write_text(md_content, encoding="utf-8")
        
        # 添加到向量库
        await vector_search.add_document(
            collection=vector_search.COLLECTION_POLICIES,
            doc_id=doc_id,
            content=content,
            metadata={
                "title": metadata.get("title", filename),
                "document_number": metadata.get("document_number", ""),
                "issuer": metadata.get("issuer", ""),
                "date": metadata.get("date", ""),
                "year": year,
                "key_points": metadata.get("key_points", []),
                "file_path": str(file_path)
            }
        )
        
        return {
            "id": doc_id,
            "filename": filename,
            "year": year,
            "metadata": metadata,
            "path": str(file_path)
        }
    
    def get_policy(self, doc_id: str, year: int = None) -> Optional[Dict]:
        """
        获取政策文件
        
        Args:
            doc_id: 文件ID
            year: 年份（可选）
            
        Returns:
            文件内容
        """
        if year:
            file_path = self._get_year_dir(year) / f"{doc_id}.md"
        else:
            # 搜索所有年份
            file_path = None
            for year_dir in self.base_path.iterdir():
                if year_dir.is_dir():
                    candidate = year_dir / f"{doc_id}.md"
                    if candidate.exists():
                        file_path = candidate
                        break
        
        if not file_path or not file_path.exists():
            return None
        
        content = file_path.read_text(encoding="utf-8")
        
        # 解析 frontmatter
        metadata = {}
        body = content
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1])
                    body = parts[2].strip()
                except:
                    pass
        
        return {
            "id": doc_id,
            "metadata": metadata,
            "content": body,
            "path": str(file_path)
        }
    
    def list_policies(self, year: int = None) -> List[Dict]:
        """
        列出政策文件
        
        Args:
            year: 年份筛选（可选）
            
        Returns:
            文件列表
        """
        results = []
        
        if year:
            year_dirs = [self._get_year_dir(year)]
        else:
            year_dirs = [d for d in self.base_path.iterdir() if d.is_dir()]
        
        for year_dir in year_dirs:
            for md_file in year_dir.glob("*.md"):
                try:
                    content = md_file.read_text(encoding="utf-8")
                    metadata = {}
                    
                    # 简单解析 frontmatter
                    if content.startswith("---"):
                        parts = content.split("---", 2)
                        if len(parts) >= 3:
                            try:
                                metadata = yaml.safe_load(parts[1])
                            except:
                                pass
                    
                    results.append({
                        "id": metadata.get("id", md_file.stem),
                        "title": metadata.get("title", md_file.stem),
                        "document_number": metadata.get("document_number", ""),
                        "issuer": metadata.get("issuer", ""),
                        "date": metadata.get("date", ""),
                        "year": metadata.get("year", int(year_dir.name)),
                        "path": str(md_file)
                    })
                except Exception as e:
                    print(f"Error reading {md_file}: {e}")
        
        # 按日期倒序
        results.sort(key=lambda x: x.get("date", ""), reverse=True)
        return results
    
    async def search_policies(self, query: str, year: int = None, limit: int = 5) -> List[Dict]:
        """
        搜索政策文件
        
        Args:
            query: 查询关键词
            year: 年份筛选
            limit: 返回数量
            
        Returns:
            搜索结果
        """
        return await vector_search.search_policies(query, year, limit)
    
    def delete_policy(self, doc_id: str, year: int = None) -> bool:
        """删除政策文件"""
        policy = self.get_policy(doc_id, year)
        if not policy:
            return False
        
        # 删除文件
        Path(policy["path"]).unlink(missing_ok=True)
        
        # 删除向量
        vector_search.delete_document(
            vector_search.COLLECTION_POLICIES,
            doc_id
        )
        
        return True


# 全局政策服务实例
policy_service = PolicyService()