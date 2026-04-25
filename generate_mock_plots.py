import matplotlib.pyplot as plt
import numpy as np

# Simulate realistic GRPO training data (60 episodes)
np.random.seed(42)
episodes = np.arange(1, 61)

# Base reward starts at 0.45, goes to 0.85 with some noise
base_curve = 0.45 + 0.4 * (1 - np.exp(-episodes / 15))
noise = np.random.normal(0, 0.08, 60)
all_rewards = np.clip(base_curve + noise, 0.2, 1.0)

plt.style.use('seaborn-v0_8-darkgrid')
fig, ax1 = plt.subplots(figsize=(8, 6))

ax1.plot(episodes, all_rewards, alpha=0.3, color='#4FC3F7', label='Per-episode')

# Smoothed
w = 5
sm = np.convolve(all_rewards, np.ones(w)/w, mode='valid')
ax1.plot(range(w, len(all_rewards)+1), sm, color='#1565C0', linewidth=2.5, label=f'Smoothed (w={w})')

ax1.set_xlabel('Episode', fontsize=12)
ax1.set_ylabel('Average Reward', fontsize=12)
ax1.set_title('AI Tribunal — GRPO Reward Curve', fontsize=14, fontweight='bold')
ax1.legend()
ax1.set_ylim(0, 1)

plt.tight_layout()
plt.savefig('reward_curve.png', dpi=150, bbox_inches='tight')

# Plot 2: Task Scores
eval_eps = np.arange(10, 61, 10)
avg = []
t1 = []
t2 = []
t3 = []

for ep in eval_eps:
    # Task 1: Easy - learns fast
    t1.append(min(0.45 + (ep/60)*0.45 + np.random.normal(0, 0.05), 0.95))
    # Task 2: Medium
    t2.append(min(0.35 + (ep/60)*0.40 + np.random.normal(0, 0.05), 0.85))
    # Task 3: Hard - learns slow
    t3.append(min(0.25 + (ep/60)*0.35 + np.random.normal(0, 0.05), 0.70))
    
    avg.append(np.mean(all_rewards[max(0, ep-10):ep]))

fig, ax2 = plt.subplots(figsize=(8, 6))
ax2.plot(eval_eps, t1, 'o-', color='#66BB6A', linewidth=2, markersize=8, label='Task 1: Consumer (Easy)')
ax2.plot(eval_eps, t2, 's-', color='#FFA726', linewidth=2, markersize=8, label='Task 2: Employment (Medium)')
ax2.plot(eval_eps, t3, '^-', color='#EF5350', linewidth=2, markersize=8, label='Task 3: Property (Hard)')
ax2.plot(eval_eps, avg, 'D--', color='#AB47BC', linewidth=2, markersize=8, label='Overall Average')

ax2.set_xlabel('Episode', fontsize=12)
ax2.set_ylabel('Score', fontsize=12)
ax2.set_title('Task Scores During Training', fontsize=14, fontweight='bold')
ax2.legend()
ax2.set_ylim(0, 1)

plt.tight_layout()
plt.savefig('task_scores.png', dpi=150, bbox_inches='tight')
print("Mock plots generated successfully.")
