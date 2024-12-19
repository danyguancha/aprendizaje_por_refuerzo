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
        self.reward_escape = 10
        self.nS = (rows * cols) ** 2 * 2
        self.nA = 4

        self.Q = self._initialize_Q_table()

    def _initialize_Q_table(self):
        """Initialize Q-table with coordinates and values."""
        Q = {}
        for i in range(self.nS):
            pol_x, pol_y, lad_x, lad_y, role = self._decode_state(i)
            Q[i] = {
                "coordinates": {"Policia": (pol_x, pol_y), "Ladron": (lad_x, lad_y), "role": role},
                "values": [0.0] * self.nA
            }
        return Q

    def _e_greedy_policy(self, state, epsilon):
        """Epsilon-greedy action selection."""
        if np.random.rand() < epsilon:
            return np.random.randint(0, self.nA)
        return np.argmax(self.Q[state]["values"])

    def _decode_state(self, state):
        """Decode state into police and thief positions, including role."""
        total_states_per_role = (self.rows * self.cols) ** 2
        role = (state // total_states_per_role) % 2
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

    def move_and_reward(self, state, action):
        """Move agents and calculate reward."""
        pol_x, pol_y, lad_x, lad_y, role = self._decode_state(state)
        moves = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right
        dx, dy = moves[action]

        if pol_x == lad_x and pol_y == lad_y:
            return state, 0, True  # Terminal state

        if role == 0:  # Police role
            new_pol_x, new_pol_y = pol_x + dx, pol_y + dy
            if not (0 <= new_pol_x < self.rows and 0 <= new_pol_y < self.cols) or self.labyrinth[new_pol_x][new_pol_y] == 1:
                return state, self.penalty_invalid, False
            pol_x, pol_y = new_pol_x, new_pol_y
            if pol_x == lad_x and pol_y == lad_y:
                return self._encode_state(pol_x, pol_y, lad_x, lad_y, role), self.reward_catch, True
            reward = -1
        else:  # Thief role
            new_lad_x, new_lad_y = lad_x + dx, lad_y + dy
            if not (0 <= new_lad_x < self.rows and 0 <= new_lad_y < self.cols) or self.labyrinth[new_lad_x][new_lad_y] == 1:
                return state, self.penalty_invalid, False
            lad_x, lad_y = new_lad_x, new_lad_y
            if lad_x == pol_x and lad_y == pol_y:
                return self._encode_state(pol_x, pol_y, lad_x, lad_y, role), -30, True
            reward = 1

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
                    role = random.randint(0, 1)
                    state = self._encode_state(pol_x, pol_y, lad_x, lad_y, role)
                    break

            cumulative_reward = 0
            done = False
            steps = 0

            while not done and steps < self.max_steps:
                action = self._e_greedy_policy(state, current_epsilon)
                next_state, reward, done = self.move_and_reward(state, action)

                self.Q[state]["values"][action] += self.alpha * (
                        reward + self.gamma * max(self.Q[next_state]["values"]) - self.Q[state]["values"][action]
                )

                state = next_state
                cumulative_reward += reward
                steps += 1

            returns.append(cumulative_reward)

        return self.Q, returns


