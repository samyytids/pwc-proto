from google.protobuf.internal import containers as _containers
from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Iterable as _Iterable, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class PopulateType(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Dataset: _ClassVar[PopulateType]
    Paper: _ClassVar[PopulateType]
Dataset: PopulateType
Paper: PopulateType

class PaperBundle(_message.Message):
    __slots__ = ("ids",)
    IDS_FIELD_NUMBER: _ClassVar[int]
    ids: _containers.RepeatedScalarFieldContainer[bytes]
    def __init__(self, ids: _Optional[_Iterable[bytes]] = ...) -> None: ...

class Empty(_message.Message):
    __slots__ = ()
    def __init__(self) -> None: ...

class PopulateRequest(_message.Message):
    __slots__ = ("populate_type",)
    POPULATE_TYPE_FIELD_NUMBER: _ClassVar[int]
    populate_type: PopulateType
    def __init__(self, populate_type: _Optional[_Union[PopulateType, str]] = ...) -> None: ...

class RedisPaperScoreRequest(_message.Message):
    __slots__ = ("embedding", "num_results", "dataset_ids")
    EMBEDDING_FIELD_NUMBER: _ClassVar[int]
    NUM_RESULTS_FIELD_NUMBER: _ClassVar[int]
    DATASET_IDS_FIELD_NUMBER: _ClassVar[int]
    embedding: _containers.RepeatedScalarFieldContainer[float]
    num_results: int
    dataset_ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, embedding: _Optional[_Iterable[float]] = ..., num_results: _Optional[int] = ..., dataset_ids: _Optional[_Iterable[int]] = ...) -> None: ...

class RedisDatasetScoreRequest(_message.Message):
    __slots__ = ("embedding", "num_results", "ids")
    EMBEDDING_FIELD_NUMBER: _ClassVar[int]
    NUM_RESULTS_FIELD_NUMBER: _ClassVar[int]
    IDS_FIELD_NUMBER: _ClassVar[int]
    embedding: _containers.RepeatedScalarFieldContainer[float]
    num_results: int
    ids: _containers.RepeatedScalarFieldContainer[int]
    def __init__(self, embedding: _Optional[_Iterable[float]] = ..., num_results: _Optional[int] = ..., ids: _Optional[_Iterable[int]] = ...) -> None: ...

class ScoreResponse(_message.Message):
    __slots__ = ("dataset_id", "score")
    DATASET_ID_FIELD_NUMBER: _ClassVar[int]
    SCORE_FIELD_NUMBER: _ClassVar[int]
    dataset_id: int
    score: float
    def __init__(self, dataset_id: _Optional[int] = ..., score: _Optional[float] = ...) -> None: ...
