import matplotlib.pyplot as plt
import numpy as np
import matplotlib as mpl

# Use better font settings
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.weight'] = 'bold'
mpl.rcParams['axes.labelweight'] = 'bold'
mpl.rcParams['axes.titleweight'] = 'bold'

# Data from Table 1 in the paper - averaged across models for each method
prevention_data = {
    'MCQ': {
        'ICW': (66.6 + 60.2 + 66.5 + 66.5) / 4,
        'TRAPDOC': (89.9 + 80.4 + 74.8 + 74.8) / 4,
        'code-glyph': (84.0 + 84.6 + 76.1 + 76.1) / 4,
        'DOPE-v1': (96.3 + 88.0 + 90.3 + 90.3) / 4,
        'DOPE-v2': (99.3 + 98.7 + 91.0 + 91.0) / 4,
    },
    'T/F': {
        'ICW': (67.8 + 62.0 + 60.5 + 60.5) / 4,
        'TRAPDOC': (83.3 + 86.6 + 81.4 + 81.4) / 4,
        'code-glyph': (86.4 + 80.8 + 80.5 + 80.5) / 4,
        'DOPE-v1': (96.7 + 89.3 + 89.8 + 89.8) / 4,
        'DOPE-v2': (100.0 + 96.7 + 90.2 + 90.2) / 4,
    },
    'Long-Form': {
        'ICW': (72.1 + 64.8 + 68.0 + 68.0) / 4,
        'TRAPDOC': (83.0 + 81.8 + 76.0 + 76.0) / 4,
        'code-glyph': (87.5 + 85.8 + 78.0 + 78.0) / 4,
        'DOPE-v1': (97.6 + 88.0 + 88.0 + 88.0) / 4,
        'DOPE-v2': (100.0 + 100.0 + 86.0 + 86.0) / 4,
    }
}

detection_data = {
    'MCQ': {
        'ICW': (70.4 + 56.1 + 98.9 + 98.9) / 4,
        'TRAPDOC': (71.6 + 72.9 + 97.6 + 98.3) / 4,
        'code-glyph': (71.6 + 65.2 + 96.3 + 100.0) / 4,
        'DOPE-v1': (91.7 + 88.6 + 99.9 + 99.9) / 4,
        'DOPE-v2': (85.2 + 82.1 + 99.8 + 99.8) / 4,
    },
    'T/F': {
        'ICW': (69.9 + 62.3 + 42.3 + 39.8) / 4,
        'TRAPDOC': (82.1 + 72.8 + 54.9 + 55.8) / 4,
        'code-glyph': (70.5 + 61.3 + 48.9 + 50.2) / 4,
        'DOPE-v1': (94.7 + 91.5 + 61.4 + 61.9) / 4,
        'DOPE-v2': (84.3 + 81.0 + 58.2 + 58.0) / 4,
    },
    'Long-Form': {
        'ICW': (100.0 + 100.0 + 97.0 + 97.0) / 4,
        'TRAPDOC': (100.0 + 100.0 + 92.6 + 92.6) / 4,
        'code-glyph': (100.0 + 100.0 + 92.6 + 94.8) / 4,
        'DOPE-v1': (100.0 + 100.0 + 98.8 + 99.6) / 4,
        'DOPE-v2': (100.0 + 100.0 + 96.3 + 96.3) / 4,
    }
}

# Setup
question_types = ['MCQ', 'T/F', 'Long-Form']
methods = ['ICW', 'TRAPDOC', 'code-glyph', 'DOPE-v1', 'DOPE-v2']
colors = ['#E63946', '#F4A261', '#2A9D8F', '#264653', '#9B5DE5']

x = np.arange(len(question_types))
width = 0.15

# Chart 1: Prevention Rate
fig1, ax1 = plt.subplots(figsize=(12, 7))
for i, method in enumerate(methods):
    values = [prevention_data[qt][method] for qt in question_types]
    bars = ax1.bar(x + i * width, values, width, label=method, color=colors[i], edgecolor='black', linewidth=1)
    for bar, val in zip(bars, values):
        ax1.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{val:.1f}',
                ha='center', va='bottom', fontsize=14, fontweight='bold', color='black')

ax1.set_xlabel('Question Type', fontsize=14, fontweight='bold')
ax1.set_ylabel('Prevention Rate (%)', fontsize=14, fontweight='bold')
ax1.set_title('Prevention Rate (%) by Question Type\n(Higher is Better - Model Refuses to Answer)',
              fontsize=16, fontweight='bold', pad=15)
ax1.set_xticks(x + width * 2)
ax1.set_xticklabels(question_types, fontsize=13, fontweight='bold')
ax1.set_ylim(50, 105)  # Start from 50
ax1.tick_params(axis='y', labelsize=11)
ax1.legend(loc='upper left', fontsize=11, framealpha=0.95, edgecolor='black')
ax1.grid(axis='y', alpha=0.4, linestyle='--', linewidth=0.8)
ax1.set_axisbelow(True)
ax1.spines['top'].set_visible(False)
ax1.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('/Users/shivenagarwal/Desktop/IGSHIELD/IGSHIELD/dope_prevention_rate.pdf', bbox_inches='tight', facecolor='white')
plt.savefig('/Users/shivenagarwal/Desktop/IGSHIELD/IGSHIELD/dope_prevention_rate.png', dpi=300, bbox_inches='tight', facecolor='white')
print("Prevention rate chart saved!")
plt.close()

# Chart 2: Detection Rate
fig2, ax2 = plt.subplots(figsize=(12, 7))
for i, method in enumerate(methods):
    values = [detection_data[qt][method] for qt in question_types]
    bars = ax2.bar(x + i * width, values, width, label=method, color=colors[i], edgecolor='black', linewidth=1)
    for bar, val in zip(bars, values):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, f'{val:.1f}',
                ha='center', va='bottom', fontsize=14, fontweight='bold', color='black')

ax2.set_xlabel('Question Type', fontsize=14, fontweight='bold')
ax2.set_ylabel('Detection Rate (%)', fontsize=14, fontweight='bold')
ax2.set_title('Detection Rate (%) by Question Type\n(Higher is Better - AI Use Detected)',
              fontsize=16, fontweight='bold', pad=15)
ax2.set_xticks(x + width * 2)
ax2.set_xticklabels(question_types, fontsize=13, fontweight='bold')
ax2.set_ylim(50, 105)  # Start from 50
ax2.tick_params(axis='y', labelsize=11)
ax2.legend(loc='lower right', fontsize=11, framealpha=0.95, edgecolor='black')
ax2.grid(axis='y', alpha=0.4, linestyle='--', linewidth=0.8)
ax2.set_axisbelow(True)
ax2.spines['top'].set_visible(False)
ax2.spines['right'].set_visible(False)
plt.tight_layout()
plt.savefig('/Users/shivenagarwal/Desktop/IGSHIELD/IGSHIELD/dope_detection_rate.pdf', bbox_inches='tight', facecolor='white')
plt.savefig('/Users/shivenagarwal/Desktop/IGSHIELD/IGSHIELD/dope_detection_rate.png', dpi=300, bbox_inches='tight', facecolor='white')
print("Detection rate chart saved!")
plt.close()

print("\nDone! PDFs exported.")
