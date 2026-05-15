import numpy as np
import random

class QLearner:
    def __init__(self, state_bins=5, actions=5):
        self.q_table = {}
        self.alpha = 0.1
        self.gamma = 0.95
        self.epsilon = 0.1
        self.actions = np.linspace(0.5, 2.0, actions)  # trail ATR multiplier

    def get_state(self, regime, profit_pips, atr_pips):
        bucket = min(4, int(abs(profit_pips) / (atr_pips + 1e-9)))
        return (regime, bucket)

    def choose_action(self, state):
        if state not in self.q_table:
            self.q_table[state] = np.zeros(len(self.actions))
        if random.random() < self.epsilon:
            return random.randint(0, len(self.actions)-1)
        return np.argmax(self.q_table[state])

    def update(self, state, action, reward, next_state):
        if state not in self.q_table:
            self.q_table[state] = np.zeros(len(self.actions))
        if next_state not in self.q_table:
            self.q_table[next_state] = np.zeros(len(self.actions))
        old = self.q_table[state][action]
        next_max = np.max(self.q_table[next_state])
        self.q_table[state][action] = old + self.alpha * (reward + self.gamma * next_max - old)