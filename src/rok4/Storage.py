"""Provide functions to use read or write

Available storage types are :
- S3 (path are preffixed with `s3://`)
- CEPH (path are prefixed with `ceph://`)
- FILE (path are prefixed with `file://`, but it is the default paths' interpretation)
- HTTP (path are prefixed with `http://`)
- HTTPS (path are prefixed with `https://`)

According to functions, all storage types are not necessarily available.

Using CEPH storage requires environment variables :
- ROK4_CEPH_CONFFILE
- ROK4_CEPH_USERNAME
- ROK4_CEPH_CLUSTERNAME

Using S3 storage requires environment variables :
- ROK4_S3_KEY
- ROK4_S3_SECRETKEY
- ROK4_S3_URL

To use several S3 clusters, each environment variable have to contain a list (comma-separated), with the same number of elements

Example: work with 2 S3 clusters:

- ROK4_S3_KEY=KEY1,KEY2
- ROK4_S3_SECRETKEY=SKEY1,SKEY2
- ROK4_S3_URL=https://s3.storage.fr,https://s4.storage.fr

To precise the cluster to use, bucket name should be bucket_name@s3.storage.fr or bucket_name@s4.storage.fr. If no host is defined (no @) in the bucket name, first S3 cluster is used
"""

import hashlib
import os
import re
import tempfile
from enum import Enum
from shutil import copyfile
from typing import Dict, List, Tuple, Union

import boto3
import botocore.exceptions
import rados
import requests
from osgeo import gdal

gdal.UseExceptions()

from rok4.Exceptions import *


class StorageType(Enum):
    FILE = "file://"
    S3 = "s3://"
    CEPH = "ceph://"
    HTTP = "http://"
    HTTPS = "https://"


__S3_CLIENTS = {}
__S3_DEFAULT_CLIENT = None


def __get_s3_client(bucket_name: str) -> Tuple[Dict[str, Union["boto3.client", str]], str, str]:
    """Get the S3 client

    Create it if not already done

    Args:
        bucket_name (str): S3 bucket name. Could be just the bucket name, or <bucket name>@<cluster host>

    Raises:
        MissingEnvironmentError: Missing S3 storage informations
        StorageError: S3 client configuration issue

    Returns:
        Tuple[Dict[str, Union['boto3.client',str]], str, str]: the S3 informations (client, host, key, secret) and the simple bucket name
    """

    global __S3_CLIENTS, __S3_DEFAULT_CLIENT

    if not __S3_CLIENTS:
        # C'est la première fois qu'on cherche à utiliser le stockage S3, chargeons les informations depuis les variables d'environnement
        try:
            keys = os.environ["ROK4_S3_KEY"].split(",")
            secret_keys = os.environ["ROK4_S3_SECRETKEY"].split(",")
            urls = os.environ["ROK4_S3_URL"].split(",")

            if len(keys) != len(secret_keys) or len(keys) != len(urls):
                raise StorageError(
                    "S3",
                    "S3 informations in environment variables are inconsistent : same number of element in each list is required",
                )

            for i in range(len(keys)):
                h = re.sub("https?://", "", urls[i])

                if h in __S3_CLIENTS:
                    raise StorageError("S3", "A S3 cluster is defined twice (based on URL)")

                __S3_CLIENTS[h] = {
                    "client": boto3.client(
                        "s3",
                        aws_access_key_id=keys[i],
                        aws_secret_access_key=secret_keys[i],
                        endpoint_url=urls[i],
                    ),
                    "key": keys[i],
                    "secret_key": secret_keys[i],
                    "url": urls[i],
                    "host": h,
                }

                if i == 0:
                    # Le premier cluster est celui par défaut
                    __S3_DEFAULT_CLIENT = h

        except KeyError as e:
            raise MissingEnvironmentError(e)
        except Exception as e:
            raise StorageError("S3", e)

    try:
        host = bucket_name.split("@")[1]
    except IndexError:
        host = __S3_DEFAULT_CLIENT

    bucket_name = bucket_name.split("@")[0]

    if host not in __S3_CLIENTS:
        raise StorageError("S3", f"Unknown S3 cluster, according to host '{host}'")

    return __S3_CLIENTS[host], bucket_name


def disconnect_s3_clients() -> None:
    """Clean S3 clients"""

    global __S3_CLIENTS, __S3_DEFAULT_CLIENT
    __S3_CLIENTS = {}
    __S3_DEFAULT_CLIENT = None


__CEPH_CLIENT = None
__CEPH_IOCTXS = {}


def __get_ceph_ioctx(pool: str) -> "rados.Ioctx":
    """Get the CEPH IO context

    Create it (client and context) if not already done

    Args:
        pool (str): CEPH pool's name

    Raises:
        MissingEnvironmentError: Missing CEPH storage informations
        StorageError: CEPH IO context configuration issue

    Returns:
        rados.Ioctx: IO ceph context
    """
    global __CEPH_CLIENT, __CEPH_IOCTXS

    if __CEPH_CLIENT is None:
        try:
            __CEPH_CLIENT = rados.Rados(
                conffile=os.environ["ROK4_CEPH_CONFFILE"],
                clustername=os.environ["ROK4_CEPH_CLUSTERNAME"],
                name=os.environ["ROK4_CEPH_USERNAME"],
            )

            __CEPH_CLIENT.connect()

        except KeyError as e:
            raise MissingEnvironmentError(e)
        except Exception as e:
            raise StorageError("CEPH", e)

    if pool not in __CEPH_IOCTXS:
        try:
            __CEPH_IOCTXS[pool] = __CEPH_CLIENT.open_ioctx(pool)
        except Exception as e:
            raise StorageError("CEPH", e)

    return __CEPH_IOCTXS[pool]


def disconnect_ceph_clients() -> None:
    """Clean CEPH clients"""
    global __CEPH_CLIENT, __CEPH_IOCTXS
    __CEPH_CLIENT = None
    __CEPH_IOCTXS = {}


__OBJECT_SYMLINK_SIGNATURE = "SYMLINK#"


def get_infos_from_path(path: str) -> Tuple[StorageType, str, str, str]:
    """Extract storage type, the unprefixed path, the container and the basename from path (Default: FILE storage)

    For a FILE storage, the tray is the directory and the basename is the file name.

    For an object storage (CEPH or S3), the tray is the bucket or the pool and the basename is the object name.
    For a S3 bucket, format can be <bucket name>@<cluster name> to use several clusters. Cluster name is the host (without protocol)

    Args:
        path (str): path to analyse

    Returns:
        Tuple[StorageType, str, str, str]: storage type, unprefixed path, the container and the basename
    """

    if path.startswith("s3://"):
        bucket_name, object_name = path[5:].split("/", 1)
        return StorageType.S3, path[5:], bucket_name, object_name
    elif path.startswith("ceph://"):
        pool_name, object_name = path[7:].split("/", 1)
        return StorageType.CEPH, path[7:], pool_name, object_name
    elif path.startswith("file://"):
        return StorageType.FILE, path[7:], os.path.dirname(path[7:]), os.path.basename(path[7:])
    elif path.startswith("http://"):
        return StorageType.HTTP, path[7:], os.path.dirname(path[7:]), os.path.basename(path[7:])
    elif path.startswith("https://"):
        return StorageType.HTTPS, path[8:], os.path.dirname(path[8:]), os.path.basename(path[8:])
    else:
        return StorageType.FILE, path, os.path.dirname(path), os.path.basename(path)


def get_path_from_infos(storage_type: StorageType, *args) -> str:
    """Write full path from elements

    Prefixed wih storage's type, elements are joined with a slash

    Args:
        storage_type (StorageType): Storage's type for path

    Returns:
        str: Full path
    """
    return f"{storage_type.value}{os.path.join(*args)}"


def hash_file(path: str) -> str:
    """Process MD5 sum of the provided file

    Args:
        path (str): path to file

    Returns:
        str: hexadeimal MD5 sum
    """

    checker = hashlib.md5()

    with open(path, "rb") as file:
        chunk = 0
        while chunk != b"":
            chunk = file.read(65536)
            checker.update(chunk)

    return checker.hexdigest()


def get_data_str(path: str) -> str:
    """Load full data into a string

    Args:
        path (str): path to data

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage read issue
        FileNotFoundError: File or object does not exist

    Returns:
        str: Data content
    """

    return get_data_binary(path).decode("utf-8")


def get_data_binary(path: str, range: Tuple[int, int] = None) -> str:
    """Load data into a binary string

    Args:
        path (str): path to data
        range (Tuple[int, int], optional): offset and size, to make a partial read. Defaults to None.

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage read issue
        FileNotFoundError: File or object does not exist

    Returns:
        str: Data binary content
    """
    storage_type, path, tray_name, base_name = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        s3_client, bucket_name = __get_s3_client(tray_name)

        try:
            if range is None:
                data = (
                    s3_client["client"]
                    .get_object(
                        Bucket=bucket_name,
                        Key=base_name,
                    )["Body"]
                    .read()
                )
            else:
                data = (
                    s3_client["client"]
                    .get_object(
                        Bucket=bucket_name,
                        Key=base_name,
                        Range=f"bytes={range[0]}-{range[0] + range[1] - 1}",
                    )["Body"]
                    .read()
                )

        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                raise FileNotFoundError(f"{storage_type.value}{path}")
            else:
                raise StorageError("S3", e)

        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:
        ioctx = __get_ceph_ioctx(tray_name)

        try:
            if range is None:
                size, mtime = ioctx.stat(base_name)
                data = ioctx.read(base_name, size)
            else:
                data = ioctx.read(base_name, range[1], range[0])

        except rados.ObjectNotFound as e:
            raise FileNotFoundError(f"{storage_type.value}{path}")

        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:
        try:
            f = open(path, "rb")
            if range is None:
                data = f.read()
            else:
                f.seek(range[0])
                data = f.read(range[1])

            f.close()

        except FileNotFoundError as e:
            raise FileNotFoundError(f"{storage_type.value}{path}")

        except Exception as e:
            raise StorageError("FILE", e)

    elif storage_type == StorageType.HTTP or storage_type == StorageType.HTTPS:
        if range is None:
            try:
                reponse = requests.get(f"{storage_type.value}{path}", stream=True)
                data = reponse.content
                if reponse.status_code == 404:
                    raise FileNotFoundError(f"{storage_type.value}{path}")
            except Exception as e:
                raise StorageError(storage_type.name, e)
        else:
            raise NotImplementedError

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to read binary data")

    return data


def put_data_str(data: str, path: str) -> None:
    """Store string data into a file or an object

    UTF-8 encoding is used for bytes conversion

    Args:
        data (str): data to write
        path (str): destination path, where to write data

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage write issue
    """

    storage_type, path, tray_name, base_name = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        s3_client, bucket_name = __get_s3_client(tray_name)

        try:
            s3_client["client"].put_object(
                Body=data.encode("utf-8"), Bucket=bucket_name, Key=base_name
            )
        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:
        ioctx = __get_ceph_ioctx(tray_name)

        try:
            ioctx.write_full(base_name, data.encode("utf-8"))
        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:
        try:
            f = open(path, "w")
            f.write(data)
            f.close()
        except Exception as e:
            raise StorageError("FILE", e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to write string data")


def get_size(path: str) -> int:
    """Get size of file or object

    Args:
        path (str): path of file/object whom size is asked

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage read issue

    Returns:
        int: file/object size, in bytes
    """

    storage_type, path, tray_name, base_name = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        s3_client, bucket_name = __get_s3_client(tray_name)

        try:
            size = s3_client["client"].head_object(Bucket=bucket_name, Key=base_name)[
                "ContentLength"
            ]
            return int(size)
        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:
        ioctx = __get_ceph_ioctx(tray_name)

        try:
            size, mtime = ioctx.stat(base_name)
            return size
        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:
        try:
            file_stats = os.stat(path)
            return file_stats.st_size
        except Exception as e:
            raise StorageError("FILE", e)

    elif storage_type == StorageType.HTTP or storage_type == StorageType.HTTPS:
        try:
            # Le stream=True permet de ne télécharger que le header initialement
            reponse = requests.get(storage_type.value + path, stream=True).headers["content-length"]
            return reponse
        except Exception as e:
            raise StorageError(storage_type.name, e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to get size")


def exists(path: str) -> bool:
    """Do the file or object exist ?

    Args:
        path (str): path of file/object to test

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage read issue

    Returns:
        bool: file/object existing status
    """

    storage_type, path, tray_name, base_name = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        s3_client, bucket_name = __get_s3_client(tray_name)

        try:
            s3_client["client"].head_object(Bucket=bucket_name, Key=base_name)
            return True
        except botocore.exceptions.ClientError as e:
            if e.response["Error"]["Code"] == "404":
                return False
            else:
                raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:
        ioctx = __get_ceph_ioctx(tray_name)

        try:
            ioctx.stat(base_name)
            return True
        except rados.ObjectNotFound as e:
            return False
        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:
        return os.path.exists(path)

    elif storage_type == StorageType.HTTP or storage_type == StorageType.HTTPS:
        try:
            response = requests.get(storage_type.value + path, stream=True)
            if response.status_code == 200:
                return True
            else:
                return False
        except Exception as e:
            raise StorageError(storage_type.name, e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to test if exists")


def remove(path: str) -> None:
    """Remove the file/object

    Args:
        path (str): path of file/object to remove

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage removal issue
    """
    storage_type, path, tray_name, base_name = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        s3_client, bucket_name = __get_s3_client(tray_name)

        try:
            s3_client["client"].delete_object(Bucket=bucket_name, Key=base_name)
        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:
        ioctx = __get_ceph_ioctx(tray_name)

        try:
            ioctx.remove_object(base_name)
        except rados.ObjectNotFound as e:
            pass
        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:
        try:
            os.remove(path)
        except FileNotFoundError as e:
            pass
        except Exception as e:
            raise StorageError("FILE", e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to remove things")


def copy(from_path: str, to_path: str, from_md5: str = None) -> None:
    """Copy a file or object to a file or object place. If MD5 sum is provided, it is compared to sum after the copy.

    Args:
        from_path (str): source file/object path, to copy
        to_path (str): destination file/object path
        from_md5 (str, optional): MD5 sum, re-processed after copy and controlled. Defaults to None.

    Raises:
        StorageError: Unhandled copy or copy issue
        MissingEnvironmentError: Missing object storage informations
    """

    from_type, from_path, from_tray, from_base_name = get_infos_from_path(from_path)
    to_type, to_path, to_tray, to_base_name = get_infos_from_path(to_path)

    # Réalisation de la copie, selon les types de stockage
    if from_type == StorageType.FILE and to_type == StorageType.FILE:
        try:
            if to_tray != "":
                os.makedirs(to_tray, exist_ok=True)

            copyfile(from_path, to_path)

            if from_md5 is not None:
                to_md5 = hash_file(to_path)
                if to_md5 != from_md5:
                    raise StorageError(
                        f"FILE",
                        f"Invalid MD5 sum control for copy file {from_path} to {to_path} : {from_md5} != {to_md5}",
                    )

        except Exception as e:
            raise StorageError(f"FILE", f"Cannot copy file {from_path} to {to_path} : {e}")

    elif from_type == StorageType.S3 and to_type == StorageType.FILE:
        s3_client, from_bucket = __get_s3_client(from_tray)

        try:
            if to_tray != "":
                os.makedirs(to_tray, exist_ok=True)

            s3_client["client"].download_file(from_bucket, from_base_name, to_path)

            if from_md5 is not None:
                to_md5 = hash_file(to_path)
                if to_md5 != from_md5:
                    raise StorageError(
                        "S3 and FILE",
                        f"Invalid MD5 sum control for copy S3 object {from_path} to file {to_path} : {from_md5} != {to_md5}",
                    )

        except Exception as e:
            raise StorageError(
                f"S3 and FILE", f"Cannot copy S3 object {from_path} to file {to_path} : {e}"
            )

    elif from_type == StorageType.FILE and to_type == StorageType.S3:
        s3_client, to_bucket = __get_s3_client(to_tray)

        try:
            s3_client["client"].upload_file(from_path, to_bucket, to_base_name)

            if from_md5 is not None:
                to_md5 = (
                    s3_client["client"]
                    .head_object(Bucket=to_bucket, Key=to_base_name)["ETag"]
                    .strip('"')
                )
                if to_md5 != from_md5:
                    raise StorageError(
                        f"FILE and S3",
                        f"Invalid MD5 sum control for copy file {from_path} to S3 object {to_path} : {from_md5} != {to_md5}",
                    )
        except Exception as e:
            raise StorageError(
                f"FILE and S3", f"Cannot copy file {from_path} to S3 object {to_path} : {e}"
            )

    elif from_type == StorageType.S3 and to_type == StorageType.S3:
        from_s3_client, from_bucket = __get_s3_client(from_tray)
        to_s3_client, to_bucket = __get_s3_client(to_tray)

        try:
            if to_s3_client["host"] == from_s3_client["host"]:
                to_s3_client["client"].copy(
                    {"Bucket": from_bucket, "Key": from_base_name}, to_bucket, to_base_name
                )
            else:
                with tempfile.NamedTemporaryFile("w+b") as f:
                    from_s3_client["client"].download_fileobj(from_bucket, from_base_name, f)
                    to_s3_client["client"].upload_file(f.name, to_bucket, to_base_name)

            if from_md5 is not None:
                to_md5 = (
                    to_s3_client["client"]
                    .head_object(Bucket=to_bucket, Key=to_base_name)["ETag"]
                    .strip('"')
                )
                if to_md5 != from_md5:
                    raise StorageError(
                        f"S3",
                        f"Invalid MD5 sum control for copy S3 object {from_path} to {to_path} : {from_md5} != {to_md5}",
                    )

        except Exception as e:
            raise StorageError(f"S3", f"Cannot copy S3 object {from_path} to {to_path} : {e}")

    elif from_type == StorageType.CEPH and to_type == StorageType.FILE:
        ioctx = __get_ceph_ioctx(from_tray)

        if from_md5 is not None:
            checker = hashlib.md5()

        try:
            if to_tray != "":
                os.makedirs(to_tray, exist_ok=True)
            f = open(to_path, "wb")

            offset = 0
            size = 0

            while True:
                chunk = ioctx.read(from_base_name, 65536, offset)
                size = len(chunk)
                offset += size
                f.write(chunk)

                if from_md5 is not None:
                    checker.update(chunk)

                if size < 65536:
                    break

            f.close()

            if from_md5 is not None and from_md5 != checker.hexdigest():
                raise StorageError(
                    f"CEPH and FILE",
                    f"Invalid MD5 sum control for copy CEPH object {from_path} to file {to_path} : {from_md5} != {checker.hexdigest()}",
                )

        except Exception as e:
            raise StorageError(
                f"CEPH and FILE", f"Cannot copy CEPH object {from_path} to file {to_path} : {e}"
            )

    elif from_type == StorageType.FILE and to_type == StorageType.CEPH:
        ioctx = __get_ceph_ioctx(to_tray)

        if from_md5 is not None:
            checker = hashlib.md5()

        try:
            f = open(from_path, "rb")

            offset = 0
            size = 0

            while True:
                chunk = f.read(65536)
                size = len(chunk)
                ioctx.write(to_base_name, chunk, offset)
                offset += size

                if from_md5 is not None:
                    checker.update(chunk)

                if size < 65536:
                    break

            f.close()

            if from_md5 is not None and from_md5 != checker.hexdigest():
                raise StorageError(
                    f"FILE and CEPH",
                    f"Invalid MD5 sum control for copy file {from_path} to CEPH object {to_path} : {from_md5} != {checker.hexdigest()}",
                )

        except Exception as e:
            raise StorageError(
                f"FILE and CEPH", f"Cannot copy file {from_path} to CEPH object {to_path} : {e}"
            )

    elif from_type == StorageType.CEPH and to_type == StorageType.CEPH:
        from_ioctx = __get_ceph_ioctx(from_tray)
        to_ioctx = __get_ceph_ioctx(to_tray)

        if from_md5 is not None:
            checker = hashlib.md5()

        try:
            offset = 0
            size = 0

            while True:
                chunk = from_ioctx.read(from_base_name, 65536, offset)
                size = len(chunk)
                to_ioctx.write(to_base_name, chunk, offset)
                offset += size

                if from_md5 is not None:
                    checker.update(chunk)

                if size < 65536:
                    break

            if from_md5 is not None and from_md5 != checker.hexdigest():
                raise StorageError(
                    f"FILE and CEPH",
                    f"Invalid MD5 sum control for copy CEPH object {from_path} to {to_path} : {from_md5} != {checker.hexdigest()}",
                )

        except Exception as e:
            raise StorageError(f"CEPH", f"Cannot copy CEPH object {from_path} to {to_path} : {e}")

    elif from_type == StorageType.CEPH and to_type == StorageType.S3:
        from_ioctx = __get_ceph_ioctx(from_tray)

        s3_client, to_bucket = __get_s3_client(to_tray)

        if from_md5 is not None:
            checker = hashlib.md5()

        try:
            offset = 0
            size = 0

            with tempfile.NamedTemporaryFile("w+b", delete=False) as f:
                name_tmp = f.name
                while True:
                    chunk = from_ioctx.read(from_base_name, 65536, offset)
                    size = len(chunk)
                    offset += size
                    f.write(chunk)

                    if from_md5 is not None:
                        checker.update(chunk)

                    if size < 65536:
                        break

            s3_client["client"].upload_file(name_tmp, to_bucket, to_base_name)

            os.remove(name_tmp)

            if from_md5 is not None and from_md5 != checker.hexdigest():
                raise StorageError(
                    f"CEPH and S3",
                    f"Invalid MD5 sum control for copy CEPH object {from_path} to S3 object {to_path} : {from_md5} != {checker.hexdigest()}",
                )

        except Exception as e:
            raise StorageError(
                f"CEPH and S3", f"Cannot copy CEPH object {from_path} to S3 object {to_path} : {e}"
            )

    elif (
        from_type == StorageType.HTTP or from_type == StorageType.HTTPS
    ) and to_type == StorageType.FILE:
        try:
            response = requests.get(from_type.value + from_path, stream=True)
            with open(to_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)

        except Exception as e:
            raise StorageError(
                f"HTTP(S) and FILE",
                f"Cannot copy HTTP(S) object {from_path} to FILE object {to_path} : {e}",
            )

    elif (
        from_type == StorageType.HTTP or from_type == StorageType.HTTPS
    ) and to_type == StorageType.CEPH:
        to_ioctx = __get_ceph_ioctx(to_tray)

        try:
            response = requests.get(from_type.value + from_path, stream=True)
            offset = 0
            for chunk in response.iter_content(chunk_size=65536):
                if chunk:
                    size = len(chunk)
                    to_ioctx.write(to_base_name, chunk, offset)
                    offset += size

        except Exception as e:
            raise StorageError(
                f"HTTP(S) and CEPH",
                f"Cannot copy HTTP(S) object {from_path} to CEPH object {to_path} : {e}",
            )

    elif (
        from_type == StorageType.HTTP or from_type == StorageType.HTTPS
    ) and to_type == StorageType.S3:
        to_s3_client, to_bucket = __get_s3_client(to_tray)

        try:
            response = requests.get(from_type.value + from_path, stream=True)
            with tempfile.NamedTemporaryFile("w+b", delete=False) as f:
                name_fich = f.name
                for chunk in response.iter_content(chunk_size=65536):
                    if chunk:
                        f.write(chunk)

            to_s3_client["client"].upload_file(name_fich, to_tray, to_base_name)

            os.remove(name_fich)

        except Exception as e:
            raise StorageError(
                f"HTTP(S) and S3",
                f"Cannot copy HTTP(S) object {from_path} to S3 object {to_path} : {e}",
            )

    else:
        raise StorageError(
            f"{from_type.name} and {to_type.name}",
            f"Cannot copy from {from_type.name} to {to_type.name}",
        )


def link(target_path: str, link_path: str, hard: bool = False) -> None:
    """Create a symbolic link

    Args:
        target_path (str): file/object to link
        link_path (str): link to create
        hard (bool, optional): hard link rather than symbolic. Only for FILE storage. Defaults to False.

    Raises:
        StorageError: Unhandled link or link issue
        MissingEnvironmentError: Missing object storage informations
    """

    target_type, target_path, target_tray, target_base_name = get_infos_from_path(target_path)
    link_type, link_path, link_tray, link_base_name = get_infos_from_path(link_path)

    if target_type != link_type:
        raise StorageError(
            f"{target_type.name} and {link_type.name}",
            f"Cannot make link between two different storage types",
        )

    if hard and target_type != StorageType.FILE:
        raise StorageError(target_type.name, "Hard link is available only for FILE storage")

    # Réalisation du lien, selon les types de stockage
    if target_type == StorageType.S3:
        target_s3_client, target_bucket = __get_s3_client(target_tray)
        link_s3_client, link_bucket = __get_s3_client(link_tray)

        if target_s3_client["host"] != link_s3_client["host"]:
            raise StorageError(
                f"S3",
                f"Cannot make link {link_path} -> {target_path} : link works only on the same S3 cluster",
            )

        try:
            target_s3_client["client"].put_object(
                Body = f"{__OBJECT_SYMLINK_SIGNATURE}{target_bucket}/{target_base_name}".encode(),
                Bucket = link_bucket,
                Key = link_base_name
            )
        except Exception as e:
            raise StorageError("S3", e)

    elif target_type == StorageType.CEPH:
        ioctx = __get_ceph_ioctx(link_tray)

        try:
            ioctx.write_full(link_base_name, f"{__OBJECT_SYMLINK_SIGNATURE}{target_path}".encode())
        except Exception as e:
            raise StorageError("CEPH", e)

    elif target_type == StorageType.FILE:
        try:
            if hard:
                os.link(target_path, link_path)
            else:
                os.symlink(target_path, link_path)
        except Exception as e:
            raise StorageError("FILE", e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to make link")


def get_osgeo_path(path: str) -> str:
    """Return GDAL/OGR Open compliant path and configure storage access

    For a S3 input path, endpoint, access and secret keys are set and path is built with "/vsis3" root.

    For a FILE input path, only storage prefix is removed

    Args:
        path (str): Source path

    Raises:
        NotImplementedError: Storage type not handled

    Returns:
        str: GDAL/OGR Open compliant path
    """

    storage_type, unprefixed_path, tray_name, base_name = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        s3_client, bucket_name = __get_s3_client(tray_name)

        gdal.SetConfigOption("AWS_SECRET_ACCESS_KEY", s3_client["secret_key"])
        gdal.SetConfigOption("AWS_ACCESS_KEY_ID", s3_client["key"])
        gdal.SetConfigOption("AWS_S3_ENDPOINT", s3_client["host"])
        gdal.SetConfigOption("AWS_VIRTUAL_HOSTING", "FALSE")

        return f"/vsis3/{bucket_name}/{base_name}"

    elif storage_type == StorageType.FILE:
        return unprefixed_path

    else:
        raise NotImplementedError(f"Cannot get a GDAL/OGR compliant path from {path}")


def size_path(path: str) -> int:
    """Return the size of the path given (or, for the CEPH, the sum of the size of each object of the .list)

    Args:
        path (str): Source path

    Raises:
        StorageError: Unhandled link or link issue
        MissingEnvironmentError: Missing object storage informations

    Returns:
        int: size of the path
    """
    storage_type, unprefixed_path, tray_name, base_name = get_infos_from_path(path)

    if storage_type == StorageType.FILE:
        try:
            total = 0
            with os.scandir(unprefixed_path) as it:
                for entry in it:
                    if entry.is_file():
                        total += entry.stat().st_size
                    elif entry.is_dir():
                        total += size_path(entry.path)

        except Exception as e:
            raise StorageError("FILE", e)

    elif storage_type == StorageType.S3:
        s3_client, bucket_name = __get_s3_client(tray_name)

        try:
            paginator = s3_client["client"].get_paginator("list_objects_v2")
            pages = paginator.paginate(
                Bucket=bucket_name,
                Prefix=base_name + "/",
                PaginationConfig={
                    "PageSize": 10000,
                },
            )
            total = 0
            for page in pages:
                for key in page["Contents"]:
                    total += key["Size"]

        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:
        raise NotImplementedError
    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to calculate size")

    return total
