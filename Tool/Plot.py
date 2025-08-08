#!/usr/bin/env python3
import pandas as pd
import matplotlib.pyplot as plt
import settings

fda_data = pd.read_excel(settings.EXCEL_FILE, skiprows=[0])
medical_futurist_data = pd.read_csv(settings.MEDICAL_FUTURIST_FILE)


def Classification():
    value_counts = fda_data["Panel (Lead)"].value_counts()
    fig, ax = plt.subplots()
    bar_width = 0.4
    total_count = value_counts.sum()
    bars = ax.bar(value_counts.index, value_counts.values, width=bar_width)
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            round(yval, 1),
            ha="center",
            va="bottom",
        )
    plt.text(
        0.5,
        0.5,
        f"Total number of Devices: {total_count}",
        ha="center",
        va="center",
        transform=ax.transAxes,
    )
    plt.xticks(rotation=45, ha="right")
    plt.title("Classification of Devices based on Category")
    plt.xlabel("Category")
    plt.ylabel("Number of Devices")
    plt.tight_layout()
    plt.savefig(settings.REPORT_DIR + "Classification.png")


def Classification_by_algo():
    value_counts = medical_futurist_data["AI_Algo"].value_counts()
    fig, ax = plt.subplots()
    bar_width = 0.4
    total_count = value_counts.sum()

    bars = ax.bar(value_counts.index, value_counts.values, width=bar_width)
    for bar in bars:
        yval = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            yval,
            round(yval, 1),
            ha="center",
            va="bottom",
        )
    plt.text(
        0.5,
        0.5,
        f"Total number of Devices: {total_count}",
        ha="center",
        va="center",
        transform=ax.transAxes,
    )
    plt.xticks(rotation=45, ha="right")
    plt.title("Classification of Devices based on Algorithm(Medical Futurist Data)")
    plt.xlabel("Algorithm used")
    plt.ylabel("Number of Devices")
    plt.tight_layout()
    plt.savefig(settings.REPORT_DIR + "Classification_by_algo.png")


# Classification()
# Classification_by_algo()
