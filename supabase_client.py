import os
import tempfile
import unicodedata
import re
import shutil
from typing import Optional

# Import the initialized Supabase client from the database module
try:
    from database import supabase
except ImportError:
    supabase = None

# Bucket name from environment variables (as defined in .env)
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "happy-vision-imagenes")

def _ensure_client() -> bool:
    """Check that Supabase client and bucket are configured."""
    return supabase is not None and SUPABASE_BUCKET is not None


def sanitizar_nombre_sucursal(nombre: str) -> str:
    """Convierte cualquier nombre de sucursal a un identificador seguro para Supabase Storage / S3.
    Elimina acentos, tildes, virgulilla de la ñ y caracteres especiales, retornando solo
    caracteres ASCII alfanuméricos y guiones bajos en minúsculas.
    Ejemplo: 'Cruz Roja Rumiñahui' -> 'cruz_roja_ruminahui'
    """
    if not nombre:
        return "matriz"
    n = unicodedata.normalize('NFKD', str(nombre))
    n = ''.join(c for c in n if not unicodedata.combining(c))
    n = n.lower().strip()
    n = re.sub(r'[^a-z0-9_-]', '_', n)
    n = re.sub(r'_+', '_', n).strip('_')
    return n or "sucursal"


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
    Guarda copia en la caché local '_logos_cache/{nombre_limpio}.ext'.
    Si es Matriz, también actualiza 'logo.png' local.
    """
    if not _ensure_client():
        return None

    nombre_limpio = sanitizar_nombre_sucursal(sucursal_nombre)
    ext = os.path.splitext(local_path)[1].lower() or ".png"
    remote_path = f"logos/{nombre_limpio}{ext}"

    success = upload_image(local_path, remote_path)
    if success:
        try:
            tmp_dir = os.path.join(os.getcwd(), "_logos_cache")
            os.makedirs(tmp_dir, exist_ok=True)
            local_cache = os.path.join(tmp_dir, f"{nombre_limpio}{ext}")
            shutil.copy2(local_path, local_cache)

            # Si es Matriz o logo principal, guardar también en la raíz del proyecto
            if nombre_limpio == "matriz":
                shutil.copy2(local_path, os.path.join(os.getcwd(), f"logo{ext}"))
        except Exception as e:
            print(f"[Supabase] Error copiando a caché local: {e}")

        return remote_path
    return None


def download_logo_sucursal(sucursal_nombre: str) -> Optional[str]:
    """Descarga el logo de una sucursal de Supabase Storage a la caché local."""
    if not _ensure_client():
        return None

    nombre_limpio = sanitizar_nombre_sucursal(sucursal_nombre)
    variantes = [nombre_limpio]
    raw_clean = str(sucursal_nombre).lower().replace(" ", "_").replace("/", "-")
    if raw_clean not in variantes:
        variantes.append(raw_clean)

    tmp_dir = os.path.join(os.getcwd(), "_logos_cache")
    os.makedirs(tmp_dir, exist_ok=True)

    for var in variantes:
        for ext in [".png", ".jpg", ".jpeg"]:
            remote_path = f"logos/{var}{ext}"
            try:
                data = supabase.storage.from_(SUPABASE_BUCKET).download(remote_path)
                if data:
                    local_path = os.path.join(tmp_dir, f"{nombre_limpio}{ext}")
                    with open(local_path, "wb") as f:
                        f.write(data)
                    return local_path
            except Exception:
                continue

    return None


def get_logo_matriz_path() -> Optional[str]:
    """Obtiene la ruta local del logo de Matriz (o primera sucursal registrada).
    Se usa en el login y como fallback predeterminado para sucursales que no tienen logo propio.
    """
    tmp_dir = os.path.join(os.getcwd(), "_logos_cache")

    # 1. Verificar si existe matriz en _logos_cache
    for ext in [".png", ".jpg", ".jpeg"]:
        matriz_cached = os.path.join(tmp_dir, f"matriz{ext}")
        if os.path.exists(matriz_cached):
            return matriz_cached

    # 2. Intentar descargar desde Supabase Storage
    downloaded = download_logo_sucursal("Matriz")
    if downloaded:
        return downloaded

    # 3. Revisar si hay logo local en la raíz
    for cand in ["logo.png", "logo.jpg", "logo.jpeg"]:
        if os.path.exists(cand):
            return cand

    # 4. Si aún no hay, buscar la primera sucursal registrada en BD que tenga logo
    try:
        from database import cargar_sucursales
        df_suc = cargar_sucursales()
        if not df_suc.empty:
            for _, r in df_suc.iterrows():
                cand_nombre = r.get("nombre")
                if cand_nombre and sanitizar_nombre_sucursal(cand_nombre) != "matriz":
                    cand_logo = get_logo_sucursal_path(cand_nombre, fallback_a_matriz=False)
                    if cand_logo and os.path.exists(cand_logo):
                        return cand_logo
    except Exception:
        pass

    return None


def get_logo_sucursal_path(sucursal_nombre: str = None, fallback_a_matriz: bool = True) -> Optional[str]:
    """Obtiene la ruta local del logo de una sucursal.
    
    1. Si la sucursal tiene logo personalizado (en caché o Supabase Storage), lo retorna.
    2. Si NO tiene logo propio y fallback_a_matriz es True, retorna automáticamente el logo de 'Matriz'.
    3. Si tampoco existe, retorna el logo.png local del repositorio.
    """
    if sucursal_nombre:
        nombre_limpio = sanitizar_nombre_sucursal(sucursal_nombre)
        tmp_dir = os.path.join(os.getcwd(), "_logos_cache")

        # 1. Verificar caché local para esta sucursal específica
        for ext in [".png", ".jpg", ".jpeg"]:
            cached = os.path.join(tmp_dir, f"{nombre_limpio}{ext}")
            if os.path.exists(cached):
                return cached

        # 2. Intentar descargar desde Supabase Storage
        downloaded = download_logo_sucursal(sucursal_nombre)
        if downloaded:
            return downloaded

    # Si no se permite fallback a Matriz, no buscar fallbacks generales
    if not fallback_a_matriz:
        return None

    # 3. Fallback inteligente: Usar automáticamente el logo de Matriz
    if not sucursal_nombre or sanitizar_nombre_sucursal(sucursal_nombre) != "matriz":
        matriz_logo = get_logo_matriz_path()
        if matriz_logo and os.path.exists(matriz_logo):
            return matriz_logo

    # 4. Fallback al logo local del repositorio
    for cand in ["logo.png", "logo.jpg", "logo.jpeg"]:
        if os.path.exists(cand):
            return cand

    return None


def tiene_logo_personalizado(sucursal_nombre: str) -> bool:
    """Verifica si una sucursal tiene un archivo de logo exclusivo o si está usando el de Matriz."""
    if not sucursal_nombre or sanitizar_nombre_sucursal(sucursal_nombre) == "matriz":
        return True
    path = get_logo_sucursal_path(sucursal_nombre, fallback_a_matriz=False)
    return bool(path and os.path.exists(path))


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

    nombre_limpio = sanitizar_nombre_sucursal(sucursal_nombre)
    eliminado = False

    for ext in [".png", ".jpg", ".jpeg"]:
        remote_path = f"logos/{nombre_limpio}{ext}"
        try:
            supabase.storage.from_(SUPABASE_BUCKET).remove([remote_path])
            eliminado = True
        except Exception:
            pass

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
