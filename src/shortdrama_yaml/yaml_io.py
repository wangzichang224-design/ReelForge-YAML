from __future__ import annotations

import yaml

from .schema import ScriptDocument


def document_to_yaml(document: ScriptDocument) -> str:
    data = document.model_dump(mode="json", exclude_none=True)
    return yaml.safe_dump(
        data,
        allow_unicode=True,
        sort_keys=False,
        width=120,
    )


def yaml_to_document(yaml_text: str) -> ScriptDocument:
    loaded = yaml.safe_load(yaml_text)
    if not isinstance(loaded, dict):
        raise ValueError("YAML 根节点必须是 object/map。")
    return ScriptDocument.model_validate(loaded)


def yaml_to_plain_data(yaml_text: str) -> dict:
    document = yaml_to_document(yaml_text)
    return document.model_dump(mode="json", exclude_none=True)
