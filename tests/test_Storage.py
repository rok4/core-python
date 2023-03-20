from rok4.Storage import *
from rok4.Exceptions import *

import pytest
import os

import botocore.exceptions
from rados import ObjectNotFound

from unittest import mock
from unittest.mock import *

@mock.patch.dict(os.environ, {}, clear=True)
@patch("builtins.open", new_callable=mock_open, read_data=b"data")
def test_hash_file_ok(mock_file):
    try:
        md5 = hash_file("/path/to/file.ext")
        mock_file.assert_called_with("/path/to/file.ext", 'rb')
        assert md5 == "8d777f385d3dfec8815d20f7496026dc"
    except Exception as exc:
        assert False, f"FILE md5 sum raises an exception: {exc}"

@mock.patch.dict(os.environ, {}, clear=True)  
def test_get_infos_from_path():
    assert (StorageType.S3, "toto/titi", "toto", "titi") == get_infos_from_path("s3://toto/titi")
    assert (StorageType.FILE, "/toto/titi/tutu.json", "/toto/titi", "tutu.json") == get_infos_from_path("file:///toto/titi/tutu.json")
    assert (StorageType.CEPH, "toto/titi/tutu", "toto", "titi/tutu") == get_infos_from_path("ceph://toto/titi/tutu")
    assert (StorageType.FILE, "wrong://toto/titi", "wrong://toto", "titi") == get_infos_from_path("wrong://toto/titi")


@mock.patch.dict(os.environ, {}, clear=True)  
def test_get_path_from_infos():
    assert get_path_from_infos(StorageType.S3, "toto", "toto/titi") == "s3://toto/toto/titi"
    assert get_path_from_infos(StorageType.FILE, "/toto/titi", "tutu.json") == "file:///toto/titi/tutu.json"
    assert get_path_from_infos(StorageType.CEPH, "toto", "titi/tutu") == "ceph://toto/titi/tutu"

############ get_data_str

@mock.patch.dict(os.environ, {}, clear=True)
def test_s3_missing_env():
    with pytest.raises(MissingEnvironmentError):
        data = get_data_str("s3://bucket/path/to/object")


@mock.patch.dict(os.environ, {}, clear=True)
def test_ceph_missing_env():
    with pytest.raises(MissingEnvironmentError):
        data = get_data_str("ceph://bucket/path/to/object")

@mock.patch.dict(os.environ, {"ROK4_S3_URL": "a,b", "ROK4_S3_SECRETKEY": "b,c", "ROK4_S3_KEY": "c,d,e"}, clear=True)
def test_s3_invalid_envs():
    with pytest.raises(StorageError):
        data = get_data_str("s3://bucket/path/to/object")

@mock.patch.dict(os.environ, {"ROK4_S3_URL": "a", "ROK4_S3_SECRETKEY": "b", "ROK4_S3_KEY": "c"}, clear=True)
@mock.patch('rok4.Storage.boto3.client')
def test_s3_invalid_endpoint(mocked_s3_client):
    s3_instance = MagicMock()
    mocked_s3_client.side_effect = Exception('Invalid URL')
    with pytest.raises(StorageError):
        data = get_data_str("s3://bucket/path/to/object")


@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch("builtins.open", side_effect=FileNotFoundError("not_found"))
def test_file_read_error(mock_file):
    with pytest.raises(FileNotFoundError):
        data = get_data_str("file:///path/to/file.ext")
    
    mock_file.assert_called_with("/path/to/file.ext", "rb")


@mock.patch.dict(os.environ, {}, clear=True)
@patch("builtins.open", new_callable=mock_open, read_data=b"data")
def test_file_read_ok(mock_file):
    try:
        data = get_data_str("file:///path/to/file.ext")
        mock_file.assert_called_with("/path/to/file.ext", "rb")
        assert data == "data"
    except Exception as exc:
        assert False, f"FILE read raises an exception: {exc}"

@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_s3_read_nok(mocked_s3_client):
    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.get_object.side_effect = Exception('Bucket or object not found')
    mocked_s3_client.return_value = s3_instance
    with pytest.raises(StorageError):
        data = get_data_str("s3://bucket/path/to/object")

@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_s3_read_ok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_body = MagicMock()
    s3_body.read.return_value = b"data"
    s3_instance.get_object.return_value = {
        "Body": s3_body
    }
    mocked_s3_client.return_value = s3_instance

    try:
        data = get_data_str("s3://bucket/path/to/object")
        assert data == "data"
    except Exception as exc:
        assert False, f"S3 read raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_CEPH_CONFFILE": "a", "ROK4_CEPH_CLUSTERNAME": "b", "ROK4_CEPH_USERNAME": "c"}, clear=True)  
@mock.patch('rok4.Storage.rados.Rados')
def test_ceph_read_ok(mocked_rados_client):

    disconnect_ceph_clients()
    ioctx_instance = MagicMock()
    ioctx_instance.stat.return_value = (4, "date")
    ioctx_instance.read.return_value = b"data"
    ceph_instance = MagicMock()
    ceph_instance.open_ioctx.return_value = ioctx_instance
    mocked_rados_client.return_value = ceph_instance

    try:
        data = get_data_str("ceph://pool/path/to/object")
        assert data == "data"
    except Exception as exc:
        assert False, f"CEPH read raises an exception: {exc}"


############ put_data_str

@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_s3_write_nok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.put_object.side_effect = Exception('Cannot write S3 object')
    mocked_s3_client.return_value = s3_instance

    with pytest.raises(StorageError):
        put_data_str("data", "s3://bucket/path/to/object")


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_s3_write_ok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.put_object.return_value = None
    mocked_s3_client.return_value = s3_instance
    try:
        put_data_str("data", "s3://bucket/path/to/object")
    except Exception as exc:
        assert False, f"S3 write raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_CEPH_CONFFILE": "a", "ROK4_CEPH_CLUSTERNAME": "b", "ROK4_CEPH_USERNAME": "c"}, clear=True)  
@mock.patch('rok4.Storage.rados.Rados')
def test_ceph_write_ok(mocked_rados_client):

    disconnect_ceph_clients()
    ioctx_instance = MagicMock()
    ioctx_instance.write_full.return_value = None
    ceph_instance = MagicMock()
    ceph_instance.open_ioctx.return_value = ioctx_instance
    mocked_rados_client.return_value = ceph_instance

    try:
        put_data_str("data", "ceph://pool/path/to/object")
    except Exception as exc:
        assert False, f"CEPH write raises an exception: {exc}"

############ copy

@mock.patch.dict(os.environ, {}, clear=True)
@mock.patch('os.makedirs', return_value=None)
@mock.patch('rok4.Storage.copyfile', return_value=None)
@mock.patch('rok4.Storage.hash_file', return_value="toto")
def test_copy_file_file_ok(mock_hash_file, mock_copyfile, mock_makedirs):
    try:
        copy("file:///path/to/source.ext", "file:///path/to/destination.ext", "toto")
        mock_copyfile.assert_called_once_with("/path/to/source.ext", "/path/to/destination.ext")
        mock_hash_file.assert_called_once_with("/path/to/destination.ext")
        mock_makedirs.assert_called_once_with("/path/to", exist_ok=True)
    except Exception as exc:
        assert False, f"FILE -> FILE copy raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
@mock.patch('os.makedirs', return_value=None)
@mock.patch('rok4.Storage.hash_file', return_value="toto")
def test_copy_s3_file_ok(mock_hash_file, mock_makedirs, mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.download_file.return_value = None
    mocked_s3_client.return_value = s3_instance

    try:

        copy("s3://bucket/source.ext", "file:///path/to/destination.ext", "toto")
        mock_hash_file.assert_called_once_with("/path/to/destination.ext")
        mock_makedirs.assert_called_once_with("/path/to", exist_ok=True)
    except Exception as exc:
        assert False, f"S3 -> FILE copy raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
@mock.patch('os.makedirs', return_value=None)
@mock.patch('rok4.Storage.hash_file', return_value="toto")
def test_copy_s3_file_nok(mock_hash_file, mock_makedirs, mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.download_file.side_effect = Exception('Cannot download S3 object')
    mocked_s3_client.return_value = s3_instance

    with pytest.raises(StorageError):
        copy("s3://bucket/source.ext", "file:///path/to/destination.ext", "toto")
        mock_makedirs.assert_called_once_with("/path/to", exist_ok=True)


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_copy_file_s3_ok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.upload_file.return_value = None
    s3_instance.head_object.return_value = {"ETag": "toto"}
    mocked_s3_client.return_value = s3_instance

    try:
        copy("file:///path/to/source.ext", "s3://bucket/destination.ext", "toto")
    except Exception as exc:
        assert False, f"FILE -> S3 copy raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_copy_s3_s3_ok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.copy.return_value = None
    s3_instance.head_object.return_value = {"ETag": "toto"}
    mocked_s3_client.return_value = s3_instance

    try:
        copy("s3://bucket/source.ext", "s3://bucket/destination.ext", "toto")
    except Exception as exc:
        assert False, f"S3 -> S3 copy raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_copy_s3_s3_intercluster_ok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.copy.return_value = None
    s3_instance.head_object.return_value = {"ETag": "toto"}
    mocked_s3_client.return_value = s3_instance

    try:
        copy("s3://bucket@a/source.ext", "s3://bucket@b/destination.ext", "toto")
    except Exception as exc:
        assert False, f"S3 -> S3 inter cluster copy raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_copy_s3_s3_intercluster_nok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.copy.return_value = None
    s3_instance.head_object.return_value = {"ETag": "toto"}
    mocked_s3_client.return_value = s3_instance

    with pytest.raises(StorageError):
        copy("s3://bucket@a/source.ext", "s3://bucket@c/destination.ext", "toto")

@mock.patch.dict(os.environ, {"ROK4_CEPH_CONFFILE": "a", "ROK4_CEPH_CLUSTERNAME": "b", "ROK4_CEPH_USERNAME": "c"}, clear=True)  
@mock.patch('rok4.Storage.rados.Rados')
@mock.patch('os.makedirs', return_value=None)
@patch("builtins.open", new_callable=mock_open)
def test_copy_ceph_file_ok(mock_file, mock_makedirs, mocked_rados_client):

    disconnect_ceph_clients()
    ioctx_instance = MagicMock()
    ioctx_instance.read.return_value = b"data"
    ceph_instance = MagicMock()
    ceph_instance.open_ioctx.return_value = ioctx_instance
    mocked_rados_client.return_value = ceph_instance

    try:
        copy("ceph://pool/source.ext", "file:///path/to/destination.ext", "8d777f385d3dfec8815d20f7496026dc")
        mock_makedirs.assert_called_once_with("/path/to", exist_ok=True)
    except Exception as exc:
        assert False, f"CEPH -> FILE copy raises an exception: {exc}"

@mock.patch.dict(os.environ, {"ROK4_CEPH_CONFFILE": "a", "ROK4_CEPH_CLUSTERNAME": "b", "ROK4_CEPH_USERNAME": "c"}, clear=True)  
@mock.patch('rok4.Storage.rados.Rados')
@patch("builtins.open", new_callable=mock_open, read_data=b"data")
def test_copy_file_ceph_ok(mock_file, mocked_rados_client):

    disconnect_ceph_clients()
    ioctx_instance = MagicMock()
    ioctx_instance.write.return_value = None
    ceph_instance = MagicMock()
    ceph_instance.open_ioctx.return_value = ioctx_instance
    mocked_rados_client.return_value = ceph_instance

    try:
        copy("file:///path/to/source.ext", "ceph://pool/destination.ext", "8d777f385d3dfec8815d20f7496026dc")
    except Exception as exc:
        assert False, f"FILE -> CEPH copy raises an exception: {exc}"

@mock.patch.dict(os.environ, {"ROK4_CEPH_CONFFILE": "a", "ROK4_CEPH_CLUSTERNAME": "b", "ROK4_CEPH_USERNAME": "c"}, clear=True)  
@mock.patch('rok4.Storage.rados.Rados')
@patch("builtins.open", new_callable=mock_open, read_data=b"data")
def test_copy_ceph_ceph_ok(mock_file, mocked_rados_client):

    disconnect_ceph_clients()
    ioctx_instance = MagicMock()
    ioctx_instance.read.return_value = b"data"
    ioctx_instance.write.return_value = None
    ceph_instance = MagicMock()
    ceph_instance.open_ioctx.return_value = ioctx_instance
    mocked_rados_client.return_value = ceph_instance

    try:
        copy("ceph://pool1/source.ext", "ceph://pool2/destination.ext", "8d777f385d3dfec8815d20f7496026dc")
    except Exception as exc:
        assert False, f"CEPH -> CEPH copy raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_CEPH_CONFFILE": "a", "ROK4_CEPH_CLUSTERNAME": "b", "ROK4_CEPH_USERNAME": "c", "ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.rados.Rados')
@mock.patch('rok4.Storage.boto3.client')
@patch("builtins.open", new_callable=mock_open, read_data=b"data")
def test_copy_ceph_s3_ok(mock_file, mocked_s3_client, mocked_rados_client):

    disconnect_ceph_clients()
    ioctx_instance = MagicMock()
    ioctx_instance.read.return_value = b"data"
    ceph_instance = MagicMock()
    ceph_instance.open_ioctx.return_value = ioctx_instance
    mocked_rados_client.return_value = ceph_instance


    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.upload_file.return_value = None
    s3_instance.head_object.return_value = {"ETag": "8d777f385d3dfec8815d20f7496026dc"}
    mocked_s3_client.return_value = s3_instance

    try:
        copy("ceph://pool1/source.ext", "s3://bucket/destination.ext", "8d777f385d3dfec8815d20f7496026dc")
    except Exception as exc:
        assert False, f"CEPH -> S3 copy raises an exception: {exc}"



############ link

def test_link_type_nok():
    with pytest.raises(StorageError):
        link("ceph://pool1/target.ext", "file:///path/to/link.ext")

def test_link_hard_nok():
    with pytest.raises(StorageError):
        link("ceph://pool1/source.ext", "ceph://pool2/destination.ext", True)

@mock.patch.dict(os.environ, {}, clear=True)  
@mock.patch('os.symlink', return_value=None)
def test_link_file_ok(mock_link):
    try:
        link("file:///path/to/target.ext", "file:///path/to/link.ext")
        mock_link.assert_called_once_with("/path/to/target.ext", "/path/to/link.ext")
    except Exception as exc:
        assert False, f"FILE link raises an exception: {exc}"


@mock.patch.dict(os.environ, {}, clear=True)  
@mock.patch('os.link', return_value=None)
def test_hlink_file_ok(mock_link):
    try:
        link("file:///path/to/target.ext", "file:///path/to/link.ext", True)
        mock_link.assert_called_once_with("/path/to/target.ext", "/path/to/link.ext")
    except Exception as exc:
        assert False, f"FILE hard link raises an exception: {exc}"

@mock.patch.dict(os.environ, {"ROK4_CEPH_CONFFILE": "a", "ROK4_CEPH_CLUSTERNAME": "b", "ROK4_CEPH_USERNAME": "c"}, clear=True)  
@mock.patch('rok4.Storage.rados.Rados')
def test_link_ceph_ok(mocked_rados_client):

    disconnect_ceph_clients()
    ioctx_instance = MagicMock()
    ioctx_instance.write.return_value = None
    ceph_instance = MagicMock()
    ceph_instance.open_ioctx.return_value = ioctx_instance
    mocked_rados_client.return_value = ceph_instance

    try:
        link("ceph://pool1/target.ext", "ceph://pool2/link.ext")
    except Exception as exc:
        assert False, f"CEPH link raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_link_s3_ok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.put_object.return_value = None
    mocked_s3_client.return_value = s3_instance

    try:
        link("s3://bucket1/target.ext", "s3://bucket2/link.ext")
    except Exception as exc:
        assert False, f"S3 link raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_link_s3_nok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.put_object.return_value = None
    mocked_s3_client.return_value = s3_instance

    with pytest.raises(StorageError):
        link("s3://bucket1@a/target.ext", "s3://bucket2@b/link.ext")

############ get_size

@mock.patch.dict(os.environ, {}, clear=True)  
@mock.patch('os.stat')
def test_size_file_ok(mock_stat):
    mock_stat.return_value.st_size = 12
    try:
        size = get_size("file:///path/to/file.ext")
        assert size == 12
    except Exception as exc:
        assert False, f"FILE size raises an exception: {exc}"

@mock.patch.dict(os.environ, {"ROK4_CEPH_CONFFILE": "a", "ROK4_CEPH_CLUSTERNAME": "b", "ROK4_CEPH_USERNAME": "c"}, clear=True)  
@mock.patch('rok4.Storage.rados.Rados')
def test_size_ceph_ok(mocked_rados_client):

    disconnect_ceph_clients()
    ioctx_instance = MagicMock()
    ioctx_instance.stat.return_value = (12, "date")
    ceph_instance = MagicMock()
    ceph_instance.open_ioctx.return_value = ioctx_instance
    mocked_rados_client.return_value = ceph_instance

    try:
        size = get_size("ceph://pool/object.ext")
        assert size == 12
    except Exception as exc:
        assert False, f"CEPH size raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_size_s3_ok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.head_object.return_value = {"ContentLength": '"12"'}
    mocked_s3_client.return_value = s3_instance

    try:
        size = get_size("s3://bucket/object.ext")
        assert size == 12
    except Exception as exc:
        assert False, f"S3 size raises an exception: {exc}"


############ exists

@mock.patch.dict(os.environ, {}, clear=True)  
@mock.patch('os.path.exists', return_value=True)
def test_exists_file_ok(mock_exists):
    try:
        assert exists("file:///path/to/file.ext")
    except Exception as exc:
        assert False, f"FILE exists raises an exception: {exc}"

    mock_exists.return_value = False
    try:
        assert not exists("file:///path/to/file.ext")
    except Exception as exc:
        assert False, f"FILE not exists raises an exception: {exc}"

@mock.patch.dict(os.environ, {"ROK4_CEPH_CONFFILE": "a", "ROK4_CEPH_CLUSTERNAME": "b", "ROK4_CEPH_USERNAME": "c"}, clear=True)  
@mock.patch('rok4.Storage.rados.Rados')
def test_exists_ceph_ok(mocked_rados_client):

    disconnect_ceph_clients()
    ioctx_instance = MagicMock()
    ioctx_instance.stat.return_value = None
    ceph_instance = MagicMock()
    ceph_instance.open_ioctx.return_value = ioctx_instance
    mocked_rados_client.return_value = ceph_instance

    try:
        assert exists("ceph://pool/object.ext")
    except Exception as exc:
        assert False, f"CEPH exists raises an exception: {exc}"

    ioctx_instance.stat.side_effect = rados.ObjectNotFound("error")
    try:
        assert not exists("ceph://pool/object.ext")
    except Exception as exc:
        assert False, f"CEPH not exists raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_exists_s3_ok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.head_object.return_value = None
    mocked_s3_client.return_value = s3_instance

    try:
        assert exists("s3://bucket/object.ext")
    except Exception as exc:
        assert False, f"S3 exists raises an exception: {exc}"

    s3_instance.head_object.side_effect = botocore.exceptions.ClientError(operation_name='InvalidKeyPair.Duplicate', error_response={"Error": {"Code": "404"}})
    try:
        assert not exists("s3://bucket/object.ext")
    except Exception as exc:
        assert False, f"CEPH not exists raises an exception: {exc}"


############ remove

@mock.patch.dict(os.environ, {}, clear=True)  
@mock.patch('os.remove')
def test_remove_file_ok(mock_remove):
    mock_remove.return_value = None
    try:
        remove("file:///path/to/file.ext")
    except Exception as exc:
        assert False, f"FILE deletion raises an exception: {exc}"

    mock_remove.side_effect = FileNotFoundError("error")
    try:
        remove("file:///path/to/file.ext")
    except Exception as exc:
        assert False, f"FILE deletion (not found) raises an exception: {exc}"

@mock.patch.dict(os.environ, {"ROK4_CEPH_CONFFILE": "a", "ROK4_CEPH_CLUSTERNAME": "b", "ROK4_CEPH_USERNAME": "c"}, clear=True)  
@mock.patch('rok4.Storage.rados.Rados')
def test_remove_ceph_ok(mocked_rados_client):

    disconnect_ceph_clients()
    ioctx_instance = MagicMock()
    ioctx_instance.remove_object.return_value = None
    ceph_instance = MagicMock()
    ceph_instance.open_ioctx.return_value = ioctx_instance
    mocked_rados_client.return_value = ceph_instance

    try:
        remove("ceph://pool/object.ext")
    except Exception as exc:
        assert False, f"CEPH deletion raises an exception: {exc}"

    ioctx_instance.stat.side_effect = rados.ObjectNotFound("error")
    try:
        Exception("ceph://pool/object.ext")
    except Exception as exc:
        assert False, f"CEPH deletion (not found) raises an exception: {exc}"


@mock.patch.dict(os.environ, {"ROK4_S3_URL": "https://a,https://b", "ROK4_S3_SECRETKEY": "a,b", "ROK4_S3_KEY": "a,b"}, clear=True)  
@mock.patch('rok4.Storage.boto3.client')
def test_remove_s3_ok(mocked_s3_client):

    disconnect_s3_clients()
    s3_instance = MagicMock()
    s3_instance.delete_object.return_value = None
    mocked_s3_client.return_value = s3_instance

    try:
        remove("s3://bucket/object.ext")
    except Exception as exc:
        assert False, f"S3 deletion raises an exception: {exc}"