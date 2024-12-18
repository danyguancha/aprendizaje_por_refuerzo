
import numpy as np
import random
import matplotlib.pyplot as plt


class QLearningMaze:
    def __init__(self, labyrinth, rows, cols, alpha=0.4, gamma=0.99, epsilon=0.1, max_episodes=1000, max_steps=200):
        self.labyrinth = labyrinth
        self.rows = rows
        self.cols = cols
        self.alpha = alpha
        self.gamma = gamma
        self.epsilon = epsilon
        self.max_episodes = max_episodes
        self.max_steps = max_steps

        self.penalty_invalid = -10
        self.reward_catch = 100
        self.reward_escape = 10  # Recompensa mayor para el ladrón al alejarse
        self.nS = (rows * cols) ** 2 * 2  # Duplicar estados por roles
        self.nA = 4  # Acciones: arriba, abajo, izquierda, derecha

        self.Q = self._initialize_Q_table()

    def _initialize_Q_table(self):
        """Initialize Q-table with zeros."""
        Q = {}
        for i in range(self.nS):
            Q[i] = [0.0] * self.nA
        return Q

    def _e_greedy_policy(self, state, epsilon):
        """Epsilon-greedy action selection."""
        if np.random.rand() < epsilon:
            return np.random.randint(0, self.nA)
        return np.argmax(self.Q[state])

    def _decode_state(self, state):
        """Decode state into police and thief positions, including role."""
        total_states_per_role = (self.rows * self.cols) ** 2
        role = (state // total_states_per_role) % 2  # 0: police, 1: thief
        state %= total_states_per_role
        lad_y = state % self.cols
        lad_x = (state // self.cols) % self.rows
        pol_y = (state // (self.cols * self.rows)) % self.cols
        pol_x = state // (self.cols * self.rows * self.cols)
        return pol_x, pol_y, lad_x, lad_y, role

    def _encode_state(self, pol_x, pol_y, lad_x, lad_y, role):
        """Encode police and thief positions into a single state, including role."""
        base_state = (pol_x * self.cols * self.rows * self.cols +
                      pol_y * self.rows * self.cols +
                      lad_x * self.cols + lad_y)
        total_states_per_role = (self.rows * self.cols) ** 2
        return base_state + role * total_states_per_role

    def _distance(self, x1, y1, x2, y2):
        """Calculate Manhattan distance between two points."""
        return abs(x1 - x2) + abs(y1 - y2)

    def move_and_reward(self, state, action):
        """Move agents and calculate reward."""
        pol_x, pol_y, lad_x, lad_y, role = self._decode_state(state)
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
        dx, dy = moves[action]

        # Check if thief and police are already in the same position
        if pol_x == lad_x and pol_y == lad_y:
            return state, 0, True  # No further moves, terminal state

        if role == 0:  # Police role
            new_pol_x, new_pol_y = pol_x + dx, pol_y + dy

            # Check for invalid movement (boundaries or walls)
            if not (0 <= new_pol_x < self.rows and 0 <= new_pol_y < self.cols) or self.labyrinth[new_pol_x][new_pol_y] == 1:
                reward = self.penalty_invalid  # Penalize invalid moves
                return state, reward, False

            # Update police position
            pol_x, pol_y = new_pol_x, new_pol_y

            # Check if the police caught the thief
            if pol_x == lad_x and pol_y == lad_y:
                reward = self.reward_catch
                return self._encode_state(pol_x, pol_y, lad_x, lad_y, role), reward, True

            # Default reward for valid moves
            reward = -1  # Penalización leve para que busque al ladrón

        else:  # Thief role
            new_lad_x, new_lad_y = lad_x + dx, lad_y + dy

            # Check for invalid movement (boundaries or walls)
            if not (0 <= new_lad_x < self.rows and 0 <= new_lad_y < self.cols) or self.labyrinth[new_lad_x][new_lad_y] == 1:
                reward = self.penalty_invalid  # Penalize invalid moves
                return state, reward, False


            # Update thief position
            lad_x, lad_y = new_lad_x, new_lad_y
            if lad_x == pol_x and lad_y == lad_y:
                reward = -30
                return self._encode_state(pol_x, pol_y, lad_x, lad_y, role), reward, True

            # Default reward for valid moves
            reward = 1
        # Return new state and reward
        return self._encode_state(pol_x, pol_y, lad_x, lad_y, role), reward, False


    def train(self):
        """Train the Q-learning agent."""
        returns = []
        current_epsilon = self.epsilon

        for episode in range(self.max_episodes):
            current_epsilon = max(0.01, current_epsilon * 0.99)

            while True:
                pol_x, pol_y = random.randint(0, self.rows - 1), random.randint(0, self.cols - 1)
                lad_x, lad_y = random.randint(0, self.rows - 1), random.randint(0, self.cols - 1)
                if (self.labyrinth[pol_x][pol_y] == 0 and self.labyrinth[lad_x][lad_y] == 0
                        and (pol_x != lad_x or pol_y != lad_y)):
                    role = random.randint(0, 1)  # Randomly assign role (0: police, 1: thief)
                    state = self._encode_state(pol_x, pol_y, lad_x, lad_y, role)
                    break

            cumulative_reward = 0
            done = False
            steps = 0

            while not done and steps < self.max_steps:
                action = self._e_greedy_policy(state, current_epsilon)
                next_state, reward, done = self.move_and_reward(state, action)

                self.Q[state][action] += self.alpha * (
                        reward + self.gamma * max(self.Q[next_state]) - self.Q[state][action]
                )

                state = next_state
                cumulative_reward += reward
                steps += 1

            returns.append(cumulative_reward)
        return self.Q, returns


# Ejemplo de uso
def main():
    maze = [
        [0, 0, 0],
        [0, 1, 0],
        [0, 0, 0]
    ]

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

    print("\nSample Q-Table Values (State, Police, Thief, Role, Q-Values):")
    for state, q_values in Q_table.items():
        pol_x, pol_y, lad_x, lad_y, role = q_learning._decode_state(state)
        role_name = "Police" if role == 0 else "Thief"
        print(f"State {state}: Police=({pol_x}, {pol_y}), Thief=({lad_x}, {lad_y}), Role={role_name}, Q-Values={q_values}")


if __name__ == "__main__":
    main()