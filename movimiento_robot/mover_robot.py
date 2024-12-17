from comunicacion_arduino.comunicacion import send_command

def mover_robot(politica, posicionesRobot):
    """
    Controla el movimiento del robot basado en la política y la posición actual detectada.
    El robot avanza hacia adelante mientras se centra en la casilla, manteniendo la lógica de política.
    """
    # Validación inicial rápida
    if not posicionesRobot:
        print("No se detectó posición del robot.")
        return

    # Extraer información del robot de manera más clara
    robot_actual = posicionesRobot[0]
    posicionActual = robot_actual["cell_index"]
    angulo = robot_actual["angle"]
    ultima_posicion = next(reversed(politica))

    # Definir mapeo de ángulos para las direcciones
    DIRECCIONES = {
        0: (90, 105, "Arriba"),   # Arriba
        1: (255, 285, "Abajo"),   # Abajo
        2: (165, 195, "Izquierda"),  # Izquierda
        3: (345, 15, "Derecha")   # Derecha
    }

    # Determinar la política máxima para la posición actual
    p_actual = politica[posicionActual]
    max_valor = max(p_actual)
    direccion_objetivo = p_actual.index(max_valor)

    # Verificar si necesita calibración
    if _requiere_calibracion(robot_actual):
        calibrar_robot(robot_actual)
        return

    # Lógica de movimiento
    comando = _determinar_comando(angulo, DIRECCIONES, direccion_objetivo)

    if comando:
        send_command(comando)
        print(f"Movimiento: {DIRECCIONES[direccion_objetivo][2]}")

def _requiere_calibracion(robot_actual):
    """Verifica si el robot necesita calibración."""
    centro_x = robot_actual["cell_center_x"]
    centro_y = robot_actual["cell_center_y"]
    x_actual = robot_actual["x"]
    y_actual = robot_actual["y"]
    centro_width = robot_actual["cell_width"] // 2
    centro_height = robot_actual["cell_height"] // 2

    return (abs(x_actual - centro_x) > 0.25 * centro_width or 
            abs(y_actual - centro_y) > 0.25 * centro_height)

def _determinar_comando(angulo_actual, DIRECCIONES, direccion_objetivo):
    """Determina el comando de movimiento basado en el ángulo y la dirección objetivo."""
    for idx, (min_ang, max_ang, _) in DIRECCIONES.items():
        if idx == direccion_objetivo:
            if (min_ang <= angulo_actual <= max_ang) or \
               (idx == 3 and (angulo_actual <= max_ang or angulo_actual >= 345)):
                return "w"  # Avanzar
    
    # Si no está en el ángulo correcto, calcular giro
    angulos_objetivo = {
        3: 0,   # Adelante
        2: 180, # Izquierda
        1: 270, # Abajo
        0: 90   # Arriba
    }
    
    angulo_objetivo = angulos_objetivo[direccion_objetivo]
    return calcular_giro(angulo_actual, angulo_objetivo)

def calcular_giro(angulo_actual, angulo_deseado):
    """Calcula la dirección de giro más eficiente."""
    diferencia = (angulo_deseado - angulo_actual + 360) % 360
    return "a" if diferencia <= 180 else "d"

def calibrar_robot(detected_shapes):
    """
    Calibra el robot para mantenerlo en línea recta.
    Corrige desviaciones horizontales y verticales.
    """
    centro_x = detected_shapes['cell_center_x']
    centro_y = detected_shapes['cell_center_y']
    tolerancia = 15

    # Corrección horizontal
    diferencia_x = detected_shapes['x'] - centro_x
    if abs(diferencia_x) > tolerancia:
        comando = "d" if diferencia_x > tolerancia else "a"
        send_command(comando)
        print(f"Corrigiendo horizontal: {comando}")

    # Corrección vertical
    diferencia_y = detected_shapes['y'] - centro_y
    if abs(diferencia_y) > tolerancia:
        comando = "a" if diferencia_y > tolerancia else "d"
        send_command(comando)
        print(f"Corrigiendo vertical: {comando}")

    # Avanzar después de la corrección
    send_command("w")










# from comunicacion_arduino.comunicacion import send_command

# def mover_robot(politica, posicionesRobot):
#     """
#     Controla el movimiento del robot basado en la política y la posición actual detectada.
#     El robot avanza hacia adelante mientras se centra en la casilla, manteniendo la lógica de política.
#     """
#     if not posicionesRobot:  # Si no se detectan posiciones, no hacer nada
#         print("No se detectó posición del robot.")
#         return

#     robot_actual = posicionesRobot[0]  # Tomar la posición del primer robot detectado
#     posicionActual = robot_actual["cell_index"] # Índice de la casilla actual del robot
#     angulo = robot_actual["angle"] # Ángulo del robot
#     centro_casilla_x = robot_actual["cell_center_x"] # Coordenadas del centro de la casilla
#     centro_casilla_y = robot_actual["cell_center_y"] # Coordenadas del centro de la casilla
#     centro_x = robot_actual["cell_width"] // 2 # Centro de la casilla en X
#     centro_y = robot_actual["cell_height"] // 2 # Centro de la casilla en Y
#     max_valor = max(politica[posicionActual]) # Valor máximo en la política de la casilla actual
#     ultima_posicion = next(reversed(politica)) # Última posición en la política

#     p_anterior = politica[posicionActual] # Política de la casilla anterior
#     p_siguiente = politica[posicionActual + 1] if posicionActual < ultima_posicion else politica[ultima_posicion]
#     pos_x = robot_actual["x"]
#     pos_y = robot_actual["y"]


#     # Comprobar las direcciones en la política
#     if p_anterior != p_siguiente and (pos_x < centro_casilla_x - 0.25 * centro_x or pos_x > centro_casilla_x + 0.25* centro_x):
#         print("Calibrando el robot")
#         calibrar_robot(robot_actual)
#         return
#     elif p_anterior != p_siguiente and (pos_y < centro_casilla_y - 0.25 * centro_y or pos_y > centro_casilla_y + 0.25* centro_y):
#         print("Calibrando el robot")
#         calibrar_robot(robot_actual)
#         return
#     elif politica[posicionActual][3] == max_valor and (angulo < 15 or angulo > 345): # Movimiento hacia la derecha
#         print("Derecha")
#         comando_avance = "w"
#     elif politica[posicionActual][2] == max_valor and (angulo > 165 and angulo < 195):  # Movimiento hacia Izquierda
#         print("Izquierda")
#         comando_avance = "w"
#     elif politica[posicionActual][1] == max_valor and (angulo > 255 and angulo < 285):  # Movimiento hacia la Abajo
#         print("Abajo")
#         comando_avance = "w"
#     elif politica[posicionActual][0] == max_valor and (angulo > 65 and angulo < 105):  # Movimiento hacia la Arriba
#         print("Arriba")
#         comando_avance = "w"
#     else:
#         print("No hay camino directo, calculando giro hacia el ángulo más cercano")

#         # Ángulos objetivo para cada dirección
#         angulos_objetivo = {
#             3: 0,   # Adelante
#             2: 180, # Izquierda
#             1: 270, # Abajo
#             0: 90   # Arriba
#         }

#         # Encontrar el ángulo objetivo más cercano según la política
#         angulo_mas_cercano = None
#         for direccion, angulo_obj in angulos_objetivo.items():
#             if politica[posicionActual][direccion] == max_valor:
#                 if angulo_mas_cercano is None or abs((angulo - angulo_obj) % 360) < abs((angulo - angulo_mas_cercano) % 360):
#                     angulo_mas_cercano = angulo_obj

#         # Determinar el giro necesario
#         if angulo_mas_cercano is not None:
#             comando_giro = calcular_giro(angulo, angulo_mas_cercano)
#             send_command(comando_giro)
#             print(f"Girando hacia el ángulo más cercano: {angulo_mas_cercano}, comando: {comando_giro}")
#             return  # Salir para permitir que complete el giro
#         else:
#             print("No hay ángulo válido en la política.")
#             return

#     # Comandos de centrado combinados con avance
#     comandos_centrado = []

#     """# Verificar desplazamiento horizontal
#     if robot_actual["x"] < centro_x :  # Margen de tolerancia
#         comandos_centrado.append("d")  # Mover ligeramente a la derecha
#     elif robot_actual["x"] > centro_x :
#         comandos_centrado.append("a")  # Mover ligeramente a la izquierda
#     """

#     # Verificar desplazamiento vertical
#     """if robot_actual["y"] < centro_y:
#         comandos_centrado.append("d")  # Mover ligeramente hacia derecha
#     elif robot_actual["y"] > centro_y:
#         comandos_centrado.append("a")  # Mover ligeramente hacia izquierda"""

#     # Ejecutar comandos
#     if comandos_centrado:
#         # Enviar comando de centrado
#         send_command(comandos_centrado[0])
#         print(f"Centrando: {comandos_centrado[0]}")
    
#     # Enviar comando de avance
#     send_command(comando_avance)
#     print("Avanzando")

# def calcular_giro(angulo_actual, angulo_deseado):
#         diferencia = (angulo_deseado - angulo_actual + 360) % 360
#         if diferencia <= 180:
#             return "a"  # Girar a la derecha
#         else:
#             return "d"  # Girar a la izquierda

# def calibrar_robot(detected_shapes):
#     """
#     Calibra el robot para mantenerlo en línea recta hacia adelante en ambos sentidos.
#     Si x aumenta, el robot va de izquierda a derecha. Si x disminuye, va de derecha a izquierda.
#     """
#     centro_x = detected_shapes['cell_center_x']
#     centro_y = detected_shapes['cell_center_y']

#     # Calcular desviaciones
#     diferencia_x = detected_shapes['x'] - centro_x
#     diferencia_y = detected_shapes['y'] - centro_y
#     tolerancia = 15

#     if abs(diferencia_x) > tolerancia:
#         if diferencia_x > tolerancia:
#             print("Corrigiendo horizontal derecha con 'd'")
#             send_command("d")
#         elif diferencia_x < -tolerancia:
#             print("Corrigiendo horizontal izquierda con 'a'")
#             send_command("a")

#     # Corrección en el eje Y (desviación vertical)
#     if abs(diferencia_y) > tolerancia:
#         if diferencia_y > tolerancia:
#             print("Corrigiendo vertical abajo con 'a'")
#             send_command("a")
#         elif diferencia_y < -tolerancia:
#             print("Corrigiendo vertical arriba con 'd'")
#             send_command("d")
#     send_command("w")  # Avanzar
#     # Imprimir las diferencias para depuración
#     print(f"Diferencia en X: {diferencia_x}, Diferencia en Y: {diferencia_y}")