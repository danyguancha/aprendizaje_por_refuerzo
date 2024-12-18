from comunicacion_arduino.comunicacion import send_command
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def mover_robot(politica, posicionesRobot):
    """
    Control the robot's movement based on policy and current detected position.
    """
    try:
        if not politica or not posicionesRobot:
            logger.warning("No policy or robot position detected.")
            return False

        # Encontrar el robot principal
        robot_actual = next((robot for robot in posicionesRobot if robot['shape'] == 8), 
                            posicionesRobot[0] if posicionesRobot else None)
        
        if not robot_actual:
            logger.error("No valid robot shape found.")
            return False

        # Extraer parámetros esenciales
        posicion_actual = robot_actual["cell_index"]
        max_valor = max(politica[posicion_actual])
        angulo = robot_actual["angle"]
        centro_x = robot_actual["cell_center_x"]
        centro_y = robot_actual["cell_center_y"]
        pos_x = robot_actual["x"]
        pos_y = robot_actual["y"]

        # Calcular tolerancia
        tolerancia = 0.35 * robot_actual["cell_width"]

        # Verificar si el robot está centrado
        if (abs(pos_x - centro_x) <= tolerancia and 
            abs(pos_y - centro_y) <= tolerancia):
            logger.info("Robot centrado - movimiento directo")
            return avanzar_direccion(politica, posicion_actual, angulo, max_valor)

        # Si hay desviación, calibrar y forzar avance
        logger.info("Calibrando robot")
        calibrar_robot(robot_actual)
        
        # Forzar avance después de calibración
        time.sleep(0.5)  # Pequeña pausa para estabilización
        send_command("w")
        time.sleep(0.5)  # Pausa adicional para asegurar movimiento

        return True

    except Exception as e:
        logger.error(f"Error en movimiento del robot: {e}")
        return False

def avanzar_direccion(politica, posicion_actual, angulo, max_valor):
    """
    Determinar dirección de movimiento y enviar comando.
    """
    try:
        DIRECCIONES = [
            {"nombre": "Arriba", "angulo_obj": 90, "ang_min": 65, "ang_max": 105, "index": 0},
            {"nombre": "Abajo", "angulo_obj": 270, "ang_min": 255, "ang_max": 285, "index": 1},
            {"nombre": "Izquierda", "angulo_obj": 180, "ang_min": 165, "ang_max": 195, "index": 2},
            {"nombre": "Derecha", "angulo_obj": 0, "ang_min": 345, "ang_max": 15, "index": 3}
        ]

        for direccion in DIRECCIONES:
            if politica[posicion_actual][direccion['index']] == max_valor:
                # Si el ángulo está dentro del rango, avanzar directamente
                if direccion['ang_min'] <= angulo <= direccion['ang_max']:
                    logger.info(f"{direccion['nombre']} - Avanzando")
                    send_command("w")
                    time.sleep(0.5)  # Asegurar movimiento
                else:
                    # Girar hacia la dirección deseada
                    logger.info(f"Girando hacia {direccion['nombre']}")
                    giro = calcular_giro(angulo, direccion['angulo_obj'])
                    send_command(giro)
                    send_command(giro)
                    time.sleep(0.2)  # Tiempo para girar
                    #send_command("w")  # Avanzar después de girar
                    #time.sleep(0.5)  # Asegurar movimiento
                return True

        logger.warning("No hay dirección válida para avanzar")
        return False

    except Exception as e:
        logger.error(f"Error en movimiento de dirección: {e}")
        return False

def calcular_giro(angulo_actual, angulo_deseado):
    """
    Calcular dirección de giro para acercarse al ángulo deseado.
    """
    diferencia = (angulo_deseado - angulo_actual + 360) % 360
    return "a" if diferencia <= 180 else "d"

def calibrar_robot(detected_shapes):
    """
    Calibrar robot si se detecta una desviación significativa.
    """
    try:
        centro_x = detected_shapes['cell_center_x']
        centro_y = detected_shapes['cell_center_y']
        diferencia_x = detected_shapes['x'] - centro_x
        diferencia_y = detected_shapes['y'] - centro_y
        tolerancia = 15  # Sensibilidad de calibración

        # Corrección horizontal
        if abs(diferencia_x) > tolerancia:
            comando_x = "d" if diferencia_x > 0 else "a"
            logger.info(f"Corrigiendo horizontal con {comando_x}")
            send_command(comando_x)
            time.sleep(0.3)  # Tiempo para corrección

        # Corrección vertical
        if abs(diferencia_y) > tolerancia:
            comando_y = "a" if diferencia_y > 0 else "d"
            logger.info(f"Corrigiendo vertical con {comando_y}")
            send_command(comando_y)
            time.sleep(0.3)  # Tiempo para corrección

        logger.info("Calibración completada. Forzando avance.")
        send_command("w")
        time.sleep(0.5)  # Asegurar movimiento
        return True

    except Exception as e:
        logger.error(f"Error durante calibración del robot: {e}")
        return False