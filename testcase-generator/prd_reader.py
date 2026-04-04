#!/usr/bin/env python3
"""
PRD Reader - PRD / PRD/MD 文件内容提取器
支持 PDF 和 Markdown 文件的自动内容识别与提取

用法:
    python prd_reader.py <file_path> [--output OUTPUT_FILE] [--encoding ENCODING]
    python prd_reader.py ./requirements/prd.pdf
    python prd_reader.py ./requirements/prd.md
    python prd_reader.py ./requirements/prd.pdf --output extracted_content.txt

依赖安装:
    pip install pdfplumber  # PDF 支持
    # Markdown 无需额外依赖
"""

import argparse
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any


# ============================================================================
# PDF 提取模块
# ============================================================================

def extract_pdf(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    从 PDF 文件中提取文本内容。

    Args:
        file_path: PDF 文件路径
        encoding: 输出编码（用于处理特殊字符）

    Returns:
        包含提取结果的字典
    """
    try:
        import pdfplumber
    except ImportError:
        return {
            "success": False,
            "error": "pdfplumber 未安装。请运行: pip install pdfplumber",
            "content": "",
            "pages": 0,
            "file_type": "pdf"
        }

    content_parts = []
    total_pages = 0

    try:
        with pdfplumber.open(file_path) as pdf:
            total_pages = len(pdf.pages)

            for page_num, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                if text and text.strip():
                    content_parts.append(f"\n--- 第 {page_num} 页 ---\n{text}")

        full_content = "\n".join(content_parts)

        return {
            "success": True,
            "content": full_content,
            "pages": total_pages,
            "file_type": "pdf",
            "file_path": os.path.abspath(file_path),
            "file_size": os.path.getsize(file_path),
            "encoding": encoding
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"PDF 解析失败: {str(e)}",
            "content": "",
            "pages": 0,
            "file_type": "pdf"
        }


# ============================================================================
# Markdown 提取模块
# ============================================================================

def extract_markdown(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    读取 Markdown 文件内容。

    Args:
        file_path: MD 文件路径
        encoding: 文件编码

    Returns:
        包含读取结果的字典
    """
    try:
        with open(file_path, "r", encoding=encoding) as f:
            content = f.read()

        # 移除 BOM (Byte Order Mark) 如果存在
        if content.startswith('\ufeff'):
            content = content[1:]

        # 统计行数
        lines = content.split('\n')
        non_empty_lines = [l for l in lines if l.strip()]

        return {
            "success": True,
            "content": content,
            "lines": len(lines),
            "non_empty_lines": len(non_empty_lines),
            "file_type": "markdown",
            "file_path": os.path.abspath(file_path),
            "file_size": os.path.getsize(file_path),
            "encoding": encoding
        }

    except FileNotFoundError:
        return {
            "success": False,
            "error": f"文件不存在: {file_path}",
            "content": "",
            "file_type": "markdown"
        }
    except UnicodeDecodeError:
        # 尝试其他常见编码
        for alt_encoding in ["gbk", "gb2312", "latin-1"]:
            try:
                with open(file_path, "r", encoding=alt_encoding) as f:
                    content = f.read()
                return {
                    "success": True,
                    "content": content,
                    "file_type": "markdown",
                    "file_path": os.path.abspath(file_path),
                    "file_size": os.path.getsize(file_path),
                    "encoding": alt_encoding,
                    "note": f"使用备用编码 {alt_encoding} 读取成功"
                }
            except:
                continue

        return {
            "success": False,
            "error": f"文件编码不支持，请确保文件编码为 UTF-8 或 GBK",
            "content": "",
            "file_type": "markdown"
        }
    except Exception as e:
        return {
            "success": False,
            "error": f"Markdown 读取失败: {str(e)}",
            "content": "",
            "file_type": "markdown"
        }


# ============================================================================
# 主文件类型识别与路由
# ============================================================================

def identify_and_extract(file_path: str, encoding: str = "utf-8") -> Dict[str, Any]:
    """
    自动识别文件类型并提取内容。

    Args:
        file_path: 文件路径（支持相对路径和绝对路径）
        encoding: 编码（仅对 Markdown 有效）

    Returns:
        提取结果字典
    """
    if not os.path.exists(file_path):
        return {
            "success": False,
            "error": f"文件不存在: {file_path}",
            "content": ""
        }

    # 获取文件扩展名
    ext = Path(file_path).suffix.lower()

    # 路由到对应提取器
    if ext == ".pdf":
        result = extract_pdf(file_path, encoding)
    elif ext in [".md", ".markdown"]:
        result = extract_markdown(file_path, encoding)
    else:
        # 尝试作为文本文件读取
        result = extract_markdown(file_path, encoding)
        result["file_type"] = "unknown"
        result["note"] = f"未知文件类型 (.{ext})，尝试作为文本文件读取"

    # 添加元信息
    result["input_path"] = os.path.abspath(file_path)
    result["input_filename"] = os.path.basename(file_path)

    return result


def print_result(result: Dict[str, Any], output_file: Optional[str] = None, quiet: bool = False):
    """
    格式化输出结果。

    Args:
        result: 提取结果
        output_file: 可选的输出文件路径
        quiet: 静默模式（仅输出内容）
    """
    if not result["success"]:
        print(f"错误: {result.get('error', '未知错误')}", file=sys.stderr)
        sys.exit(1)

    if quiet:
        # 仅输出内容，用于管道传输
        print(result["content"])
        return

    # 格式化输出
    print("=" * 60)
    print(f"文件读取成功")
    print("=" * 60)
    print(f"📄 文件名: {result['input_filename']}")
    print(f"📁 路径:   {result['input_path']}")
    print(f"📊 类型:   {result['file_type'].upper()}")

    if result["file_type"] == "pdf":
        print(f"📑 页数:   {result['pages']} 页")

    print(f"📏 大小:   {result['file_size']} bytes")
    if "encoding" in result:
        print(f"🔤 编码:   {result['encoding']}")
    if "note" in result:
        print(f"💡 注意:   {result['note']}")

    print("-" * 60)
    print(f"内容预览 (前 500 字符):")
    print("-" * 60)
    preview = result["content"][:500]
    if len(result["content"]) > 500:
        preview += "\n... [内容已截断]"
    print(preview)
    print("-" * 60)
    print(f"✅ 总字符数: {len(result['content'])}")

    # 输出到文件
    if output_file:
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result["content"])
        print(f"\n💾 内容已保存到: {output_file}")


# ============================================================================
# 命令行入口
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="PRD Reader - PRD/MD 文件内容提取器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    python prd_reader.py ./requirements/prd.pdf
    python prd_reader.py ./requirements/prd.md
    python prd_reader.py ./prd.pdf --output extracted.txt
    python prd_reader.py ./doc.md --encoding gbk

支持的文件格式:
    - PDF (.pdf)  - 需要安装 pdfplumber: pip install pdfplumber
    - Markdown (.md, .markdown) - 无额外依赖
        """
    )

    parser.add_argument(
        "file_path",
        help="PRD 文件路径 (支持 PDF 或 Markdown)"
    )

    parser.add_argument(
        "-o", "--output",
        help="将提取内容保存到指定文件"
    )

    parser.add_argument(
        "-e", "--encoding",
        default="utf-8",
        help="文件编码 (默认: utf-8)"
    )

    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="静默模式，仅输出内容（适用于管道传输）"
    )

    args = parser.parse_args()

    # 执行提取
    result = identify_and_extract(args.file_path, args.encoding)

    # 输出结果
    print_result(result, args.output, args.quiet)


if __name__ == "__main__":
    main()
