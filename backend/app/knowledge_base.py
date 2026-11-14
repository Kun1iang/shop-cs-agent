from dataclasses import dataclass
from pathlib import Path

import jieba
from rank_bm25 import BM25Okapi

from app.config import BASE_DIR


@dataclass(frozen=True)
class PolicyChunk:
    source: str
    title: str
    content: str


@dataclass(frozen=True)
class PolicySearchResult:
    source: str
    title: str
    content: str
    score: float


def tokenize(text: str) -> list[str]:
    return [
        token.strip().lower()
        for token in jieba.lcut(text)
        if token.strip()
    ]


class KnowledgeBase:
    def __init__(self, knowledge_dir: Path | None = None) -> None:
        self.knowledge_dir = knowledge_dir or (
            BASE_DIR / "data" / "knowledge"
        )
        self.chunks: list[PolicyChunk] = []
        self._bm25: BM25Okapi | None = None
        self._load()

    def _load(self) -> None:
        chunks: list[PolicyChunk] = []
        for path in sorted(self.knowledge_dir.glob("*.md")):
            text = path.read_text(encoding="utf-8")
            for raw_section in text.split("\n## "):
                section = raw_section.strip()
                if not section:
                    continue
                lines = section.splitlines()
                if lines[0].startswith("# "):
                    lines = lines[1:]
                    if not lines:
                        continue
                title = lines[0].strip()
                content = "\n".join(lines[1:]).strip()
                if not content:
                    continue
                chunks.append(
                    PolicyChunk(
                        source=path.name,
                        title=title,
                        content=content,
                    )
                )

        self.chunks = chunks
        self._bm25 = (
            BM25Okapi([tokenize(chunk.content) for chunk in chunks])
            if chunks
            else None
        )

    def search(self, query: str, top_k: int = 3) -> list[PolicySearchResult]:
        if self._bm25 is None or not self.chunks:
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        scores = self._bm25.get_scores(query_tokens)
        ranked = sorted(
            zip(self.chunks, scores, strict=True),
            key=lambda item: item[1],
            reverse=True,
        )
        return [
            PolicySearchResult(
                source=chunk.source,
                title=chunk.title,
                content=chunk.content,
                score=float(score),
            )
            for chunk, score in ranked[:top_k]
            if score > 0
        ]


knowledge_base = KnowledgeBase()

