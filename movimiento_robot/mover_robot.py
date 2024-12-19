
from comunicacion_arduino.comunicacion import send_command

roles = {8: 0, 9: 1}
def mover_robot(politica, posicionesRobot):
    """
    Controla el movimiento del robot basado en la política y la posición actual detectada.
    El robot avanza hacia adelante mientras se centra en la casilla, manteniendo la lógica de política.
    posicionesRobot = detected_shapes
    """
    global roles
    if not posicionesRobot:  # Si no se detectan posiciones, no hacer nada
        print("No se detectó posición del robot.")
        return

    
    robot_actual = posicionesRobot[0]  # Tomar la posición del primer robot detectado
    robot_id = robot_actual['shape'] # puede ser 8 policia o 9 ladron
    robot_role = roles.get(robot_id, None)  # Obtener el rol del robot

    if robot_role is None:
        print(f"El robot con ID {robot_id} no tiene un rol asignado.")
        return
    angulo = robot_actual["angle"] # Ángulo del robot
    pos_x = robot_actual["x"]
    pos_y = robot_actual["y"]
    centro_casilla_x = robot_actual["cell_center_x"] # Coordenadas del centro de la casilla
    centro_casilla_y = robot_actual["cell_center_y"] # Coordenadas del centro de la casilla
    centro_x = robot_actual["cell_width"] // 2 # Centro de la casilla en X
    centro_y = robot_actual["cell_height"] // 2 # Centro de la casilla en Y
    x, y = robot_actual["row"], robot_actual["col"] # Coordenadas de la casilla actual
    if robot_role == 0:
        objetivo = "Policia"
    else:
        objetivo = "Ladron"

    for estado, datos in politica.items():
        coordenada_objetivo = politica[estado]['coordinates'][objetivo]
        rol_politica = politica[estado]['coordinates']['role']

        if robot_role == rol_politica and (x, y) == coordenada_objetivo:
            if abs(pos_x - centro_casilla_x) > 0.25 * centro_x or abs(pos_y - centro_casilla_y) > 0.25 * centro_y:
                print("Calibrando el robot")
                calibrar_robot(robot_actual)
                return
            elif politica[estado]['values'][3] == 1 and (angulo < 10 or angulo > 350):
                print("Moviendo hacia la derecha")
                send_command("w")
                calibrar_robot(robot_actual)
            elif politica[estado]['values'][2] == 1 and (angulo > 170 and angulo < 190):
                print("Moviendo hacia la izquierda")
                send_command("w")
                calibrar_robot(robot_actual)
            elif politica[estado]['values'][1] == 1 and (angulo > 260 and angulo < 280):
                print("Moviendo hacia abajo")
                send_command("w")
                calibrar_robot(robot_actual)
            elif politica[estado]['values'][0] == 1 and (angulo > 80 and angulo < 100):
                print("Moviendo hacia arriba")
                send_command("w")
                calibrar_robot(robot_actual)
            else:
                print("Calculando giro hacia el ángulo más cercano")
                angulos_objetivo = {
                    3: 0,   # Adelante
                    2: 180, # Izquierda
                    1: 270, # Abajo
                    0: 90   # Arriba
                }
                angulo_mas_cercano = None
                for direccion, angulo_obj in angulos_objetivo.items():
                    if politica[estado]['values'][direccion] == 1:
                        if angulo_mas_cercano is None or abs((angulo - angulo_obj) % 360) < abs((angulo - angulo_mas_cercano) % 360):
                            angulo_mas_cercano = angulo_obj
                if angulo_mas_cercano:
                    comando_giro = calcular_giro(angulo, angulo_mas_cercano)
                    send_command(comando_giro)
                    print(f"Girando hacia: {angulo_mas_cercano}, comando: {comando_giro}")
                    return
    
    

    # coordenada_camara_p = (0,0)
    # coordenada_camara_l = (0,2)
    # rol_camara = 0
    # if robot_actual['role'] == 0:
    #     coordenada_camara_p = (robot_actual['row'], robot_actual['col'])
    #     rol_camara = 0
    # else:
    #     coordenada_camara_l = (robot_actual['row'], robot_actual['col'])
    #     rol_camara = 1

    # for estado, datos in politica.items():
    #     ultima_posicion = next(reversed(politica))
    #     p_anterior = politica[estado] # Política de la casilla anterior
    #     p_siguiente = politica[estado + 1] if estado < ultima_posicion else politica[ultima_posicion]
    #     coordenada_policia = politica[estado]['coordinates']['Policia']
    #     coordenada_ladron = politica[estado]['coordinates']['Ladron']
    #     rol_politica = politica[estado]['coordinates']['role']

    #     if rol_camara == rol_politica and coordenada_camara_p == coordenada_policia and coordenada_camara_l == coordenada_ladron:
    #         if p_anterior != p_siguiente and (pos_x < centro_casilla_x - 0.25 * centro_x or pos_x > centro_casilla_x + 0.25* centro_x):
    #             print("Calibrando el robot")
    #             calibrar_robot(robot_actual)
    #             return
    #         elif p_anterior != p_siguiente and (pos_y < centro_casilla_y - 0.25 * centro_y or pos_y > centro_casilla_y + 0.25* centro_y):
    #             print("Calibrando el robot")
    #             calibrar_robot(robot_actual)
    #             return
    #         elif politica[estado]['values'][3] == 1 and (angulo < 10 or angulo > 350): # Movimiento hacia la derecha
    #             print("Derecha")
    #             send_command("w")
    #             calibrar_robot(robot_actual)
    #         elif politica[estado]['values'][2] == 1 and (angulo > 170 and angulo < 190):  # Movimiento hacia Izquierda
    #             print("Izquierda")
    #             send_command("w")
    #             calibrar_robot(robot_actual)
    #         elif politica[estado]['values'][1] == 1 and (angulo > 260 and angulo < 280):  # Movimiento hacia la Abajo
    #             print("Abajo")
    #             send_command("w")
    #             calibrar_robot(robot_actual)
    #         elif politica[estado]['values'][0] == 1 and (angulo > 80 and angulo < 100):  # Movimiento hacia la Arriba
    #             print("Arriba")
    #             send_command("w")
    #             calibrar_robot(robot_actual)
    #         else:
    #             print("No hay camino directo, calculando giro hacia el ángulo más cercano")
    #             # Ángulos objetivo para cada dirección
    #             angulos_objetivo = {
    #                 3: 0,   # Adelante
    #                 2: 180, # Izquierda
    #                 1: 270, # Abajo
    #                 0: 90   # Arriba
    #             }
    #             # Encontrar el ángulo objetivo más cercano según la política
    #             angulo_mas_cercano = None
    #             for direccion, angulo_obj in angulos_objetivo.items():
    #                 if politica[estado]['values'][direccion] == 1:
    #                     if angulo_mas_cercano is None or abs((angulo - angulo_obj) % 360) < abs((angulo - angulo_mas_cercano) % 360):
    #                         angulo_mas_cercano = angulo_obj
    #             # Determinar el giro necesario
    #             if angulo_mas_cercano is not None:
    #                 comando_giro = calcular_giro(angulo, angulo_mas_cercano)
    #                 send_command(comando_giro)
    #                 print(f"Girando hacia el ángulo más cercano: {angulo_mas_cercano}, comando: {comando_giro}")
    #                 return  # Salir para permitir que complete el giro
    #             else:
    #                 print("No hay ángulo válido en la política.")
    #                 return
    #         # Comandos de centrado combinados con avance
    #         #comandos_centrado = []
    #         """# Verificar desplazamiento horizontal
    #         if robot_actual["x"] < centro_x :  # Margen de tolerancia
    #             comandos_centrado.append("d")  # Mover ligeramente a la derecha
    #         elif robot_actual["x"] > centro_x :
    #             comandos_centrado.append("a")  # Mover ligeramente a la izquierda
    #         """
    #         # Verificar desplazamiento vertical
    #         """if robot_actual["y"] < centro_y:
    #             comandos_centrado.append("d")  # Mover ligeramente hacia derecha
    #         elif robot_actual["y"] > centro_y:
    #             comandos_centrado.append("a")  # Mover ligeramente hacia izquierda"""
    #         # Ejecutar comandos
    #         """if comandos_centrado:
    #             # Enviar comando de centrado
    #             send_command(comandos_centrado[0])
    #             print(f"Centrando: {comandos_centrado[0]}")
            
    #         # Enviar comando de avance
    #         send_command(comando_avance)
    #         print("Avanzando")"""
def calcular_giro(angulo_actual, angulo_deseado):
        diferencia = (angulo_deseado - angulo_actual + 360) % 360
        if diferencia <= 180:
            return "a"  # Girar a la derecha
        else:
            return "d"  # Girar a la izquierda
        

def calibrar_robot(detected_shapes):
    """
    Calibra el robot para corregir desviaciones en posición y ángulo.
    Mantiene al robot centrado en las casillas y orientado correctamente.
    """
    # Variables de posición
    centro_x = detected_shapes['cell_center_x']
    centro_y = detected_shapes['cell_center_y']
    pos_x = detected_shapes['x']
    pos_y = detected_shapes['y']
    tolerancia_posicion = 10  # Tolerancia para considerar que el robot está centrado

    # Variables de ángulo
    angulo_actual = detected_shapes['angle']  # Ángulo actual del robot
    angulos_objetivo = [0, 90, 180, 270]  # Ángulos objetivo posibles (este, norte, oeste, sur)
    tolerancia_angulo = 10  # Tolerancia para considerar el ángulo como correcto

    # Determinar el ángulo más cercano al actual
    angulo_cercano = min(angulos_objetivo, key=lambda angulo: abs((angulo - angulo_actual) % 360))

    # Corregir orientación si está fuera del rango permitido
    if abs((angulo_actual - angulo_cercano) % 360) > tolerancia_angulo:
        if (angulo_cercano - angulo_actual) % 360 < 180:
            print(f"Corrigiendo orientación girando a la izquierda ('a') hacia {angulo_cercano}°")
            send_command("a")  # Girar hacia la izquierda
        else:
            print(f"Corrigiendo orientación girando a la derecha ('d') hacia {angulo_cercano}°")
            send_command("d")  # Girar hacia la derecha
        return  # Salir para permitir que complete el giro antes de avanzar

    # Corregir posición horizontal si está fuera del rango permitido
    if angulo_cercano in [90, 270]:
        diferencia_x = pos_x - centro_x
        if abs(diferencia_x) > tolerancia_posicion:
            if diferencia_x > 0:
                print("Corrigiendo posición moviendo ligeramente a la izquierda ('a')")
                send_command("a")  # Mover a la izquierda
            else:
                print("Corrigiendo posición moviendo ligeramente a la derecha ('d')")
                send_command("d")  # Mover a la derecha
            return  # Salir para permitir que complete el movimiento antes de avanzar
    elif angulo_cercano in [0, 180]:
        # Corregir posición vertical si está fuera del rango permitido
        diferencia_y = pos_y - centro_y
        if abs(diferencia_y) > tolerancia_posicion:
            if diferencia_y > 0:
                print("Corrigiendo posición moviendo hacia abajo ('s')")
                send_command("a")  # Mover hacia abajo
            else:
                print("Corrigiendo posición moviendo hacia arriba ('w')")
                send_command("d")  # Mover hacia arriba
            return  # Salir para permitir que complete el movimiento antes de avanzar
    else:
        # Si tanto el ángulo como la posición son correctos, avanzar
        print("Robot correctamente orientado y centrado, avanzando con 'w'")
        send_command("w")

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