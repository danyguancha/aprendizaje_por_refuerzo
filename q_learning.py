# pylint: disable=no-member
import cv2
import numpy as np
import random
import comunicacionArduino

# URL de DroidCam
url = "http://192.168.129.6:4747/video"

# Parámetros de la cuadrícula
rows = 3  # Número de filas
cols = 3  # Número de columnas
thickness = 1  # Grosor de las líneas

# Valores iniciales de Canny
canny_threshold1 = 50
canny_threshold2 = 150
dilatacion = 2  # Tamaño de la dilatación
count = 0

# Q-Learning
def inicializar_Q(nS, nA, tipo='ones'):
    Q = {}
    for i in range(nS):
        lista = []
        for j in range(nA):
            if tipo == 'ones':
                lista.append(1.0)
            else:
                lista.append(random.random())
        Q[i] = lista
    return Q

def e_greedy(s, Q, epsilon, nA):
    return np.argmax(Q[s]) if np.random.rand() > epsilon else np.random.randint(0, nA)

def move_and_reward(state, action, labyrinth):
    x, y = state // cols, state % cols
    moves = [(0, -1), (0, 1), (-1, 0), (1, 0)] # Arriba, abajo, izquierda, derecha
    dx, dy = moves[action]
    nx, ny = x + dx, y + dy

    if 0 <= nx < rows and 0 <= ny < cols:
        next_state = nx * cols + ny
        reward = -1 if labyrinth[nx][ny] == 0 else -20
        done = labyrinth[nx][ny] == 1 or (nx == rows - 1 and ny == cols - 1)
        return next_state, reward, done
    return state, -1, False

def q_learning(labyrinth, alpha, gamma, epsilon, nS, nA, k):
    Q = inicializar_Q(nS, nA)
    retorno = []
    for episodio in range(k):
        retorno_acumulado = 0
        # Ir al primer estado del espisodio
        state = 0
        # elegir la accion usando e-greedy
        action = e_greedy(state, Q, epsilon, nA)
        done = False        
        while not done:
            next_state, reward, done = move_and_reward(state, action, labyrinth)
            next_action = np.argmax(Q[next_state])
            retorno_acumulado += reward
            if not done:
                Q[state][action] += alpha * (reward + (gamma * Q[next_state][next_action]) - Q[state][action])
            else:
                Q[state][action] += alpha * (reward - Q[state][action])
                retorno.append(retorno_acumulado)
            state, action = next_state, next_action
    return Q, retorno

# Generar el laberinto
def maze_generate(filas, columnas):
    laberinto = [[1 for _ in range(columnas)] for _ in range(filas)]
    direcciones = [(0, -1), (0, 1), (-1, 0), (1, 0)]  # Arriba, abajo, izquierda, derecha

    def dfs(x, y):
        laberinto[x][y] = 0
        random.shuffle(direcciones)
        for dx, dy in direcciones:
            nx, ny = x + 2 * dx, y + 2 * dy
            if 0 <= nx < filas and 0 <= ny < columnas and laberinto[nx][ny] == 1:
                laberinto[x + dx][y + dy] = 0
                dfs(nx, ny)

    laberinto[0][0] = 0
    dfs(0, 0)
    laberinto[filas - 1][columnas - 1] = 0
    return laberinto

# Dibujar la cuadrícula en el frame
def draw_grid(frame, rows, cols, thickness=1):
    height, width, _ = frame.shape
    cell_height = height // rows
    cell_width = width // cols
    for i in range(1, rows):
        cv2.line(frame, (0, i * cell_height), (width, i * cell_height), (0, 255, 0), thickness)
    for j in range(1, cols):
        cv2.line(frame, (j * cell_width, 0), (j * cell_width, height), (0, 255, 0), thickness)
    return frame

# Detectar formas (círculos y triángulos) en la imagen y asociar a celdas
def detect_shapes_in_image(image, rows, cols, threshold1, threshold2,dilatacion):
    """Detecta círculos y triángulos en la imagen completa y calcula las celdas correspondientes."""
    detected_shapes = []
    height, width, _ = image.shape
    cell_height = height // rows
    cell_width = width // cols


    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Umbral inverso para detectar regiones negras
    _, thresh = cv2.threshold(gray, 50, 255, cv2.THRESH_BINARY_INV)

    # Detección de círculos con HoughCircles
    blurred = cv2.GaussianBlur(gray, (9, 9), 2)
    circles = cv2.HoughCircles(
        blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=30,
        param1=50, param2=30, minRadius=10, maxRadius=50
    )

    # Procesar círculos detectados
    if circles is not None:
        circles = np.round(circles[0, :]).astype("int")  # Convertir a enteros
        for circle in circles:
            center_x, center_y, radius = circle
            row = center_y // cell_height
            col = center_x // cell_width
            cell_index = row * cols + col  # Índice de la celda
            cell_center_x = col * cell_width + cell_width // 2
            cell_center_y = row * cell_height + cell_height // 2

            # Dibujar círculo
            cv2.circle(image, (center_x, center_y), radius, (0, 255, 0), 2)
            cv2.putText(
                image,
                f"{cell_index}",
                (center_x-10, center_y ),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
            cv2.putText(
                image,
                f"{center_x},{center_y}",
                (center_x - 30, center_y+20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (255, 255, 255),
                2
            )
            detected_shapes.append({
                "shape": "circle",
                "row": row,
                "col": col,
                "cell_index": cell_index,
                "x":center_x,
                "y":center_y,
                "cell_center_x":cell_center_x,
                "cell_center_y": cell_center_y,
            })
            image = draw_dotted_line_in_cell(image, cell_center_x, cell_center_y, cell_width, cell_height)

    bordes = cv2.Canny(gray, threshold1, threshold2)
    kernel = np.ones((dilatacion, dilatacion), np.uint8)
    bordes = cv2.dilate(bordes, kernel)
    cv2.imshow("Bordes Modificado", bordes)
    figuras, jerarquia = cv2.findContours(bordes, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
    if jerarquia is not None:
        jerarquia = jerarquia[0]
    i=0
    for contour in figuras:
        if jerarquia[i][3] == -1:
            approx = cv2.approxPolyDP(contour, 0.05 * cv2.arcLength(contour, True), True)
            area = cv2.contourArea(contour)
            if len(approx) == 3 and area >= 500 and area < 3000:  # Triángulo
                x, y, w, h = cv2.boundingRect(contour)
                center_x, center_y = x + w // 2, y + h // 2  # Centro aproximado del triángulo
                row = center_y // cell_height
                col = center_x // cell_width
                cell_index = row * cols + col  # Índice de la celda

                # Dibujar triángulo
                cv2.drawContours(image, [approx], -1, (255, 0, 0), 2)
                cv2.putText(
                    image,
                    f"{cell_index}",
                    (center_x , center_y+10 ),
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
                cell_center_x = col * cell_width + cell_width // 2
                cell_center_y = row * cell_height + cell_height // 2

                detected_shapes.append({
                    "shape": "triangle",
                    "row": row,
                    "col": col,
                    "cell_index": cell_index,
                    "x": center_x,
                    "y": center_y,
                    "cell_center_x": cell_center_x,
                    "cell_center_y": cell_center_y,
                })
                image=draw_dotted_line_in_cell(image, cell_center_x, cell_center_y, cell_width, cell_height)
                break
    return detected_shapes, image

def draw_dotted_line_in_cell(image, cell_center_x, cell_center_y, cell_width, cell_height):
    """Dibuja una línea punteada roja dentro de la celda en los ejes del centro de la celda."""
    # Definir los límites de la celda
    cell_left = cell_center_x - cell_width // 2
    cell_right = cell_center_x + cell_width // 2
    cell_top = cell_center_y - cell_height // 2
    cell_bottom = cell_center_y + cell_height // 2

    # Dibujar línea punteada roja en el eje horizontal
    for x in range(cell_left, cell_right, 10):  # Incremento para punteado
        cv2.line(image, (x, cell_center_y), (x + 5, cell_center_y), (0, 0, 255), 1)

    # Dibujar línea punteada roja en el eje vertical
    for y in range(cell_top, cell_bottom, 10):  # Incremento para punteado
        cv2.line(image, (cell_center_x, y), (cell_center_x, y + 5), (0, 0, 255), 1)
    return image

def fill_cells(frame, matrix, alpha):
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
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 0), -1)

    # Aplicar transparencia a los rectángulos negros
    cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)

    return frame

def mover_robot(politica, posicionesRobot):
    
    # Verificar que haya robots detectados
    if not posicionesRobot:
        print("No se detectaron robots.")
        return

    

    # Obtener la posición actual del primer robot detectado
    robot_actual = posicionesRobot[0]  # Usar el primer robot detectado
    posicionActual = robot_actual["cell_index"]

    mayor_valor = max(politica[posicionActual])
    print(mayor_valor)
    print('Posicion Actual: ', posicionActual)
    print("Posición actual según política:", politica[posicionActual])
    if politica[posicionActual][3] == mayor_valor:  # Movimiento hacia adelante
        print("Adelante")
        comunicacionArduino.send_command("w")
    elif politica[posicionActual][2] == mayor_valor: # Movimiento hacia la izquierda
        print('Izquierda')
        comunicacionArduino.send_command('a')
    elif politica[posicionActual][1] == mayor_valor: # Movimiento hacia atras
        print('Abajo')
        comunicacionArduino.send_command('s')
    elif politica[posicionActual][0] == mayor_valor: # Movimiento hacia la derecha
        print('Derecha')
        comunicacionArduino.send_command('d')



    # Leer la acción desde la política

    
# Configurar el video y la simulación
cap = cv2.VideoCapture(url)
if not cap.isOpened():
    print("No se pudo conectar a la cámara.")
else:
    print(f"Conexión exitosa. Analizando video con cuadrícula de {rows}x{cols}...")
    cv2.namedWindow('Ajustes')
    cv2.createTrackbar('Canny Th1', 'Ajustes', canny_threshold1, 255, lambda x: None)
    cv2.createTrackbar('Canny Th2', 'Ajustes', canny_threshold2, 255, lambda x: None)

    maze = maze_generate(rows, cols)
    alpha = 0.4
    gamma = 0.999
    epsilon = 0.1
    nS = rows * cols 
    nA = 4
    k = 3000
    Q, retorno = q_learning(maze, alpha, gamma, epsilon, nS, nA, k)

    state = 0
    while True:
        count += 1
        ret, frame = cap.read()
        if not ret:
            print("Error al capturar el video.")
            break

        frame = draw_grid(frame, rows, cols, thickness)
        detected_shapes, frame_with_shapes = detect_shapes_in_image(frame, rows, cols, canny_threshold1, canny_threshold2, dilatacion)
        #frame_with_grid = draw_grid(frame_with_shapes, rows, cols, thickness)

        frame=fill_cells(frame,maze,alpha)
        #frame = highlight_start_end(frame, rows, cols)
        # Mostrar el frame con los ajustes
        cv2.imshow('Cuadrícula con análisis', frame)

        """for shape in detected_shapes:
            state = shape["cell_index"]
            action = np.argmax(Q[state])
            next_state, _, done = move_and_reward(state, action, maze)
            state = next_state if not done else 0  # Reiniciar si se alcanza la meta"""

        #cv2.imshow('Cuadrícula con análisis', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

        if count % 24 == 0:
            mover_robot(Q, detected_shapes)


cap.release()
cv2.destroyAllWindows()
