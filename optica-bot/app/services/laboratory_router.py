def seleccionar_laboratorio(tipo_lente: str, tratamiento: str = None) -> str:
    tipo = tipo_lente.lower()
    trat = (tratamiento or "").lower()
    
    if "progresivo" in tipo:
        return "Laboratorio Premium Vision"
    
    if "fotocromatico" in trat or "transition" in trat:
        return "Laboratorio Specialty Lenses"
    
    if "azul" in trat or "blue" in trat:
        return "Laboratorio Digital Coatings"
        
    if "alto indice" in tipo or "1.67" in tipo:
        return "Laboratorio High Index"
        
    return "Laboratorio Local CR39"
