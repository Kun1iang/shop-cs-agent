from app.knowledge_base import knowledge_base


def test_policy_search_finds_refund_rule() -> None:
    results = knowledge_base.search("七天无理由退款")

    assert results
    assert results[0].title == "七天无理由退款"
    assert "7 个自然日" in results[0].content


def test_policy_search_finds_approval_threshold() -> None:
    results = knowledge_base.search("多少钱需要人工审批")

    assert results
    assert any("50 元" in result.content for result in results)
