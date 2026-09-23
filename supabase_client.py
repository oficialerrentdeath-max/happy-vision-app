import os
import tempfile
from typing import Optional

# Import the initialized Supabase client from the database module
try:
    from database import supabase
except ImportError:
    supabase = None

# Bucket name from environment variables (as defined in .env)
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "happy-vision")

def _ensure_client() -> bool:
    """Check that Supabase client and bucket are configured."""
    return supabase is not None and SUPABASE_BUCKET is not None


def upload_image(local_path: str, remote_path: str) -> bool:
    """Upload a local file to Supabase Storage.

    Parameters
    ----------
    local_path: str
        Absolute path to the file on the local filesystem.
    remote_path: str
        Desired path inside the bucket (e.g., "logos/logo.png").

    Returns
    -------
    bool
        True if the upload succeeded, False otherwise.
    """
    if not _ensure_client():
        return False
    try:
        ext = os.path.splitext(local_path)[1].lower()
        content_type_map = {
            ".png": "image/png",
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".gif": "image/gif",
            ".webp": "image/webp",
        }
        content_type = content_type_map.get(ext, "image/png")

        with open(local_path, "rb") as f:
            data = f.read()

        # Delete first to avoid duplicate conflicts, then upload
        try:
            supabase.storage.from_(SUPABASE_BUCKET).remove([remote_path])
        except Exception:
            pass  # Ignorar si no existía

        res = supabase.storage.from_(SUPABASE_BUCKET).upload(
            remote_path,
            data,
            {"content-type": content_type, "upsert": "true"},
        )

        # SDK v1 returns an object, v2 may raise on error
        if hasattr(res, "get") and res.get("error"):
            print(f"[Supabase] Upload error: {res['error']}")
            return False
        return True
    except Exception as e:
        print(f"[Supabase] Exception during upload_image: {e}")
        return False


def upload_logo_sucursal(local_path: str, sucursal_nombre: str) -> Optional[str]:
    """Sube el logo de una sucursal a Supabase Storage y retorna la ruta remota.

    Parameters
    ----------
    local_path: str
        Ruta local del archivo de imagen.
    sucursal_nombre: str
        Nombre de la sucursal (se usa para nombrar el archivo en storage).

    Returns
    -------
    Optional[str]
        La ruta remota dentro del bucket si fue exitoso, None si falló.
    """
    if not _ensure_client():
        return None

    # Normalizar nombre: quitar espacios, minúsculas
    nombre_limpio = sucursal_nombre.lower().replace(" ", "_").replace("/", "-")
    ext = os.path.splitext(local_path)[1].lower() or ".png"
    remote_path = f"logos/{nombre_limpio}{ext}"

    success = upload_image(local_path, remote_path)
    if success:
        return remote_path
    return None


def download_logo_sucursal(sucursal_nombre: str) -> Optional[str]:
    """Descarga el logo de una sucursal de Supabase Storage a un archivo temporal.

    Parameters
    ----------
    sucursal_nombre: str
        Nombre de la sucursal.

    Returns
    -------
    Optional[str]
        Ruta local del archivo descargado, o None si no existe / hubo error.
    """
    if not _ensure_client():
        return None

    nombre_limpio = sucursal_nombre.lower().replace(" ", "_").replace("/", "-")

    for ext in [".png", ".jpg", ".jpeg"]:
        remote_path = f"logos/{nombre_limpio}{ext}"
        try:
            data = supabase.storage.from_(SUPABASE_BUCKET).download(remote_path)
            if data:
                # Guardar en directorio temporal del proyecto
                tmp_dir = os.path.join(os.getcwd(), "_logos_cache")
                os.makedirs(tmp_dir, exist_ok=True)
                local_path = os.path.join(tmp_dir, f"{nombre_limpio}{ext}")
                with open(local_path, "wb") as f:
                    f.write(data)
                return local_path
        except Exception:
            continue  # Probar siguiente extensión

    return None


def get_logo_sucursal_path(sucursal_nombre: str) -> Optional[str]:
    """Obtiene la ruta local del logo de una sucursal.
    
    Primero verifica caché local, si no existe lo descarga de Supabase.
    Fallback a logo.png local si no hay logo de sucursal.

    Parameters
    ----------
    sucursal_nombre: str
        Nombre de la sucursal.

    Returns
    -------
    Optional[str]
        Ruta al archivo de logo a usar, o None si no hay ninguno.
    """
    if sucursal_nombre:
        nombre_limpio = sucursal_nombre.lower().replace(" ", "_").replace("/", "-")
        tmp_dir = os.path.join(os.getcwd(), "_logos_cache")

        # 1. Verificar caché local
        for ext in [".png", ".jpg", ".jpeg"]:
            cached = os.path.join(tmp_dir, f"{nombre_limpio}{ext}")
            if os.path.exists(cached):
                return cached

        # 2. Intentar descargar desde Supabase Storage
        downloaded = download_logo_sucursal(sucursal_nombre)
        if downloaded:
            return downloaded

    # 3. Fallback al logo local del repositorio
    for cand in ["logo.png", "logo.jpg", "logo.jpeg"]:
        if os.path.exists(cand):
            return cand

    return None


def public_url(path: str, expires_in: int = 3600) -> Optional[str]:
    """Generate a signed URL for a private object.

    Parameters
    ----------
    path: str
        Path inside the bucket (e.g., "logos/logo.png").
    expires_in: int, optional
        Seconds until the URL expires. Default is 1 hour.

    Returns
    -------
    Optional[str]
        The signed URL if successful, otherwise ``None``.
    """
    if not _ensure_client():
        return None
    try:
        res = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(path, expires_in)
        # Expected format: {"signedURL": "https://...", "error": None}
        if isinstance(res, dict):
            if res.get("error"):
                print(f"[Supabase] Signed URL error: {res['error']}")
                return None
            return res.get("signedURL") or res.get("signedUrl")
        # SDK v2 may return an object
        if hasattr(res, "signed_url"):
            return res.signed_url
        return None
    except Exception as e:
        print(f"[Supabase] Exception during public_url: {e}")
        return None


def delete_logo_sucursal(sucursal_nombre: str) -> bool:
    """Elimina el logo de una sucursal de Supabase Storage y borra la caché local.

    Returns ``True`` on success, ``False`` otherwise.
    """
    if not _ensure_client():
        return False

    nombre_limpio = sucursal_nombre.lower().replace(" ", "_").replace("/", "-")
    eliminado = False

    for ext in [".png", ".jpg", ".jpeg"]:
        remote_path = f"logos/{nombre_limpio}{ext}"
        try:
            supabase.storage.from_(SUPABASE_BUCKET).remove([remote_path])
            eliminado = True
        except Exception:
            pass  # No existía, ok

        # Limpiar caché local también
        tmp_dir = os.path.join(os.getcwd(), "_logos_cache")
        cached = os.path.join(tmp_dir, f"{nombre_limpio}{ext}")
        if os.path.exists(cached):
            try:
                os.remove(cached)
                eliminado = True
            except Exception:
                pass

    return eliminado


def delete_image(path: str) -> bool:
    """Delete an object from the bucket.

    Returns ``True`` on success, ``False`` otherwise.
    """
    if not _ensure_client():
        return False
    try:
        res = supabase.storage.from_(SUPABASE_BUCKET).remove([path])
        if isinstance(res, dict) and res.get("error"):
            print(f"[Supabase] Delete error: {res['error']}")
            return False
        return True
    except Exception as e:
        print(f"[Supabase] Exception during delete_image: {e}")
        return False
