# pylint: disable=no-member
import cv2
import numpy as np
import random
import math
import comunicacionArduinoMAC
# URL de DroidCam
url = "http://192.168.129.6:4747/video"

# Parámetros de la cuadrícula
rows = 3  # Número de filas
cols = 3  # Número de columnas
thickness = 1  # Grosor de las líneas
count = 0

# Valores iniciales de Canny
canny_threshold1 = 50
canny_threshold2 = 150

politica = {0: [0,0,0,1],
            1: [0,0,0,1],
            2: [0,1,0,0],
            3: [0,1,0,0],
            4: [0,0,0,0],
            5: [0,1,0,0],
            6: [0,0,0,1],
            7: [0,0,0,1],
            8: [0,0,0,0],
            }

def maze_generate(filas, columnas):
    """
    Genera un laberinto de dimensiones filas x columnas.
    Los caminos están representados por 0 y las paredes por 1.
    Garantiza que (0,0) es el inicio y (filas-1,columnas-1) es la meta con un camino solucionable.
    """
    # Crear una matriz llena de paredes (1)
    laberinto = [[1 for _ in range(columnas)] for _ in range(filas)]

    # Direcciones de movimiento: (dx, dy) para celdas ortogonales
    direcciones = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    def en_rango(x, y):
        """Verifica si una celda está dentro del rango del laberinto."""
        return 0 <= x < filas and 0 <= y < columnas

    def dfs(x, y):
        """Algoritmo DFS para construir el laberinto."""
        laberinto[x][y] = 0  # Marca el camino actual como "camino"
        random.shuffle(direcciones)  # Aleatoriza el orden de las direcciones
        for dx, dy in direcciones:
            nx, ny = x + 2 * dx, y + 2 * dy  # Saltar una celda para garantizar paredes entre caminos
            if en_rango(nx, ny) and laberinto[nx][ny] == 1:  # Si es una celda válida y no visitada
                # Romper la pared entre la celda actual y la siguiente
                laberinto[x + dx][y + dy] = 0
                # Continuar el DFS desde la celda siguiente
                dfs(nx, ny)

    # Inicializar el laberinto
    laberinto[0][0] = 0  # Crear la entrada
    dfs(0, 0)

    # Crear la salida
    laberinto[filas - 1][columnas - 1] = 0  # Asegurar que el punto final sea siempre un camino

    # Conectar la salida al camino más cercano si está aislada
    if laberinto[filas - 2][columnas - 1] == 1 and laberinto[filas - 1][columnas - 2] == 1:
        laberinto[filas - 2][columnas - 1] = 0  # Romper la pared superior

    # Devolver la matriz del laberinto
    return laberinto
def draw_grid(frame, rows, cols, thickness=1):
    """Dibuja una cuadrícula en el frame."""
    height, width, _ = frame.shape
    cell_height = height // rows
    cell_width = width // cols

    for i in range(1, rows):  # Líneas horizontales
        cv2.line(frame, (0, i * cell_height), (width, i * cell_height), (0, 255, 0), thickness)
    for j in range(1, cols):  # Líneas verticales
        cv2.line(frame, (j * cell_width, 0), (j * cell_width, height), (0, 255, 0), thickness)
    return frame

def calculate_angle(points):
    """
    Calcula el ángulo de inclinación en grados de un código QR dado.
    Se basa en las coordenadas de las esquinas.
    """
    # Extraer las coordenadas de las esquinas superiores izquierda y derecha
    top_left = points[0]
    top_right = points[1]

    # Calcular el ángulo en radianes
    delta_y = top_right[1] - top_left[1]
    delta_x = top_right[0] - top_left[0]
    angle = np.arctan2(delta_y, delta_x)  # Ángulo en radianes

    # Convertir a grados
    return np.degrees(angle)

def normalize_angle(angle):
    """
    Normaliza el ángulo para que esté entre 0° y 360°.
    El ángulo aumenta en sentido contrario a las manecillas del reloj.
    """
    angle = angle % 360  # Asegura que el ángulo esté dentro del rango [0, 360)
    if angle < 0:
        angle += 360  # Convertir a un ángulo positivo
    return angle

def detect_shapes_in_image(image, rows, cols, qr_detector):
    detected_shapes = []

    # Detectar y decodificar un solo código QR
    data, points, _ = qr_detector.detectAndDecode(image)

    if points is not None:
        points = points.reshape((-1, 2)).astype(int)

        # Dibujar los recuadros alrededor del código QR
        for i in range(len(points)):
            cv2.line(image, tuple(points[i]), tuple(points[(i + 1) % len(points)]), (0, 255, 0), 3)

        # Calcular la inclinación
        angle = calculate_angle(points)

        # Normalizar el ángulo para que esté en el rango [0, 360]
        angle = normalize_angle(angle)

        # Calcular el centro del QR
        qr_center_x = int(np.mean(points[:, 0]))
        qr_center_y = int(np.mean(points[:, 1]))
        qr_center = (qr_center_x, qr_center_y)

        # Calcular la fila y columna de la cuadrícula
        height, width = image.shape[:2]
        cell_width = width / cols
        cell_height = height / rows

        # Calcular en qué celda (fila, columna) se encuentra el centro del QR
        row = int(qr_center_y // cell_height)
        col = int(qr_center_x // cell_width)

        # Calcular el centro de la celda
        cell_center_x = (col + 0.5) * cell_width
        cell_center_x=cell_center_x//1

        cell_center_y = (row + 0.5) * cell_height
        cell_center_y = cell_center_y//1
        cell_center = (cell_center_x, cell_center_y)

        # Flecha indicando cero grados (horizontal a la derecha) desde el centro
        arrow_tip_zero = (qr_center_x + 50, qr_center_y)  # Flecha hacia la derecha (0°)
        cv2.arrowedLine(image, qr_center, arrow_tip_zero, (0, 0, 255), 2, tipLength=0.3)

        # Flecha azul indicando el ángulo detectado
        # Convertir el ángulo a radianes para calcular la dirección de la flecha azul
        angle_rad = np.radians(angle)
        arrow_tip_blue = (int(qr_center_x + 100 * np.cos(angle_rad)), int(qr_center_y + 100 * np.sin(angle_rad)))
        cv2.arrowedLine(image, qr_center, arrow_tip_blue, (255, 0, 0), 2, tipLength=0.3)

        # Mostrar los datos y la inclinación en pantalla

        if data:
            #cv2.putText(image, f"QR: {data}", (10, 50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2, cv2.LINE_AA)
            pass
        angle2 = 360 - angle


        # Guardar los resultados con la fila y columna
        cell_center_x = math.floor(cell_center[0])

        cell_center_y = math.floor(cell_center[1])
        center_x=qr_center[0]
        center_y=qr_center[1]
        cell_index = row * cols + col  # Índice de la celda
        detected_shapes.append({
            "shape": data,
            "angle": angle2,
            "x":qr_center[0],
            "y": qr_center[1],
            "cell_center_x": cell_center_x,
            "cell_center_y": cell_center_y,
            "cell_index":cell_index,
            "row": row,
            "col": col,
            "cell_width":cell_width,
            "cell_height": cell_height,
        })
        cv2.putText(
            image,
            f"{cell_index}",
            (center_x - 10, center_y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            2
        )
        cv2.putText(
            image,
            f"{center_x},{center_y}",
            (center_x - 30, center_y + 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            2
        )
        cv2.putText(image, f"{angle2:.2f}'' ", (center_x-30, center_y + 50), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255),
                   2,
                    cv2.LINE_AA)


        image = draw_dotted_line_in_cell(image, cell_center_x, cell_center_y, cell_width, cell_height)
    return detected_shapes, image


def draw_dotted_line_in_cell(image, cell_center_x, cell_center_y, cell_width, cell_height):
    """Dibuja una línea punteada roja dentro de la celda en los ejes del centro de la celda."""
    # Definir los límites de la celda
    cell_left = int(cell_center_x - cell_width // 2)
    cell_right = int(cell_center_x + cell_width // 2)
    cell_top = int(cell_center_y - cell_height // 2)
    cell_bottom = int(cell_center_y + cell_height // 2)

    # Dibujar línea punteada roja en el eje horizontal

    for x in range(cell_left, cell_right, 10):  # Incremento para punteado
        cv2.line(image, (x, cell_center_y), (x + 5, cell_center_y), (0, 0, 255), 1)

    # Dibujar línea punteada roja en el eje vertical
    for y in range(cell_top, cell_bottom, 10):  # Incremento para punteado
        cv2.line(image, (cell_center_x, y), (cell_center_x, y + 5), (0, 0, 255), 1)
    return image
def fill_cells(frame, matrix, alpha=0.7):
    """Rellena de color negro translúcido los cuadrantes correspondientes a los valores '1' en la matriz."""
    rows, cols = len(matrix), len(matrix[0])
    height, width, _ = frame.shape
    cell_height = height // rows
    cell_width = width // cols

    overlay = frame.copy()  # Hacemos una copia para aplicar el color translúcido

    for i in range(rows):
        for j in range(cols):
            if matrix[i][j] == 1:
                # Coordenadas del cuadrante
                x1, y1 = j * cell_width, i * cell_height
                x2, y2 = x1 + cell_width, y1 + cell_height
                # Rellenar el cuadrante con color negro (translúcido)
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 255), -1)

    # Aplicar transparencia a los rectángulos negros
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    return frame
def highlight_start_end(frame, rows, cols):
    """Colorea en translúcido verde (0,0) y rojo (rows-1, cols-1)."""
    height, width, _ = frame.shape
    cell_height = height // rows
    cell_width = width // cols

    # Coordenadas del inicio (0, 0)
    x1_start, y1_start = 0, 0
    x2_start, y2_start = cell_width, cell_height
    overlay = frame.copy()
    cv2.rectangle(overlay, (x1_start, y1_start), (x2_start, y2_start), (0, 255, 0), -1)  # Verde

    # Coordenadas del final (rows-1, cols-1)
    x1_end, y1_end = (cols - 1) * cell_width, (rows - 1) * cell_height
    x2_end, y2_end = x1_end + cell_width, y1_end + cell_height
    cv2.rectangle(overlay, (x1_end, y1_end), (x2_end, y2_end), (255, 0, 0), -1)  # Rojo

    # Agregar transparencia
    alpha = 0.5  # Nivel de transparencia
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    return frame

def on_trackbar_change(x):
    """Callback para manejar los cambios en las trackbars."""
    pass

def calibrar_robot(detected_shapes):
    """
    Calibra el robot para mantenerlo en línea recta hacia adelante en ambos sentidos.
    Si x aumenta, el robot va de izquierda a derecha. Si x disminuye, va de derecha a izquierda.
    """
    centro_x = detected_shapes['cell_center_x']
    centro_y = detected_shapes['cell_center_y']

    # Calcular desviaciones
    diferencia_x = detected_shapes['x'] - centro_x
    diferencia_y = detected_shapes['y'] - centro_y
    tolerancia = 15

    # Corrección en el eje Y (desviación vertical)
    if abs(diferencia_y) > tolerancia:  # Si la desviación es significativa
        if diferencia_y > tolerancia:  # Desviación hacia abajo (derecha en vista)
            print("Corrigiendo hacia la izquierda con 'a'")
            comunicacionArduinoMAC.send_command("a")
        elif diferencia_y < -tolerancia:  # Desviación hacia arriba (izquierda en vista)
            print("Corrigiendo hacia la derecha con 'd'")
            comunicacionArduinoMAC.send_command("d")

    # Imprimir las diferencias para depuración
    print(f"Diferencia en X: {diferencia_x}, Diferencia en Y: {diferencia_y}")

def mover_robot(politica, posicionesRobot):
    """
    Controla el movimiento del robot basado en la política y la posición actual detectada.
    El robot avanza hacia adelante mientras se centra en la casilla, manteniendo la lógica de política.
    """
    if not posicionesRobot:  # Si no se detectan posiciones, no hacer nada
        print("No se detectó posición del robot.")
        return

    robot_actual = posicionesRobot[0]  # Tomar la posición del primer robot detectado
    posicionActual = robot_actual["cell_index"]
    angulo = robot_actual["angle"]
    
    centro_x = robot_actual["cell_width"] // 2
    centro_y = robot_actual["cell_height"] // 2

    # Comprobar las direcciones en la política
    if politica[posicionActual][3] == 1 and (angulo < 15 or angulo > 345): # Movimiento hacia la derecha
        print("Derecha")
        comando_avance = "w"
    elif politica[posicionActual][2] == 1 and (angulo > 165 and angulo < 195):  # Movimiento hacia Izquierda
        print("Izquierda")
        comando_avance = "w"
    elif politica[posicionActual][1] == 1 and (angulo > 255 and angulo < 285):  # Movimiento hacia la Abajo
        print("Abajo")
        comando_avance = "w"
    elif politica[posicionActual][0] == 1 and (angulo > 65 and angulo < 105):  # Movimiento hacia la Arriba
        print("Arriba")
        comando_avance = "w"
    else:
        print("No hay camino directo, calculando giro hacia el ángulo más cercano")

        # Ángulos objetivo para cada dirección
        angulos_objetivo = {
            3: 0,   # Adelante
            2: 180, # Izquierda
            1: 270, # Abajo
            0: 90   # Arriba
        }

        # Encontrar el ángulo objetivo más cercano según la política
        angulo_mas_cercano = None
        for direccion, angulo_obj in angulos_objetivo.items():
            if politica[posicionActual][direccion] == 1:
                if angulo_mas_cercano is None or abs((angulo - angulo_obj) % 360) < abs((angulo - angulo_mas_cercano) % 360):
                    angulo_mas_cercano = angulo_obj

        # Determinar el giro necesario
        if angulo_mas_cercano is not None:
            comando_giro = calcular_giro(angulo, angulo_mas_cercano)
            comunicacionArduinoMAC.send_command(comando_giro)
            print(f"Girando hacia el ángulo más cercano: {angulo_mas_cercano}, comando: {comando_giro}")
            return  # Salir para permitir que complete el giro
        else:
            print("No hay ángulo válido en la política.")
            return

    # Comandos de centrado combinados con avance
    comandos_centrado = []

    """# Verificar desplazamiento horizontal
    if robot_actual["x"] < centro_x :  # Margen de tolerancia
        comandos_centrado.append("d")  # Mover ligeramente a la derecha
    elif robot_actual["x"] > centro_x :
        comandos_centrado.append("a")  # Mover ligeramente a la izquierda
"""

    # Verificar desplazamiento vertical
    if robot_actual["y"] < centro_y:
        comandos_centrado.append("d")  # Mover ligeramente hacia derecha
    elif robot_actual["y"] > centro_y:
        comandos_centrado.append("a")  # Mover ligeramente hacia izquierda

    # Ejecutar comandos
    if comandos_centrado:
        # Enviar comando de centrado
        comunicacionArduinoMAC.send_command(comandos_centrado[0])
        print(f"Centrando: {comandos_centrado[0]}")
    
    # Enviar comando de avance
    comunicacionArduinoMAC.send_command(comando_avance)
    print("Avanzando")

def calcular_giro(angulo_actual, angulo_deseado):
        diferencia = (angulo_deseado - angulo_actual + 360) % 360
        if diferencia <= 180:
            return "a"  # Girar a la derecha
        else:
            return "d"  # Girar a la izquierda


# Abre el video desde la URL
cap = cv2.VideoCapture(url)
#cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("No se pudo conectar a la cámara en la URL proporcionada.")
else:
    print(f"Conexión exitosa. Analizando video con cuadrícula de {rows}x{cols}...")

    # Crear ventana y trackbars
    cv2.namedWindow('Ajustes')
    cv2.createTrackbar('Canny Th1', 'Ajustes', canny_threshold1, 255, on_trackbar_change)
    cv2.createTrackbar('Canny Th2', 'Ajustes', canny_threshold2, 255, on_trackbar_change)
    cv2.createTrackbar('Dilatacion', 'Ajustes', 2, 15, on_trackbar_change)
    #maze = maze_generate(rows, cols)
    maze = [[0, 0,0],[0,1,0], [0,0,0]]
    #tablaQ=aplicarQlearning(maze)

    print(maze)
    qr_detector = cv2.QRCodeDetector()
    while True:
        count += 4
        ret, frame = cap.read()
        if not ret:
            print("Error al capturar el video.")
            break

        # Obtener valores de las trackbars
        threshold1 = cv2.getTrackbarPos('Canny Th1', 'Ajustes')
        threshold2 = cv2.getTrackbarPos('Canny Th2', 'Ajustes')
        dilatacion = cv2.getTrackbarPos('Dilatacion', 'Ajustes')

        # Analizar el frame con los umbrales ajustados
        detected_shapes, frame_with_shapes = detect_shapes_in_image(frame, rows, cols, qr_detector)
        #detected_shapes=[{"shape": "triangle","row":1,"col": 0,"cell_index": 3,"x": 100,"y": 100}]
        #moverRobot(tablaQ,cell_index,x,y)
        print(detected_shapes)
        # Dibujar la cuadrícula en el frame
        frame_with_grid = draw_grid(frame_with_shapes, rows, cols, thickness)

        frame=fill_cells(frame_with_grid,maze)
        frame = highlight_start_end(frame, rows, cols)
        # Mostrar el frame con los ajustes
        cv2.imshow('Cuadrícula con análisis', frame_with_grid)

        if count % 24 == 0:
            print("Enviando comando")
            #comunicacionArduino.send_command("w")
            mover_robot(politica, detected_shapes)

        # Presiona 'q' para salir
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        

# Libera recursos
cap.release()
cv2.destroyAllWindows()
