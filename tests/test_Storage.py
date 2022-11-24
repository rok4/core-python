from rok4.Storage import *
from rok4.Exceptions import *

import pytest
import os
import botocore
import boto3
from moto import mock_s3
os.environ["MOTO_S3_CUSTOM_ENDPOINTS"] = "https://s3.ign.fr"
from unittest.mock import *
from unittest import mock

@mock.patch.dict(os.environ, {}, clear=True)
def test_missing_env():
    with pytest.raises(MissingEnvironmentError):
        data = get_data_str("s3://bucket/path/to/object")

@mock.patch.dict(os.environ, {"ROK4_S3_URL": "a", "ROK4_S3_SECRETKEY": "b", "ROK4_S3_KEY": "c"})
@mock_s3
def test_s3_invalid_endpoint():
    with pytest.raises(StorageError):
        data = get_data_str("s3://bucket/path/to/object")

@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://s3.ign.fr", "ROK4_S3_SECRETKEY": "b", "ROK4_S3_KEY": "c"})
@mock_s3
def test_s3_read_error_no_bucket():
    conn = boto3.client(
        's3',
        aws_access_key_id=os.environ["ROK4_S3_KEY"],
        aws_secret_access_key=os.environ["ROK4_S3_SECRETKEY"],
        endpoint_url=os.environ["ROK4_S3_URL"]
    )
    with pytest.raises(StorageError):
        data = get_data_str("s3://bucket/path/to/object")

@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://s3.ign.fr", "ROK4_S3_SECRETKEY": "b", "ROK4_S3_KEY": "c"})
@mock_s3
def test_s3_read_error_no_object():
    conn = boto3.client(
        's3',
        aws_access_key_id=os.environ["ROK4_S3_KEY"],
        aws_secret_access_key=os.environ["ROK4_S3_SECRETKEY"],
        endpoint_url=os.environ["ROK4_S3_URL"]
    )
    conn.create_bucket(Bucket='bucket')
    with pytest.raises(StorageError):
        data = get_data_str("s3://bucket/path/to/object")

@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://s3.ign.fr", "ROK4_S3_SECRETKEY": "b", "ROK4_S3_KEY": "c"})
@mock_s3
def test_s3_read_ok():
    conn = boto3.client(
        's3',
        aws_access_key_id=os.environ["ROK4_S3_KEY"],
        aws_secret_access_key=os.environ["ROK4_S3_SECRETKEY"],
        endpoint_url=os.environ["ROK4_S3_URL"]
    )
    conn.create_bucket(Bucket='bucket')
    conn.put_object(Bucket='bucket', Key="path/to/object", Body="data")
    try:
        data = get_data_str("s3://bucket/path/to/object")
        assert data == "data"
    except Exception as exc:
        assert False, f"S3 read raises an exception: {exc}"
    

@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch("builtins.open", side_effect=FileNotFoundError("not_found"))
def test_file_read_error(mock_open):
    with pytest.raises(StorageError):
        data = get_data_str("file:///path/to/file.ext")
    
    mock_open.assert_called_with("/path/to/file.ext")

@mock.patch.dict(os.environ, {}, clear=True)
@patch("builtins.open", new_callable=mock_open, read_data="data")
def test_file_read_ok(mock_file):
    try:
        data = get_data_str("file:///path/to/file.ext")
        mock_file.assert_called_with("/path/to/file.ext")
        assert data == "data"
    except Exception as exc:
        assert False, f"FILE read raises an exception: {exc}"


@mock.patch.dict(os.environ, {}, clear=True)
@patch("builtins.open", new_callable=mock_open, read_data=b"data")
def test_file_hash_ok(mock_file):
    try:
        md5 = hash_file("/path/to/file.ext")
        mock_file.assert_called_with("/path/to/file.ext", "rb")
        assert md5 == "8d777f385d3dfec8815d20f7496026dc"
    except Exception as exc:
        assert False, f"FILE read raises an exception: {exc}"

def test_get_infos_from_path():
    assert (StorageType.S3, "toto/titi", "toto", "titi") == get_infos_from_path("s3://toto/titi")
    assert (StorageType.FILE, "/toto/titi/tutu.json", "/toto/titi", "tutu.json") == get_infos_from_path("file:///toto/titi/tutu.json")
    assert (StorageType.CEPH, "toto/titi/tutu", "toto", "titi/tutu") == get_infos_from_path("ceph://toto/titi/tutu")
    assert (StorageType.FILE, "wrong://toto/titi", "wrong://toto", "titi") == get_infos_from_path("wrong://toto/titi")


def test_get_path_from_infos():
    assert get_path_from_infos(StorageType.S3, "toto", "toto/titi") == "s3://toto/toto/titi"
    assert get_path_from_infos(StorageType.FILE, "/toto/titi", "tutu.json") == "file:///toto/titi/tutu.json"
    assert get_path_from_infos(StorageType.CEPH, "toto", "titi/tutu") == "ceph://toto/titi/tutu"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://s3.ign.fr", "ROK4_S3_SECRETKEY": "b", "ROK4_S3_KEY": "c"})
@mock_s3
def test_s3_write_ok():
    conn = boto3.client(
        's3',
        aws_access_key_id=os.environ["ROK4_S3_KEY"],
        aws_secret_access_key=os.environ["ROK4_S3_SECRETKEY"],
        endpoint_url=os.environ["ROK4_S3_URL"]
    )
    conn.create_bucket(Bucket='bucket')
    try:
        put_data_str("data", "s3://bucket/path/to/object")
    except Exception as exc:
        assert False, f"S3 read raises an exception: {exc}"