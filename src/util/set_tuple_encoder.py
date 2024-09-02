import json
from dataclasses import is_dataclass, asdict
from typing import Any, cast

from curator.curator_types import CuratorRepo


class SetTupleEncoder(json.JSONEncoder):
    def default(self, obj: Any) -> Any:
        if isinstance(obj, (set, tuple)):
            return {'__{}__'.format(type(obj).__name__): list(obj)}
        if is_dataclass(obj):
            # https://github.com/python/mypy/issues/17550:
            return {'__dataclass__': obj.__class__.__name__, 'data': asdict(obj)}  # type: ignore
        return json.JSONEncoder.default(self, obj)

    def encode(self, obj: Any) -> Any:
        def preprocess(obj: Any) -> Any:
            if isinstance(obj, dict):
                return {
                    json.dumps(
                        preprocess(k) if isinstance(k, (tuple, set, CuratorRepo)) else k
                    ): preprocess(v)
                    for k, v in obj.items()
                }
            elif isinstance(obj, list):
                return [preprocess(item) for item in obj]
            elif isinstance(obj, (tuple, set)):
                return [preprocess(item) for item in obj]
            elif is_dataclass(obj):
                return preprocess(asdict(obj))  # type: ignore
            return obj

        return super().encode(preprocess(obj))
