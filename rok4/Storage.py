"""Provide functions to use read or write

Available storage types are :
- S3 (path are preffixed with `s3://`)
- CEPH (path are preffixed with `ceph://`)
- FILE (path are preffixed with `file://`, but it is the default paths' interpretation)

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

import boto3
import botocore.exceptions
import tempfile
import re
import os
import rados
import hashlib
from typing import Dict, List, Tuple
from enum import Enum
from shutil import copyfile

from rok4.Exceptions import *

class StorageType(Enum):
    FILE = "file://"
    S3 = "s3://"
    CEPH = "ceph://"

__S3_CLIENTS = dict()
__S3_DEFAULT_CLIENT = None
def __get_s3_client(bucket_name: str) -> Tuple['boto3.client', str, str]:
    """Get the S3 client

    Create it if not already done

    Args:
        bucket_name (str): S3 bucket name. Could be just the bucket name, or <bucket name>@<cluster host>

    Raises:
        MissingEnvironmentError: Missing S3 storage informations
        StorageError: S3 client configuration issue

    Returns:
        Tuple['boto3.client', str, str]: the S3 client, the cluster host and the simple bucket name
    """    
    global __S3_CLIENTS, __S3_DEFAULT_CLIENT

    if not __S3_CLIENTS:
        # C'est la première fois qu'on cherche à utiliser le stockage S3, chargeons les informations depuis les variables d'environnement
        try:
            keys = os.environ["ROK4_S3_KEY"].split(",")
            secret_keys = os.environ["ROK4_S3_SECRETKEY"].split(",")
            urls = os.environ["ROK4_S3_URL"].split(",")

            if len(keys) != len(secret_keys) or len(keys) != len(urls):
                raise StorageError("S3", "S3 informations in environment variables are inconsistent : same number of element in each list is required")

            for i in range(len(keys)):

                h = re.sub("https?://", "", urls[i])

                if urls[i] in __S3_CLIENTS:
                    raise StorageError("S3", "A S3 cluster is defined twice (based on URL)")

                __S3_CLIENTS[h] = boto3.client(
                    's3',
                    aws_access_key_id = keys[i],
                    aws_secret_access_key = secret_keys[i],
                    endpoint_url = urls[i]
                )

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

    return __S3_CLIENTS[host], host, bucket_name

def disconnect_s3_clients() -> None:
    """Clean S3 clients
    """    
    global __S3_CLIENTS, __S3_DEFAULT_CLIENT
    __S3_CLIENTS = dict()
    __S3_DEFAULT_CLIENT = None

__CEPH_CLIENT = None
__CEPH_IOCTXS = dict()
def __get_ceph_ioctx(pool: str) -> 'rados.Ioctx':
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
                conffile = os.environ["ROK4_CEPH_CONFFILE"],
                clustername = os.environ["ROK4_CEPH_CLUSTERNAME"],
                name = os.environ["ROK4_CEPH_USERNAME"]
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
    """Clean CEPH clients
    """    
    global __CEPH_CLIENT, __CEPH_IOCTXS
    __CEPH_CLIENT = None
    __CEPH_IOCTXS = dict()

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

    with open(path,'rb') as file:
        chunk = 0
        while chunk != b'':
            chunk = file.read(65536)
            checker.update(chunk)

    return checker.hexdigest()

def get_data_str(path: str) -> str:
    """Load data into a string

    Args:
        path (str): path to data

    Raises:
        MissingEnvironmentError: Missing object storage informations
        StorageError: Storage read issue

    Returns:
        str: Data content
    """

    storage_type, path, tray_name, base_name  = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        
        s3_client, host, tray_name = __get_s3_client(tray_name)

        try:
            with tempfile.NamedTemporaryFile("w+b") as f:
                s3_client.download_fileobj(tray_name, base_name, f)
                f.seek(0)
                data = f.read().decode('utf-8')
                f.close()
        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:
        
        ioctx = __get_ceph_ioctx(tray_name)

        try:
            size, mtime = ioctx.stat(base_name)
            data = ioctx.read(base_name, size).decode('utf-8')
        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:

        try:
            f = open(path)
            data = f.read()
            f.close()
        except Exception as e:
            raise StorageError("FILE", e)

    else:
        raise StorageError("UNKNOWN", "Unhandled storage type to read string data")

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

    storage_type, path, tray_name, base_name  = get_infos_from_path(path)

    if storage_type == StorageType.S3:
        
        s3_client, host, tray_name = __get_s3_client(tray_name)

        try:
            s3_client.put_object(
                Body = data.encode('utf-8'),
                Bucket = tray_name,
                Key = base_name
            )
        except Exception as e:
            raise StorageError("S3", e)

    elif storage_type == StorageType.CEPH:
        
        ioctx = __get_ceph_ioctx(tray_name)

        try:
            ioctx.write_full(base_name, data.encode('utf-8'))
        except Exception as e:
            raise StorageError("CEPH", e)

    elif storage_type == StorageType.FILE:

        try:
            f = open(path, 'w')
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

    storage_type, path, tray_name, base_name  = get_infos_from_path(path)

    if storage_type == StorageType.S3:

        s3_client, host, tray_name = __get_s3_client(tray_name)

        try:
            size = s3_client.head_object(Bucket=tray_name, Key=base_name)["ContentLength"].strip('"')
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

    storage_type, path, tray_name, base_name  = get_infos_from_path(path)

    if storage_type == StorageType.S3:

        s3_client, host, tray_name = __get_s3_client(tray_name)

        try:
            s3_client.head_object(Bucket=tray_name, Key=base_name)
            return True
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == "404":
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
    storage_type, path, tray_name, base_name  = get_infos_from_path(path)

    if storage_type == StorageType.S3:

        s3_client, host, tray_name = __get_s3_client(tray_name)

        try:
            s3_client.delete_object(
                Bucket=tray_name,
                Key=base_name
            )
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

    from_type, from_path, from_tray, from_base_name  = get_infos_from_path(from_path)
    to_type, to_path, to_tray, to_base_name  = get_infos_from_path(to_path)

    # Réalisation de la copie, selon les types de stockage
    if from_type == StorageType.FILE and to_type == StorageType.FILE :
        
        try:
            if to_tray != "":
                os.makedirs(to_tray, exist_ok=True)

            copyfile(from_path, to_path)

            if from_md5 is not None :
                to_md5 = hash_file(to_path)
                if to_md5 != from_md5:
                    raise StorageError(f"FILE", f"Invalid MD5 sum control for copy file {from_path} to {to_path} : {from_md5} != {to_md5}")

        except Exception as e:
            raise StorageError(f"FILE", f"Cannot copy file {from_path} to {to_path} : {e}")

    elif from_type == StorageType.S3 and to_type == StorageType.FILE :
        
        s3_client, host, from_tray = __get_s3_client(from_tray)

        try:
            if to_tray != "":
                os.makedirs(to_tray, exist_ok=True)
            
            s3_client.download_file(from_tray, from_base_name, to_path)

            if from_md5 is not None :
                to_md5 = hash_file(to_path)
                if to_md5 != from_md5:
                    raise StorageError("S3 and FILE", f"Invalid MD5 sum control for copy S3 object {from_path} to file {to_path} : {from_md5} != {to_md5}")

        except Exception as e:
            raise StorageError(f"S3 and FILE", f"Cannot copy S3 object {from_path} to file {to_path} : {e}")

    elif from_type == StorageType.FILE and to_type == StorageType.S3 :

        s3_client, host, to_tray = __get_s3_client(to_tray)
        
        try:
            s3_client.upload_file(from_path, to_tray, to_base_name)

            if from_md5 is not None :
                to_md5 = s3_client.head_object(Bucket=to_tray, Key=to_base_name)["ETag"].strip('"')
                if to_md5 != from_md5:
                    raise StorageError(f"FILE and S3", f"Invalid MD5 sum control for copy file {from_path} to S3 object {to_path} : {from_md5} != {to_md5}")
        except Exception as e:
            raise StorageError(f"FILE and S3", f"Cannot copy file {from_path} to S3 object {to_path} : {e}")

    elif from_type == StorageType.S3 and to_type == StorageType.S3 :

        from_s3_client, from_host, from_tray = __get_s3_client(from_tray)
        to_s3_client, to_host, to_tray = __get_s3_client(to_tray)

        try:
            if to_host == from_host:
                to_s3_client.copy(
                    {
                        'Bucket': from_tray,
                        'Key': from_base_name
                    }, 
                    to_tray, to_base_name
                )
            else:
                with tempfile.NamedTemporaryFile("w+b") as f:
                    from_s3_client.download_fileobj(from_tray, from_base_name, f)
                    to_s3_client.upload_file(f.name, to_tray, to_base_name)

            if from_md5 is not None :
                to_md5 = to_s3_client.head_object(Bucket=to_tray, Key=to_base_name)["ETag"].strip('"')
                if to_md5 != from_md5:
                    raise StorageError(f"S3", f"Invalid MD5 sum control for copy S3 object {from_path} to {to_path} : {from_md5} != {to_md5}")

        except Exception as e:
            raise StorageError(f"S3", f"Cannot copy S3 object {from_path} to {to_path} : {e}")
        

    elif from_type == StorageType.CEPH and to_type == StorageType.FILE :

        ioctx = __get_ceph_ioctx(from_tray)

        if from_md5 is not None:
            checker = hashlib.md5()

        try:

            if to_tray != "":
                os.makedirs(to_tray, exist_ok=True)
            f = open(to_path, 'wb')

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
                raise StorageError(f"CEPH and FILE", f"Invalid MD5 sum control for copy CEPH object {from_path} to file {to_path} : {from_md5} != {checker.hexdigest()}")

        except Exception as e:
            raise StorageError(f"CEPH and FILE", f"Cannot copy CEPH object {from_path} to file {to_path} : {e}")


    elif from_type == StorageType.FILE and to_type == StorageType.CEPH :

        ioctx = __get_ceph_ioctx(to_tray)
        
        if from_md5 is not None:
            checker = hashlib.md5()

        try:
            f = open(from_path, 'rb')

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
                raise StorageError(f"FILE and CEPH", f"Invalid MD5 sum control for copy file {from_path} to CEPH object {to_path} : {from_md5} != {checker.hexdigest()}")

        except Exception as e:
            raise StorageError(f"FILE and CEPH", f"Cannot copy file {from_path} to CEPH object {to_path} : {e}")


    elif from_type == StorageType.CEPH and to_type == StorageType.CEPH :

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
                raise StorageError(f"FILE and CEPH", f"Invalid MD5 sum control for copy CEPH object {from_path} to {to_path} : {from_md5} != {checker.hexdigest()}")

        except Exception as e:
            raise StorageError(f"CEPH", f"Cannot copy CEPH object {from_path} to {to_path} : {e}")



    elif from_type == StorageType.CEPH and to_type == StorageType.S3 :

        from_ioctx = __get_ceph_ioctx(from_tray)

        to_s3_client, to_host, to_tray = __get_s3_client(to_tray)

        try:

            offset = 0
            size = 0

            with tempfile.NamedTemporaryFile("w+b") as f:
                while True:
                    chunk = from_ioctx.read(from_base_name, 65536, offset)
                    size = len(chunk)
                    offset += size
                    f.write(chunk)

                    if size < 65536:
                        break
                
                to_s3_client.upload_file(f.name, to_tray, to_base_name)

            if from_md5 is not None :
                to_md5 = to_s3_client.head_object(Bucket=to_tray, Key=to_base_name)["ETag"].strip('"')
                if to_md5 != from_md5:
                    raise StorageError(f"CEPH and S3", f"Invalid MD5 sum control for copy CEPH object {from_path} to S3 object {to_path} : {from_md5} != {to_md5}")

        except Exception as e:
            raise StorageError(f"CEPH", f"Cannot copy CEPH object {from_path} to S3 object {to_path} : {e}")

    else:
        raise StorageError(f"{from_type.name} and {to_type.name}", f"Cannot copy from {from_type.name} to {to_type.name}")



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

    target_type, target_path, target_tray, target_base_name  = get_infos_from_path(target_path)
    link_type, link_path, link_tray, link_base_name  = get_infos_from_path(link_path)

    if target_type != link_type:
        raise StorageError(f"{target_type.name} and {link_type.name}", f"Cannot make link between two different storage types")

    if hard and target_type != StorageType.FILE:
        raise StorageError(target_type.name, "Hard link is available only for FILE storage")

    # Réalisation du lien, selon les types de stockage
    if target_type == StorageType.S3:

        target_s3_client, target_host, target_tray = __get_s3_client(target_tray)
        link_s3_client, link_host, link_tray = __get_s3_client(link_tray)

        if link_host != target_host:
            raise StorageError(f"S3", f"Cannot make link {link_path} -> {target_path} : link works only on the same S3 cluster")

        try:
            target_s3_client.put_object(
                Body = f"{__OBJECT_SYMLINK_SIGNATURE}{target_tray}/{target_base_name}".encode('utf-8'),
                Bucket = link_tray,
                Key = link_base_name
            )
        except Exception as e:
            raise StorageError("S3", e)

    elif target_type == StorageType.CEPH:
        
        ioctx = __get_ceph_ioctx(link_tray)

        try:
            ioctx.write_full(link_base_name, f"{__OBJECT_SYMLINK_SIGNATURE}{target_path}".encode('utf-8'))
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
