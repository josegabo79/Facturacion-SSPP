def calcular_cu_ponderados(datos):
    """
    Toma los datos planos y calcula el Costo Unitario dividiendo el valor en pesos 
    entre el consumo total. Ahora cuenta con un escudo para valores nulos (None).
    """
    try:
        valor_consumo = datos.get("Consumo_Total", 0)
        if valor_consumo is None:
            valor_consumo = 0
            
        consumo_total = float(valor_consumo)
    except (ValueError, TypeError):
        consumo_total = 0.0

    if consumo_total > 0:
        campos_pesos = {
            "CU_Generacion": "Subtotal_Generacion",
            "CU_Comercializacion": "Subtotal_Comercializacion",
            "CU_Perdidas": "Subtotal_Perdidas",
            "CU_Transporte_Nacional": "Subtotal_Transporte_Nac",
            "CU_Transporte_Regional": "Subtotal_Transporte_Reg",
            "CU_Distribucion": "Subtotal_Distribucion",
            "CU_Restricciones": "Subtotal_Restricciones"
        }
        for cu, subtotal in campos_pesos.items():
            valor_sub = datos.get(subtotal, 0)
            if valor_sub is None:
                valor_sub = 0
                
            valor_pesos = float(valor_sub)
            datos[cu] = round(valor_pesos / consumo_total, 4)
            
    return datos