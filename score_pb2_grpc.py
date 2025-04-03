# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc
import warnings
from typing import Iterable, Any
import numpy as np
from time import time
import logging
from redis.commands.search.query import Query
from redis.client import Pipeline
from redisvl.index import SearchIndex
logging.basicConfig(level=logging.INFO)
from psycopg2 import connect
from redis_conn import PAPER_REDIS_POOL, DATASET_REDIS_POOL
from redis import Redis 
import pwc_proto.score_pb2 as score__pb2
from collections import defaultdict

GRPC_GENERATED_VERSION = '1.71.0'
GRPC_VERSION = grpc.__version__
_version_not_supported = False

try:
    from grpc._utilities import first_version_is_lower
    _version_not_supported = first_version_is_lower(GRPC_VERSION, GRPC_GENERATED_VERSION)
except ImportError:
    _version_not_supported = True

if _version_not_supported:
    raise RuntimeError(
        f'The grpc package installed is at version {GRPC_VERSION},'
        + f' but the generated code in score_pb2_grpc.py depends on'
        + f' grpcio>={GRPC_GENERATED_VERSION}.'
        + f' Please upgrade your grpc module to grpcio>={GRPC_GENERATED_VERSION}'
        + f' or downgrade your generated code using grpcio-tools<={GRPC_VERSION}.'
    )


class ScoreGetterStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.DatasetScore = channel.unary_stream(
                '/score.ScoreGetter/DatasetScore',
                request_serializer=score__pb2.RedisDatasetScoreRequest.SerializeToString,
                response_deserializer=score__pb2.ScoreResponse.FromString,
                _registered_method=True)
        self.PaperScore = channel.unary_stream(
                '/score.ScoreGetter/PaperScore',
                request_serializer=score__pb2.RedisPaperScoreRequest.SerializeToString,
                response_deserializer=score__pb2.ScoreResponse.FromString,
                _registered_method=True)
        self.Populate = channel.unary_unary(
                '/score.ScoreGetter/Populate',
                request_serializer=score__pb2.PopulateRequest.SerializeToString,
                response_deserializer=score__pb2.Empty.FromString,
                _registered_method=True)

def process_pipeline_output(output: list) -> list[float]:
    output = output[1:]
    result = []
    for idx, i in enumerate(output):
        if idx % 2 == 0:
            continue
        result.append(float(i[1]))
    return result


def filtered_query(client, embedding, ids):
    results = dict()
    info = client.ft("paper_db").info()
    num_docs = info['num_docs']
    pipeline: Pipeline = client.pipeline()
    for dataset_id in ids:
        query = (
            Query("@dataset_id:{$dataset_id}=>[KNN $k @embedding $vec as vector_distance]")
            .return_fields("vector_distance")
            .sort_by("vector_distance", asc=False)
            .dialect(2)
            .paging(0, num_docs)
        )
        pipeline.ft("paper_db").search(
            query,
            query_params={"vec": embedding, "k": 200, "dataset_id": dataset_id},
        )
    results_list = pipeline.execute()
    for dataset_id, res in zip(ids, results_list):
        res = process_pipeline_output(res)
        if res:
            score = np.mean(res)
        else:
            score = 0.0
        results[dataset_id] = score
    results = {k: v for k, v in sorted(results.items(), key=lambda item: item[1], reverse=True)}
    return results


class ScoreGetterServicer(object):
    """Missing associated documentation comment in .proto file."""

    def DatasetScore(self, request: score__pb2.RedisDatasetScoreRequest, context):
        embedding = np.array(request.embedding).astype(dtype=np.float32).tobytes()
        num_results = request.num_results
        dataset_ids = set(request.ids)
        with Redis(connection_pool=DATASET_REDIS_POOL) as client:
            info = client.ft("dataset_db").info()
            num_docs = info['num_docs']
            query = (
                Query(f"*=>[KNN $k @embedding $vec as vector_distance]")
                .return_fields("dataset_id", "vector_distance")
                .sort_by("vector_distance", asc=False)
                .dialect(2)
                .paging(0, num_docs)
            )
            results = client.ft("dataset_db").search(
                query, 
                query_params={"vec": embedding, "k": num_docs},   
            ).docs
            result_count = 0
            for r in results:
                intified_dataset_id = int(r["dataset_id"])
                if intified_dataset_id in dataset_ids:
                    result_count += 1
                    yield score__pb2.ScoreResponse(dataset_id=intified_dataset_id, score=float(r["vector_distance"]))
                if result_count == num_results:
                    break
                
    def PaperScore(self, request: score__pb2.RedisPaperScoreRequest, context):
        embedding = np.array(request.embedding).astype(dtype=np.float32).tobytes()
        num_results = request.num_results
        ids: list[int] = request.dataset_ids
        with Redis(connection_pool=PAPER_REDIS_POOL) as client:
            results = filtered_query(client, embedding, ids)

        result_count = 0
        for idx, (k, v) in enumerate(results.items()):
            result_count += 1
            yield score__pb2.ScoreResponse(dataset_id=int(k), score=float(v))
            if result_count == num_results:
                break

            

    def Populate(self, request: score__pb2.PopulateRequest, context):
        if request.populate_type == 1:
            with connect(dbname="papers_with_code", host="main-db", user="samyytids",port=5432, password="Pokemon11") as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT dp.dataset_id, pe.paper_id, pe.embedding FROM paper_embedding pe JOIN dataset_paper dp ON dp.paper_id = pe.paper_id")
                    papers = cur.fetchall()

            papers = list(map(lambda x: {"dataset_id":x[0], "paper_id":x[1].tobytes().hex(), "embedding":np.array(eval(x[2])).astype(np.float32).tobytes()}, papers))
            with Redis(connection_pool=PAPER_REDIS_POOL) as client:
                index = SearchIndex.from_yaml("./paper_schema.yaml", redis_client=client)
                index.create(overwrite=True, drop=True)
                index.load(papers)

        elif request.populate_type == 0:
            with connect(dbname="papers_with_code", host="main-db", user="samyytids",port=5432, password="Pokemon11") as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT dataset_id, embedding FROM dataset_embedding")
                    datasets = cur.fetchall()
            datasets = list(map(lambda x: {"dataset_id":x[0], "embedding":np.array(eval(x[1])).astype(np.float32).tobytes()}, datasets))
            with Redis(connection_pool=DATASET_REDIS_POOL) as client:
                index = SearchIndex.from_yaml("./dataset_schema.yaml", redis_client=client)
                index.create(overwrite=True, drop=True)
                index.load(datasets)
        else:
            raise Exception(f"Invalild populate type chosen {request.populate_type}")
        return score__pb2.Empty()



def add_ScoreGetterServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'DatasetScore': grpc.unary_stream_rpc_method_handler(
                    servicer.DatasetScore,
                    request_deserializer=score__pb2.RedisDatasetScoreRequest.FromString,
                    response_serializer=score__pb2.ScoreResponse.SerializeToString,
            ),
            'PaperScore': grpc.unary_stream_rpc_method_handler(
                    servicer.PaperScore,
                    request_deserializer=score__pb2.RedisPaperScoreRequest.FromString,
                    response_serializer=score__pb2.ScoreResponse.SerializeToString,
            ),
            'Populate': grpc.unary_unary_rpc_method_handler(
                    servicer.Populate,
                    request_deserializer=score__pb2.PopulateRequest.FromString,
                    response_serializer=score__pb2.Empty.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'score.ScoreGetter', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))
    server.add_registered_method_handlers('score.ScoreGetter', rpc_method_handlers)


 # This class is part of an EXPERIMENTAL API.
class ScoreGetter(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def DatasetScore(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/score.ScoreGetter/DatasetScore',
            score__pb2.DatasetScoreRequest.SerializeToString,
            score__pb2.ScoreResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def PaperScore(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(
            request,
            target,
            '/score.ScoreGetter/PaperScore',
            score__pb2.PaperScoreRequest.SerializeToString,
            score__pb2.ScoreResponse.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)

    @staticmethod
    def Populate(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(
            request,
            target,
            '/score.ScoreGetter/Populate',
            score__pb2.PopulateRequest.SerializeToString,
            score__pb2.Empty.FromString,
            options,
            channel_credentials,
            insecure,
            call_credentials,
            compression,
            wait_for_ready,
            timeout,
            metadata,
            _registered_method=True)
