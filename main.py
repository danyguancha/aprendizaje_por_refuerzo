import requests
from movimiento_robot.mover_robot import mover_robot
from sarsa.Sarsa import aplicarSarsa
from qLearning.Q_learning import QLearningMaze

# URL de DroidCam
#url = "http://100.114.230.21:4747/video"
# URL del servidor
server_url = "http://192.168.24.176:5000" 

count = 0


# Definición de la política
politica = {
    0: [0, 0, 0, 1],  
    1: [0, 0, 0, 1], 
    2: [0, 1, 0, 0],  
    3: [0, 1, 0, 0], 
    4: [0, 0, 0, 0],  
    5: [0, 1, 0, 0], 
    6: [0, 0, 0, 1], 
    7: [0, 0, 0, 1],
    8: [1, 0, 0, 0],  
}


# Abre el video desde la URL
#maze = requests.get(f"{server_url}/maze")
try:
    response_maze = requests.get(f"{server_url}/maze", timeout=25)
    if response_maze.status_code == 200:
        maze = response_maze.json()
except requests.exceptions.RequestException as e:
    print("Error al enviar solicitud al servidor:", e)
"""maze = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0]
    ]"""
q_learning = QLearningMaze(
                labyrinth=maze,
                rows=3,
                cols=3,
                alpha=0.4,
                gamma=0.99,
                epsilon=0.4,
                max_episodes=8000,
                max_steps=5000
            )

Q_table, returns = q_learning.train()


while True:
    try:
        response = requests.get(f"{server_url}/detect_shapes", timeout=25)
        if response.status_code == 200:
            detected_shapes = response.json()
            print("Formas detectadas:", detected_shapes)
            
            for state, q_values in Q_table.items():
                pol_x, pol_y, lad_x, lad_y, rol = q_learning._decode_state(state)
                
                # Seleccionar valores de Q_table según el rol
                if rol == 0:  # Policía
                    q_values_rol = q_values[:len(Q_table)//2]  # Primera mitad
                    mover_robot(q_values_rol, detected_shapes)
                elif rol == 1:  # Ladrón
                    q_values_rol = q_values[len(Q_table)//2:]  # Segunda mitad
                    mover_robot(q_values_rol, detected_shapes)
                # Comparar las coordenadas con las formas detectadas
                for shape in detected_shapes:
                    if shape["role"] == 0 and shape['row'] == pol_x and shape['col'] == pol_y:
                        print("Se detectó al policía en las coordenadas:", pol_x, pol_y)
                    elif shape["role"] == 1 and shape['row'] == lad_x and shape['col'] == lad_y:
                        print("Se detectó al ladrón en las coordenadas:", lad_x, lad_y)
            
            # Mover los robots usando la función existente
            #mover_robot(Q_table, detected_shapes)
            
    except requests.exceptions.RequestException as e:
        print("Error al enviar solicitud al servidor:", e)

