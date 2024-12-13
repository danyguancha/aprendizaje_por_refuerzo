# pylint: disable=no-member
import cv2
import numpy as np
import random
import matplotlib.pyplot as plt


# URL y parámetros de la cuadrícula
url = "http://192.168.1.108:4747/video"
rows, cols, thickness = 7, 7, 1
canny_threshold1, canny_threshold2 = 50, 150

# Inicializar Q-Table
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

# Política e-greedy
def e_greedy(s, Q, epsilon, nA):
    return np.argmax(Q[s]) if np.random.rand() > epsilon else np.random.randint(0, nA)

# Movimiento y recompensa
def move_and_reward(state, action, labyrinth):
    x, y = state // cols, state % cols
    moves = [(0, 1), (0, -1), (1, 0), (-1, 0)]
    dx, dy = moves[action]
    nx, ny = x + dx, y + dy

    if 0 <= nx < rows and 0 <= ny < cols:
        next_state = nx * cols + ny
        reward = -1 if labyrinth[nx][ny] == 0 else -20
        done = labyrinth[nx][ny] == 1 or (nx == rows - 1 and ny == cols - 1)
        return next_state, reward, done
    return state, -1, False

# Algoritmo Q-Learning
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
    direcciones = [(0, 1), (1, 0), (0, -1), (-1, 0)]

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

# Resaltar estado actual del agente
def highlight_state(frame, state):
    height, width, _ = frame.shape
    cell_height = height // rows
    cell_width = width // cols
    x = (state % cols) * cell_width
    y = (state // cols) * cell_height
    overlay = frame.copy()
    cv2.rectangle(overlay, (x, y), (x + cell_width, y + cell_height), (255, 0, 0), -1)
    cv2.addWeighted(overlay, 0.3, frame, 0.7, 0, frame)
    return frame

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
        ret, frame = cap.read()
        if not ret:
            print("Error al capturar el video.")
            break

        frame = draw_grid(frame, rows, cols, thickness)
        frame = highlight_state(frame, state)
        cv2.imshow('Cuadrícula con análisis', frame)

        action = np.argmax(Q[state])
        next_state, _, done = move_and_reward(state, action, maze)
        state = next_state if not done else 0  # Reiniciar si se alcanza la meta

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()



""""def q_learning(labyrinth, alpha, gamma, epsilon, episodes):
    nS, nA = rows * cols, 4
    Q = inicializar_Q(nS, nA)

    for ep in range(episodes):
        s = 0  # Estado inicial
        done = False
        while not done:
            a = e_greedy(s, Q, epsilon, nA)
            next_s, reward, done = move_and_reward(s, a, labyrinth)
            Q[s, a] += alpha * (reward + gamma * np.max(Q[next_s]) - Q[s, a])
            s = next_s
    return Q"""



"""
def mover_robot(politica, posicionesRobot, maze):

    Mueve el robot considerando las restricciones del laberinto.
    
    Args:
    - politica (dict): Diccionario que define los movimientos posibles
    - posicionesRobot (list): Lista de posiciones detectadas del robot
    - maze (list of lists): Matriz que representa el laberinto (0 es camino, 1 es pared)
    
    if not posicionesRobot:  # Si no se detectan formas, no hacer nada
        print("No se detectó posición del robot.")
        return

    robot_actual = posicionesRobot[0]  # Tomar la posición del primer robot detectado
    posicionActual = robot_actual["cell_index"]
    rows = len(maze)
    cols = len(maze[0])

    print(rows, cols)

    # Función para verificar si un movimiento es válido
    def movimiento_valido(nueva_fila, nueva_columna):
        # Verificar si la nueva posición está dentro del tablero y no es una pared
        return (0 <= nueva_fila < rows and 
                0 <= nueva_columna < cols and 
                maze[nueva_fila][nueva_columna] == 0)


    # Convertir la posición actual en coordenadas de fila y columna
    fila_actual = posicionActual // cols
    columna_actual = posicionActual % cols

    print("Posición actual:", politica[posicionActual])

    # Movimiento hacia adelante
    if politica[posicionActual][3] == 1:
        nueva_fila = fila_actual 
        nueva_columna = columna_actual + 1
        if movimiento_valido(nueva_fila, nueva_columna):
            print("Adelante")
            comunicacionArduino.send_command("w")
            calibrar_robot(robot_actual)
        else:
            calibrar_robot(robot_actual)
            print("Movimiento hacia adelante bloqueado")

    # Movimiento hacia izquierda
    elif politica[posicionActual][2] == 1:
        nueva_fila = fila_actual
        nueva_columna = columna_actual - 1  # Hacia la izquierda
        if movimiento_valido(nueva_fila, nueva_columna):
            print("Izquierda")
            comunicacionArduino.send_command("a")
            calibrar_robot(robot_actual)
        else:
            #print("Movimiento hacia la izquierda bloqueado")
            calibrar_robot(robot_actual)

    # Movimiento hacia atras
    elif politica[posicionActual][1] == 1:
        nueva_fila = fila_actual + 1  # Hacia abajo
        nueva_columna = columna_actual
        if movimiento_valido(nueva_fila, nueva_columna):
            print("Abajo")
            comunicacionArduino.send_command("s")
            calibrar_robot(robot_actual)
        else:
            #print("Movimiento hacia abajo bloqueado")
            calibrar_robot(robot_actual)

    # Movimiento hacia la derecha
    elif politica[posicionActual][0] == 1:
        nueva_fila = fila_actual
        nueva_columna = columna_actual + 1  # Hacia la derecha
        if movimiento_valido(nueva_fila, nueva_columna):
            print("Derecha")
            comunicacionArduino.send_command("d")
            calibrar_robot(robot_actual)
        else:
            print("Movimiento hacia la derecha bloqueado")

"""





def mover_robot(politica, posicionesRobot):
    """
    Controla el movimiento del robot basado en la política y la posición actual detectada.
    """
    if not posicionesRobot:  # Si no se detectan posiciones, no hacer nada
        print("No se detectó posición del robot.")
        return

    robot_actual = posicionesRobot[0]  # Tomar la posición del primer robot detectado
    posicionActual = robot_actual["cell_index"]
    angulo = robot_actual["angle"]

    # Función para calcular el giro hacia el ángulo más cercano
    def calcular_giro(angulo_actual, angulo_deseado):
        diferencia = (angulo_deseado - angulo_actual + 360) % 360
        if diferencia <= 180:
            return "d"  # Girar a la derecha
        else:
            return "a"  # Girar a la izquierda

    # Comprobar las direcciones en la política
    if politica[posicionActual][3] == 1 and (angulo < 10 or angulo > 350):
        print("Adelante")
        comunicacionArduino.send_command("w")
    elif politica[posicionActual][2] == 1 and (angulo > 260 and angulo < 280):  # Movimiento hacia Abajo
        print("Abajo")
        comunicacionArduino.send_command("w")
    elif politica[posicionActual][1] == 1 and (angulo > 160 and angulo < 200):  # Movimiento hacia la Izquierda
        print("Izquierda")
        comunicacionArduino.send_command("w")  # Avanzar
    elif politica[posicionActual][0] == 1 and (angulo > 70 and angulo < 110):  # Movimiento hacia la Arriba
        print("Arriba")
        comunicacionArduino.send_command("w")  # Avanzar
    else:
        print("No hay camino, calculando giro hacia el ángulo más cercano")

        # Ángulos objetivo para cada dirección
        angulos_objetivo = {
            3: 0,   # Adelante
            2: 270, # Abajo
            1: 180, # Izquierda
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
            comunicacionArduino.send_command(comando_giro)
            print(f"Girando hacia el ángulo más cercano: {angulo_mas_cercano}, comando: {comando_giro}")
        else:
            print("No hay ángulo válido en la política.")


