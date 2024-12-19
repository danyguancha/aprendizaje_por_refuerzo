import numpy as np
import random
import json


# Q-Learning
def inicializar_Q(nS, nA, tipo='ones'):
    Q = {}
    for i in range(nS):
        if tipo == 'ones':
            Q[i] = [1.0] * nA
        else:
            Q[i] = [random.random() for _ in range(nA)]
    return Q

def e_greedy(s, Q, epsilon, nA):
    if np.random.rand() >= epsilon:
        accion = np.argmax(Q[s])
    else:
        accion = np.random.randint(0, nA)
    return accion

def move_and_reward(state, action, labyrinth, rows, cols):
    x, y = state // cols, state % cols
    moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # Arriba, abajo, izquierda, derecha
    dx, dy = moves[action]
    nx, ny = x + dx, y + dy

    if 0 <= nx < rows and 0 <= ny < cols:  # Verificar límites del laberinto
        next_state = nx * cols + ny
        if labyrinth[nx][ny] == 1:  # Celda bloqueada
            return state, -20, False
        elif nx == rows - 1 and ny == cols - 1:  # Meta
            return next_state, 50, True
        else:  # Movimiento válido
            return next_state, 0, False
    return state, -1, False  # Movimiento inválido



def convertir_a_politica(Q_table):
    """
    Convierte una tabla Q en una política binaria (0 y 1).
    
    Parameters:
        Q_table (dict): Tabla Q con estados como claves y un diccionario con valores Q.
    
    Returns:
        dict: Política derivada de la tabla Q.
    """
    politica = {}
    for estado, data in Q_table.items():
        valores = data["values"]  # Extraemos los valores Q del estado
        
        # Verificar si todos los valores son iguales
        if len(set(valores)) == 1:  # Todos los valores Q son iguales
            # Asignar 0 a todas las acciones (sin preferencia)
            politica[estado] = [0] * len(valores)
        else:
            # Obtener el índice del valor máximo
            max_valor = max(valores)
            indice_max = valores.index(max_valor)
            
            # Crear una lista de ceros del mismo tamaño que los valores
            politica_estado = [0] * len(valores)
            # Colocar un 1 en la posición de la acción óptima
            politica_estado[indice_max] = 1
            
            # Guardar la política para este estado
            politica[estado] = politica_estado
    
    return politica
def actualizar_tabla_Q_con_politica(Q_table, politica):
    """
    Actualiza la tabla Q reemplazando los valores por la política derivada (ceros y unos).

    Parameters:
        Q_table (dict): Tabla Q original.
        politica (dict): Política derivada, donde cada estado tiene acciones con 0 y 1.

    Returns:
        dict: Tabla Q actualizada con valores según la política.
    """
    Q_actualizada = {}
    for estado, datos in Q_table.items():
        # Obtenemos la política para este estado
        valores_politica = politica.get(estado, [0] * len(datos["values"]))
        
        # Creamos una nueva entrada con los valores de política
        Q_actualizada[estado] = {
            "coordinates": datos["coordinates"],
            "values": valores_politica
        }
    
    return Q_actualizada


def guardar_tabla(diccionario, nombre_archivo):
    ruta = 'tablas/'+nombre_archivo
    try:
        with open(ruta, 'w') as archivo:
            json.dump(diccionario, archivo, indent=4)
    except Exception as e:
        print(f"Error al guardar los datos: {e}")

"""def leer_tabla(nombre_archivo):
    ruta = 'tablas/'+nombre_archivo
    try:
        with open(ruta, 'r') as archivo:
            datos = json.load(archivo)
            return datos
    except FileNotFoundError:
        print(f"Error: El archivo {ruta} no existe")
        return None
    except json.JSONDecodeError:
        print(f"Error: El archivo {ruta} no tiene un formato JSON válido")
        return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None"""
    

def leer_tabla(nombre_archivo):
    ruta = 'tablas/'+nombre_archivo
    try:
        with open(ruta, 'r') as archivo:
            datos = json.load(archivo)
            # Convertir las claves a enteros
            datos_convertidos = {int(estado): valor for estado, valor in datos.items()}
            return datos_convertidos
    except FileNotFoundError:
        print(f"Error: El archivo {ruta} no existe")
        return None
    except json.JSONDecodeError:
        print(f"Error: El archivo {ruta} no tiene un formato JSON válido")
        return None
    except Exception as e:
        print(f"Error al leer el archivo: {e}")
        return None
